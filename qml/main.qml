import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

Window {
    id: floatWindow

    // ── Window flags ───────────────────────────────────────────────────────
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "transparent"
    visible: true  // ← 关键：确保窗口可见

    // Initial size — height will adjust to content
    width: 900
    height: Math.max(latestLabel.implicitHeight + 30, 100)  // 确保最小高度

    // ── Public properties ──────────────────────────────────────────────────
    property int    fontSize: initialFontSize
    property string fontColor: "#FFFFFF"
    property int    bgAlpha:  140

    Connections {
        target: subtitleController
        function onTextReady(msg){
            addText(msg)
        }
    }


    // ── Subtitle queue (max 3) ─────────────────────────────────────────────
    property var subtitleTexts: []

    function addText(text) {
        console.log("添加字幕:", text);  // 添加调试输出
        subtitleTexts.push(text);
        if (subtitleTexts.length > 2)
            subtitleTexts.shift();
        refreshLabels();
    }

    function refreshLabels() {
        var len = subtitleTexts.length;
        if (len >= 1) {
            latestLabel.text = subtitleTexts[len - 1];
            latestLabel.visible = true;
        }
        if (len >= 2) {
            history1Label.text = subtitleTexts[len - 2];
            history1Label.visible = true;
        } else {
            history1Label.visible = false;
        }
        Qt.callLater(reAnchor);
    }

    // ── Screen positioning — grow upward from bottom-left ──────────────────
    property int marginLeft: 50
    property int marginBottom: 80

    function reAnchor() {
        var screenHeight = Screen.height || 1080;
        y = screenHeight - height - marginBottom;
        console.log("窗口位置:", x, y, "高度:", height);  // 调试输出
    }

    x: marginLeft
    Component.onCompleted: {
        console.log("QML 窗口已加载");
        reAnchor();
        // 添加默认测试文本
        addText("字幕应用已启动");
    }

    onHeightChanged: reAnchor()

    // ── Drag support ───────────────────────────────────────────────────────
    MouseArea {
        id: dragArea
        anchors.fill: parent
        hoverEnabled: true
        property point lastMousePos: Qt.point(0, 0)
        property bool isDragging: false

        onPressed: function(mouse) {
            lastMousePos = Qt.point(mouse.x, mouse.y);
            isDragging = true;
        }
        onPositionChanged: function(mouse) {
            if (isDragging) {
                floatWindow.x += mouse.x - lastMousePos.x;
                floatWindow.y += mouse.y - lastMousePos.y;
            }
        }
        onReleased: {
            isDragging = false;
        }
        onExited: {
            isDragging = false;
        }
    }

    // ── Visual container ───────────────────────────────────────────────────
    Rectangle {
        id: container
        anchors.fill: parent
        color: "transparent"
        clip: false

        Column {
            id: labelColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 0
            spacing: dragArea.containsMouse ? 4 : 0

            // ── History label 1 ───────────────────────────────────────────
            Rectangle {
                id: history1Bg
                anchors.left: parent.left
                anchors.right: parent.right
                height: dragArea.containsMouse && history1Label.visible
                        ? history1Label.implicitHeight + 20 : 0
                color: dragArea.containsMouse
                    ? Qt.rgba(0, 0, 0, bgAlpha * 0.75 / 255)
                    : "transparent"
                radius: 8
                clip: true

                Behavior on height { NumberAnimation { duration: 200 } }
                Behavior on color  { ColorAnimation  { duration: 200 } }

                Text {
                    id: history1Label
                    anchors.centerIn: parent
                    width: parent.width - 28
                    color: dragArea.containsMouse
                        ? Qt.rgba(1, 1, 1, 130/255)
                        : "transparent"
                    font.pointSize: dragArea.containsMouse ? fontSize * 0.75 : 12  // ← 改为 12
                    font.family: "Microsoft YaHei"
                    wrapMode: Text.WordWrap
                    visible: text !== "" && text !== undefined

                    Behavior on font.pointSize { NumberAnimation { duration: 200 } }
                    Behavior on color          { ColorAnimation  { duration: 200 } }
                }
            }

            // ── Latest label (always visible) ──────────────────────────────
            Rectangle {
                id: latestBg
                anchors.left: parent.left
                anchors.right: parent.right
                height: Math.max(latestLabel.implicitHeight + 28, 50)
                color: Qt.rgba(0, 0, 0, bgAlpha / 255)
                radius: 10
                border.color: Qt.rgba(255, 255, 255, 0.1)
                border.width: 1

                Text {
                    id: latestLabel
                    anchors.centerIn: parent
                    width: parent.width - 36
                    color: fontColor
                    font.pointSize: fontSize
                    font.family: "Microsoft YaHei"
                    font.weight: Font.Bold
                    wrapMode: Text.WordWrap
                    text: "等待语音输入..."
                    visible: true
                }
            }
        }
    }
}