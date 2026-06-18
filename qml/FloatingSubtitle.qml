import QtQuick
import QtQuick.Controls

Window {
    id: floatWindow

    // ── Window flags ───────────────────────────────────────────────────────
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    color: "transparent"

    // Initial size — height will adjust to content
    width: 900
    height: Math.max(latestLabel.implicitHeight + 30, 10)

    // ── Public properties ──────────────────────────────────────────────────
    property int    fontSize:  appConfig ? appConfig.fontSize : 32
    property string fontColor: "#FFFFFF"
    property int    bgAlpha:  140

    // ── Subtitle queue (max 3) ─────────────────────────────────────────────
    property var subtitleTexts: []

    function addText(text) {
        subtitleTexts.push(text);
        if (subtitleTexts.length > 3)
            subtitleTexts.shift();
        refreshLabels();
    }

    function refreshLabels() {
        var len = subtitleTexts.length;
        // latest = always the last entry
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
        if (len >= 3) {
            history2Label.text = subtitleTexts[len - 3];
            history2Label.visible = true;
        } else {
            history2Label.visible = false;
        }
        // Re-anchor after content change
        Qt.callLater(reAnchor);
    }

    // ── Screen positioning — grow upward from bottom-left ──────────────────
    property int marginLeft: 50
    property int marginBottom: 80

    function reAnchor() {
        y = (Screen.height > 0 ? Screen.height : 1080) - height - marginBottom;
    }

    x: marginLeft
    Component.onCompleted: reAnchor()

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
        // Clip keeps collapsed history labels from showing
        clip: false

        Column {
            id: labelColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 0
            spacing: dragArea.containsMouse ? 4 : 0

            // ── History label 2 (oldest) ───────────────────────────────────
            Rectangle {
                id: history2Bg
                anchors.left: parent.left
                anchors.right: parent.right
                height: dragArea.containsMouse && history2Label.visible
                        ? history2Label.implicitHeight + 20 : 0
                color: dragArea.containsMouse
                       ? Qt.rgba(0, 0, 0, bgAlpha * 0.75 / 255)
                       : "transparent"
                radius: 8
                clip: true

                Behavior on height { NumberAnimation { duration: 200 } }
                Behavior on color  { ColorAnimation  { duration: 200 } }

                Text {
                    id: history2Label
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 0
                    width: parent.width - 28
                    color: dragArea.containsMouse
                           ? Qt.rgba(1, 1, 1, 130/255)
                           : "transparent"
                    font.pointSize: dragArea.containsMouse
                                    ? fontSize * 0.75 : 0.1
                    font.family: "Microsoft YaHei"
                    wrapMode: Text.WordWrap
                    visible: text !== "" && text !== undefined

                    Behavior on font.pointSize { NumberAnimation { duration: 200 } }
                    Behavior on color          { ColorAnimation  { duration: 200 } }
                }
            }

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
                    font.pointSize: dragArea.containsMouse
                                    ? fontSize * 0.75 : 0.1
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
                height: latestLabel.implicitHeight + 28
                color: Qt.rgba(0, 0, 0, bgAlpha / 255)
                radius: 10

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

    // ── Respond to external fontSize changes ───────────────────────────────
    Connections {
        target: appConfig
        function onFontSizeChanged() {
            // Force label re-evaluation
            floatWindow.fontSize = appConfig.fontSize;
            Qt.callLater(reAnchor);
        }
    }
}
