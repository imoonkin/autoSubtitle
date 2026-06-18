import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: homePage

    // ── Reference to the floating subtitle window (set by main.qml) ────────
    property var floatingWindow: null

    // ── Track latest subtitle text locally ─────────────────────────────────
    property string latestText: ""

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        // ── Status card ───────────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 56
            color: "#2a2a2a"
            radius: 8
            border.color: "#3e3e3e"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 14

                Text {
                    text: "ℹ️"
                    font.pointSize: 18
                    color: "#4da6ff"
                }

                Text {
                    id: statusLabel
                    text: subtitleController ? subtitleController.statusText : "服务尚未启动"
                    color: "#cccccc"
                    font.pointSize: 12
                    font.family: "Microsoft YaHei"
                    Layout.fillWidth: true
                }
            }
        }

        // ── Toggle button ─────────────────────────────────────────────────
        Button {
            id: toggleBtn
            Layout.fillWidth: true
            Layout.preferredHeight: 42

            text: (subtitleController && subtitleController.isRunning)
                  ? "🛑 停止字幕服务" : "🚀 启动字幕服务"

            palette.button: (subtitleController && subtitleController.isRunning)
                            ? "#c0392b" : "#27ae60"
            palette.buttonText: "#ffffff"

            background: Rectangle {
                radius: 8
                color: (subtitleController && subtitleController.isRunning)
                       ? "#c0392b" : "#27ae60"
            }

            contentItem: Text {
                text: toggleBtn.text
                color: "#ffffff"
                font.pointSize: 13
                font.family: "Microsoft YaHei"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            onClicked: {
                if (!subtitleController) return;
                if (subtitleController.isRunning) {
                    subtitleController.stopService();
                } else {
                    subtitleController.startService();
                }
            }
        }

        // ── Font size slider ──────────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 56
            color: "#2a2a2a"
            radius: 8

            RowLayout {
                anchors.fill: parent
                anchors.margins: 14

                Text {
                    text: "字幕字体大小:"
                    color: "#cccccc"
                    font.pointSize: 12
                    font.family: "Microsoft YaHei"
                }

                Slider {
                    id: homeSizeSlider
                    Layout.fillWidth: true
                    from: 12
                    to: 72
                    stepSize: 1
                    value: appConfig ? appConfig.fontSize : 32

                    onMoved: {
                        if (appConfig) appConfig.fontSize = value;
                    }
                }

                Text {
                    text: homeSizeSlider.value.toFixed(0)
                    color: "#888888"
                    font.pointSize: 12
                    Layout.preferredWidth: 30
                }
            }
        }

        // ── Subtitle preview area ─────────────────────────────────────────
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 140
            color: "#1a1a1a"
            border.color: "#3e3e3e"
            radius: 8

            Text {
                id: previewText
                anchors.centerIn: parent
                width: parent.width - 30
                text: latestText !== "" ? latestText : "这里是实时智能字幕显示区域"
                color: "#FFFFFF"
                font.pointSize: appConfig ? appConfig.fontSize : 32
                font.family: "Microsoft YaHei"
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }
        }

        Item { Layout.fillHeight: true }
    }

    // ── Wire up signals from subtitleController ────────────────────────────
    Connections {
        target: subtitleController
        enabled: subtitleController !== null

        function onTextReady(text) {
            latestText = text;
            // Forward to floating subtitle window
            if (homePage.floatingWindow) {
                homePage.floatingWindow.addText(text);
            }
        }

        function onStatusChanged(text) {
            // statusLabel is bound to subtitleController.statusText, auto-updates
        }

        function onRunningChanged(running) {
            if (homePage.floatingWindow) {
                if (running) {
                    homePage.floatingWindow.show();
                } else {
                    homePage.floatingWindow.hide();
                }
            }
        }
    }
}
