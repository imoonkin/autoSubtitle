import os
import queue
import sys
import pyaudiowpatch as pyaudio
import onnxruntime as ort
import modelServer
import callModel
from audio_processor import AudioSliceProcessor, TARGET_SAMPLE_RATE
from PySide6.QtCore import QThread, Signal

# 🌟 兼容 Python 3.11 以下版本
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

def load_config():
    """加载 TOML 配置文件"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "config.toml")
    
    if not os.path.exists(config_path):
        print(f"❌ 未找到配置文件: {config_path}，请检查！")
        exit(1)
         
    with open(config_path, "rb") as f:
        return tomllib.load(f)

def init_resources(config):
    # 🌟 从 TOML 中提取所有模型配置
    models_config = config.get("models", {})
    llm_config = models_config.get("llm", {})
    vad_config = config.get("models", {}).get("vad", {})

    # 1. 启动核心大模型服务器 (将配置字典传入)
    if not modelServer.start_llama_server(llm_config):
        print("❌ 核心服务器未能拉起，程序退出。")
        exit(1)

    # 2. 拉起 VAD 引擎
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf_model_path = vad_config.get("model_path", "models/silero_vad.onnx")
    
    if not os.path.isabs(conf_model_path):
        model_path = os.path.abspath(os.path.join(current_dir, conf_model_path))
    else:
        model_path = conf_model_path
    
    try:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"未找到 VAD 模型文件: {model_path}")
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        ort_session = ort.InferenceSession(model_path, sess_options=opts, providers=['CPUExecutionProvider'])
        print(f"🧠 [Silero ONNX v5] 成功加载模型: {model_path}")
    except Exception as e:
        print(f"❌ VAD 模型拉起失败: {e}")
        exit(1)

    # 3. 初始化 WASAPI 环回设备
    p = pyaudio.PyAudio()
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
        print(f"🎤 [WASAPI 环回] 成功捕获系统声音设备: {default_speakers['name']}")
        hardware_sample_rate = int(default_speakers["defaultSampleRate"])
        print(f"🎛️ 声卡硬件原生采样率: {hardware_sample_rate}Hz")
    except Exception as e:
        print(f"❌ 无法初始化 WASAPI 设备: {e}")
        p.terminate()
        exit(1)
        
    return p, ort_session, default_speakers, hardware_sample_rate


class SubtitleWorker(QThread):
    # 🌟 定义两个信号：一个传字幕文本，一个传状态更新
    text_ready = Signal(str)
    status_changed = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = False

    def run(self):
        self.running = True
        self.status_changed.emit("正在拉起模型服务与音频设备...")
        
        # 1. 载入资源 (原 init_resources 逻辑)
        try:
            from backend import init_resources # 假设你的初始化函数还在
            p, ort_session, default_speakers, hardware_sample_rate = init_resources(self.config)
        except Exception as e:
            self.status_changed.emit(f"错误: {str(e)}")
            return

        audio_queue = queue.Queue()
        def audio_callback(in_data, frame_count, time_info, status_flags):
            audio_queue.put(in_data)
            return (None, pyaudio.paContinue)

        hardware_chunk_size = int(hardware_sample_rate * 0.1)
        stream = p.open(
            format=pyaudio.paInt16, channels=1, rate=hardware_sample_rate,
            input=True, input_device_index=default_speakers["index"],
            frames_per_buffer=hardware_chunk_size, stream_callback=audio_callback
        )
        
        vad_config = self.config.get("models", {}).get("vad", {})
        processor = AudioSliceProcessor(ort_session, hardware_sample_rate, vad_config)
        llm_config = self.config.get("models", {}).get("llm", {})
        
        stream.start_stream()
        self.status_changed.emit("🎤 正在监听系统声音...")

        # 2. 主循环
        while self.running and stream.is_active():
            try:
                chunk = audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            
            payload_bytes = processor.process_chunk(chunk)
            if payload_bytes:
                final_text = callModel.process_and_translate_audio(
                    payload_bytes, TARGET_SAMPLE_RATE, llm_config=llm_config
                )
                if final_text:
                    # 🌟 关键：通过信号发送给 GUI 渲染
                    self.text_ready.emit(final_text)

        # 3. 释放资源
        stream.stop_stream()
        stream.close()
        p.terminate()
        self.status_changed.emit("服务已停止。")

    def stop(self):
        self.running = False


