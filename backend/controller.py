"""字幕服务控制器 — QML 和后台线程之间的桥梁。

暴露为 QML 上下文属性 "subtitleController"。
"""
from PySide6.QtCore import QObject, Property, Signal

from config import load_config_dict
from backend.worker import SubtitleWorker


class SubtitleController(QObject):
    textReady = Signal(str)
    statusChanged = Signal(str)
    runningChanged = Signal(bool)

    def __init__(self):
        super().__init__()
        self._worker = None
        self._running = False
        self._status_text = "服务尚未启动"

    # ── isRunning ───────────────────────────────────────────────────────
    def _get_running(self): return self._running
    def _set_running(self, v):
        if self._running != v:
            self._running = v
            self.runningChanged.emit(v)
    isRunning = Property(bool, fget=_get_running, notify=runningChanged)

    # ── statusText ──────────────────────────────────────────────────────
    def _get_status_text(self): return self._status_text
    def _set_status_text(self, v):
        if self._status_text != v:
            self._status_text = v
            self.statusChanged.emit(v)
    statusText = Property(str, fget=_get_status_text, notify=statusChanged)

    # ── slots ───────────────────────────────────────────────────────────

    def startService(self):
        if self._worker is not None:
            return

        data = load_config_dict()
        if not data:
            self._set_status_text("错误: 无法加载配置文件")
            return

        self._worker = SubtitleWorker(data)
        self._worker.TextReady.connect(self._on_text_ready)
        self._worker.StatusChanged.connect(self._on_status_changed)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
        self._set_running(True)

    def stopService(self):
        if self._worker is None:
            return
        self._worker.stop()

    # ── internal ────────────────────────────────────────────────────────

    def _on_text_ready(self, text: str):
        self.textReady.emit(text)

    def _on_status_changed(self, text: str):
        self._set_status_text(text)

    def _on_finished(self):
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        self._set_running(False)
