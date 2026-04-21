import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 1200
    height: 800
    title: "Stock scanner"

    Material.theme: Material.Dark
    Material.accent: Material.Blue

    Rectangle {
        anchors.fill: parent
        color: "#121212"

        ColumnLayout {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: 20
            spacing: 10        

            Button {
                text: "Show chart"
                Layout.alignment: Qt.AlignLeft
            }

            Button {
                text: "The wall strategy"
                Layout.alignment: Qt.AlignLeft
            }

            Button {
                text: "3T strategy"
                Layout.alignment: Qt.AlignLeft
            }
        }
    }
}