"""音频设备与模型初始化。 """
import os
import pyaudiowpatch as pyaudio
import onnxruntime as ort
import sherpa_onnx
import onnxruntime_genai as og


def init_resources(config: dict):
    """
    初始化 VAD 引擎、Sherpa-ONNX(SenseVoice)、ONNXRuntime-GenAI(NLLB) 及 WASAPI 环回设备。
    """
    models_config = config.get("models", {})
    vad_config = models_config.get("vad", {})
    asr_config = models_config.get("asr", {})       # 新增：ASR 配置
    trans_config = models_config.get("translate", {}) # 新增：翻译配置

    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ==================== 1. 加载 Silero VAD 模型 ====================
    conf_model_path = vad_config.get("model_path", "models/silero_vad.onnx")
    vad_model_path = (
        os.path.abspath(os.path.join(current_dir, conf_model_path))
        if not os.path.isabs(conf_model_path)
        else conf_model_path
    )
    if not os.path.exists(vad_model_path):
        print(f"❌ 未找到 VAD 模型文件: {vad_model_path}")
        exit(1)

    opts = ort.SessionOptions()
    opts.inter_op_num_threads = 1
    opts.intra_op_num_threads = 1
    ort_session = ort.InferenceSession(
        vad_model_path, sess_options=opts, providers=["CPUExecutionProvider"]
    )
    print(f"🧠 [Silero ONNX v5] 成功加载 VAD 模型: {vad_model_path}")

    # ==================== 2. 加载 Sherpa-ONNX (SenseVoice ASR) ====================
    # SenseVoice 通常是非流式模型，需要 model, tokens 等文件路径
    sensevoice_model = asr_config.get("model_path", "models/sensevoice-small.onnx")
    sensevoice_tokens = asr_config.get("tokens_path", "models/tokens.txt")
    
    # 转换为绝对路径
    sensevoice_model = os.path.abspath(os.path.join(current_dir, sensevoice_model)) if not os.path.isabs(sensevoice_model) else sensevoice_model
    sensevoice_tokens = os.path.abspath(os.path.join(current_dir, sensevoice_tokens)) if not os.path.isabs(sensevoice_tokens) else sensevoice_tokens

    if not os.path.exists(sensevoice_model) or not os.path.exists(sensevoice_tokens):
        print(f"❌ 未找到 SenseVoice 识别模型或 tokens 文件")
        exit(1)

    # 组装 sherpa_onnx 的离线(Offline)模型配置
    asr_recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=sensevoice_model,
        tokens=sensevoice_tokens,
        num_threads=asr_config.get("num_threads", 2),
        use_gpu=asr_config.get("use_gpu", False),
    )
    print(f"🎙️ [Sherpa ONNX] SenseVoice ASR 模型加载成功")

    # ==================== 3. 加载 ONNXRuntime-GenAI (NLLB) ====================
    # NLLB 通过 onnxruntime_genai 加载时，需要传入包含 config.json 和模型的文件夹路径
    nllb_model_dir = trans_config.get("model_dir", "models/nllb_onnx_genai")
    nllb_model_dir = os.path.abspath(os.path.join(current_dir, nllb_model_dir)) if not os.path.isabs(nllb_model_dir) else nllb_model_dir

    if not os.path.exists(nllb_model_dir):
        print(f"❌ 未找到 NLLB 翻译模型目录: {nllb_model_dir}")
        exit(1)

    try:
        # 使用 og.Model 加载整个模型文件夹
        translator_model = og.Model(nllb_model_dir)
        translator_tokenizer = og.Tokenizer(translator_model)
        print(f"🔤 [ONNX GenAI] NLLB 翻译模型及分词器加载成功")
    except Exception as e:
        print(f"❌ NLLB 模型加载失败: {e}")
        exit(1)

    # ==================== 4. 初始化 WASAPI 环回设备 ====================
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

    # 返回所有初始化后的资源
    return {
        "pyaudio_instance": p,
        "vad_session": ort_session,
        "asr_recognizer": asr_recognizer,
        "translator_model": translator_model,
        "translator_tokenizer": translator_tokenizer,
        "default_speakers": default_speakers,
        "hardware_sample_rate": hardware_sample_rate,
    }
