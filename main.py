# main.py (位于项目根目录)
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from qfluentwidgets import setTheme, Theme
from gui.main_window import MainWindow

if __name__ == "__main__":
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    app = QApplication(sys.argv)

    modern_font = QFont("Microsoft YaHei", 10) 
    modern_font.setStyleStrategy(QFont.PreferAntialias)
    modern_font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(modern_font)


    setTheme(Theme.DARK) 
    
    w = MainWindow()
    w.show()
    
    sys.exit(app.exec())
