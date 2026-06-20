import os
import sys
import time
from PySide6.QtGui import QGuiApplication, QFont
from PySide6.QtQml import QQmlApplicationEngine
from config import load_config_dict
from backend.controller import SubtitleController

if __name__ == "__main__":
    # 保持缩放策略
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

    app = QGuiApplication(sys.argv)

    # 设置全局字体
    modern_font = QFont("Microsoft YaHei", 10)
    modern_font.setStyleStrategy(QFont.PreferAntialias)
    modern_font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(modern_font)

    # 1. 实例化后端对象
    config_data = load_config_dict()
    subtitle_controller = SubtitleController()
    subtitle_controller.startService()
    # 2. 创建 QML 引擎
    engine = QQmlApplicationEngine()

    # 3. 将 Python 后端对象注入到 QML 全局上下文中
    font_size = config_data.get("gui", {}).get("font_size", 32)
    engine.rootContext().setContextProperty("initialFontSize", font_size)
    engine.rootContext().setContextProperty("subtitleController", subtitle_controller)
    
    # 4. 加载主 QML 文件
    qml_file = os.path.join(os.path.dirname(__file__), "qml\\main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        sys.exit(-1)

    

    sys.exit(app.exec())
