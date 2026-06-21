"""语音识别处理器。"""
import base64
import io
import wave
import re
import json
import httpx 

def pcm_to_wav_bytes(pcm_bytes: bytes, sample_rate=16000) -> bytes:
    """将原生 PCM 字节流转换为标准 WAV 字节流。"""
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    wav_io.seek(0)
    return wav_io.read()

class AsrClient:
    def __init__(self, config: dict):
        """初始化 ASR 客户端配置。"""
        self.server_url = config.get("server_url")
        
    def transcribe(self, raw_audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """输入音频字节流，通过流式接口请求并返回清洗后的完整文本。"""
        if not raw_audio_bytes:
            return ""
        wav_bytes = pcm_to_wav_bytes(raw_audio_bytes, sample_rate)
        audio_base64 = base64.b64encode(wav_bytes).decode('utf-8')

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ],
            "stream": True, 
            "reasoning_format": "none",
            "return_progress": True,
            "backend_sampling": False,
            "timings_per_token": True
        }

        full_text = ""
        try:
            with httpx.stream("POST", self.server_url, json=payload, timeout=25.0) as response:
                if response.status_code != 200:
                    print(f"❌ [API] Failed with status: {response.status_code}")
                    return f"[语音识别错误: HTTP {response.status_code}]"
                    
                for line in response.iter_lines():
                    if not line.strip():
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    if line.strip() == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(line)
                        choices = chunk_json.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                full_text += token
                    except Exception:
                        pass
                        
            clean_text = re.sub(r"^language.+?<asr_text>", "", full_text).strip()
            return clean_text
            
        except httpx.RequestError as exc:
            print(f"❌ [API] Connection error: {exc}")
            return f"[语音识别通信断开: {exc}]"
