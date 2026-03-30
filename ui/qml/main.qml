import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window

    visible: true
    width: 1520
    height: 920
    title: "FEM2D Studio"
    color: "#d8dde5"

    property color bgWindow: "#d8dde5"
    property color bgDark: "#2f3742"
    property color bgToolbar: "#e7ebf0"
    property color bgPanel: "#f4f6f9"
    property color bgPanel2: "#eef2f6"
    property color bgPanel3: "#ffffff"
    property color borderColor: "#c8d0da"
    property color textMain: "#1f2a36"
    property color textMuted: "#5f6b78"
    property color accent: "#4f79c7"
    property color accentSoft: "#dbe6fb"
    property color viewportBg: "#f9fbfd"

    property string shell_status: "工程界面骨架已加载"
    property string viewport_mode: "模型"
    property string current_workspace: "模型-1"
    property string selection_info: "无"

    component HeaderActionButton: ToolButton {
        id: control

        property bool emphasized: false

        implicitHeight: 28
        implicitWidth: Math.max(68, label.implicitWidth + 20)
        padding: 0
        hoverEnabled: true

        background: Rectangle {
            radius: 4
            color: control.down
                   ? (control.emphasized ? "#416ab2" : "#dbe3ec")
                   : control.hovered
                     ? (control.emphasized ? "#5a84d2" : "#eef3f8")
                     : (control.emphasized ? accent : "#f8fafc")
            border.color: control.emphasized ? "#4068b0" : "#cdd6e0"
        }

        contentItem: Text {
            id: label
            text: control.text
            color: control.emphasized ? "#ffffff" : textMain
            font.pixelSize: 12
            font.bold: control.emphasized
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    component HeaderComboBox: ComboBox {
        id: control

        implicitWidth: 124
        implicitHeight: 28
        leftPadding: 10
        rightPadding: 26
        hoverEnabled: true

        contentItem: Text {
            text: control.displayText
            color: textMain
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
        }

        background: Rectangle {
            radius: 4
            color: control.down ? "#eef3f8" : "#f8fafc"
            border.color: "#cdd6e0"
        }

        indicator: Canvas {
            x: control.width - width - 10
            y: (control.height - height) / 2
            width: 10
            height: 6
            contextType: "2d"

            onPaint: {
                context.reset()
                context.beginPath()
                context.moveTo(0, 0)
                context.lineTo(width, 0)
                context.lineTo(width / 2, height)
                context.closePath()
                context.fillStyle = "#5f6b78"
                context.fill()
            }
        }

        delegate: ItemDelegate {
            width: control.width
            text: modelData
            highlighted: control.highlightedIndex === index

            contentItem: Text {
                text: modelData
                color: textMain
                font.pixelSize: 12
                verticalAlignment: Text.AlignVCenter
            }

            background: Rectangle {
                color: parent.highlighted ? accentSoft : (parent.hovered ? "#f6f9fd" : "#ffffff")
            }
        }

        popup: Popup {
            y: control.height + 4
            width: control.width
            padding: 1

            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex
            }

            background: Rectangle {
                radius: 4
                color: "#ffffff"
                border.color: "#cdd6e0"
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 86
            color: bgDark
            border.color: "#25303b"
            clip: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    color: bgDark

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 12

                        Label {
                            text: "FEM2D Studio"
                            color: "#f2f5f8"
                            font.pixelSize: 16
                            font.bold: true
                        }

                        Rectangle {
                            width: 1
                            height: 16
                            color: "#65707c"
                        }

                        Label {
                            text: "当前工程：" + current_workspace
                            color: "#cfd7e1"
                            font.pixelSize: 13
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            radius: 4
                            color: "#44505d"
                            border.color: "#536170"
                            implicitWidth: 150
                            implicitHeight: 22

                            Label {
                                anchors.centerIn: parent
                                text: "模式：" + appController.current_mode
                                color: "#eef3f7"
                                font.pixelSize: 12
                            }
                        }

                        Rectangle {
                            radius: 4
                            color: "#44505d"
                            border.color: "#536170"
                            implicitWidth: 190
                            implicitHeight: 22

                            Label {
                                anchors.centerIn: parent
                                text: "状态：" + appController.status_text
                                color: "#eef3f7"
                                font.pixelSize: 12
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: bgToolbar
                    border.color: "#c7d0da"
                    clip: true

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8

                        Rectangle {
                            radius: 6
                            color: "#f3f6fa"
                            border.color: borderColor
                            implicitHeight: 38
                            Layout.preferredWidth: 278
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 6

                                Label {
                                    text: "文件"
                                    color: textMuted
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                HeaderActionButton {
                                    text: "新建"
                                    onClicked: {
                                        appController.new_model()
                                        shell_status = "已新建空项目"
                                    }
                                }

                                HeaderActionButton {
                                    text: "打开"
                                    onClicked: shell_status = "打开工程：占位功能"
                                }

                                HeaderActionButton {
                                    text: "保存"
                                    onClicked: shell_status = "保存工程：占位功能"
                                }
                            }
                        }

                        Rectangle {
                            radius: 6
                            color: "#f3f6fa"
                            border.color: borderColor
                            implicitHeight: 38
                            Layout.preferredWidth: 440
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 6

                                Label {
                                    text: "建模"
                                    color: textMuted
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                HeaderActionButton {
                                    text: "节点"
                                    onClicked: {
                                        appController.set_node_mode()
                                        shell_status = "已切换到节点编辑模式"
                                    }
                                }

                                HeaderActionButton {
                                    text: "单元"
                                    onClicked: {
                                        appController.set_element_mode()
                                        shell_status = "已切换到单元编辑模式"
                                    }
                                }

                                HeaderActionButton {
                                    text: "材料"
                                    onClicked: shell_status = "材料编辑：占位功能"
                                }

                                HeaderActionButton {
                                    text: "约束"
                                    onClicked: shell_status = "约束编辑：占位功能"
                                }

                                HeaderActionButton {
                                    text: "载荷"
                                    onClicked: shell_status = "载荷编辑：占位功能"
                                }
                            }
                        }

                        Rectangle {
                            radius: 6
                            color: "#f3f6fa"
                            border.color: borderColor
                            implicitHeight: 38
                            Layout.preferredWidth: 278
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 6

                                Label {
                                    text: "分析"
                                    color: textMuted
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                HeaderActionButton {
                                    text: "网格"
                                    onClicked: shell_status = "网格模块：占位功能"
                                }

                                HeaderActionButton {
                                    text: "求解"
                                    emphasized: true
                                    onClicked: shell_status = "求解入口：占位功能"
                                }

                                HeaderActionButton {
                                    text: "结果"
                                    onClicked: shell_status = "结果查看：占位功能"
                                }
                            }
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            radius: 6
                            color: "#f3f6fa"
                            border.color: borderColor
                            implicitHeight: 38
                            Layout.preferredWidth: 214
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 8

                                Label {
                                    text: "视图"
                                    color: textMuted
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                HeaderComboBox {
                                    Layout.fillWidth: true
                                    model: ["模型", "网格", "结果"]
                                    currentIndex: 0
                                    onActivated: {
                                        viewport_mode = currentText
                                        shell_status = "视图模式切换到 " + currentText
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            Rectangle {
                SplitView.minimumWidth: 250
                SplitView.preferredWidth: 280
                color: bgPanel2
                border.color: borderColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        radius: 6
                        color: "#e6ebf1"
                        border.color: borderColor

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10

                            Label {
                                text: "导航区"
                                color: textMain
                                font.pixelSize: 13
                                font.bold: true
                            }

                            Item {
                                Layout.fillWidth: true
                            }

                            Label {
                                text: "模块"
                                color: textMuted
                                font.pixelSize: 12
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 6
                        color: bgPanel3
                        border.color: borderColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Label {
                                text: "模块浏览器"
                                color: textMain
                                font.pixelSize: 13
                                font.bold: true
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: "#fbfcfd"
                                border.color: "#d7dee6"
                                radius: 4

                                ListView {
                                    anchors.fill: parent
                                    clip: true
                                    model: [
                                        "零件",
                                        "属性",
                                        "装配",
                                        "分析步",
                                        "相互作用",
                                        "载荷",
                                        "网格",
                                        "任务",
                                        "后处理"
                                    ]

                                    delegate: ItemDelegate {
                                        width: ListView.view.width
                                        text: modelData
                                        onClicked: {
                                            selection_info = modelData
                                            shell_status = "进入模块：" + modelData + "（占位）"
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 240
                        radius: 6
                        color: bgPanel3
                        border.color: borderColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Label {
                                text: "模型树"
                                color: textMain
                                font.pixelSize: 13
                                font.bold: true
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: "#fbfcfd"
                                border.color: "#d7dee6"
                                radius: 4

                                ListView {
                                    anchors.fill: parent
                                    clip: true
                                    model: [
                                        "模型-1",
                                        "  ├─ 零件",
                                        "  ├─ 材料",
                                        "  ├─ 截面",
                                        "  ├─ 装配",
                                        "  ├─ 分析步",
                                        "  ├─ 载荷",
                                        "  └─ 网格"
                                    ]

                                    delegate: ItemDelegate {
                                        width: ListView.view.width
                                        text: modelData
                                        onClicked: {
                                            selection_info = modelData
                                            shell_status = "选中：" + modelData
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 180
                        radius: 6
                        color: bgPanel3
                        border.color: borderColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Label {
                                text: "快捷操作"
                                color: textMain
                                font.pixelSize: 13
                                font.bold: true
                            }

                            Button {
                                Layout.fillWidth: true
                                text: "创建节点"
                                onClicked: {
                                    appController.set_node_mode()
                                    shell_status = "创建节点：占位功能"
                                }
                            }

                            Button {
                                Layout.fillWidth: true
                                text: "创建单元"
                                onClicked: {
                                    appController.set_element_mode()
                                    shell_status = "创建单元：占位功能"
                                }
                            }

                            Button {
                                Layout.fillWidth: true
                                text: "分配材料"
                                onClicked: shell_status = "分配材料：占位功能"
                            }
                        }
                    }
                }
            }

            SplitView {
                SplitView.fillWidth: true
                orientation: Qt.Vertical

                Rectangle {
                    SplitView.fillHeight: true
                    color: bgPanel
                    border.color: borderColor

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 40
                            radius: 6
                            color: "#e6ebf1"
                            border.color: borderColor

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 10

                                Repeater {
                                    model: ["零件", "属性", "装配", "分析步", "载荷", "网格", "任务", "后处理"]

                                    delegate: Rectangle {
                                        implicitWidth: 92
                                        implicitHeight: 26
                                        radius: 4
                                        color: index === 0 ? accentSoft : "#f6f8fa"
                                        border.color: index === 0 ? accent : "#cfd6df"

                                        Label {
                                            anchors.centerIn: parent
                                            text: modelData
                                            color: index === 0 ? accent : textMain
                                            font.pixelSize: 12
                                            font.bold: index === 0
                                        }
                                    }
                                }

                                Item {
                                    Layout.fillWidth: true
                                }

                                Label {
                                    text: "视口"
                                    color: textMuted
                                    font.pixelSize: 12
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 6
                            color: bgPanel3
                            border.color: borderColor

                            Rectangle {
                                id: viewportHeader
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                height: 36
                                color: "#edf1f5"
                                border.color: "#d3dae3"

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 12

                                    Label {
                                        text: "视口：1"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle {
                                        width: 1
                                        height: 16
                                        color: "#c7d0da"
                                    }

                                    Label {
                                        text: "视图：" + viewport_mode
                                        color: textMuted
                                        font.pixelSize: 12
                                    }

                                    Label {
                                        text: "当前选择：" + selection_info
                                        color: textMuted
                                        font.pixelSize: 12
                                    }

                                    Item {
                                        Layout.fillWidth: true
                                    }

                                    Label {
                                        text: "模式：" + appController.current_mode
                                        color: textMuted
                                        font.pixelSize: 12
                                    }
                                }
                            }

                            Rectangle {
                                id: viewport
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: viewportHeader.bottom
                                anchors.bottom: parent.bottom
                                anchors.margins: 14
                                radius: 4
                                color: viewportBg
                                border.color: "#d6dde6"

                                Repeater {
                                    model: 18
                                    delegate: Rectangle {
                                        x: index * (viewport.width / 18)
                                        y: 0
                                        width: 1
                                        height: viewport.height
                                        color: "#eef2f6"
                                    }
                                }

                                Repeater {
                                    model: 12
                                    delegate: Rectangle {
                                        x: 0
                                        y: index * (viewport.height / 12)
                                        width: viewport.width
                                        height: 1
                                        color: "#eef2f6"
                                    }
                                }

                                Column {
                                    anchors.centerIn: parent
                                    spacing: 10

                                    Label {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: "中央视口"
                                        font.pixelSize: 28
                                        font.bold: true
                                        color: textMain
                                    }

                                    Label {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: "后续在这里接入背景图、节点、单元、约束、载荷与结果可视化"
                                        color: textMuted
                                    }

                                    Label {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: "当前视图：" + viewport_mode + "   |   当前模式：" + appController.current_mode
                                        color: textMuted
                                    }
                                }

                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.bottom: parent.bottom
                                    anchors.margins: 10
                                    width: 188
                                    height: 28
                                    radius: 4
                                    color: "#eef2f7"
                                    border.color: "#ccd5df"

                                    Label {
                                        anchors.centerIn: parent
                                        text: "X: 0.000   Y: 0.000"
                                        color: textMuted
                                        font.pixelSize: 12
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    SplitView.minimumHeight: 180
                    SplitView.preferredHeight: 230
                    color: bgPanel2
                    border.color: borderColor

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 34
                            radius: 6
                            color: "#e6ebf1"
                            border.color: borderColor

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 16

                                Label {
                                    text: "消息"
                                    color: accent
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                Label {
                                    text: "命令"
                                    color: textMuted
                                    font.pixelSize: 13
                                }

                                Label {
                                    text: "历史"
                                    color: textMuted
                                    font.pixelSize: 13
                                }

                                Label {
                                    text: "结果"
                                    color: textMuted
                                    font.pixelSize: 13
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 6
                            color: bgPanel3
                            border.color: borderColor

                            TextArea {
                                anchors.fill: parent
                                anchors.margins: 8
                                readOnly: true
                                wrapMode: TextEdit.Wrap
                                text:
                                    ">> FEM2D Studio 已启动\n" +
                                    ">> 后端连接成功\n" +
                                    ">> 当前状态：" + appController.status_text + "\n" +
                                    ">> 当前模式：" + appController.current_mode + "\n" +
                                    ">> 说明：当前为工程软件界面骨架版，后续将逐步接入真实功能。\n" +
                                    ">> 提示：下一步建议把 FEMModel 真实接到右侧面板与模型树。"
                            }
                        }
                    }
                }
            }

            Rectangle {
                SplitView.minimumWidth: 300
                SplitView.preferredWidth: 360
                color: bgPanel2
                border.color: borderColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        radius: 6
                        color: "#e6ebf1"
                        border.color: borderColor

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 18

                            Label {
                                text: "检查器"
                                color: accent
                                font.pixelSize: 13
                                font.bold: true
                            }

                            Label {
                                text: "属性"
                                color: textMuted
                                font.pixelSize: 13
                            }

                            Label {
                                text: "显示"
                                color: textMuted
                                font.pixelSize: 13
                            }

                            Label {
                                text: "任务"
                                color: textMuted
                                font.pixelSize: 13
                            }
                        }
                    }

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        ColumnLayout {
                            width: parent.width
                            spacing: 10

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 6
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 200

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "模型概要"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 1
                                        color: "#e2e8ef"
                                    }

                                    Label { text: "当前状态：" + appController.status_text; color: textMain }
                                    Label { text: "当前模式：" + appController.current_mode; color: textMain }
                                    Label { text: "节点数：0"; color: textMain }
                                    Label { text: "单元数：0"; color: textMain }
                                    Label { text: "材料数：0"; color: textMain }
                                    Label { text: "约束数：0"; color: textMain }
                                    Label { text: "载荷数：0"; color: textMain }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 6
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 120

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "当前选择"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 1
                                        color: "#e2e8ef"
                                    }

                                    Label { text: "对象：" + selection_info; color: textMain }
                                    Label { text: "类型：占位"; color: textMain }
                                    Label { text: "编号：—"; color: textMain }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 6
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 270

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "属性编辑器"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 1
                                        color: "#e2e8ef"
                                    }

                                    Label { text: "名称"; color: textMuted }
                                    TextField { placeholderText: "未选中对象" }

                                    Label { text: "类型"; color: textMuted }
                                    ComboBox { model: ["节点", "单元", "材料", "约束", "载荷"] }

                                    Label { text: "参数"; color: textMuted }
                                    TextArea {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 120
                                        placeholderText: "这里后续显示节点 / 单元 / 材料 / 约束 / 载荷等对象的真实参数"
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 6
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 200

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "显示选项"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 1
                                        color: "#e2e8ef"
                                    }

                                    CheckBox { text: "显示节点"; checked: true }
                                    CheckBox { text: "显示单元"; checked: true }
                                    CheckBox { text: "显示编号"; checked: true }
                                    CheckBox { text: "显示约束"; checked: true }
                                    CheckBox { text: "显示载荷"; checked: true }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 6
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 190

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "任务 / 求解"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 1
                                        color: "#e2e8ef"
                                    }

                                    TextField { text: "任务-1" }
                                    ComboBox { model: ["静力分析", "平面应力", "平面应变"] }

                                    Button {
                                        text: "提交任务"
                                        onClicked: shell_status = "提交任务：占位功能"
                                    }

                                    Button {
                                        text: "查看日志"
                                        onClicked: shell_status = "查看日志：占位功能"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            color: "#d7dce3"
            border.color: "#bcc5d0"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 16

                Label {
                    text: "状态：" + appController.status_text
                    color: textMain
                    font.pixelSize: 12
                }

                Label {
                    text: "模式：" + appController.current_mode
                    color: textMain
                    font.pixelSize: 12
                }

                Label {
                    Layout.fillWidth: true
                    text: "提示：" + shell_status
                    color: textMuted
                    font.pixelSize: 12
                    elide: Text.ElideRight
                }

                Label {
                    text: "视图：" + viewport_mode
                    color: textMain
                    font.pixelSize: 12
                }
            }
        }
    }
}