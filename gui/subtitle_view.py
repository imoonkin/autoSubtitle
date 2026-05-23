from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (FluentWindow, SubtitleLabel, PushButton, Slider, 
                            CardWidget, IconWidget, FluentIcon, BodyLabel)

# 🎔 1. 悬浮字幕视窗 (追求极致的纯净与穿透)
class FloatingSubtitleView(QWidget):
    def __init__(self):
        super().__init__()
        # 无边框、永远置顶、工具窗口属性（不在任务栏显示独立图标）
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 内部字幕文本
        self.layout = QVBoxLayout(self)
        self.label = SubtitleLabel("等待语音输入...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        
        # 初始化样式
        self.update_style(32, "#FFFFFF", 150) # 默认大小、白色、半透明背景
        self.resize(900, 120)

    def update_style(self, size, color_hex, bg_alpha):
        # 动态修改字体大小与颜色
        self.label.setFont(QFont("Microsoft YaHei", size, QFont.Weight.Bold))
        self.label.setStyleSheet(f"color: {color_hex};")
        # 动态修改悬浮窗背景板底色与透明度
        self.setStyleSheet(f"background-color: rgba(0, 0, 0, {bg_alpha}); border-radius: 10px;")

    def set_text(self, text):
        self.label.setText(text)

    # 支持鼠标按住拖动悬浮窗位置
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_drag = True
            self.m_DragPosition = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.m_drag:
            self.move(event.globalPosition().toPoint() - self.m_DragPosition)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.m_drag = False
