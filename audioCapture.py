import model_server
import callModel
import numpy as np
import pyaudiowpatch as pyaudio
from scipy.signal import resample_poly
import wave
import os
import queue

TARGET_SAMPLE_RATE = 16000
# 10秒总数据量: 10 * 16000 * 2 字节 = 320000 字节
WINDOW_SIZE_BYTES = 320000

# 启动核心大模型服务器
if not model_server.start_llama_server():
    print("❌ 核心服务器未能拉起，程序退出。")
    exit(1)

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
    HARDWARE_SAMPLE_RATE = int(default_speakers["defaultSampleRate"])
    print(f"🎛️ 声卡硬件原生采样率: {HARDWARE_SAMPLE_RATE}Hz")
except Exception as e:
    print(f"❌ 无法初始化 WASAPI 设备: {e}")
    p.terminate()
    exit()

# 线程安全队列，用于接收底层回调的原始音频块
audio_queue = queue.Queue()

# PyAudio 底层回调函数：硬件一有数据立刻塞入队列，确保零丢包
def audio_callback(in_data, frame_count, time_info, status_flags):
    audio_queue.put(in_data)
    return (None, pyaudio.paContinue)

# 设置底层单次读取 0.1 秒的数据块，保证流式处理的平滑度
HARDWARE_CHUNK_SIZE = int(HARDWARE_SAMPLE_RATE * 0.1)

stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=HARDWARE_SAMPLE_RATE,
    input=True,
    input_device_index=default_speakers["index"],
    frames_per_buffer=HARDWARE_CHUNK_SIZE,
    stream_callback=audio_callback
)

print("\n🚀 [生产模式] 开始监听系统声音并实时识别模型中...")
print("💡 按 Ctrl+C 退出。")

audio_rolling_buffer = bytearray()
current_dir = os.path.dirname(os.path.abspath(__file__))
debug_wav_path = os.path.join(current_dir, "debug_current.wav")

# 计算硬件采集 1 整秒所需的字节数 (int16 占用 2 字节)
one_second_hardware_bytes = HARDWARE_SAMPLE_RATE * 2
raw_processing_buffer = bytearray()

try:
    stream.start_stream()
    while stream.is_active():
        try:
            # 从队列中获取 0.1 秒的音频块，设置超时防止死锁
            chunk = audio_queue.get(timeout=1.0)
            raw_processing_buffer.extend(chunk)
        except queue.Empty:
            continue

        # 核心对齐：只有当原始缓冲区攒够整整 1 秒数据时，才进行重采样
        if len(raw_processing_buffer) >= one_second_hardware_bytes:
            # 切分出精确的 1 秒硬件原始数据
            raw_second = bytes(raw_processing_buffer[:one_second_hardware_bytes])
            del raw_processing_buffer[:one_second_hardware_bytes]

            # 转换为 float32 进行高精度重采样
            hardware_audio = np.frombuffer(raw_second, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 严格在 1 秒边界上进行多相滤波重采样，彻底消除电音、变调
            target_audio = resample_poly(hardware_audio, TARGET_SAMPLE_RATE, HARDWARE_SAMPLE_RATE).astype(np.float32)
            target_bytes = (target_audio * 32768.0).astype(np.int16).tobytes()
            audio_rolling_buffer.extend(target_bytes)

            # 当目标重采样缓冲区达到 10 秒时，打包输出
            if len(audio_rolling_buffer) >= WINDOW_SIZE_BYTES:
                print(f"\n⏰ [时间窗满 10s] 打包数据并发送至大模型...")
                
                # 提取 10 秒数据
                payload_bytes = bytes(audio_rolling_buffer[:WINDOW_SIZE_BYTES])
                # 安全切片删除，保留可能多出来的微量尾部数据，防止时间轴断裂
                del audio_rolling_buffer[:WINDOW_SIZE_BYTES] 

                # 保留本地 debug 保存功能，方便你随时确认音频源依然干净
                try:
                    with wave.open(debug_wav_path, 'wb') as wav_file:
                        wav_file.setnchannels(1)        # 单声道
                        wav_file.setsampwidth(2)       # 16位 (2字节)
                        wav_file.setframerate(TARGET_SAMPLE_RATE) # 16000Hz
                        wav_file.writeframes(payload_bytes)
                    print(f"💾 [Debug] 本地备份成功: {debug_wav_path}")
                except Exception as e:
                    print(f"⚠️ [Debug] 保存 WAV 失败: {e}")

                # 调用大模型处理并翻译音频（此时阻塞主循环是安全的，后台线程仍在疯狂吃音频数据）
                final_text = callModel.process_and_translate_audio(payload_bytes, TARGET_SAMPLE_RATE)
                if final_text:
                    print(f"【✨ 10秒区间字幕】: {final_text}\n")
                else:
                    print("当前区间未检测到有效语音文本。")

except KeyboardInterrupt:
    print("\n停止监听。")
finally:
    if 'stream' in locals():
        stream.stop_stream()
        stream.close()
    p.terminate()
    print("🎤 录音设备与服务器已安全释放。")
