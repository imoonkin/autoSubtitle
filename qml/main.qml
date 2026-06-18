import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    visible: true
    width: 750
    height: 600
    title: "AI 实时智能字幕系统"

    // Dark theme background
    background: Rectangle { color: "#1e1e1e" }

    // ── Main layout: sidebar + content ─────────────────────────────────────
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ── Left sidebar navigation ───────────────────────────────────────
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 180
            color: "#1c1c1c"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                // App title
                Text {
                    text: "autoSubtitle"
                    color: "#4da6ff"
                    font.pointSize: 14
                    font.bold: true
                    font.family: "Microsoft YaHei"
                    Layout.leftMargin: 6
                    Layout.topMargin: 6
                    Layout.bottomMargin: 10
                }

                // ── Nav button: Home ──────────────────────────────────────
                Button {
                    id: btnHome
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38

                    property bool isActive: stackLayout.currentIndex === 0

                    background: Rectangle {
                        radius: 6
                        color: btnHome.isActive ? "#333333" : "transparent"
                    }

                    contentItem: RowLayout {
                        spacing: 8
                        Text {
                            text: "🏠"
                            font.pointSize: 14
                        }
                        Text {
                            text: "主控制台"
                            color: "#cccccc"
                            font.pointSize: 12
                            font.family: "Microsoft YaHei"
                        }
                    }

                    onClicked: stackLayout.currentIndex = 0
                }

                // ── Nav button: Settings ──────────────────────────────────
                Button {
                    id: btnSettings
                    Layout.fillWidth: true
                    Layout.preferredHeight: 38

                    property bool isActive: stackLayout.currentIndex === 1

                    background: Rectangle {
                        radius: 6
                        color: btnSettings.isActive ? "#333333" : "transparent"
                    }

                    contentItem: RowLayout {
                        spacing: 8
                        Text {
                            text: "⚙️"
                            font.pointSize: 14
                        }
                        Text {
                            text: "设置面板"
                            color: "#cccccc"
                            font.pointSize: 12
                            font.family: "Microsoft YaHei"
                        }
                    }

                    onClicked: stackLayout.currentIndex = 1
                }

                // Spacer
                Item { Layout.fillHeight: true }

                // Version hint
                Text {
                    text: "v0.1.0"
                    color: "#555555"
                    font.pointSize: 10
                    font.family: "Microsoft YaHei"
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }

        // ── Right content area ────────────────────────────────────────────
        StackLayout {
            id: stackLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: 0

            HomeInterface {
                id: homeInterface
                floatingWindow: floatingSubtitle
            }

            SettingsInterface {
                id: settingsInterface
            }
        }
    }

    // ── Floating subtitle overlay window ───────────────────────────────────
    FloatingSubtitle {
        id: floatingSubtitle
        visible: false  // shown when service starts
    }
}
