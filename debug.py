import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
# 导入专门适配 PySide6 的 Fluent 组件
from qfluentwidgets import PrimaryPushButton, Slider, SwitchButton, RadioButton, ImageLabel

# 1. 鼠标穿透的透明字幕窗口
class SubtitleOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        # 核心：无边框 | 窗口置顶 | 鼠标输入穿透（不干扰底层软件）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.WindowTransparentForInput
        )
        # 背景完全透明
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(800, 150)
        
        # 字幕文本标签
        self.label = QLabel("等待语音流输入...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 默认样式：大字号、白色文本、带半透明黑底背景
        self.update_style(size=28, opacity=120)
        self.setCentralWidget(self.label)

    def update_style(self, size, opacity):
        # 动态更新字幕的 CSS 样式
        style_str = f"""
            font-size: {size}px; 
            color: #FFFFFF; 
            font-family: 'Microsoft YaHei', sans-serif;
            font-weight: bold;
            background-color: rgba(0, 0, 0, {opacity});
            border-radius: 10px;
        """
        self.label.setStyleSheet(style_str)

# 2. 现代感 Fluent 设置面板
class SettingsWindow(QWidget):
    def __init__(self, overlay_window):
        super().__init__()
        self.overlay = overlay_window
        self.setWindowTitle("智能字幕设置面板")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 功能组件 1：字幕开关
        self.toggle_switch = SwitchButton(self)
        self.toggle_switch.setChecked(True)
        self.toggle_switch.checkedChanged.connect(self.on_toggle_subtitle)
        layout.addWidget(QLabel("启用字幕叠加层:"))
        layout.addWidget(self.toggle_switch)

        # 功能组件 2：字号调节滑动条
        self.size_slider = Slider(Qt.Orientation.Horizontal, self)
        self.size_slider.setRange(16, 50)
        self.size_slider.setValue(28)
        self.size_slider.valueChanged.connect(self.sync_settings)
        layout.addWidget(QLabel("字幕大小调节:"))
        layout.addWidget(self.size_slider)

        # 功能组件 3：背景不透明度调节
        self.opacity_slider = Slider(Qt.Orientation.Horizontal, self)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(120)
        self.opacity_slider.valueChanged.connect(self.sync_settings)
        layout.addWidget(QLabel("背景不透明度 (0-255):"))
        layout.addWidget(self.opacity_slider)

    def sync_settings(self):
        # 实时将设置面板的数据同步至透明字幕层
        size = self.size_slider.value()
        opacity = self.opacity_slider.value()
        self.overlay.update_style(size, opacity)

    def on_toggle_subtitle(self, is_checked):
        if is_checked:
            self.overlay.show()
        else:
            self.overlay.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 依次实例化并显示两个窗口
    overlay = SubtitleOverlay()
    overlay.show()
    
    settings = SettingsWindow(overlay)
    settings.show()
    
    sys.exit(app.exec())
