import numpy as np
from scipy.signal import resample_poly

TARGET_SAMPLE_RATE = 16000
SILERO_CHUNK_SAMPLES = 512
SILERO_CHUNK_BYTES = SILERO_CHUNK_SAMPLES * 2

class AudioSliceProcessor:
    def __init__(self, ort_session, hardware_sample_rate, vad_config):
        self.ort_session = ort_session
        self.hardware_sample_rate = hardware_sample_rate
        self.one_second_hardware_bytes = hardware_sample_rate * 2
        
        # 🌟 从外部配置动态加载参数
        self.vad_threshold = vad_config.get("threshold", 0.50)
        self.max_speech_duration_s = vad_config.get("max_speech_duration_s", 10)
        self.max_silence_chunks = vad_config.get("max_silence_chunks", 25)
        
        # 缓冲区与状态
        self.raw_processing_buffer = bytearray()
        self.audio_rolling_buffer = bytearray()
        self.sentence_accumulator = bytearray()
        
        # V5 核心上下文与 3D 状态矩阵
        self.context_samples = np.zeros(64, dtype=np.float32)
        self.state = np.zeros((2, 1, 128), dtype=np.float32)
        self.is_speaking = False
        self.silence_counter = 0

    def reset_state(self):
        self.sentence_accumulator.clear()
        self.is_speaking = False
        self.silence_counter = 0
        self.state = np.zeros((2, 1, 128), dtype=np.float32)

    def process_chunk(self, chunk):
        self.raw_processing_buffer.extend(chunk)
        
        if len(self.raw_processing_buffer) < self.one_second_hardware_bytes:
            return None
            
        raw_second = bytes(self.raw_processing_buffer[:self.one_second_hardware_bytes])
        del self.raw_processing_buffer[:self.one_second_hardware_bytes]
        
        hardware_audio = np.frombuffer(raw_second, dtype=np.int16).astype(np.float32) / 32768.0
        target_audio = resample_poly(hardware_audio, TARGET_SAMPLE_RATE, self.hardware_sample_rate).astype(np.float32)
        target_bytes = (target_audio * 32768.0).astype(np.int16).tobytes()
        self.audio_rolling_buffer.extend(target_bytes)
        
        payload_bytes = None
        
        while len(self.audio_rolling_buffer) >= SILERO_CHUNK_BYTES:
            vad_chunk_bytes = bytes(self.audio_rolling_buffer[:SILERO_CHUNK_BYTES])
            del self.audio_rolling_buffer[:SILERO_CHUNK_BYTES]
            
            audio_int16 = np.frombuffer(vad_chunk_bytes, dtype=np.int16).copy()
            current_chunk_float32 = audio_int16.astype(np.float32) / 32768.0
            
            full_audio_frame = np.concatenate([self.context_samples, current_chunk_float32])
            self.context_samples = current_chunk_float32[-64:].copy()
            
            input_data = np.expand_dims(full_audio_frame, axis=0)
            inputs = {
                'input': input_data,
                'sr': np.array(TARGET_SAMPLE_RATE, dtype=np.int64),
                'state': self.state
            }
            
            out, next_state = self.ort_session.run(None, inputs)
            speech_prob = float(out.item())
            
            self.state = np.array(next_state, dtype=np.float32)
            
            # 使用动态阈值
            if speech_prob >= self.vad_threshold:
                self.silence_counter = 0
                if not self.is_speaking:
                    print("\n🎙️ [VAD] 检测到人类说话声启动...")
                    self.is_speaking = True
                self.sentence_accumulator.extend(vad_chunk_bytes)
            else:
                if self.is_speaking:
                    self.silence_counter += 1
                    self.sentence_accumulator.extend(vad_chunk_bytes)
                else:
                    self.sentence_accumulator.extend(vad_chunk_bytes)
                    max_pre_speech_bytes = SILERO_CHUNK_BYTES * 5
                    if len(self.sentence_accumulator) > max_pre_speech_bytes:
                        del self.sentence_accumulator[:-max_pre_speech_bytes]
            
            should_trigger_llm = False
            
            # 使用动态断句红线和时限
            if self.is_speaking and self.silence_counter >= self.max_silence_chunks:
                print("🛑 [VAD] 检测到预设长尾静音，断句成功！准备交由大模型...")
                should_trigger_llm = True
            elif len(self.sentence_accumulator) >= (self.max_speech_duration_s * TARGET_SAMPLE_RATE * 2):
                print(f"⏳ [VAD] 单句时长抵达 {self.max_speech_duration_s} 秒红线，启动安全分段截断...")
                should_trigger_llm = True
                
            if should_trigger_llm:
                if self.silence_counter >= self.max_silence_chunks:
                    silence_bytes_to_strip = self.silence_counter * SILERO_CHUNK_BYTES
                    if silence_bytes_to_strip < len(self.sentence_accumulator):
                        payload_bytes = bytes(self.sentence_accumulator[:-silence_bytes_to_strip])
                    else:
                        payload_bytes = bytes(self.sentence_accumulator)
                else:
                    payload_bytes = bytes(self.sentence_accumulator)
                
                if len(payload_bytes) < (TARGET_SAMPLE_RATE * 0.4 * 2):
                    self.reset_state()
                    payload_bytes = None
                    break
                
                self.reset_state()
                break
                
        return payload_bytes
