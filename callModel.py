import io
import wave
import base64
import httpx

CHAT_API_URL = "http://127.0.0.1:8080/v1/chat/completions"

def pcm_to_wav_bytes(pcm_bytes, sample_rate=16000) -> bytes:
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    wav_io.seek(0)
    return wav_io.read()

def process_and_translate_audio(raw_audio_bytes, sample_rate=16000):
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
                            "format": "wav"  # Using WAV but following the exact schema
                        }
                    }
                ]
            }
        ],
        "stream": True,                # 🔥 Matches WebUI streaming flag
        "reasoning_format": "auto",    # 🔥 Matches WebUI reasoning flag
        "return_progress": True,
        "backend_sampling": False,
        "timings_per_token": True
    }


    full_text = ""
    try:
        print("📡 [API] Sending WebUI-identical audio payload...")
        
        # 3. Use httpx.stream to consume the server's SSE (Server-Sent Events) tokens
        with httpx.stream("POST", CHAT_API_URL, json=payload, timeout=25.0) as response:
            if response.status_code != 200:
                print(f"❌ [API] Failed with status: {response.status_code}")
                return None
                
            for line in response.iter_lines():
                if not line.strip():
                    continue
                
                # Clean up standard OpenAI SSE "data: " prefix
                if line.startswith("data: "):
                    line = line[6:]
                    
                if line.strip() == "[DONE]":
                    break
                    
                try:
                    import json
                    chunk_json = json.loads(line)
                    choices = chunk_json.get("choices", [])
                    if choices:
                        # Stream chunks use 'delta' instead of 'message'
                        delta = choices[0].get("delta", {})
                        token = delta.get("content", "")
                        if token:
                            full_text += token
                            # Print tokens in real-time as they arrive from the GPU
                            print(token, end="", flush=True)
                except Exception:
                    pass
                    
        print() 
        return full_text.strip()
        
    except httpx.RequestError as exc:
        print(f"❌ [API] Connection error: {exc}")
        return None