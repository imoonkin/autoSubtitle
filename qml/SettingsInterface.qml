import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Item {
    id: settingsPage

    // ── Toast state ────────────────────────────────────────────────────────
    property string toastMessage: ""
    property bool   toastSuccess: true
    property bool   toastVisible: false

    function showToast(success, message) {
        toastSuccess = success;
        toastMessage = message;
        toastVisible = true;
        toastTimer.restart();
    }

    Timer {
        id: toastTimer
        interval: 3000
        onTriggered: toastVisible = false
    }

    // ── Wire configSaved signal ────────────────────────────────────────────
    Connections {
        target: appConfig
        enabled: appConfig !== null
        function onConfigSaved(success, message) {
            settingsPage.showToast(success, message);
        }
    }

    // ── Scrollable content ─────────────────────────────────────────────────
    ScrollView {
        anchors.fill: parent
        clip: true
        background: Rectangle { color: "#1e1e1e" }

        ColumnLayout {
            width: settingsPage.width > 40 ? settingsPage.width - 40 : 560
            x: 20
            spacing: 20

            // Page title
            Text {
                text: "设置面板"
                color: "#ffffff"
                font.bold: true
                font.pointSize: 16
                font.family: "Microsoft YaHei"
                Layout.topMargin: 20
            }

            // ═══════════════════════════════════════════════════════════════
            // 1. 🎨 字幕外观设置
            // ═══════════════════════════════════════════════════════════════
            Rectangle {
                Layout.fillWidth: true
                height: subtitleGroupCol.implicitHeight + 24
                color: "#262626"
                radius: 8

                ColumnLayout {
                    id: subtitleGroupCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 10

                    Text {
                        text: "🎨 字幕外观设置"
                        color: "#ffffff"
                        font.pointSize: 14
                        font.bold: true
                        font.family: "Microsoft YaHei"
                    }

                    // Font size card
                    Rectangle {
                        Layout.fillWidth: true
                        height: 56
                        color: "#2a2a2a"
                        radius: 6

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text {
                                    text: "字体大小"
                                    color: "#ffffff"
                                    font.bold: true
                                    font.pointSize: 12
                                    font.family: "Microsoft YaHei"
                                }
                                Text {
                                    text: "调整悬浮字幕窗口的文字大小"
                                    color: "#a0a0a0"
                                    font.pointSize: 11
                                    font.family: "Microsoft YaHei"
                                }
                            }

                            Slider {
                                id: fontSizeSlider
                                from: 16; to: 60; stepSize: 1
                                value: appConfig ? appConfig.fontSize : 32
                                Layout.preferredWidth: 150
                                onMoved: { if (appConfig) appConfig.fontSize = value; }
                            }

                            Text {
                                text: fontSizeSlider.value.toFixed(0)
                                color: "#ffffff"
                                font.pointSize: 12
                                Layout.preferredWidth: 28
                            }
                        }
                    }
                }
            }

            // ═══════════════════════════════════════════════════════════════
            // 2. 🎙️ VAD 语音断句设置
            // ═══════════════════════════════════════════════════════════════
            Rectangle {
                Layout.fillWidth: true
                height: vadGroupCol.implicitHeight + 24
                color: "#262626"
                radius: 8

                ColumnLayout {
                    id: vadGroupCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 10

                    Text {
                        text: "🎙️ VAD 语音断句设置 [models.vad]"
                        color: "#ffffff"
                        font.pointSize: 14
                        font.bold: true
                        font.family: "Microsoft YaHei"
                    }

                    // VAD model path card
                    Rectangle {
                        Layout.fillWidth: true; height: 56
                        color: "#2a2a2a"; radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { text: "VAD 模型路径"; color: "#ffffff"; font.bold: true; font.pointSize: 12; font.family: "Microsoft YaHei" }
                                Text { text: "ONNX 格式的语音检测模型"; color: "#a0a0a0"; font.pointSize: 11; font.family: "Microsoft YaHei" }
                            }
                            TextField {
                                id: vadPathField
                                Layout.preferredWidth: 220
                                text: appConfig ? appConfig.vadModelPath : ""
                                color: "#ffffff"; font.pointSize: 11; font.family: "Microsoft YaHei"
                                background: Rectangle { color: "#1a1a1a"; radius: 4; border.color: "#3e3e3e" }
                                onTextChanged: { if (appConfig) appConfig.vadModelPath = text; }
                            }
                            Button {
                                Layout.preferredWidth: 70
                                background: Rectangle { color: "#3a3a3a"; radius: 4 }
                                contentItem: Text { text: "浏览..."; color: "#ffffff"; font.pointSize: 11; font.family: "Microsoft YaHei"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                onClicked: vadFileDialog.open()
                            }
                        }
                    }

                    // max_silence_chunks
                    Rectangle {
                        Layout.fillWidth: true; height: 56
                        color: "#2a2a2a"; radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { text: "静音强断红线 (max_silence_chunks)"; color: "#ffffff"; font.bold: true; font.pointSize: 12; font.family: "Microsoft YaHei" }
                                Text { text: "多少个静音块后判定为一句话结束"; color: "#a0a0a0"; font.pointSize: 11; font.family: "Microsoft YaHei" }
                            }
                            Slider {
                                id: silenceSlider
                                from: 5; to: 100; stepSize: 1
                                value: appConfig ? appConfig.maxSilenceChunks : 25
                                Layout.preferredWidth: 150
                                onMoved: { if (appConfig) appConfig.maxSilenceChunks = value; }
                            }
                            Text { text: silenceSlider.value.toFixed(0); color: "#ffffff"; font.pointSize: 12; Layout.preferredWidth: 28 }
                        }
                    }

                    // max_speech_duration_s
                    Rectangle {
                        Layout.fillWidth: true; height: 56
                        color: "#2a2a2a"; radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { text: "单句最长限制 (max_speech_duration_s)"; color: "#ffffff"; font.bold: true; font.pointSize: 12; font.family: "Microsoft YaHei" }
                                Text { text: "超过该秒数即使没停顿也强制断句"; color: "#a0a0a0"; font.pointSize: 11; font.family: "Microsoft YaHei" }
                            }
                            Slider {
                                id: durationSlider
                                from: 3; to: 30; stepSize: 1
                                value: appConfig ? appConfig.maxSpeechDurationS : 10
                                Layout.preferredWidth: 150
                                onMoved: { if (appConfig) appConfig.maxSpeechDurationS = value; }
                            }
                            Text { text: durationSlider.value.toFixed(0); color: "#ffffff"; font.pointSize: 12; Layout.preferredWidth: 28 }
                        }
                    }
                }
            }

            // ═══════════════════════════════════════════════════════════════
            // 3. 🧠 ASR / LLM 核心配置
            // ═══════════════════════════════════════════════════════════════
            Rectangle {
                Layout.fillWidth: true
                height: llmGroupCol.implicitHeight + 24
                color: "#262626"
                radius: 8

                ColumnLayout {
                    id: llmGroupCol
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 10

                    Text {
                        text: "🧠 ASR / LLM 核心配置 [models.llm]"
                        color: "#ffffff"
                        font.pointSize: 14
                        font.bold: true
                        font.family: "Microsoft YaHei"
                    }

                    // Part A: Helper function for file-path cards
                    // (repeated inline below for reliability)

                    // ── llama-server exe path ─────────────────────────────
                    Rectangle {
                        Layout.fillWidth: true; height: 56
                        color: "#2a2a2a"; radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { text: "llama-server 执行文件"; color: "#ffffff"; font.bold: true; font.pointSize: 12; font.family: "Microsoft YaHei" }
                                Text { text: "llama-server.exe 的存放路径"; color: "#a0a0a0"; font.pointSize: 11; font.family: "Microsoft YaHei" }
                            }
                            TextField {
                                id: llmExePathField
                                Layout.preferredWidth: 220
                                text: appConfig ? appConfig.llmExePath : ""
                                color: "#ffffff"; font.pointSize: 11; font.family: "Microsoft YaHei"
                                background: Rectangle { color: "#1a1a1a"; radius: 4; border.color: "#3e3e3e" }
                                onTextChanged: { if (appConfig) appConfig.llmExePath = text; }
                            }
                            Button {
                                Layout.preferredWidth: 70
                                background: Rectangle { color: "#3a3a3a"; radius: 4 }
                                contentItem: Text { text: "浏览..."; color: "#ffffff"; font.pointSize: 11; font.family: "Microsoft YaHei"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                onClicked: llmExeFileDialog.open()
                            }
                        }
                    }

                    // ── ASR model path ────────────────────────────────────
                    Rectangle {
                        Layout.fillWidth: true; height: 56
                        color: "#2a2a2a"; radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { text: "ASR 模型路径"; color: "#ffffff"; font.bold: true; font.pointSize: 12; font.family: "Microsoft YaHei" }
                                Text { text: "ASR语音模型的 .gguf 文件"; color: "#a0a0a0"; font.pointSize: 11; font.family: "Microsoft YaHei" }
                            }
                            TextField {
                                id: llmModelPathField
                                Layout.preferredWidth: 220
                                text: appConfig ? appConfig.llmModelPath : ""
                                color: "#ffffff"; font.pointSize: 11; font.family: "Microsoft YaHei"
                                background: Rectangle { color: "#1a1a1a"; radius: 4; border.color: "#3e3e3e" }
                                onTextChanged: { if (appConfig) appConfig.llmModelPath = text; }
                            }
                            Button {
                                Layout.preferredWidth: 70
                                background: Rectangle { color: "#3a3a3a"; radius: 4 }
                                contentItem: Text { text: "浏览..."; color: "#ffffff"; font.pointSize: 11; font.family: "Microsoft YaHei"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                onClicked: llmModelFileDialog.open()
                            }
                        }
                    }

                    // ── mmproj path ───────────────────────────────────────
                    Rectangle {
                        Layout.fillWidth: true; height: 56
                        color: "#2a2a2a"; radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { text: "多模态投影文件 (mmproj)"; color: "#ffffff"; font.bold: true; font.pointSize: 12; font.family: "Microsoft YaHei" }
                                Text { text: "Qwen3-ASR 必须的 mmproj 路径"; color: "#a0a0a0"; font.pointSize: 11; font.family: "Microsoft YaHei" }
                            }
                            TextField {
                                id: llmMmprojPathField
                                Layout.preferredWidth: 220
                                text: appConfig ? appConfig.llmMmprojPath : ""
                                color: "#ffffff"; font.pointSize: 11; font.family: "Microsoft YaHei"
                                background: Rectangle { color: "#1a1a1a"; radius: 4; border.color: "#3e3e3e" }
                                onTextChanged: { if (appConfig) appConfig.llmMmprojPath = text; }
                            }
                            Button {
                                Layout.preferredWidth: 70
                                background: Rectangle { color: "#3a3a3a"; radius: 4 }
                                contentItem: Text { text: "浏览..."; color: "#ffffff"; font.pointSize: 11; font.family: "Microsoft YaHei"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                onClicked: llmMmprojFileDialog.open()
                            }
                        }
                    }

                    // ── ngl slider ────────────────────────────────────────
                    Rectangle {
                        Layout.fillWidth: true; height: 56
                        color: "#2a2a2a"; radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { text: "GPU 卸载层数 (ngl)"; color: "#ffffff"; font.bold: true; font.pointSize: 12; font.family: "Microsoft YaHei" }
                                Text { text: "核心显卡填0，独立显卡（Vulkan/CUDA）填99"; color: "#a0a0a0"; font.pointSize: 11; font.family: "Microsoft YaHei" }
                            }
                            Slider {
                                id: nglSlider
                                from: 0; to: 150; stepSize: 1
                                value: appConfig ? appConfig.ngl : 99
                                Layout.preferredWidth: 150
                                onMoved: { if (appConfig) appConfig.ngl = value; }
                            }
                            Text { text: nglSlider.value.toFixed(0); color: "#ffffff"; font.pointSize: 12; Layout.preferredWidth: 28 }
                        }
                    }

                    // ── ctx_size slider ───────────────────────────────────
                    Rectangle {
                        Layout.fillWidth: true; height: 56
                        color: "#2a2a2a"; radius: 6
                        RowLayout {
                            anchors.fill: parent; anchors.margins: 12
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 2
                                Text { text: "上下文窗口大小 (ctx_size)"; color: "#ffffff"; font.bold: true; font.pointSize: 12; font.family: "Microsoft YaHei" }
                                Text { text: "推理上下文大小，ASR 默认为 4096"; color: "#a0a0a0"; font.pointSize: 11; font.family: "Microsoft YaHei" }
                            }
                            Slider {
                                id: ctxSlider
                                from: 512; to: 8192; stepSize: 1
                                value: appConfig ? appConfig.ctxSize : 4096
                                Layout.preferredWidth: 150
                                onMoved: { if (appConfig) appConfig.ctxSize = value; }
                            }
                            Text { text: ctxSlider.value.toFixed(0); color: "#ffffff"; font.pointSize: 12; Layout.preferredWidth: 28 }
                        }
                    }
                }
            }

            // ═══════════════════════════════════════════════════════════════
            // 4. 💾 保存按钮
            // ═══════════════════════════════════════════════════════════════
            Button {
                Layout.fillWidth: true
                Layout.preferredHeight: 42

                background: Rectangle { color: "#2563eb"; radius: 8 }

                contentItem: Text {
                    text: "💾 保存并应用配置"
                    color: "#ffffff"
                    font.pointSize: 13; font.bold: true
                    font.family: "Microsoft YaHei"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: { if (appConfig) appConfig.saveConfig(); }
            }

            // Bottom spacer
            Item { Layout.preferredHeight: 30 }

        } // end ColumnLayout
    } // end ScrollView

    // ── Toast overlay ──────────────────────────────────────────────────────
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 30
        width: toastLabel.implicitWidth + 40
        height: 44
        radius: 8
        color: toastSuccess ? "#166534" : "#7f1d1d"
        border.color: toastSuccess ? "#22c55e" : "#ef4444"
        visible: toastVisible

        Text {
            id: toastLabel
            anchors.centerIn: parent
            text: toastMessage
            color: "#ffffff"
            font.pointSize: 12
            font.family: "Microsoft YaHei"
        }
    }

    // ═══════════════════════════════════════════════════════════════════
    // File dialogs
    // ═══════════════════════════════════════════════════════════════════

    FileDialog {
        id: vadFileDialog
        title: "选择 VAD 模型文件"
        fileMode: FileDialog.OpenFile
        nameFilters: ["ONNX Files (*.onnx)", "All Files (*.*)"]
        onAccepted: {
            var path = selectedFile.toString().replace(/^file:\/\/\//, "");
            vadPathField.text = decodeURIComponent(path);
        }
    }

    FileDialog {
        id: llmExeFileDialog
        title: "选择 llama-server 执行文件"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Executables (*.exe)", "All Files (*.*)"]
        onAccepted: {
            var path = selectedFile.toString().replace(/^file:\/\/\//, "");
            llmExePathField.text = decodeURIComponent(path);
        }
    }

    FileDialog {
        id: llmModelFileDialog
        title: "选择 ASR 模型文件"
        fileMode: FileDialog.OpenFile
        nameFilters: ["GGUF Models (*.gguf)", "All Files (*.*)"]
        onAccepted: {
            var path = selectedFile.toString().replace(/^file:\/\/\//, "");
            llmModelPathField.text = decodeURIComponent(path);
        }
    }

    FileDialog {
        id: llmMmprojFileDialog
        title: "选择多模态投影文件"
        fileMode: FileDialog.OpenFile
        nameFilters: ["GGUF Models (*.gguf)", "All Files (*.*)"]
        onAccepted: {
            var path = selectedFile.toString().replace(/^file:\/\/\//, "");
            llmMmprojPathField.text = decodeURIComponent(path);
        }
    }
}
