# gui/main_window.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (FluentWindow, SubtitleLabel, PushButton, Slider, 
                            CardWidget, IconWidget, FluentIcon, BodyLabel)

# 🌟 核心修正：正确导入根目录的后端逻辑和同级目录的字幕窗
import backend  
from gui.subtitle_view import FloatingSubtitleView

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("home_interface")
        self.init_ui()
        
        # 🌟 加载根目录配置文件
        self.config = backend.load_config()
        self.worker = None
        
        # 🌟 关键：实例化字幕窗，并将其父对象设为 self（或保持无父对象但由主窗持有生命周期）
        self.sub_view = FloatingSubtitleView()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 状态卡片
        self.status_card = CardWidget(self)
        card_layout = QHBoxLayout(self.status_card)
        self.status_icon = IconWidget(FluentIcon.INFO, self)
        self.status_label = BodyLabel("服务尚未启动", self)
        card_layout.addWidget(self.status_icon)
        card_layout.addWidget(self.status_label)
        card_layout.addStretch()
        layout.addWidget(self.status_card)

        # 启动按钮
        self.btn_toggle = PushButton("🚀 启动字幕服务", self)
        self.btn_toggle.clicked.connect(self.toggle_service)
        layout.addWidget(self.btn_toggle)

        # 字体大小滑动条
        size_layout = QHBoxLayout()
        size_layout.addWidget(BodyLabel("字幕字体大小:", self))
        self.slider_size = Slider(Qt.Orientation.Horizontal, self)
        self.slider_size.setRange(16, 60)
        self.slider_size.setValue(32)
        self.slider_size.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(self.slider_size)
        layout.addLayout(size_layout)

        layout.addStretch()

    def toggle_service(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_toggle.setText("🚀 启动字幕服务")
            self.sub_view.hide()
        else:
            # 🌟 实例化 backend.py 里的线程类
            self.worker = backend.SubtitleWorker(self.config)
            self.worker.text_ready.connect(self.sub_view.set_text)
            self.worker.status_changed.connect(self.status_label.setText)
            self.worker.start()
            
            self.btn_toggle.setText("🛑 停止字幕服务")
            self.sub_view.show()

    def on_size_changed(self, value):
        self.sub_view.update_style(value, "#FFFFFF", 150)
