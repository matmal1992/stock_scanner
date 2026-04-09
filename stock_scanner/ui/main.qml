import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    visible: true
    width: 400
    height: 300
    title: "Stock scanner"

    Rectangle {
        anchors.fill: parent

        Button {
            text: "Test"
            anchors.centerIn: parent
        }
    }
}