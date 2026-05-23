# gui/main_window.py
from qfluentwidgets import FluentWindow, FluentIcon
from gui.home_interface import HomeInterface
from gui.setting_interface import SettingInterface

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 实时智能字幕系统")
        self.resize(750, 600)  # 设置页内容稍多，稍微加宽一点窗口
        
        # 1. 实例化主控制台
        self.home_interface = HomeInterface(self)
        
        # 2. 🌟 实例化设置页面，并将 home_interface 作为参数传进去（以便两个页面实现通信）
        self.setting_interface = SettingInterface(self.home_interface, self)
        
        # 3. 将页面添加到侧边栏导航中
        self.addSubInterface(self.home_interface, FluentIcon.HOME, "主控制台")
        self.addSubInterface(self.setting_interface, FluentIcon.SETTING, "设置面板")
        
        # 初始化设置页面的字体大小初始值（从 config 加载，防止每次打开都是默认的 32）
        gui_config = self.setting_interface.config.get("gui", {})
        saved_size = gui_config.get("font_size", 32)
        self.setting_interface.size_card.setValue(saved_size)
        self.home_interface.sub_view.update_style(saved_size, "#FFFFFF", 150)
        
        gui_config = self.setting_interface.config.get("gui", {})
        saved_size = gui_config.get("font_size", 32)
        # 使用带大写 V 的标准 Qt 方法为自定义滑块卡片赋值
        self.setting_interface.size_card.setValue(saved_size) 
        self.home_interface.sub_view.update_style(saved_size, "#FFFFFF", 150)