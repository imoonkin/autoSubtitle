"""语音识别处理器。"""
import os
import numpy as np
import sherpa_onnx

class AsrProcessor:
    def __init__(self, current_dir: str, asr_config: dict, target_sample_rate: int = 16000):
        """
        在类内部自主初始化 Sherpa-ONNX (SenseVoice ASR) 模型
        """
        self.target_sample_rate = target_sample_rate
        
        # 1. 路径解析与安全检查
        sensevoice_model = asr_config.get("model_path", "models/sensevoice-small.onnx")
        sensevoice_tokens = asr_config.get("tokens_path", "models/tokens.txt")
        
        self.model_path = os.path.abspath(os.path.join(current_dir, sensevoice_model)) if not os.path.isabs(sensevoice_model) else sensevoice_model
        self.tokens_path = os.path.abspath(os.path.join(current_dir, sensevoice_tokens)) if not os.path.isabs(sensevoice_tokens) else sensevoice_tokens
        
        if not os.path.exists(self.model_path) or not os.path.exists(self.tokens_path):
            raise FileNotFoundError(f"❌ 语音识别未找到 SenseVoice 模型或 tokens 文件: \n模型: {self.model_path}\nTokens: {self.tokens_path}")
            
        # 2. 自主组装并初始化 OfflineRecognizer
        self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=self.model_path,
            tokens=self.tokens_path,
            num_threads=asr_config.get("num_threads", 2),
        )
        print(f"🎙️ [Sherpa ONNX] SenseVoice ASR 引擎在类内部初始化成功")

    def transcribe(self, payload) -> str:
        """输入音频数据，返回识别后的文本。"""
        if payload is None:
            return ""

        # 确保音频数据为 float32 类型的 numpy 数组，范围在 [-1.0, 1.0]
        if isinstance(payload, bytes):
            audio_data = np.frombuffer(payload, dtype=np.int16).astype(np.float32) / 32768.0
        else:
            audio_data = np.asarray(payload, dtype=np.float32)

        # 调用内部绑定的识别器
        asr_stream = self.recognizer.create_stream()
        asr_stream.accept_waveform(self.target_sample_rate, audio_data)
        self.recognizer.decode_stream(asr_stream)
        
        return asr_stream.result.text.strip()
