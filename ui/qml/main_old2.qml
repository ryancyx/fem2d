import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes

ApplicationWindow {
    id: window
    objectName: "mainWindow"

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

    property bool leftPanelVisible: true
    property bool rightPanelVisible: true

    property string activeViewportTool: "add"

    property real viewportPadding: 52
    property real fallbackModelWidth: 4
    property real fallbackModelHeight: 3
    property real cursorModelX: 0.0
    property real cursorModelY: 0.0

    property real viewportZoom: 1.0
    property real viewportPanX: 0.0
    property real viewportPanY: 0.0
    property real minViewportZoom: 0.1
    property real maxViewportZoom: 20.0
    property real lastPanMouseX: 0.0
    property real lastPanMouseY: 0.0

    function clamp(value, minValue, maxValue) {
        return Math.max(minValue, Math.min(maxValue, value))
    }

    function setViewportTool(toolName) {
        activeViewportTool = toolName

        if (toolName === "add") {
            if (appController.current_mode === "element") {
                shell_status = "视口工具：单元选点（点击节点进行选点）"
            } else {
                shell_status = "视口工具：添加节点"
            }
        } else if (toolName === "move") {
            shell_status = "视口工具：移动视图"
        } else if (toolName === "delete") {
            if (appController.current_mode === "element") {
                shell_status = "单元模式下不使用删除工具，请点击节点进行选点"
            } else {
                shell_status = "视口工具：删除节点"
            }
        }
    }

    function resetViewportTransform() {
        viewportZoom = 1.0
        viewportPanX = 0.0
        viewportPanY = 0.0
        shell_status = "已重置视口缩放和平移"
    }

    function deleteCurrentNodeFromView() {
        var ok = appController.delete_selected_node()
        if (ok) {
            refreshNodeModel()
            syncSelectedNodeEditor()
            shell_status = "已删除当前选中节点"
        } else {
            shell_status = appController.status_text
        }
    }

    function deleteCurrentElementFromView() {
        var ok = appController.delete_selected_element()
        if (ok) {
            refreshElementModel()
            syncSelectedElementEditor()
            shell_status = "已删除当前选中单元"
        } else {
            shell_status = appController.status_text
        }
    }

    function refreshNodeModel() {
        nodeListModel.clear()
        var rows = appController.get_node_rows()
        for (var i = 0; i < rows.length; i++) {
            nodeListModel.append({
                node_id: rows[i].id,
                node_x: rows[i].x,
                node_y: rows[i].y
            })
        }

        if (elementCanvas)
            elementCanvas.requestPaint()
    }

    function findNodeRowById(nodeId) {
        for (var i = 0; i < nodeListModel.count; i++) {
            var row = nodeListModel.get(i)
            if (row.node_id == nodeId || row.id == nodeId)
                return row
        }
        return null
    }

    function refreshElementModel() {
        var rows = appController.get_element_rows()
        var copy = []
        for (var i = 0; i < rows.length; i++) {
            copy.push({
                element_id: rows[i].id,
                node_ids: rows[i].node_ids,
                material_id: rows[i].material_id,
                element_type: rows[i].element_type
            })
        }
        elementRowsCache = copy

        if (elementCanvas)
            elementCanvas.requestPaint()
    }

    function refreshNodeResultModel() {
        nodeResultModel.clear()
        var rows = appController.get_node_result_rows()
        for (var i = 0; i < rows.length; i++) {
            nodeResultModel.append(rows[i])
        }
    }

    function refreshElementResultModel() {
        elementResultModel.clear()
        var rows = appController.get_element_result_rows()
        for (var i = 0; i < rows.length; i++) {
            elementResultModel.append(rows[i])
        }
    }

    function refreshSelectionInfo() {
        if (appController.selected_element_exists && appController.current_mode === "element") {
            selection_info = "单元 " + appController.selected_element_id
        } else if (appController.selected_node_exists) {
            selection_info = "节点 " + appController.selected_node_id
        } else if (appController.selected_element_exists) {
            selection_info = "单元 " + appController.selected_element_id
        } else {
            selection_info = "无"
        }
    }

    function syncSelectedNodeEditor() {
        if (appController.selected_node_exists) {
            selectedNodeIdValue.text = String(appController.selected_node_id)
            selectedXField.text = Number(appController.selected_node_x).toString()
            selectedYField.text = Number(appController.selected_node_y).toString()
        } else {
            selectedNodeIdValue.text = "—"
            selectedXField.text = ""
            selectedYField.text = ""
        }

        refreshSelectionInfo()
    }

    function syncSelectedElementEditor() {
        if (appController.selected_element_exists) {
            selectedElementIdValue.text = String(appController.selected_element_id)
            selectedElementNodeIdsValue.text = appController.selected_element_node_ids_info.join(" - ")
            selectedElementMaterialValue.text = String(appController.selected_element_material_id)
            selectedElementTypeValue.text = appController.selected_element_type
        } else {
            selectedElementIdValue.text = "—"
            selectedElementNodeIdsValue.text = "—"
            selectedElementMaterialValue.text = "—"
            selectedElementTypeValue.text = "—"
        }

        refreshSelectionInfo()
    }

    function refreshAllData() {
        refreshNodeModel()
        refreshElementModel()
        refreshNodeResultModel()
        refreshElementResultModel()
        syncSelectedNodeEditor()
        syncSelectedElementEditor()
    }

    function elementSelectionSummary() {
        if (appController.selected_element_node_count === 0)
            return "无"

        var ids = appController.selected_element_node_ids
        var parts = []
        for (var i = 0; i < ids.length; i++) {
            parts.push(String(ids[i]))
        }
        return parts.join(" - ")
    }

    function viewportMinX() {
        if (nodeListModel.count === 0)
            return 0

        var minValue = nodeListModel.get(0).node_x
        for (var i = 1; i < nodeListModel.count; i++) {
            minValue = Math.min(minValue, nodeListModel.get(i).node_x)
        }
        return Math.min(0, minValue)
    }

    function viewportMaxX() {
        if (nodeListModel.count === 0)
            return fallbackModelWidth

        var maxValue = nodeListModel.get(0).node_x
        for (var i = 1; i < nodeListModel.count; i++) {
            maxValue = Math.max(maxValue, nodeListModel.get(i).node_x)
        }
        return Math.max(maxValue, viewportMinX() + fallbackModelWidth)
    }

    function viewportMinY() {
        if (nodeListModel.count === 0)
            return 0

        var minValue = nodeListModel.get(0).node_y
        for (var i = 1; i < nodeListModel.count; i++) {
            minValue = Math.min(minValue, nodeListModel.get(i).node_y)
        }
        return Math.min(0, minValue)
    }

    function viewportMaxY() {
        if (nodeListModel.count === 0)
            return fallbackModelHeight

        var maxValue = nodeListModel.get(0).node_y
        for (var i = 1; i < nodeListModel.count; i++) {
            maxValue = Math.max(maxValue, nodeListModel.get(i).node_y)
        }
        return Math.max(maxValue, viewportMinY() + fallbackModelHeight)
    }

    function viewportRangeX() {
        var value = viewportMaxX() - viewportMinX()
        return value <= 0 ? 1 : value
    }

    function viewportRangeY() {
        var value = viewportMaxY() - viewportMinY()
        return value <= 0 ? 1 : value
    }

    function baseNodeToViewportX(xValue) {
        var usableWidth = Math.max(1, viewport.width - viewportPadding * 2)
        return viewportPadding + ((xValue - viewportMinX()) / viewportRangeX()) * usableWidth
    }

    function baseNodeToViewportY(yValue) {
        var usableHeight = Math.max(1, viewport.height - viewportPadding * 2)
        return viewport.height - viewportPadding - ((yValue - viewportMinY()) / viewportRangeY()) * usableHeight
    }

    function nodeToViewportX(xValue) {
        var centerX = viewport.width / 2
        var baseX = baseNodeToViewportX(xValue)
        return centerX + (baseX - centerX) * viewportZoom + viewportPanX
    }

    function nodeToViewportY(yValue) {
        var centerY = viewport.height / 2
        var baseY = baseNodeToViewportY(yValue)
        return centerY + (baseY - centerY) * viewportZoom + viewportPanY
    }

    function viewportToBaseX(viewX) {
        var centerX = viewport.width / 2
        return centerX + (viewX - viewportPanX - centerX) / viewportZoom
    }

    function viewportToBaseY(viewY) {
        var centerY = viewport.height / 2
        return centerY + (viewY - viewportPanY - centerY) / viewportZoom
    }

    function viewportToModelX(viewX) {
        var baseX = viewportToBaseX(viewX)
        var usableWidth = Math.max(1, viewport.width - viewportPadding * 2)
        var normalized = (baseX - viewportPadding) / usableWidth
        normalized = Math.max(0, Math.min(1, normalized))
        return viewportMinX() + normalized * viewportRangeX()
    }

    function viewportToModelY(viewY) {
        var baseY = viewportToBaseY(viewY)
        var usableHeight = Math.max(1, viewport.height - viewportPadding * 2)
        var normalized = (viewport.height - viewportPadding - baseY) / usableHeight
        normalized = Math.max(0, Math.min(1, normalized))
        return viewportMinY() + normalized * viewportRangeY()
    }

    function viewportPointIsValid(viewX, viewY) {
        var baseX = viewportToBaseX(viewX)
        var baseY = viewportToBaseY(viewY)

        return baseX >= viewportPadding
            && baseX <= viewport.width - viewportPadding
            && baseY >= viewportPadding
            && baseY <= viewport.height - viewportPadding
    }

    function zoomViewportAt(viewX, viewY, wheelDeltaY) {
        var beforeModelX = viewportToModelX(viewX)
        var beforeModelY = viewportToModelY(viewY)

        var factor = wheelDeltaY > 0 ? 1.2 : 0.833333
        viewportZoom = clamp(viewportZoom * factor, minViewportZoom, maxViewportZoom)

        var afterViewX = nodeToViewportX(beforeModelX)
        var afterViewY = nodeToViewportY(beforeModelY)

        viewportPanX += viewX - afterViewX
        viewportPanY += viewY - afterViewY

        cursorModelX = beforeModelX
        cursorModelY = beforeModelY

        shell_status = "视口缩放：" + Number(viewportZoom * 100).toFixed(0) + "%"
    }

    ListModel {
        id: nodeListModel
    }

    property var elementRowsCache: []


    ListModel {
        id: nodeResultModel
    }

    ListModel {
        id: elementResultModel
    }

    Connections {
        target: appController
        ignoreUnknownSignals: true

        function onNodeDataChanged() {
            refreshNodeModel()
        }

        function onSelectedNodeChanged() {
            syncSelectedNodeEditor()
        }

        function onSelectedElementChanged() {
            syncSelectedElementEditor()
            if (elementCanvas)
                elementCanvas.requestPaint()
        }

        function onElementDataChanged() {
            refreshElementModel()
        }

        function onElementSelectionChanged() {
            if (elementCanvas)
                elementCanvas.requestPaint()
        }

        function onSolverResultsChanged() {
            refreshNodeResultModel()
            refreshElementResultModel()
        }
    }

    Component.onCompleted: {
        refreshAllData()
    }

    onViewportZoomChanged: {
        if (elementCanvas)
            elementCanvas.requestPaint()
    }

    onViewportPanXChanged: {
        if (elementCanvas)
            elementCanvas.requestPaint()
    }

    onViewportPanYChanged: {
        if (elementCanvas)
            elementCanvas.requestPaint()
    }

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

    component HeaderIconButton: ToolButton {
        id: control

        property bool active: false

        implicitHeight: 28
        implicitWidth: 34
        padding: 0
        hoverEnabled: true

        background: Rectangle {
            radius: 4
            color: control.down
                   ? (control.active ? "#416ab2" : "#dbe3ec")
                   : control.hovered
                     ? (control.active ? "#5a84d2" : "#eef3f8")
                     : (control.active ? accent : "#f8fafc")
            border.color: control.active ? "#4068b0" : "#cdd6e0"
        }

        contentItem: Text {
            text: control.text
            color: control.active ? "#ffffff" : textMain
            font.pixelSize: 15
            font.bold: control.active
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
                            Layout.preferredWidth: 258
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
                                        refreshAllData()
                                        resetViewportTransform()
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
                            Layout.preferredWidth: 454
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
                                    id: nodeModeHeaderButton
                                    objectName: "nodeModeButton"
                                    text: "节点"
                                    onClicked: {
                                        appController.set_node_mode()
                                        activeViewportTool = "add"
                                        shell_status = "已切换到节点编辑模式"
                                    }
                                }

                                HeaderActionButton {
                                    text: "单元"
                                    onClicked: {
                                        appController.set_element_mode()
                                        activeViewportTool = "move"
                                        shell_status = "已切换到单元编辑模式，请点击节点进行选点"
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
                            Layout.preferredWidth: 314
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
                                    objectName: "solveHeaderButton"
                                    text: "求解"
                                    emphasized: true
                                    onClicked: {
                                        var ok = appController.solve_model()
                                        if (ok) {
                                            shell_status = "求解完成"
                                            refreshNodeResultModel()
                                            refreshElementResultModel()
                                        } else {
                                            shell_status = "求解失败"
                                        }
                                    }
                                }

                                HeaderActionButton {
                                    text: "结果"
                                    onClicked: shell_status = "结果查看：请查看右侧结果摘要"
                                }
                            }
                        }

                        Rectangle {
                            radius: 6
                            color: "#f3f6fa"
                            border.color: borderColor
                            implicitHeight: 38
                            Layout.preferredWidth: 240
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 6

                                Label {
                                    text: "画布"
                                    color: textMuted
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                HeaderIconButton {
                                    text: "+"
                                    active: activeViewportTool === "add"
                                    ToolTip.visible: hovered
                                    ToolTip.text: "添加节点"
                                    onClicked: setViewportTool("add")
                                }

                                HeaderIconButton {
                                    text: "↔"
                                    active: activeViewportTool === "move"
                                    ToolTip.visible: hovered
                                    ToolTip.text: "移动视图"
                                    onClicked: setViewportTool("move")
                                }

                                HeaderIconButton {
                                    text: "×"
                                    active: activeViewportTool === "delete"
                                    ToolTip.visible: hovered
                                    ToolTip.text: "删除节点"
                                    onClicked: setViewportTool("delete")
                                }

                                HeaderIconButton {
                                    text: "⟳"
                                    ToolTip.visible: hovered
                                    ToolTip.text: "重置视图"
                                    onClicked: resetViewportTransform()
                                }

                                HeaderIconButton {
                                    text: "⌫"
                                    enabled: appController.selected_node_exists
                                    ToolTip.visible: hovered
                                    ToolTip.text: "删除当前选中节点"
                                    onClicked: deleteCurrentNodeFromView()
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
            id: mainSplitView
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            Rectangle {
                id: leftPanel
                visible: leftPanelVisible
                SplitView.minimumWidth: leftPanelVisible ? 240 : 0
                SplitView.preferredWidth: leftPanelVisible ? 280 : 0
                color: bgPanel2
                border.color: borderColor

                ScrollView {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.topMargin: 10
                    anchors.bottomMargin: 10
                    anchors.rightMargin: 6
                    clip: true
                    leftPadding: 0
                    topPadding: 0
                    bottomPadding: 0
                    rightPadding: 14

                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOff

                    contentWidth: availableWidth

                    ColumnLayout {
                        width: Math.max(0, leftPanel.width - 30)
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
                            Layout.preferredHeight: 240
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
                            Layout.preferredHeight: 980
                            radius: 6
                            color: bgPanel3
                            border.color: borderColor

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                Label {
                                    text: "建模操作"
                                    color: textMain
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                Button {
                                    Layout.fillWidth: true
                                    text: "快速新建节点"
                                    onClicked: {
                                        appController.add_test_node()
                                        refreshNodeModel()
                                        syncSelectedNodeEditor()
                                        shell_status = "已快速新建节点"
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    text: "新建材料"
                                    onClicked: {
                                        appController.add_test_material()
                                        shell_status = "已新建材料"
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    text: "创建单元（选3点）"
                                    enabled: appController.selected_element_node_count === 3
                                    onClicked: {
                                        var ok = appController.create_element_from_selected_nodes()
                                        shell_status = appController.status_text
                                        if (ok) {
                                            refreshElementModel()
                                        }
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    text: "清空单元选点"
                                    enabled: appController.selected_element_node_count > 0
                                    onClicked: {
                                        appController.clear_element_node_selection()
                                        shell_status = appController.status_text
                                        if (elementCanvas)
                                            elementCanvas.requestPaint()
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 34
                                    radius: 4
                                    color: "#fff7e2"
                                    border.color: "#ecd9a2"

                                    Label {
                                        anchors.centerIn: parent
                                        text: "当前单元选点： " + elementSelectionSummary()
                                        color: "#7a5a00"
                                        font.pixelSize: 12
                                        font.bold: appController.selected_element_node_count > 0
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    text: "施加约束"
                                    onClicked: {
                                        appController.add_test_constraint()
                                        shell_status = "已施加约束"
                                    }
                                }

                                Button {
                                    Layout.fillWidth: true
                                    text: "施加载荷"
                                    onClicked: {
                                        appController.add_test_load()
                                        shell_status = "已施加载荷"
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 1
                                    color: "#e2e8ef"
                                }

                                Label {
                                    text: "按坐标添加节点"
                                    color: textMain
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    columnSpacing: 8
                                    rowSpacing: 8

                                    Label {
                                        text: "X"
                                        color: textMuted
                                    }

                                    TextField {
                                        id: addNodeXField
                                        objectName: "addNodeXField"
                                        Layout.fillWidth: true
                                        placeholderText: "输入 X 坐标"
                                    }

                                    Label {
                                        text: "Y"
                                        color: textMuted
                                    }

                                    TextField {
                                        id: addNodeYField
                                        objectName: "addNodeYField"
                                        Layout.fillWidth: true
                                        placeholderText: "输入 Y 坐标"
                                    }
                                }

                                Button {
                                    objectName: "addNodeButton"
                                    Layout.fillWidth: true
                                    text: "新增节点"
                                    onClicked: {
                                        var ok = appController.add_node_by_text(addNodeXField.text, addNodeYField.text)
                                        if (ok) {
                                            refreshNodeModel()
                                            syncSelectedNodeEditor()
                                            shell_status = "已按坐标添加节点"
                                            addNodeXField.text = ""
                                            addNodeYField.text = ""
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 1
                                    color: "#e2e8ef"
                                }

                                Label {
                                    text: "节点列表"
                                    color: textMain
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 260
                                    color: "#fbfcfd"
                                    border.color: "#d7dee6"
                                    radius: 4

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 6

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 32
                                            radius: 4
                                            color: "#eef2f6"

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: 8
                                                anchors.rightMargin: 8
                                                spacing: 8

                                                Label {
                                                    text: "ID"
                                                    font.bold: true
                                                    Layout.preferredWidth: 42
                                                    color: textMain
                                                }

                                                Label {
                                                    text: "X"
                                                    font.bold: true
                                                    Layout.preferredWidth: 88
                                                    color: textMain
                                                }

                                                Label {
                                                    text: "Y"
                                                    font.bold: true
                                                    Layout.preferredWidth: 88
                                                    color: textMain
                                                }
                                            }
                                        }

                                        ListView {
                                            id: nodeListView
                                            objectName: "nodeListView"
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            clip: true
                                            spacing: 4
                                            model: nodeListModel

                                            ScrollBar.vertical: ScrollBar {
                                                policy: ScrollBar.AsNeeded
                                                width: 10
                                            }

                                            delegate: Rectangle {
                                                width: nodeListView.width
                                                height: 36
                                                radius: 4
                                                border.color: appController.is_node_in_element_selection(model.node_id)
                                                              ? "#d18b00"
                                                              : (model.node_id === appController.selected_node_id ? accent : "#d7dee6")
                                                color: appController.is_node_in_element_selection(model.node_id)
                                                       ? "#fff1cc"
                                                       : (model.node_id === appController.selected_node_id
                                                          ? accentSoft
                                                          : (index % 2 === 0 ? "#fcfdff" : "#f6f9fc"))

                                                MouseArea {
                                                    anchors.fill: parent
                                                    onClicked: {
                                                        if (appController.current_mode === "element") {
                                                            appController.toggle_element_node_selection(model.node_id)
                                                            shell_status = appController.status_text
                                                            if (elementCanvas)
                                                                elementCanvas.requestPaint()
                                                        } else {
                                                            appController.select_node(model.node_id)
                                                            syncSelectedNodeEditor()
                                                            shell_status = "已选中节点 " + model.node_id
                                                        }
                                                    }
                                                }

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 8
                                                    anchors.rightMargin: 8
                                                    spacing: 8

                                                    Label {
                                                        text: model.node_id
                                                        Layout.preferredWidth: 42
                                                        color: textMain
                                                        font.bold: model.node_id === appController.selected_node_id
                                                    }

                                                    Label {
                                                        text: Number(model.node_x).toFixed(3)
                                                        Layout.preferredWidth: 88
                                                        color: textMain
                                                    }

                                                    Label {
                                                        text: Number(model.node_y).toFixed(3)
                                                        Layout.preferredWidth: 88
                                                        color: textMain
                                                    }
                                                }
                                            }

                                            footer: nodeListModel.count === 0 ? emptyNodeFooter : null
                                        }

                                        Component {
                                            id: emptyNodeFooter

                                            Label {
                                                width: nodeListView.width
                                                text: "暂无节点"
                                                horizontalAlignment: Text.AlignHCenter
                                                color: textMuted
                                                topPadding: 20
                                            }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 1
                                        color: "#e2e8ef"
                                    }

                                    Label {
                                        text: "单元列表"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 230
                                        color: "#fbfcfd"
                                        border.color: "#d7dee6"
                                        radius: 4

                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 6
                                            spacing: 6

                                            Rectangle {
                                                Layout.fillWidth: true
                                                Layout.preferredHeight: 32
                                                radius: 4
                                                color: "#eef2f6"

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 8
                                                    anchors.rightMargin: 8
                                                    spacing: 8

                                                    Label {
                                                        text: "ID"
                                                        font.bold: true
                                                        Layout.preferredWidth: 40
                                                        color: textMain
                                                    }

                                                    Label {
                                                        text: "节点"
                                                        font.bold: true
                                                        Layout.preferredWidth: 130
                                                        color: textMain
                                                    }

                                                    Label {
                                                        text: "类型"
                                                        font.bold: true
                                                        Layout.fillWidth: true
                                                        color: textMain
                                                    }
                                                }
                                            }

                                            ListView {
                                                id: elementListView
                                                objectName: "elementListView"
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                                clip: true
                                                spacing: 4
                                                model: elementRowsCache

                                                ScrollBar.vertical: ScrollBar {
                                                    policy: ScrollBar.AsNeeded
                                                    width: 10
                                                }

                                                delegate: Rectangle {
                                                    width: elementListView.width
                                                    height: 40
                                                    radius: 4
                                                    property var rowData: modelData

                                                    border.color: rowData && rowData.element_id === appController.selected_element_id
                                                                  ? "#1f5fbf" : "#d7dee6"
                                                    color: rowData && rowData.element_id === appController.selected_element_id
                                                           ? "#dbe6fb"
                                                           : (index % 2 === 0 ? "#fcfdff" : "#f6f9fc")

                                                    MouseArea {
                                                        anchors.fill: parent
                                                        onClicked: {
                                                            if (rowData) {
                                                                appController.select_element(rowData.element_id)
                                                                syncSelectedElementEditor()
                                                                shell_status = appController.status_text
                                                            }
                                                        }
                                                    }

                                                    RowLayout {
                                                        anchors.fill: parent
                                                        anchors.leftMargin: 8
                                                        anchors.rightMargin: 8
                                                        spacing: 8

                                                        Label {
                                                            text: rowData ? rowData.element_id : ""
                                                            Layout.preferredWidth: 40
                                                            color: textMain
                                                            font.bold: rowData && rowData.element_id === appController.selected_element_id
                                                        }

                                                        Label {
                                                            text: rowData ? rowData.node_ids.join("-") : ""
                                                            Layout.preferredWidth: 130
                                                            color: textMain
                                                            elide: Text.ElideRight
                                                        }

                                                        Label {
                                                            text: rowData ? rowData.element_type : ""
                                                            Layout.fillWidth: true
                                                            color: textMain
                                                        }
                                                    }
                                                }

                                                footer: elementRowsCache.length === 0 ? emptyElementFooter : null
                                            }

                                            Component {
                                                id: emptyElementFooter

                                                Label {
                                                    width: elementListView.width
                                                    text: "暂无单元"
                                                    horizontalAlignment: Text.AlignHCenter
                                                    color: textMuted
                                                    topPadding: 20
                                                }
                                            }
                                        }
                                    }
                                }
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
                                        text: "工具：" + activeViewportTool + "    缩放：" + Number(viewportZoom * 100).toFixed(0) + "%"
                                        color: textMuted
                                        font.pixelSize: 12
                                    }
                                }
                            }

                            Rectangle {
                                id: viewport
                                objectName: "viewportRect"
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: viewportHeader.bottom
                                anchors.bottom: parent.bottom
                                anchors.margins: 14
                                radius: 4
                                color: viewportBg
                                border.color: "#d6dde6"
                                clip: true

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

                                Item {
                                    id: elementCanvas
                                    anchors.fill: parent
                                    z: 1

                                    function requestPaint() {
                                        // Shape 基于属性绑定自动刷新，这里保留空函数兼容旧调用
                                    }

                                    Repeater {
                                        model: elementRowsCache

                                        delegate: Item {
                                            id: elementShapeItem
                                            anchors.fill: parent

                                            property var ids: (modelData && modelData.node_ids) ? modelData.node_ids : []
                                            property var n1: ids && ids.length > 0 ? findNodeRowById(ids[0]) : null
                                            property var n2: ids && ids.length > 1 ? findNodeRowById(ids[1]) : null
                                            property var n3: ids && ids.length > 2 ? findNodeRowById(ids[2]) : null

                                            visible: n1 !== null && n2 !== null && n3 !== null

                                            z: (modelData && modelData.element_id === appController.selected_element_id) ? 2 : 1

                                            Shape {
                                                anchors.fill: parent
                                                visible: elementShapeItem.visible

                                                ShapePath {
                                                    strokeColor: (modelData && modelData.element_id === appController.selected_element_id) ? "#1f5fbf" : "#4f79c7"
                                                    strokeWidth: (modelData && modelData.element_id === appController.selected_element_id) ? 3.2 : 2.2
                                                    fillColor: (modelData && modelData.element_id === appController.selected_element_id) ? "#c9dcffbb" : "#dbe6fb99"
                                                    capStyle: ShapePath.RoundCap
                                                    joinStyle: ShapePath.RoundJoin
                                                    startX: nodeToViewportX(elementShapeItem.n1.node_x)
                                                    startY: nodeToViewportY(elementShapeItem.n1.node_y)

                                                    PathLine {
                                                        x: nodeToViewportX(elementShapeItem.n2.node_x)
                                                        y: nodeToViewportY(elementShapeItem.n2.node_y)
                                                    }
                                                    PathLine {
                                                        x: nodeToViewportX(elementShapeItem.n3.node_x)
                                                        y: nodeToViewportY(elementShapeItem.n3.node_y)
                                                    }
                                                    PathLine {
                                                        x: nodeToViewportX(elementShapeItem.n1.node_x)
                                                        y: nodeToViewportY(elementShapeItem.n1.node_y)
                                                    }
                                                }
                                            }

                                            Label {
                                                visible: elementShapeItem.visible
                                                text: String(modelData ? modelData.element_id : "")
                                                color: "#1f2a36"
                                                font.pixelSize: 12
                                                font.bold: true
                                                x: (nodeToViewportX(elementShapeItem.n1.node_x)
                                                    + nodeToViewportX(elementShapeItem.n2.node_x)
                                                    + nodeToViewportX(elementShapeItem.n3.node_x)) / 3 + 4
                                                y: (nodeToViewportY(elementShapeItem.n1.node_y)
                                                    + nodeToViewportY(elementShapeItem.n2.node_y)
                                                    + nodeToViewportY(elementShapeItem.n3.node_y)) / 3 - 16
                                            }
                                        }
                                    }

                                    Item {
                                        id: tempElementPreview
                                        anchors.fill: parent
                                        z: 2

                                        property var p0: appController.selected_element_node_count > 0
                                                         ? findNodeRowById(appController.selected_element_node_ids[0]) : null
                                        property var p1: appController.selected_element_node_count > 1
                                                         ? findNodeRowById(appController.selected_element_node_ids[1]) : null
                                        property var p2: appController.selected_element_node_count > 2
                                                         ? findNodeRowById(appController.selected_element_node_ids[2]) : null

                                        Shape {
                                            anchors.fill: parent
                                            visible: appController.selected_element_node_count === 2
                                                     && tempElementPreview.p0 !== null
                                                     && tempElementPreview.p1 !== null

                                            ShapePath {
                                                strokeColor: "#d18b00"
                                                strokeWidth: 2.2
                                                fillColor: "transparent"
                                                capStyle: ShapePath.RoundCap
                                                joinStyle: ShapePath.RoundJoin
                                                startX: nodeToViewportX(tempElementPreview.p0.node_x)
                                                startY: nodeToViewportY(tempElementPreview.p0.node_y)

                                                PathLine {
                                                    x: nodeToViewportX(tempElementPreview.p1.node_x)
                                                    y: nodeToViewportY(tempElementPreview.p1.node_y)
                                                }
                                            }
                                        }

                                        Shape {
                                            anchors.fill: parent
                                            visible: appController.selected_element_node_count === 3
                                                     && tempElementPreview.p0 !== null
                                                     && tempElementPreview.p1 !== null
                                                     && tempElementPreview.p2 !== null

                                            ShapePath {
                                                strokeColor: "#d18b00"
                                                strokeWidth: 2.2
                                                fillColor: "#fff3c433"
                                                capStyle: ShapePath.RoundCap
                                                joinStyle: ShapePath.RoundJoin
                                                startX: nodeToViewportX(tempElementPreview.p0.node_x)
                                                startY: nodeToViewportY(tempElementPreview.p0.node_y)

                                                PathLine {
                                                    x: nodeToViewportX(tempElementPreview.p1.node_x)
                                                    y: nodeToViewportY(tempElementPreview.p1.node_y)
                                                }
                                                PathLine {
                                                    x: nodeToViewportX(tempElementPreview.p2.node_x)
                                                    y: nodeToViewportY(tempElementPreview.p2.node_y)
                                                }
                                                PathLine {
                                                    x: nodeToViewportX(tempElementPreview.p0.node_x)
                                                    y: nodeToViewportY(tempElementPreview.p0.node_y)
                                                }
                                            }
                                        }
                                    }
                                }

                                MouseArea {
                                    id: viewportMouseArea
                                    objectName: "viewportMouseArea"
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    acceptedButtons: Qt.LeftButton
                                    z: 0

                                    onWheel: function(wheel) {
                                        if ((wheel.modifiers & Qt.ControlModifier) !== 0) {
                                            zoomViewportAt(wheel.x, wheel.y, wheel.angleDelta.y)
                                            wheel.accepted = true
                                        }
                                    }

                                    onPressed: function(mouse) {
                                        if (activeViewportTool === "move") {
                                            lastPanMouseX = mouse.x
                                            lastPanMouseY = mouse.y
                                            mouse.accepted = true
                                        }
                                    }

                                    onPositionChanged: function(mouse) {
                                        if (activeViewportTool === "move" && pressed) {
                                            viewportPanX += mouse.x - lastPanMouseX
                                            viewportPanY += mouse.y - lastPanMouseY
                                            lastPanMouseX = mouse.x
                                            lastPanMouseY = mouse.y
                                            shell_status = "正在移动视图"
                                            return
                                        }

                                        if (window.viewportPointIsValid(mouse.x, mouse.y)) {
                                            window.cursorModelX = window.viewportToModelX(mouse.x)
                                            window.cursorModelY = window.viewportToModelY(mouse.y)
                                        }
                                    }

                                    onClicked: function(mouse) {
                                        if (!window.viewportPointIsValid(mouse.x, mouse.y))
                                            return

                                        window.cursorModelX = window.viewportToModelX(mouse.x)
                                        window.cursorModelY = window.viewportToModelY(mouse.y)

                                        if (activeViewportTool === "delete") {
                                            deleteCurrentNodeFromView()
                                            return
                                        }

                                        if (activeViewportTool !== "add") {
                                            return
                                        }

                                        if (appController.current_mode === "element") {
                                            return
                                        }

                                        if (appController.current_mode !== "node") {
                                            shell_status = "当前不是节点模式，无法通过视口创建节点"
                                            return
                                        }

                                        var ok = appController.add_node_by_coord(
                                                    window.cursorModelX,
                                                    window.cursorModelY
                                                )
                                        if (ok) {
                                            refreshNodeModel()
                                            syncSelectedNodeEditor()

                                            shell_status = "已在视口创建节点 ("
                                                           + Number(window.cursorModelX).toFixed(3)
                                                           + ", "
                                                           + Number(window.cursorModelY).toFixed(3)
                                                           + ")"
                                        }
                                    }
                                }

                                Column {
                                    anchors.centerIn: parent
                                    spacing: 10
                                    visible: nodeListModel.count === 0

                                    Label {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: "中央视口"
                                        font.pixelSize: 28
                                        font.bold: true
                                        color: textMain
                                    }

                                    Label {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: "节点模式下可点击空白处创建节点；单元模式下请直接点击节点选点；按住 Ctrl + 鼠标滚轮缩放"
                                        color: textMuted
                                    }

                                    Label {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: "当前视图：" + viewport_mode + "   |   当前模式：" + appController.current_mode
                                        color: textMuted
                                    }
                                }

                                Repeater {
                                    model: nodeListModel

                                    delegate: Item {
                                        width: 100
                                        height: 40
                                        x: window.nodeToViewportX(model.node_x) - 8
                                        y: window.nodeToViewportY(model.node_y) - 8
                                        z: 2

                                        Rectangle {
                                            width: 16
                                            height: 16
                                            radius: 8
                                            border.width: 2
                                            border.color: appController.is_node_in_element_selection(model.node_id)
                                                          ? "#d18b00"
                                                          : (model.node_id === appController.selected_node_id ? accent : "#3d74c5")
                                            color: appController.is_node_in_element_selection(model.node_id)
                                                   ? "#ffd86b"
                                                   : (model.node_id === appController.selected_node_id ? accent : "#8fb1ea")

                                            MouseArea {
                                                anchors.fill: parent
                                                onClicked: {
                                                    if (appController.current_mode === "element") {
                                                        appController.toggle_element_node_selection(model.node_id)
                                                        shell_status = appController.status_text
                                                        if (appController.selected_element_node_count === 3) {
                                                            shell_status = appController.status_text + "，已选满3个节点，可直接创建单元"
                                                        }
                                                        if (elementCanvas)
                                                            elementCanvas.requestPaint()
                                                        return
                                                    }

                                                    if (activeViewportTool === "delete") {
                                                        appController.select_node(model.node_id)
                                                        syncSelectedNodeEditor()
                                                        deleteCurrentNodeFromView()
                                                        return
                                                    }

                                                    appController.select_node(model.node_id)
                                                    syncSelectedNodeEditor()
                                                    shell_status = "在视口中选中节点 " + model.node_id
                                                }
                                            }
                                        }

                                        Label {
                                            x: 22
                                            y: -2
                                            text: model.node_id + " (" + Number(model.node_x).toFixed(1) + ", " + Number(model.node_y).toFixed(1) + ")"
                                            color: textMain
                                            font.pixelSize: 12
                                        }
                                    }
                                }

                                Rectangle {
                                    anchors.right: parent.right
                                    anchors.bottom: parent.bottom
                                    anchors.margins: 10
                                    width: 420
                                    height: 28
                                    radius: 4
                                    color: "#eef2f7"
                                    border.color: "#ccd5df"

                                    Label {
                                        anchors.centerIn: parent
                                        text: appController.selected_node_exists
                                              ? ("缩放: "
                                                 + Number(viewportZoom * 100).toFixed(0)
                                                 + "%   鼠标: X="
                                                 + Number(window.cursorModelX).toFixed(3)
                                                 + "  Y="
                                                 + Number(window.cursorModelY).toFixed(3)
                                                 + "   |   节点 "
                                                 + appController.selected_node_id
                                                 + "  (" + Number(appController.selected_node_x).toFixed(3)
                                                 + ", " + Number(appController.selected_node_y).toFixed(3) + ")")
                                              : ("缩放: "
                                                 + Number(viewportZoom * 100).toFixed(0)
                                                 + "%   鼠标: X="
                                                 + Number(window.cursorModelX).toFixed(3)
                                                 + "  Y="
                                                 + Number(window.cursorModelY).toFixed(3))
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
                                    ">> 当前选择：" + selection_info + "\n" +
                                    ">> 当前视口工具：" + activeViewportTool + "\n" +
                                    ">> 视口缩放：" + Number(viewportZoom * 100).toFixed(0) + "%\n" +
                                    ">> 求解结果状态：" + (appController.solver_has_result ? "已有结果" : "暂无结果") + "\n" +
                                    ">> 提示：" + shell_status + "\n" +
                                    ">> 说明：当前为工程软件界面骨架版，已增量接入节点编辑、缩放、平移、删除与折叠侧栏功能。"
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: rightPanel
                visible: rightPanelVisible
                SplitView.minimumWidth: rightPanelVisible ? 300 : 0
                SplitView.preferredWidth: rightPanelVisible ? 320 : 0
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
                                implicitHeight: 244

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
                                    Label { text: "节点数：" + appController.node_count; color: textMain }
                                    Label { text: "单元数：" + appController.element_count; color: textMain }
                                    Label { text: "材料数：" + appController.material_count; color: textMain }
                                    Label { text: "约束数：" + appController.constraint_count; color: textMain }
                                    Label { text: "载荷数：" + appController.load_count; color: textMain }
                                    Label {
                                        text: "结果状态：" + (appController.solver_has_result ? "已有结果" : "暂无结果")
                                        color: textMain
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 6
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 150

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

                                    Label {
                                        text: "对象：" + selection_info
                                        color: textMain
                                    }

                                    Label {
                                        text: "类型：" + (appController.selected_element_exists && appController.current_mode === "element"
                                                         ? "单元"
                                                         : (appController.selected_node_exists
                                                            ? "节点"
                                                            : (appController.selected_element_exists ? "单元" : "无")))
                                        color: textMain
                                    }

                                    Label {
                                        text: "编号：" + (appController.selected_element_exists && appController.current_mode === "element"
                                                         ? appController.selected_element_id
                                                         : (appController.selected_node_exists
                                                            ? appController.selected_node_id
                                                            : (appController.selected_element_exists ? appController.selected_element_id : "—")))
                                        color: textMain
                                    }

                                    Label {
                                        text: "单元临时选点：" + elementSelectionSummary()
                                        color: "#7a5a00"
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 6
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 470

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

                                    Label { text: "节点对象"; color: textMuted }

                                    Label {
                                        id: selectedNodeIdValue
                                        text: "—"
                                        color: textMain
                                        font.pixelSize: 14
                                        font.bold: true
                                    }

                                    Label { text: "X 坐标"; color: textMuted }

                                    TextField {
                                        id: selectedXField
                                        objectName: "selectedXField"
                                        Layout.fillWidth: true
                                        enabled: appController.selected_node_exists && appController.current_mode !== "element"
                                        placeholderText: "选中节点 X"
                                    }

                                    Label { text: "Y 坐标"; color: textMuted }

                                    TextField {
                                        id: selectedYField
                                        objectName: "selectedYField"
                                        Layout.fillWidth: true
                                        enabled: appController.selected_node_exists && appController.current_mode !== "element"
                                        placeholderText: "选中节点 Y"
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        Button {
                                            objectName: "applyNodeEditButton"
                                            Layout.fillWidth: true
                                            text: "应用坐标修改"
                                            enabled: appController.selected_node_exists && appController.current_mode !== "element"
                                            onClicked: {
                                                var ok = appController.update_selected_node_position_by_text(selectedXField.text, selectedYField.text)
                                                if (ok) {
                                                    refreshNodeModel()
                                                    syncSelectedNodeEditor()
                                                    shell_status = "已更新节点坐标"
                                                }
                                            }
                                        }

                                        Button {
                                            objectName: "clearNodeSelectionButton"
                                            Layout.fillWidth: true
                                            text: "取消节点选中"
                                            onClicked: {
                                                appController.clear_node_selection()
                                                syncSelectedNodeEditor()
                                                shell_status = "已取消节点选中"
                                            }
                                        }
                                    }

                                    Button {
                                        Layout.fillWidth: true
                                        text: "删除当前节点"
                                        enabled: appController.selected_node_exists && appController.current_mode !== "element"
                                        onClicked: deleteCurrentNodeFromView()
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 1
                                        color: "#e2e8ef"
                                    }

                                    Label { text: "单元对象"; color: textMuted }

                                    Label {
                                        id: selectedElementIdValue
                                        text: "—"
                                        color: textMain
                                        font.pixelSize: 14
                                        font.bold: true
                                    }

                                    Label { text: "节点连接"; color: textMuted }

                                    Label {
                                        id: selectedElementNodeIdsValue
                                        text: "—"
                                        color: textMain
                                        Layout.fillWidth: true
                                    }

                                    Label { text: "材料编号"; color: textMuted }

                                    Label {
                                        id: selectedElementMaterialValue
                                        text: "—"
                                        color: textMain
                                    }

                                    Label { text: "单元类型"; color: textMuted }

                                    Label {
                                        id: selectedElementTypeValue
                                        text: "—"
                                        color: textMain
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        Button {
                                            Layout.fillWidth: true
                                            text: "取消单元选中"
                                            enabled: appController.selected_element_exists
                                            onClicked: {
                                                appController.clear_element_selection()
                                                syncSelectedElementEditor()
                                                shell_status = "已取消单元选中"
                                            }
                                        }

                                        Button {
                                            Layout.fillWidth: true
                                            text: "删除当前单元"
                                            enabled: appController.selected_element_exists
                                            onClicked: deleteCurrentElementFromView()
                                        }
                                    }

                                    Item {
                                        Layout.fillHeight: true
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
                                implicitHeight: 220

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
                                        objectName: "solveTaskButton"
                                        text: "提交任务并求解"
                                        onClicked: {
                                            var ok = appController.solve_model()
                                            if (ok) {
                                                shell_status = "右侧任务区求解完成"
                                                refreshNodeResultModel()
                                                refreshElementResultModel()
                                            } else {
                                                shell_status = "右侧任务区求解失败"
                                            }
                                        }
                                    }

                                    Button {
                                        text: "查看日志"
                                        onClicked: shell_status = "查看日志：占位功能"
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 6
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 360

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "结果摘要"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 1
                                        color: "#e2e8ef"
                                    }

                                    Label {
                                        text: "节点位移结果"
                                        color: textMain
                                        font.bold: true
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 110
                                        color: "#fbfcfd"
                                        border.color: "#d7dee6"
                                        radius: 4

                                        ListView {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            clip: true
                                            spacing: 4
                                            model: nodeResultModel

                                            delegate: Rectangle {
                                                width: ListView.view.width
                                                height: 28
                                                radius: 4
                                                color: index % 2 === 0 ? "#fcfdff" : "#f6f9fc"
                                                border.color: "#e1e7ee"

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 6
                                                    anchors.rightMargin: 6
                                                    spacing: 8

                                                    Label {
                                                        text: "N" + model.node_id
                                                        Layout.preferredWidth: 44
                                                        color: textMain
                                                    }

                                                    Label {
                                                        text: "Ux=" + Number(model.ux).toExponential(3)
                                                        Layout.fillWidth: true
                                                        color: textMain
                                                    }

                                                    Label {
                                                        text: "Uy=" + Number(model.uy).toExponential(3)
                                                        Layout.fillWidth: true
                                                        color: textMain
                                                    }
                                                }
                                            }

                                            footer: nodeResultModel.count === 0 ? emptyNodeResultLabel : null
                                        }

                                        Component {
                                            id: emptyNodeResultLabel

                                            Label {
                                                width: parent ? parent.width : 200
                                                text: "暂无节点位移结果"
                                                horizontalAlignment: Text.AlignHCenter
                                                color: textMuted
                                                topPadding: 20
                                            }
                                        }
                                    }

                                    Label {
                                        text: "单元结果"
                                        color: textMain
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
                                            anchors.margins: 4
                                            clip: true
                                            spacing: 4
                                            model: elementResultModel

                                            delegate: Rectangle {
                                                width: ListView.view.width
                                                height: 32
                                                radius: 4
                                                color: index % 2 === 0 ? "#fcfdff" : "#f6f9fc"
                                                border.color: "#e1e7ee"

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 6
                                                    anchors.rightMargin: 6
                                                    spacing: 8

                                                    Label {
                                                        text: "E" + model.element_id
                                                        Layout.preferredWidth: 44
                                                        color: textMain
                                                    }

                                                    Label {
                                                        text: "σx=" + Number(model.stress_x).toExponential(2)
                                                        Layout.fillWidth: true
                                                        color: textMain
                                                    }

                                                    Label {
                                                        text: "σy=" + Number(model.stress_y).toExponential(2)
                                                        Layout.fillWidth: true
                                                        color: textMain
                                                    }
                                                }
                                            }

                                            footer: elementResultModel.count === 0 ? emptyElementResultLabel : null
                                        }

                                        Component {
                                            id: emptyElementResultLabel

                                            Label {
                                                width: parent ? parent.width : 200
                                                text: "暂无单元结果"
                                                horizontalAlignment: Text.AlignHCenter
                                                color: textMuted
                                                topPadding: 20
                                            }
                                        }
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
                    text: "工具：" + activeViewportTool
                    color: textMain
                    font.pixelSize: 12
                }

                Label {
                    text: "缩放：" + Number(viewportZoom * 100).toFixed(0) + "%"
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

    Rectangle {
        id: leftPanelToggleHandle
        z: 30
        width: 22
        height: 58
        radius: 11
        color: "#eef2f6"
        border.color: borderColor
        opacity: 0.94

        x: leftPanelVisible ? leftPanel.width - width / 2 : 0
        y: Math.max(104, window.height / 2 - height / 2)

        Text {
            anchors.centerIn: parent
            text: leftPanelVisible ? "◀" : "▶"
            color: textMuted
            font.pixelSize: 14
            font.bold: true
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true

            onEntered: parent.color = accentSoft
            onExited: parent.color = "#eef2f6"

            onClicked: {
                leftPanelVisible = !leftPanelVisible
                shell_status = leftPanelVisible ? "已展开左侧栏" : "已隐藏左侧栏"
            }
        }
    }

    Rectangle {
        id: rightPanelToggleHandle
        z: 30
        width: 22
        height: 58
        radius: 11
        color: "#eef2f6"
        border.color: borderColor
        opacity: 0.94

        x: rightPanelVisible ? window.width - rightPanel.width - width / 2 : window.width - width
        y: Math.max(104, window.height / 2 - height / 2)

        Text {
            anchors.centerIn: parent
            text: rightPanelVisible ? "▶" : "◀"
            color: textMuted
            font.pixelSize: 14
            font.bold: true
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true

            onEntered: parent.color = accentSoft
            onExited: parent.color = "#eef2f6"

            onClicked: {
                rightPanelVisible = !rightPanelVisible
                shell_status = rightPanelVisible ? "已展开右侧栏" : "已隐藏右侧栏"
            }
        }
    }
}