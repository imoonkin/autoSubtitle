from PySide6.QtCore import Qt, QSize, QTimer, QEvent
from PySide6.QtGui import QFont, QColor, QResizeEvent
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from qfluentwidgets import BodyLabel

# 🎔 1. 悬浮字幕视窗 (完美左下角锚定 + 样式表防抖版)
class FloatingSubtitleView(QWidget):
    def __init__(self):
        super().__init__()
        # 无边框、永远置顶、工具窗口属性
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 强制开启强鼠标追踪
        self.setMouseTracking(True)
        
        # 固定宽度，高度完全交由内容撑开
        self.setFixedWidth(900)
        
        # 样式参数
        self.font_size = 32
        self.font_color = "#FFFFFF"
        self.bg_alpha = 140 
        
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(12)
        
        # 队列管理最多3个标签
        self.labels_list = []
        
        # 核心锚点：记录窗口理论上的“固定左下角”桌面坐标
        self.anchor_bottom_left = None
        
        # 初始提示
        self.set_text("等待语音输入...")
        
        # 拖拽状态
        self.m_drag = False
        self.m_DragPosition = None

    def _apply_dynamic_styles(self):
        """
        核心修复：利用 Qt 样式表的 :hover 伪状态来控制历史字幕的显示与隐藏！
        哪怕窗口失焦，操作系统的 CSS 伪状态触发也绝对不会引起任何高频抖动死循环。
        """
        # 1. 先为整个大窗口定义基础样式
        base_style = "FloatingSubtitleView { background: transparent; }"
        
        # 2. 为最新一条字幕定义样式（永远显示，独立淡黑背景）
        latest_style = f"""
            .LatestLabel {{
                color: {self.font_color}; 
                background-color: rgba(0, 0, 0, {self.bg_alpha}); 
                border-radius: 10px;
                padding: 14px 18px;
            }}
        """
        
        # 3. 为历史字幕定义【悬停触发样式】
        # 平时（非悬停）：高宽、内边距、背景全部归零，实现真正的完美隐藏和文字自适应
        # 悬停时（hover）：瞬间展开，显现淡黑背景
        history_style = f"""
            .HistoryLabel {{
                qproperty-textInteractionFlags: Qt.NoTextInteraction;
                font-size: 0px;
                color: transparent;
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }}
            FloatingSubtitleView:hover .HistoryLabel {{
                font-size: {int(self.font_size * 0.75)}px;
                color: rgba(255, 255, 255, 130); 
                background-color: rgba(0, 0, 0, {int(self.bg_alpha * 0.75)}); 
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """
        self.setStyleSheet(base_style + latest_style + history_style)

    def set_text(self, text):
        # 1. 创建新字幕标签
        new_label = BodyLabel(text, self)
        new_label.setWordWrap(True)
        
        # 2. 压入布局和列表
        self.main_layout.addWidget(new_label)
        self.labels_list.append(new_label)
        
        # 3. 超过3条时，彻底淘汰最旧的
        if len(self.labels_list) > 3:
            old_label = self.labels_list.pop(0)
            self.main_layout.removeWidget(old_label)
            old_label.deleteLater()
            
        # 4. 动态重设所有现存标签的类名（通过类名让 CSS 样式表精准控制）
        for i, label in enumerate(self.labels_list):
            if i == len(self.labels_list) - 1:
                label.setProperty("class", "LatestLabel")
                label.setFont(QFont("Microsoft YaHei", self.font_size, QFont.Weight.Bold))
            else:
                label.setProperty("class", "HistoryLabel")
                label.setFont(QFont("Microsoft YaHei", int(self.font_size * 0.75)))
                
        # 5. 重新刷新样式表应用
        self._apply_dynamic_styles()
        
        # 6. 核心：强制触发高度重算，文字变长时立刻完美适配，无需鼠标点击！
        self.main_layout.activate()
        self.adjustSize()

    # ====== 核心重写：强行以左下角为原点对齐 ======
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        
        # 如果是第一次运行或者拖拽刚结束，先初始化左下角锚点
        if self.anchor_bottom_left is None:
            self.anchor_bottom_left = self.geometry().bottomLeft()
            return
            
        # 无论是因为文字变长、变短，还是鼠标悬停展开，只要高度一变，立刻重新计算顶边 Y 轴
        new_height = event.size().height()
        new_x = self.anchor_bottom_left.x()
        new_y = self.anchor_bottom_left.y() - new_height + 1
        
        # 强行移回正确位置，实现100%完美的“向上生长”
        self.move(new_x, new_y)

    # 鼠标拖拽支持：拖拽时和释放时需要精准更新左下角钉子的位置
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.m_drag = True
            self.m_DragPosition = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.m_drag:
            self.move(event.globalPosition().toPoint() - self.m_DragPosition)
            self.anchor_bottom_left = self.geometry().bottomLeft()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.m_drag = False
        self.anchor_bottom_left = self.geometry().bottomLeft()


# 测试运行代码
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    view = FloatingSubtitleView()
    # 放置在桌面偏下方，方便观察完美的左下角对齐向上生长效果
    view.move(200, 650)
    view.show()
    
    counter = 1
    def test_add_text():
        global counter
        if counter % 2 == 0:
            # 模拟极长的文本，测试自适应刷新和左下角锁定
            txt = f"【第 {counter} 条】这是一条特别长特别长特别长的测试字幕内容！旨在测试当文本突然变得非常多的时候，窗口能不能在不点击的情况下自动完美扩展高宽，并且左下角死死钉在桌面不动，完全往上面生长！"
        else:
            txt = f"【第 {counter} 条】短字幕测试。"
        view.set_text(txt)
        counter += 1
        
    timer = QTimer()
    timer.timeout.connect(test_add_text)
    timer.start(3000)
    
    sys.exit(app.exec())
