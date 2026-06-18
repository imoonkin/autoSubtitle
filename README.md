import onnxruntime as ort          # 1. 专门用来跑轻量的 Silero VAD
import sherpa_onnx as sherpa       # 2. 专门用来跑 SenseVoice ASR (瞬间拿文本)
import onnxruntime_genai as og     # 3. 专门用来跑 NLLB 翻译模型 (处理繁琐的翻译循环)
