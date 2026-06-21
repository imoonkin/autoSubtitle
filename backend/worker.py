"""后台字幕处理线程。 """
import os
import queue
import pyaudiowpatch as pyaudio
from PySide6.QtCore import QThread, Signal

from backend.audio_processor import AudioSliceProcessor, TARGET_SAMPLE_RATE
from backend.asr_client import AsrClient

# 🌟 引入拆分后的服务管理器与客户端翻译器
from backend.llm_server import LlamaServerManager
from backend.translate_client import TranslateClient

class SubtitleWorker(QThread):
    TextReady = Signal(str)
    StatusChanged = Signal(str)

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.running = False

    def run(self):
        self.running = True
        self.StatusChanged.emit("正在拉起本地大模型引擎...")
        
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        models_config = self.config.get("models", {})
        vad_config = models_config.get("vad", {})
        asr_config = models_config.get("asr", {})
        trans_config = models_config.get("translate", {})

        # ==================== 1. 初始化大模型后台守护进程 ====================
        self.asr_server = LlamaServerManager(current_dir, asr_config,"asr_server")
        self.asr_server.start(threads=asr_config.get("threads"))

        self.translate_server = LlamaServerManager(current_dir, trans_config,"translate_server")
        self.translate_server.start(threads=trans_config.get("threads"))

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
            self.StatusChanged.emit(f"硬件驱动挂载失败: {str(e)}")
            self.asr_server.stop() 
            self.translate_server.stop() 
            p.terminate()
            return

        # ==================== 3. 实例化功能业务组件 ====================
        try:
            processor = AudioSliceProcessor(current_dir, hw_rate, vad_config)
            asr_processor = AsrClient(asr_config)
            translator = TranslateClient(trans_config) # 纯 Client，传入配置即可
        except Exception as e:
            print(f"业务组件初始化失败: {str(e)}")
            self.StatusChanged.emit(f"业务引擎拉起失败: {str(e)}")
            self.asr_server.stop()
            self.translate_server.stop()
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
        self.StatusChanged.emit("🎤 正在监听系统声音...")

        # ==================== 5. 核心管道流水线 ====================
        try:
            while self.running and stream.is_active():
                try:
                    chunk = audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                payload = processor.process_chunk(chunk)
                if payload is not None:
                    asr_result = asr_processor.transcribe(payload,TARGET_SAMPLE_RATE)
                    if not asr_result:
                        continue

                    translated_text = translator.translate(asr_result)
                    
                    final_output = f"识别: {asr_result} \n翻译: {translated_text}"
                    print(final_output)
                    self.TextReady.emit(translated_text)

        except Exception as e:
            self.StatusChanged.emit(f"字幕管道流异常: {str(e)}")
        finally:
            # ==================== 6. 严丝合缝的安全清理 ====================
            stream.stop_stream()
            stream.close()
            p.terminate()
            # 彻底毁灭后台大模型进程
            self.asr_server.stop()
            self.translate_server.stop()
            self.StatusChanged.emit("服务已停止。")

    def stop(self):
        self.running = False
