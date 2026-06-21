import httpx

class TranslateClient:
    def __init__(self, trans_config: dict):
        self.server_url = trans_config.get("server_url")
        self.tgt_lang = trans_config.get("tgt_lang", "English")
        self.temperature = trans_config.get("temperature", 0.3)
        
    def translate(self, text: str) -> str:
        if not text:
            return ""
        
        payload = {
            "messages": [
                {
                    "role": "system", 
                    "content": f"You are a professional translator. Translate the user input into {self.tgt_lang}. Respond ONLY with the translation without any markdown tags."
                },
                {"role": "user", "content": text}
            ],
            "temperature": self.temperature
        }
        
        try:
            response = httpx.post(self.server_url, json=payload, timeout=5.0)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                return f"[翻译错误: HTTP {response.status_code}]"
        except httpx.RequestError as e:
            return f"[翻译通信断开: {e}]"
