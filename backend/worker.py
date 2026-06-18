"""后台字幕处理线程。
"""
import queue
import pyaudiowpatch as pyaudio
from backend.audio_processor import AudioSliceProcessor, TARGET_SAMPLE_RATE
from PySide6.QtCore import QThread, Signal

from backend.init import init_resources

class SubtitleWorker(QThread):
    text_ready = Signal(str)
    status_changed = Signal(str)

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.running = False

    def run(self):
        self.running = True
        self.status_changed.emit("初始化...")

        try:
            p, ort_session, speakers, hw_rate = init_resources(self.config)
        except Exception as e:
            self.status_changed.emit(f"错误: {str(e)}")
            return

        audio_queue = queue.Queue()

        def audio_callback(in_data, frame_count, time_info, status_flags):
            audio_queue.put(in_data)
            return (None, pyaudio.paContinue)

        chunk_size = int(hw_rate * 0.1)
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=hw_rate,
            input=True,
            input_device_index=speakers["index"],
            frames_per_buffer=chunk_size,
            stream_callback=audio_callback,
        )

        vad_config = self.config.get("models", {}).get("vad", {})
        processor = AudioSliceProcessor(ort_session, hw_rate, vad_config)
        llm_config = self.config.get("models", {}).get("llm", {})

        stream.start_stream()
        self.status_changed.emit("🎤 正在监听系统声音...")

        while self.running and stream.is_active():
            try:
                chunk = audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            payload = processor.process_chunk(chunk)
            if payload:
                text = callModel.process_and_translate_audio(
                    payload, TARGET_SAMPLE_RATE, llm_config=llm_config
                )
                if text:
                    self.text_ready.emit(text)

        stream.stop_stream()
        stream.close()
        p.terminate()
        self.status_changed.emit("服务已停止。")

    def stop(self):
        self.running = False
