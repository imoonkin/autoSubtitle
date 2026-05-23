# main.py (位于项目根目录)
import sys
from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme
from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 统一设置 qfluentwidgets 的暗色主题
    setTheme(Theme.DARK) 
    
    # 启动主窗口
    w = MainWindow()
    w.show()
    
    sys.exit(app.exec())
