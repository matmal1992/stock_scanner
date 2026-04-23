import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs

ApplicationWindow {
    visible: true
    width: 1200
    height: 800
    title: "Stock scanner"

    Material.theme: Material.Dark
    Material.accent: Material.Blue

        FileDialog {
        id: fileDialog
        title: "Select parquet file"
        nameFilters: ["Parquet files (*.parquet)"]
        onAccepted: {
            console.log("Selected:", selectedFile)
            bridge.loadChart(selectedFile)
        }
    }

    RowLayout {
        anchors.fill: parent

        // SIDEBAR (menu po lewej)
        Rectangle {
            Layout.preferredWidth: 220
            Layout.fillHeight: true
            color: "#1e1e1e"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10

                Label {
                    text: "Strategies"
                    font.pixelSize: 18
                    color: "white"
                }

                Button { text: "Show chart" 
                         onClicked: fileDialog.open()
                }

                Button { text: "Speculation bubble" }
                Button { text: "The wall strategy" }
                // defined urls/sources for news, only selected stocks, maybe some sentiment analysis included
                Button { text: "News tracker" } 

                Button { text: "3T strategy"
                         onClicked: bridge.run3T()
                }

                Item { Layout.fillHeight: true } // wypycha dół

                Button {
                    text: "Settings"
                }
            }
        }

        // MAIN PANEL (wykresy / tabela)
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#121212"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10

                Label {
                    text: "Main Panel"
                    font.pixelSize: 20
                    color: "white"
                }

                // Placeholder pod wykres
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 8
                    color: "#2a2a2a"

                    Label {
                        text: "Chart / Table will be here"
                        anchors.centerIn: parent
                        color: "#aaaaaa"
                    }
                }
            }
        }
    }
}