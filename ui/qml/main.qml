import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 1200
    height: 800
    title: "FEM 2D App"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            width: 220
            color: "#20242b"
            Layout.fillHeight: true

            Label {
                anchors.centerIn: parent
                text: "左侧工具区"
                color: "white"
            }
        }

        Rectangle {
            color: "#2b3038"
            Layout.fillWidth: true
            Layout.fillHeight: true

            Label {
                anchors.centerIn: parent
                text: "中央画布区"
                color: "white"
            }
        }

        Rectangle {
            width: 260
            color: "#20242b"
            Layout.fillHeight: true

            Label {
                anchors.centerIn: parent
                text: "右侧属性区"
                color: "white"
            }
        }
    }
}