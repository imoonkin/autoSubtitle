# gui/setting_interface.py
import os
import tomli_w
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (ScrollArea, SettingCardGroup, PushButton, 
                            PrimaryPushButton, InfoBar, InfoBarPosition,
                            BodyLabel, LineEdit, Slider, SimpleCardWidget)

import backend

# 🌟 修复点：改用 SimpleCardWidget 自动跟随主窗的暗色主题
class SliderSettingCard(SimpleCardWidget):
    def __init__(self, title, content, min_v, max_v, default_v, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        
        # 整体布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 0, 16, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 左侧文字区
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        # 🌟 指定颜色或使用特定的暗色主题类名
        self.title_label = BodyLabel(title, self)
        self.title_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        self.content_label = BodyLabel(content, self)
        self.content_label.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.content_label)
        
        # 右侧控制区
        self.h_layout = QHBoxLayout()
        self.val_label = BodyLabel(str(default_v), self)
        self.val_label.setFixedWidth(30)
        self.val_label.setStyleSheet("color: #FFFFFF;")
        
        self.slider = Slider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(min_v, max_v)
        self.slider.setValue(default_v)
        self.slider.setFixedWidth(150)
        
        self.slider.valueChanged.connect(lambda v: self.val_label.setText(str(v)))
        
        self.h_layout.addWidget(self.slider)
        self.h_layout.addWidget(self.val_label)
        self.h_layout.setSpacing(10)
        
        # 组装
        main_layout.addLayout(text_layout)
        main_layout.addStretch()
        main_layout.addLayout(self.h_layout)

    def value(self):
        return self.slider.value()

    def setValue(self, val):
        self.slider.setValue(int(val))


# 🌟 修复点：改用 SimpleCardWidget 并处理文字颜色
class FileChooserSettingCard(SimpleCardWidget):
    def __init__(self, title, content, is_folder=False, file_filter="All Files (*.*)", parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.is_folder = is_folder
        self.file_filter = file_filter
        
        # 整体布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 0, 16, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 左侧文字区
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self.title_label = BodyLabel(title, self)
        self.title_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        self.content_label = BodyLabel(content, self)
        self.content_label.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.content_label)
        
        # 右侧控制区
        self.h_layout = QHBoxLayout()
        self.line_edit = LineEdit(self)
        self.line_edit.setFixedWidth(220)
        
        self.btn_browse = PushButton("浏览...", self)
        self.btn_browse.clicked.connect(self.browse_path)
        
        self.h_layout.addWidget(self.line_edit)
        self.h_layout.addWidget(self.btn_browse)
        self.h_layout.setSpacing(10)
        
        # 组装
        main_layout.addLayout(text_layout)
        main_layout.addStretch()
        main_layout.addLayout(self.h_layout)
        
    def browse_path(self):
        if self.is_folder:
            path = QFileDialog.getExistingDirectory(self, "选择文件夹", self.line_edit.text())
        else:
            path, _ = QFileDialog.getOpenFileName(self, "选择文件", self.line_edit.text(), self.file_filter)
        
        if path:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rel_path = os.path.relpath(path, current_dir)
            if not rel_path.startswith(".."):
                self.line_edit.setText(rel_path.replace("\\", "/"))
            else:
                self.line_edit.setText(path.replace("\\", "/"))

    def value(self):
        return self.line_edit.text()

    def setValue(self, text):
        self.line_edit.setText(text)


class SettingInterface(ScrollArea):
    def __init__(self, home_interface, parent=None):
        super().__init__(parent=parent)
        self.home_interface = home_interface
        self.setObjectName("setting_interface")
        
        self.config = backend.load_config()
        
        self.scroll_widget = QWidget()
        self.layout = QVBoxLayout(self.scroll_widget)
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(20)
        
        vad_conf = self.config.get("models", {}).get("vad", {})
        llm_conf = self.config.get("models", {}).get("llm", {})
        gui_conf = self.config.get("gui", {})
        
        # -------------------------------------------------------------
        # 1. 🎨 字幕外观设置组
        # -------------------------------------------------------------
        self.subtitle_group = SettingCardGroup("🎨 字幕外观设置", self.scroll_widget)
        # 🌟 给组标题加上暗色主题标签样式
        self.subtitle_group.titleLabel.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        
        self.size_card = SliderSettingCard(
            "字体大小", "调整悬浮字幕窗口的文字大小", 
            16, 60, int(gui_conf.get("font_size", 32)), self.subtitle_group
        )
        self.size_card.slider.valueChanged.connect(self.on_font_size_changed)
        self.subtitle_group.addSettingCard(self.size_card)
        self.layout.addWidget(self.subtitle_group)
        
        # -------------------------------------------------------------
        # 2. 🎙️ VAD 语音断句设置组
        # -------------------------------------------------------------
        self.vad_group = SettingCardGroup("🎙️ VAD 语音断句设置 [models.vad]", self.scroll_widget)
        self.vad_group.titleLabel.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        
        self.vad_path_card = FileChooserSettingCard("VAD 模型路径", "ONNX 格式的语音检测模型", False, "ONNX Files (*.onnx)", self.vad_group)
        self.vad_path_card.setValue(vad_conf.get("model_path", ""))
        self.vad_group.addSettingCard(self.vad_path_card)
        
        self.silence_card = SliderSettingCard(
            "静音强断红线 (max_silence_chunks)", "多少个静音块后判定为一句话结束", 
            5, 100, int(vad_conf.get("max_silence_chunks", 25)), self.vad_group
        )
        self.vad_group.addSettingCard(self.silence_card)
        
        self.duration_card = SliderSettingCard(
            "单句最长限制 (max_speech_duration_s)", "超过该秒数即使没停顿也强制断句", 
            3, 30, int(vad_conf.get("max_speech_duration_s", 10)), self.vad_group
        )
        self.vad_group.addSettingCard(self.duration_card)
        
        self.layout.addWidget(self.vad_group)
        
        # -------------------------------------------------------------
        # 3. 🧠 LLM / ASR 模型与服务配置组
        # -------------------------------------------------------------
        self.llm_group = SettingCardGroup("🧠 ASR / LLM 核心配置 [models.llm]", self.scroll_widget)
        self.llm_group.titleLabel.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        
        self.exe_path_card = FileChooserSettingCard("llama-server 执行文件", "llama-server.exe 的存放路径", False, "Executables (*.exe)", self.llm_group)
        self.exe_path_card.setValue(llm_conf.get("exe_path", ""))
        self.llm_group.addSettingCard(self.exe_path_card)
        
        self.model_path_card = FileChooserSettingCard("ASR 模型路径", "ASR语音模型的 .gguf 文件", False, "GGUF Models (*.gguf)", self.llm_group)
        self.model_path_card.setValue(llm_conf.get("model_path", ""))
        self.llm_group.addSettingCard(self.model_path_card)
        
        self.mmproj_path_card = FileChooserSettingCard("多模态投影文件 (mmproj)", "Qwen3-ASR 必须的 mmproj 路径", False, "GGUF Models (*.gguf)", self.llm_group)
        self.mmproj_path_card.setValue(llm_conf.get("mmproj_path", ""))
        self.llm_group.addSettingCard(self.mmproj_path_card)
        
        self.ngl_card = SliderSettingCard(
            "GPU 卸载层数 (ngl)", "核心显卡填0，独立显卡（Vulkan/CUDA）填99", 
            0, 150, int(llm_conf.get("ngl", 99)), self.llm_group
        )
        self.llm_group.addSettingCard(self.ngl_card)
        
        self.ctx_card = SliderSettingCard(
            "上下文窗口大小 (ctx_size)", "推理上下文大小，ASR 默认为 4096", 
            512, 8192, int(llm_conf.get("ctx_size", 4096)), self.llm_group
        )
        self.llm_group.addSettingCard(self.ctx_card)
        
        self.layout.addWidget(self.llm_group)
        
        # -------------------------------------------------------------
        # 4. 💾 保存控制区
        # -------------------------------------------------------------
        self.btn_save = PrimaryPushButton("💾 保存并应用配置", self.scroll_widget)
        self.btn_save.clicked.connect(self.save_settings)
        self.layout.addWidget(self.btn_save)
        
        self.layout.addStretch()
        self.setWidget(self.scroll_widget)
        self.setWidgetResizable(True)
        
        # 🌟 强化滚动区域的纯暗色调底色，防白底闪烁
        self.setStyleSheet("""
            QScrollArea { background: #202020; border: none; }
            QWidget { background: transparent; }
        """)

    def on_font_size_changed(self, value):
        if self.home_interface and self.home_interface.sub_view:
            self.home_interface.sub_view.update_style(value, "#FFFFFF", 150)

    def save_settings(self):
        """保存配置"""
        if "models" not in self.config: self.config["models"] = {}
        if "vad" not in self.config["models"]: self.config["models"]["vad"] = {}
        if "llm" not in self.config["models"]: self.config["models"]["llm"] = {}
        if "gui" not in self.config: self.config["gui"] = {}
        # 映射数据
        self.config["models"]["vad"]["model_path"] = self.vad_path_card.value()
        self.config["models"]["vad"]["max_silence_chunks"] = int(self.silence_card.value())
        self.config["models"]["vad"]["max_speech_duration_s"] = int(self.duration_card.value())
        self.config["models"]["llm"]["exe_path"] = self.exe_path_card.value()
        self.config["models"]["llm"]["model_path"] = self.model_path_card.value()
        self.config["models"]["llm"]["mmproj_path"] = self.mmproj_path_card.value()
        self.config["models"]["llm"]["ngl"] = str(self.ngl_card.value())
        self.config["models"]["llm"]["ctx_size"] = str(self.ctx_card.value())
        self.config["gui"]["font_size"] = self.size_card.value()
        self.home_interface.config = self.config
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, "config.toml")
            with open(config_path, "w", encoding="utf-8") as f:
                tomli_w.dump(self.config, f)
            InfoBar.success("保存成功", "配置已成功写入 config.toml！", Qt.Orientation.Horizontal, True, InfoBarPosition.TOP, 3000, self.window())
        except Exception as e:
            InfoBar.error("保存失败", f"无法写入配置文件: {str(e)}", Qt.Orientation.Horizontal, True, InfoBarPosition.TOP, 4000, self.window())