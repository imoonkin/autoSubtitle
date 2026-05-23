import io
import wave
import base64
import httpx
import json

def pcm_to_wav_bytes(pcm_bytes, sample_rate=16000) -> bytes:
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    wav_io.seek(0)
    return wav_io.read()

def process_and_translate_audio(raw_audio_bytes, sample_rate=16000, llm_config=None):
    """
    Converts raw PCM data into a WAV base64 string and streams token completions 
    from the llama-server via a dynamically constructed URL.
    """
    # 🌟 Dynamically build the API endpoint using our TOML configurations
    if llm_config is None:
        llm_config = {}
        
    host = llm_config.get("host", "127.0.0.1")
    port = str(llm_config.get("port", "8080"))
    chat_api_url = f"http://{host}:{port}/v1/chat/completions"

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
        "reasoning_format": "none",  # ⚡ Synced with --reasoning-format none in modelServer
        "return_progress": True,
        "backend_sampling": False,
        "timings_per_token": True
    }
    
    full_text = ""
    try:
        print("📡 [API] Sending WebUI-identical audio payload...")
        
        with httpx.stream("POST", chat_api_url, json=payload, timeout=25.0) as response:
            if response.status_code != 200:
                print(f"❌ [API] Failed with status: {response.status_code}")
                return None
                
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
                    
        return full_text.strip()
        
    except httpx.RequestError as exc:
        print(f"❌ [API] Connection error: {exc}")
        return None
