"""音频设备与模型初始化。

从原 coordinator.py 中提取，不依赖 Qt，纯业务逻辑。
"""
import os
import pyaudiowpatch as pyaudio
import onnxruntime as ort
import modelServer


def init_resources(config: dict):
    """初始化模型服务 + VAD 引擎 + WASAPI 环回设备。

    Returns: (pyaudio_instance, ort_session, default_speakers, hardware_sample_rate)
    """
    models_config = config.get("models", {})
    llm_config = models_config.get("llm", {})
    vad_config = models_config.get("vad", {})

    # 1. 启动 llama-server
    if not modelServer.start_llama_server(llm_config):
        print("❌ 核心服务器未能拉起，程序退出。")
        exit(1)

    # 2. 加载 Silero VAD 模型
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conf_model_path = vad_config.get("model_path", "models/silero_vad.onnx")

    model_path = (
        os.path.abspath(os.path.join(current_dir, conf_model_path))
        if not os.path.isabs(conf_model_path)
        else conf_model_path
    )

    if not os.path.exists(model_path):
        print(f"❌ 未找到 VAD 模型文件: {model_path}")
        exit(1)

    opts = ort.SessionOptions()
    opts.inter_op_num_threads = 1
    opts.intra_op_num_threads = 1
    ort_session = ort.InferenceSession(
        model_path, sess_options=opts, providers=["CPUExecutionProvider"]
    )
    print(f"🧠 [Silero ONNX v5] 成功加载模型: {model_path}")

    # 3. 初始化 WASAPI 环回
    p = pyaudio.PyAudio()
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = p.get_device_info_by_index(
            wasapi_info["defaultOutputDevice"]
        )
        if not default_speakers["isLoopbackDevice"]:
            for loopback in p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
        print(f"🎤 [WASAPI] 捕获设备: {default_speakers['name']}")
        hardware_sample_rate = int(default_speakers["defaultSampleRate"])
        print(f"🎛️ 采样率: {hardware_sample_rate}Hz")
    except Exception as e:
        print(f"❌ WASAPI 初始化失败: {e}")
        p.terminate()
        exit(1)

    return p, ort_session, default_speakers, hardware_sample_rate
