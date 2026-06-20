"""后台字幕处理线程。 """
import os
import queue
import pyaudiowpatch as pyaudio
from PySide6.QtCore import QThread, Signal

from backend.audio_processor import AudioSliceProcessor, TARGET_SAMPLE_RATE
from backend.asr_processor import AsrProcessor

# 🌟 引入拆分后的服务管理器与客户端翻译器
from backend.translator_server import LlamaServerManager
from backend.translator import HttpTranslator

class SubtitleWorker(QThread):
    text_ready = Signal(str)
    status_changed = Signal(str)

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.running = False

    def run(self):
        self.running = True
        self.status_changed.emit("正在拉起本地大模型引擎...")
        
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        models_config = self.config.get("models", {})
        vad_config = models_config.get("vad", {})
        asr_config = models_config.get("asr", {})
        trans_config = models_config.get("translate", {})

        # ==================== 1. 初始化大模型后台守护进程 ====================
        # 使用实例属性来持有，避免 run() 栈帧释放后被意外 GC
        self._server_manager = LlamaServerManager(current_dir, trans_config)
        # 如果你想通过配置文件来控制是否拉起本地 Server，可以在这里加个 if 判断
        self._server_manager.start(threads=trans_config.get("threads", 4))

        # ==================== 2. 初始化 WASAPI 环回设备 ====================
        p = pyaudio.PyAudio()
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            if not speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if speakers["name"] in loopback["name"]:
                        speakers = loopback
                        break
            hw_rate = int(speakers["defaultSampleRate"])
        except Exception as e:
            self.status_changed.emit(f"硬件驱动挂载失败: {str(e)}")
            self._server_manager.stop() # 记得同步关闭刚才拉起的 server
            p.terminate()
            return

        # ==================== 3. 实例化功能业务组件 ====================
        try:
            processor = AudioSliceProcessor(current_dir, hw_rate, vad_config)
            asr_processor = AsrProcessor(current_dir, asr_config, TARGET_SAMPLE_RATE)
            translator = HttpTranslator(trans_config) # 纯 Client，传入配置即可
        except Exception as e:
            print(f"业务组件初始化失败: {str(e)}")
            self.status_changed.emit(f"业务引擎拉起失败: {str(e)}")
            self._server_manager.stop()
            p.terminate()
            return

        # ==================== 4. 环回捕获流准备 ====================
        audio_queue = queue.Queue()
        def audio_callback(in_data, frame_count, time_info, status_flags):
            audio_queue.put(in_data)
            return (None, pyaudio.paContinue)

        chunk_size = int(hw_rate * 0.1)
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=hw_rate,
            input=True,
            input_device_index=speakers["index"],
            frames_per_buffer=chunk_size,
            stream_callback=audio_callback,
        )

        stream.start_stream()
        self.status_changed.emit("🎤 正在监听系统声音...")

        # ==================== 5. 核心管道流水线 ====================
        try:
            while self.running and stream.is_active():
                try:
                    chunk = audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                payload = processor.process_chunk(chunk)
                if payload is not None:
                    asr_result = asr_processor.transcribe(payload)
                    if not asr_result:
                        continue

                    translated_text = translator.translate(asr_result)
                    
                    final_output = f"识别: {asr_result} \n翻译: {translated_text}"
                    print(final_output)
                    self.text_ready.emit(final_output)

        except Exception as e:
            self.status_changed.emit(f"字幕管道流异常: {str(e)}")
        finally:
            # ==================== 6. 严丝合缝的安全清理 ====================
            stream.stop_stream()
            stream.close()
            p.terminate()
            # 彻底毁灭后台大模型进程
            self._server_manager.stop()
            self.status_changed.emit("服务已停止。")

    def stop(self):
        self.running = False
