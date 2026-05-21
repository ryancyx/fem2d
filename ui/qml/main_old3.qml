import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes
import QtQuick.Dialogs

ApplicationWindow {
    id: window
    objectName: "mainWindow"

    visible: true
    width: 1600
    height: 920
    title: "FEM2D Studio"
    color: "#d8dde3"

    property color bgWindow: "#d8dde3"
    property color bgDark: "#1f2730"
    property color bgToolbar: "#e7ebf0"
    property color bgPanel: "#f4f6f8"
    property color bgPanel2: "#edf1f4"
    property color bgPanel3: "#fbfcfc"
    property color borderColor: "#c7d0d9"
    property color textMain: "#1f2933"
    property color textMuted: "#6b7785"
    property color accent: "#5f7488"
    property color accentSoft: "#e2e8ed"
    property color accentLine: "#95a3af"
    property color viewportBg: "#f7f9fb"

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
    property bool viewportPanActive: false
    property bool viewportPanMoved: false


    FileDialog {
        id: openProjectDialog
        title: "打开 FEM2D 工程"
        fileMode: FileDialog.OpenFile
        nameFilters: ["FEM2D 工程文件 (*.json)", "所有文件 (*)"]

        onAccepted: {
            var ok = appController.load_project_from_file(selectedFile)
            shell_status = appController.status_text
            if (ok) {
                refreshAllData()
                resetViewportTransform()
            }
        }
    }

    FileDialog {
        id: saveProjectDialog
        title: "保存 FEM2D 工程"
        fileMode: FileDialog.SaveFile
        nameFilters: ["FEM2D 工程文件 (*.json)", "所有文件 (*)"]

        onAccepted: {
            var ok = appController.save_project_to_file(selectedFile)
            shell_status = appController.status_text
            if (ok) {
                refreshAllData()
            }
        }
    }

    FileDialog {
        id: exportNodeResultsDialog
        title: "导出节点位移结果"
        fileMode: FileDialog.SaveFile
        nameFilters: ["CSV 文件 (*.csv)", "所有文件 (*)"]

        onAccepted: {
            var ok = appController.export_node_results_to_csv(selectedFile)
            shell_status = appController.status_text
            if (ok) {
                refreshResultModels()
            }
        }
    }

    FileDialog {
        id: exportElementResultsDialog
        title: "导出单元应力应变结果"
        fileMode: FileDialog.SaveFile
        nameFilters: ["CSV 文件 (*.csv)", "所有文件 (*)"]

        onAccepted: {
            var ok = appController.export_element_results_to_csv(selectedFile)
            shell_status = appController.status_text
            if (ok) {
                refreshResultModels()
            }
        }
    }

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

    function findElementRowById(elementId) {
        for (var i = 0; i < elementRowsCache.length; i++) {
            var row = elementRowsCache[i]
            if (row.element_id == elementId || row.id == elementId)
                return row
        }
        return null
    }

    function edgeNodeIdsForElementRow(elementRow, edgeIndex) {
        if (!elementRow || !elementRow.node_ids || elementRow.node_ids.length !== 3)
            return []

        if (edgeIndex === 1)
            return [elementRow.node_ids[1], elementRow.node_ids[2]]
        if (edgeIndex === 2)
            return [elementRow.node_ids[2], elementRow.node_ids[0]]
        return [elementRow.node_ids[0], elementRow.node_ids[1]]
    }

    function refreshDistributedLoadEdgeHighlight() {
        if (typeof distributedLoadEdgeCombo !== "undefined") {
            selectedDistributedLoadEdgeIndex = distributedLoadEdgeCombo.currentIndex >= 0 ? distributedLoadEdgeCombo.currentIndex : 0
        }

        boundaryVisualVersion += 1

        if (elementCanvas)
            elementCanvas.requestPaint()
    }

    function refreshElementModel() {
        var rows = appController.get_element_rows()
        var copy = []
        for (var i = 0; i < rows.length; i++) {
            copy.push({
                element_id: rows[i].id,
                node_ids: rows[i].node_ids,
                material_id: rows[i].material_id,
                element_type: rows[i].element_type,
                material_color: rows[i].material_color || "#AEB8C2",
                fill_color: rows[i].fill_color || "#dbe6fb99",
                selected_fill_color: rows[i].selected_fill_color || "#c9dcffbb"
            })
        }
        elementRowsCache = copy

        if (elementCanvas)
            elementCanvas.requestPaint()
    }

    function refreshBoundaryModel() {
        var constraintRows = appController.get_constraint_rows ? appController.get_constraint_rows() : appController.get_constraints()
        var constraintCopy = []
        for (var i = 0; i < constraintRows.length; i++) {
            constraintCopy.push({
                constraint_id: constraintRows[i].id,
                node_id: constraintRows[i].node_id,
                ux_fixed: constraintRows[i].ux_fixed,
                uy_fixed: constraintRows[i].uy_fixed,
                ux_value: constraintRows[i].ux_value,
                uy_value: constraintRows[i].uy_value
            })
        }
        constraintRowsCache = constraintCopy

        var loadRows = appController.get_load_rows ? appController.get_load_rows() : appController.get_loads()
        var loadCopy = []
        for (var j = 0; j < loadRows.length; j++) {
            loadCopy.push({
                load_id: loadRows[j].id,
                node_id: loadRows[j].node_id,
                fx: loadRows[j].fx,
                fy: loadRows[j].fy,
                load_type: loadRows[j].load_type
            })
        }
        loadRowsCache = loadCopy

        var distributedRows = appController.get_distributed_load_rows ? appController.get_distributed_load_rows() : []
        var distributedCopy = []
        for (var k = 0; k < distributedRows.length; k++) {
            distributedCopy.push({
                distributed_load_id: distributedRows[k].id,
                element_id: distributedRows[k].element_id,
                local_edge_index: distributedRows[k].local_edge_index,
                node_i_id: distributedRows[k].node_i_id,
                node_j_id: distributedRows[k].node_j_id,
                qx: distributedRows[k].qx,
                qy: distributedRows[k].qy,
                load_type: distributedRows[k].load_type
            })
        }
        distributedLoadRowsCache = distributedCopy
        boundaryVisualVersion += 1

        if (elementCanvas)
            elementCanvas.requestPaint()
    }

    function constraintRowByNodeId(nodeId) {
        for (var i = 0; i < constraintRowsCache.length; i++) {
            if (constraintRowsCache[i].node_id === nodeId)
                return constraintRowsCache[i]
        }
        return null
    }

    function hasConstraintForNode(nodeId) {
        return constraintRowByNodeId(nodeId) !== null
    }

    function refreshMaterialModel() {
        var rows = appController.get_material_rows ? appController.get_material_rows() : appController.get_materials()
        var copy = []
        for (var i = 0; i < rows.length; i++) {
            copy.push({
                material_id: rows[i].id,
                material_name: rows[i].name,
                young_modulus: rows[i].young_modulus,
                poisson_ratio: rows[i].poisson_ratio,
                thickness: rows[i].thickness,
                plane_mode: rows[i].plane_mode,
                material_color: rows[i].color || "#AEB8C2"
            })
        }
        materialRowsCache = copy

        if (selectedMaterialIdForEdit !== -1) {
            var currentRow = findMaterialRowById(selectedMaterialIdForEdit)
            if (currentRow) {
                fillMaterialEditor(currentRow.material_id)
            } else {
                clearMaterialEditor()
            }
        } else if (materialRowsCache.length === 0) {
            clearMaterialEditor()
        }
    }

    function findMaterialRowById(materialId) {
        for (var i = 0; i < materialRowsCache.length; i++) {
            if (materialRowsCache[i].material_id === materialId)
                return materialRowsCache[i]
        }
        return null
    }

    function fillMaterialEditor(materialId) {
        var row = findMaterialRowById(materialId)
        if (!row)
            return

        selectedMaterialIdForEdit = row.material_id
        materialIdValue.text = String(row.material_id)
        materialNameField.text = row.material_name
        materialEField.text = Number(row.young_modulus).toString()
        materialNuField.text = Number(row.poisson_ratio).toString()
        materialThicknessField.text = Number(row.thickness).toString()
        materialPlaneModeCombo.currentIndex = 0
    }

    function clearMaterialEditor() {
        selectedMaterialIdForEdit = -1
        materialIdValue.text = "—"
        materialNameField.text = ""
        materialEField.text = ""
        materialNuField.text = ""
        materialThicknessField.text = ""
        materialPlaneModeCombo.currentIndex = 0
    }

    function materialComboIndexById(materialId) {
        for (var i = 0; i < materialRowsCache.length; i++) {
            if (materialRowsCache[i].material_id === materialId)
                return i
        }
        return -1
    }

    function materialIdAt(comboIndex) {
        if (comboIndex < 0 || comboIndex >= materialRowsCache.length)
            return -1
        return materialRowsCache[comboIndex].material_id
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

        if (contourOverlayVisible && contourCanvas)
            contourCanvas.requestPaint()
    }

    function nodeResultRowById(nodeId) {
        for (var i = 0; i < nodeResultModel.count; i++) {
            var row = nodeResultModel.get(i)
            if (row.node_id === nodeId || row.id === nodeId)
                return row
        }
        return null
    }

    function elementResultRowById(elementId) {
        for (var i = 0; i < elementResultModel.count; i++) {
            var row = elementResultModel.get(i)
            if (row.element_id === elementId || row.id === elementId)
                return row
        }
        return null
    }

    function displacementMagnitudeByNodeId(nodeId) {
        var row = nodeResultRowById(nodeId)
        if (!row)
            return NaN

        var ux = Number(row.ux)
        var uy = Number(row.uy)
        if (!isFinite(ux) || !isFinite(uy))
            return NaN

        return Math.sqrt(ux * ux + uy * uy)
    }

    function vonMisesByElementId(elementId) {
        var row = elementResultRowById(elementId)
        if (!row)
            return NaN

        var sx = Number(row.stress_x)
        var sy = Number(row.stress_y)
        var txy = Number(row.tau_xy)
        if (!isFinite(sx) || !isFinite(sy) || !isFinite(txy))
            return NaN

        var value = sx * sx - sx * sy + sy * sy + 3.0 * txy * txy
        return Math.sqrt(Math.max(value, 0.0))
    }

    function averagedVonMisesByNodeId(nodeId) {
        var sum = 0.0
        var count = 0

        for (var i = 0; i < elementRowsCache.length; i++) {
            var elementRow = elementRowsCache[i]
            if (!elementRow || !elementRow.node_ids)
                continue

            if (elementRow.node_ids.indexOf(nodeId) === -1)
                continue

            var vm = vonMisesByElementId(elementRow.element_id)
            if (isFinite(vm)) {
                sum += vm
                count += 1
            }
        }

        if (count === 0)
            return NaN
        return sum / count
    }

    function contourValueByNodeId(nodeId) {
        if (contourMode === "von_mises")
            return averagedVonMisesByNodeId(nodeId)
        return displacementMagnitudeByNodeId(nodeId)
    }

    function contourDisplayTitle() {
        if (contourMode !== "von_mises")
            return "位移云图"
        return vonMisesContourStyle === "reliable" ? "Von Mises 应力云图（可靠）" : "Von Mises 应力云图（平滑）"
    }

    function toggleVonMisesContourStyle() {
        vonMisesContourStyle = vonMisesContourStyle === "smooth" ? "reliable" : "smooth"
        contourTitle = contourDisplayTitle()
        updateContourRange()
        if (contourOverlayVisible && contourMode === "von_mises" && contourCanvas)
            contourCanvas.requestPaint()
    }

    function updateContourRange() {
        var minValue = Number.POSITIVE_INFINITY
        var maxValue = Number.NEGATIVE_INFINITY

        if (contourMode === "von_mises" && vonMisesContourStyle === "reliable") {
            for (var e = 0; e < elementRowsCache.length; e++) {
                var elementRow = elementRowsCache[e]
                if (!elementRow)
                    continue

                var elementValue = vonMisesByElementId(elementRow.element_id)
                if (!isFinite(elementValue))
                    continue

                minValue = Math.min(minValue, elementValue)
                maxValue = Math.max(maxValue, elementValue)
            }
        } else {
            for (var i = 0; i < nodeListModel.count; i++) {
                var nodeRow = nodeListModel.get(i)
                var value = contourValueByNodeId(nodeRow.node_id)
                if (!isFinite(value))
                    continue

                minValue = Math.min(minValue, value)
                maxValue = Math.max(maxValue, value)
            }
        }

        if (!isFinite(minValue) || !isFinite(maxValue)) {
            contourMinValue = 0.0
            contourMaxValue = 1.0
            return
        }

        if (Math.abs(maxValue - minValue) < 1e-30) {
            contourMinValue = minValue
            contourMaxValue = minValue + 1.0
            return
        }

        contourMinValue = minValue
        contourMaxValue = maxValue
    }

    function contourColor(value, alpha) {
        if (!isFinite(value))
            return "rgba(170, 184, 194, " + alpha + ")"

        var ratio = (value - contourMinValue) / (contourMaxValue - contourMinValue)
        ratio = Math.max(0.0, Math.min(1.0, ratio))

        // 工程常用蓝-青-绿-黄-红伪彩色，避免引入额外模块。
        var stops = [
            { p: 0.00, r: 45,  g: 84,  b: 184 },
            { p: 0.25, r: 40,  g: 172, b: 220 },
            { p: 0.50, r: 76,  g: 175, b: 80  },
            { p: 0.75, r: 245, g: 196, b: 66  },
            { p: 1.00, r: 210, g: 65,  b: 56  }
        ]

        for (var i = 0; i < stops.length - 1; i++) {
            var a = stops[i]
            var b = stops[i + 1]
            if (ratio >= a.p && ratio <= b.p) {
                var local = (ratio - a.p) / Math.max(1e-12, b.p - a.p)
                var r = Math.round(a.r + (b.r - a.r) * local)
                var g = Math.round(a.g + (b.g - a.g) * local)
                var bb = Math.round(a.b + (b.b - a.b) * local)
                return "rgba(" + r + ", " + g + ", " + bb + ", " + alpha + ")"
            }
        }

        return "rgba(210, 65, 56, " + alpha + ")"
    }

    function contourNodeToCanvasX(xValue, canvasWidth) {
        var padding = 44
        var usableWidth = Math.max(1, canvasWidth - padding * 2)
        return padding + ((xValue - viewportMinX()) / viewportRangeX()) * usableWidth
    }

    function contourNodeToCanvasY(yValue, canvasHeight) {
        var padding = 44
        var usableHeight = Math.max(1, canvasHeight - padding * 2)
        return canvasHeight - padding - ((yValue - viewportMinY()) / viewportRangeY()) * usableHeight
    }

    function openContourOverlay(modeName) {
        if (!appController.solver_has_result || nodeResultModel.count === 0) {
            shell_status = "暂无求解结果，无法显示云图"
            return
        }

        if (modeName === "von_mises" && elementResultModel.count === 0) {
            shell_status = "暂无单元应力结果，无法显示 Von Mises 云图"
            return
        }

        contourMode = modeName
        contourTitle = contourDisplayTitle()
        updateContourRange()
        contourOverlayVisible = true
        shell_status = "已打开" + contourTitle

        if (contourCanvas)
            contourCanvas.requestPaint()
    }

    function closeContourOverlay() {
        contourOverlayVisible = false
        shell_status = "已关闭云图窗口"
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

            var info = appController.get_selected_node_boundary_info()
            constraintUxCheck.checked = info.has_constraint ? info.ux_fixed : false
            constraintUyCheck.checked = info.has_constraint ? info.uy_fixed : false
            constraintUxValueField.text = info.has_constraint && info.ux_fixed ? Number(info.ux_value).toString() : ""
            constraintUyValueField.text = info.has_constraint && info.uy_fixed ? Number(info.uy_value).toString() : ""
            loadFxField.text = info.has_load ? Number(info.fx).toString() : ""
            loadFyField.text = info.has_load ? Number(info.fy).toString() : ""
        } else {
            selectedNodeIdValue.text = "—"
            selectedXField.text = ""
            selectedYField.text = ""
            constraintUxCheck.checked = false
            constraintUyCheck.checked = false
            constraintUxValueField.text = ""
            constraintUyValueField.text = ""
            loadFxField.text = ""
            loadFyField.text = ""
        }

        refreshSelectionInfo()
    }

    function syncSelectedElementEditor() {
        if (appController.selected_element_exists) {
            selectedElementIdValue.text = String(appController.selected_element_id)
            selectedElementNodeIdsValue.text = appController.selected_element_node_ids_info.join(" - ")
            selectedElementMaterialValue.text = String(appController.selected_element_material_id)
            selectedElementTypeValue.text = appController.selected_element_type

            var info = appController.get_selected_element_material_info()
            selectedElementMaterialNameValue.text = info.has_material ? info.material_name : "未分配"
            selectedElementPlaneModeValue.text = info.has_material ? info.plane_mode : "—"
            elementMaterialCombo.currentIndex = materialComboIndexById(appController.selected_element_material_id)

            if (distributedLoadEdgeCombo.currentIndex < 0)
                distributedLoadEdgeCombo.currentIndex = 0
            selectedDistributedLoadEdgeIndex = distributedLoadEdgeCombo.currentIndex >= 0 ? distributedLoadEdgeCombo.currentIndex : 0
            refreshDistributedLoadEdgeHighlight()
            syncSelectedDistributedLoadEditor()
        } else {
            selectedElementIdValue.text = "—"
            selectedElementNodeIdsValue.text = "—"
            selectedElementMaterialValue.text = "—"
            selectedElementTypeValue.text = "—"
            selectedElementMaterialNameValue.text = "—"
            selectedElementPlaneModeValue.text = "—"
            elementMaterialCombo.currentIndex = -1
            distributedLoadQxField.text = ""
            distributedLoadQyField.text = ""
            refreshDistributedLoadEdgeHighlight()
        }

        refreshSelectionInfo()
    }

    function syncSelectedDistributedLoadEditor() {
        if (typeof distributedLoadEdgeCombo === "undefined" || typeof distributedLoadQxField === "undefined" || typeof distributedLoadQyField === "undefined")
            return

        if (!appController.selected_element_exists || !appController.get_selected_element_distributed_load_info) {
            distributedLoadQxField.text = ""
            distributedLoadQyField.text = ""
            return
        }

        var edgeIndex = distributedLoadEdgeCombo.currentIndex >= 0 ? distributedLoadEdgeCombo.currentIndex : 0
        var info = appController.get_selected_element_distributed_load_info(edgeIndex)
        if (info && info.has_load) {
            distributedLoadQxField.text = Number(info.qx).toString()
            distributedLoadQyField.text = Number(info.qy).toString()
        } else {
            distributedLoadQxField.text = ""
            distributedLoadQyField.text = ""
        }
    }

    function refreshAllData() {
        refreshNodeModel()
        refreshElementModel()
        refreshMaterialModel()
        refreshBoundaryModel()
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

    function pointInTriangle(px, py, ax, ay, bx, by, cx, cy) {
        var d1 = (px - bx) * (ay - by) - (ax - bx) * (py - by)
        var d2 = (px - cx) * (by - cy) - (bx - cx) * (py - cy)
        var d3 = (px - ax) * (cy - ay) - (cx - ax) * (py - ay)

        var hasNegative = (d1 < -0.0001) || (d2 < -0.0001) || (d3 < -0.0001)
        var hasPositive = (d1 > 0.0001) || (d2 > 0.0001) || (d3 > 0.0001)

        return !(hasNegative && hasPositive)
    }

    function elementIdAtViewportPoint(viewX, viewY) {
        for (var i = elementRowsCache.length - 1; i >= 0; i--) {
            var elementRow = elementRowsCache[i]
            if (!elementRow || !elementRow.node_ids || elementRow.node_ids.length !== 3)
                continue

            var n1 = findNodeRowById(elementRow.node_ids[0])
            var n2 = findNodeRowById(elementRow.node_ids[1])
            var n3 = findNodeRowById(elementRow.node_ids[2])
            if (n1 === null || n2 === null || n3 === null)
                continue

            var inside = pointInTriangle(
                viewX,
                viewY,
                nodeToViewportX(n1.node_x),
                nodeToViewportY(n1.node_y),
                nodeToViewportX(n2.node_x),
                nodeToViewportY(n2.node_y),
                nodeToViewportX(n3.node_x),
                nodeToViewportY(n3.node_y)
            )

            if (inside)
                return elementRow.element_id
        }

        return -1
    }

    function selectElementAtViewportPoint(viewX, viewY) {
        var elementId = elementIdAtViewportPoint(viewX, viewY)
        if (elementId === -1)
            return false

        var ok = appController.select_element(elementId)
        if (ok) {
            rightPanelVisible = true
            syncSelectedElementEditor()
            refreshSelectionInfo()
            if (elementCanvas)
                elementCanvas.requestPaint()
            shell_status = "已在视口中选中单元 " + elementId + "，可在右侧直接修改材料"
        } else {
            shell_status = appController.status_text
        }

        return ok
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
    property var materialRowsCache: []
    property var constraintRowsCache: []
    property var loadRowsCache: []
    property var distributedLoadRowsCache: []
    property int selectedDistributedLoadEdgeIndex: 0
    property int boundaryVisualVersion: 0
    property int selectedMaterialIdForEdit: -1
    property int rightInspectorPageHint: 0

    // 阶段13.3：工程版云图临时覆盖窗口状态。
    // 只使用现有节点/单元/结果缓存，不改变主视口绘制逻辑。
    property bool contourOverlayVisible: false
    property string contourMode: "displacement"
    property string contourTitle: "位移云图"
    property string vonMisesContourStyle: "smooth"
    property real contourMinValue: 0.0
    property real contourMaxValue: 1.0


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

        function onMaterialDataChanged() {
            refreshMaterialModel()
            refreshElementModel()
            syncSelectedElementEditor()
        }

        function onBoundaryDataChanged() {
            refreshBoundaryModel()
            syncSelectedNodeEditor()
            syncSelectedDistributedLoadEditor()
            if (elementCanvas)
                elementCanvas.requestPaint()
        }

        function onModelStatsChanged() {
            refreshMaterialModel()
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

    component HeaderActionButton: Item {
        id: control

        property alias text: label.text
        property bool emphasized: false
        property bool enabled: true
        property bool hovered: mouseArea.containsMouse
        property bool down: mouseArea.pressed
        signal clicked

        implicitHeight: 32
        implicitWidth: Math.max(68, label.implicitWidth + 20)

        Rectangle {
            anchors.fill: parent
            radius: 10
            antialiasing: true
            color: "transparent"
            clip: true
            border.width: 0

            Rectangle {
                anchors.fill: parent
                radius: 10
                antialiasing: true
                gradient: Gradient {
                    GradientStop { position: 0.0; color: !control.enabled ? "#eef1f4" : control.down ? (control.emphasized ? "#566979" : "#d9e0e7") : control.hovered ? (control.emphasized ? "#748796" : "#f4f6f8") : (control.emphasized ? "#6f8191" : "#fafbfc") }
                    GradientStop { position: 1.0; color: !control.enabled ? "#e7ebef" : control.down ? (control.emphasized ? "#46515d" : "#cfd8e1") : control.hovered ? (control.emphasized ? "#6a7c8c" : "#eceff3") : (control.emphasized ? "#6a7c8c" : "#f1f3f5") }
                }
                border.width: 1
                border.color: !control.enabled ? "#d2d9e1" : (control.emphasized ? "#556877" : "#d2d8df")
            }
        }

        Text {
            id: label
            anchors.centerIn: parent
            color: !control.enabled ? "#8b95a1" : (control.emphasized ? "#ffffff" : textMain)
            font.pixelSize: 11
            font.bold: control.emphasized || control.down
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            enabled: control.enabled
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: control.clicked()
        }
    }

    component HeaderIconButton: Item {
        id: control

        property alias text: label.text
        property bool active: false
        property bool enabled: true
        property bool hovered: mouseArea.containsMouse
        property bool down: mouseArea.pressed
        signal clicked

        implicitHeight: 32
        implicitWidth: 36

        Rectangle {
            anchors.fill: parent
            radius: 11
            antialiasing: true
            color: "transparent"
            clip: true

            Rectangle {
                anchors.fill: parent
                radius: 11
                antialiasing: true
                gradient: Gradient {
                    GradientStop { position: 0.0; color: !control.enabled ? "#eef1f4" : control.down ? (control.active ? "#576877" : "#d8dfe6") : control.hovered ? (control.active ? "#778999" : "#f4f6f8") : (control.active ? "#6f8191" : "#fafbfc") }
                    GradientStop { position: 1.0; color: !control.enabled ? "#e7ebef" : control.down ? (control.active ? "#46515d" : "#ced7e0") : control.hovered ? (control.active ? "#6a7c8c" : "#eceff3") : (control.active ? "#6a7c8c" : "#f1f3f5") }
                }
                border.width: 1
                border.color: !control.enabled ? "#d2d9e1" : (control.active ? "#556877" : "#d2d8df")
            }
        }

        Text {
            id: label
            anchors.centerIn: parent
            color: !control.enabled ? "#8b95a1" : (control.active ? "#ffffff" : textMain)
            font.pixelSize: 15
            font.bold: control.active
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            enabled: control.enabled
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: control.clicked()
        }
    }

    component PanelActionButton: Item {
        id: control

        property alias text: label.text
        property bool emphasized: false
        property bool enabled: true
        property bool hovered: mouseArea.containsMouse
        property bool down: mouseArea.pressed
        signal clicked

        implicitHeight: 38
        implicitWidth: Math.max(96, label.implicitWidth + 36)
        Layout.minimumHeight: implicitHeight

        Rectangle {
            anchors.fill: parent
            radius: 13
            antialiasing: true
            color: "transparent"
            clip: true

            Rectangle {
                anchors.fill: parent
                radius: 13
                antialiasing: true
                gradient: Gradient {
                    GradientStop { position: 0.0; color: !control.enabled ? "#eef1f4" : control.down ? (control.emphasized ? "#576877" : "#dbe3ea") : control.hovered ? (control.emphasized ? "#778999" : "#f7f8fa") : (control.emphasized ? "#6f8191" : "#fbfcfc") }
                    GradientStop { position: 1.0; color: !control.enabled ? "#e6ebef" : control.down ? (control.emphasized ? "#46515d" : "#d1dbe3") : control.hovered ? (control.emphasized ? "#6a7c8c" : "#eef2f5") : (control.emphasized ? "#6a7c8c" : "#f0f3f6") }
                }
                border.width: 1
                border.color: !control.enabled ? "#d2d9e0" : (control.emphasized ? "#556877" : "#d4dbe3")
            }
        }

        Text {
            id: label
            anchors.centerIn: parent
            color: !control.enabled ? "#8b95a1" : (control.emphasized ? "#ffffff" : textMain)
            font.pixelSize: 11
            font.bold: control.emphasized || control.down
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            width: Math.max(0, control.width - 20)
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            enabled: control.enabled
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: control.clicked()
        }
    }

    component PanelTabButton: Item {
        id: control

        property alias text: contentLabel.text
        property bool checked: false
        property bool enabled: true
        property bool hovered: mouseArea.containsMouse
        property bool down: mouseArea.pressed
        signal clicked

        implicitHeight: 38
        implicitWidth: Math.max(84, contentLabel.implicitWidth + 32)

        Rectangle {
            anchors.fill: parent
            radius: 13
            antialiasing: true
            color: "transparent"
            clip: true

            Rectangle {
                anchors.fill: parent
                radius: 13
                antialiasing: true
                gradient: Gradient {
                    GradientStop { position: 0.0; color: !control.enabled ? "#eef1f4" : control.checked ? "#738494" : (control.down ? "#d7dfe6" : control.hovered ? "#f5f7f9" : "#fbfcfc") }
                    GradientStop { position: 1.0; color: !control.enabled ? "#e6ebef" : control.checked ? "#6a7c8c" : (control.down ? "#cfd8e1" : control.hovered ? "#edf1f4" : "#f1f4f7") }
                }
                border.width: 1
                border.color: !control.enabled ? "#d2d9e0" : (control.checked ? "#556877" : "#d4dbe3")
            }
        }

        Text {
            id: contentLabel
            anchors.centerIn: parent
            color: !control.enabled ? "#8b95a1" : (control.checked ? "#ffffff" : textMain)
            font.pixelSize: 12
            font.bold: control.checked
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        MouseArea {
            id: mouseArea
            anchors.fill: parent
            enabled: control.enabled
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: control.clicked()
        }
    }


    component PanelTextField: TextField {
        id: control

        implicitHeight: 38
        leftPadding: 14
        rightPadding: 14
        topPadding: 0
        bottomPadding: 0
        hoverEnabled: true
        focusPolicy: Qt.ClickFocus
        color: textMain
        placeholderTextColor: "#93a0ad"
        selectedTextColor: "#ffffff"
        selectionColor: "#7b8b99"
        font.pixelSize: 12

        background: Item {
            implicitWidth: control.implicitWidth
            implicitHeight: control.implicitHeight
            clip: true

            Rectangle {
                anchors.fill: parent
                radius: 12
                antialiasing: true
                color: !control.enabled ? "#eef1f4"
                      : control.activeFocus ? "#ffffff"
                      : control.hovered ? "#f8fafb"
                      : "#fbfcfc"
                border.width: control.activeFocus ? 1.5 : 1
                border.color: !control.enabled ? "#d8dee5"
                              : control.activeFocus ? "#6f8191"
                              : control.hovered ? "#b9c4ce"
                              : "#d4dbe3"
            }
        }
    }

    component PanelCheckBox: CheckBox {
        id: control

        spacing: 10
        hoverEnabled: true
        focusPolicy: Qt.NoFocus

        indicator: Item {
            implicitWidth: 20
            implicitHeight: 20
            clip: true

            Rectangle {
                anchors.fill: parent
                radius: 6
                antialiasing: true
                color: control.checked ? "#6f8191" : (control.hovered ? "#f7f9fb" : "#fbfcfc")
                border.width: 1
                border.color: control.checked ? "#556877" : "#cfd7df"
            }

            Text {
                anchors.centerIn: parent
                text: "✓"
                color: "#ffffff"
                font.pixelSize: 12
                font.bold: true
                visible: control.checked
            }
        }

        contentItem: Text {
            text: control.text
            color: textMain
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
        }
    }

    component PanelComboBox: ComboBox {
        id: control

        implicitHeight: 38
        leftPadding: 14
        rightPadding: 34
        topPadding: 0
        bottomPadding: 0
        hoverEnabled: true
        focusPolicy: Qt.NoFocus

        contentItem: Text {
            text: control.displayText
            color: control.enabled ? textMain : "#8b95a1"
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        background: Item {
            implicitWidth: control.implicitWidth
            implicitHeight: control.implicitHeight
            clip: true

            Rectangle {
                anchors.fill: parent
                radius: 12
                antialiasing: true
                color: !control.enabled ? "#eef1f4"
                      : control.down ? "#eef2f5"
                      : control.hovered ? "#f8fafb"
                      : "#fbfcfc"
                border.width: 1
                border.color: !control.enabled ? "#d8dee5"
                              : control.hovered ? "#bcc7d0"
                              : "#d4dbe3"
            }
        }

        indicator: Canvas {
            x: control.width - width - 12
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
                context.fillStyle = control.enabled ? "#687785" : "#98a3ae"
                context.fill()
            }
        }

        delegate: ItemDelegate {
            width: control.width
            height: 34
            text: modelData
            highlighted: control.highlightedIndex === index
            hoverEnabled: true
            focusPolicy: Qt.NoFocus

            contentItem: Text {
                text: modelData
                color: textMain
                font.pixelSize: 12
                verticalAlignment: Text.AlignVCenter
                leftPadding: 12
                rightPadding: 12
                elide: Text.ElideRight
            }

            background: Item {
                clip: true
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 2
                    radius: 10
                    color: parent.parent.highlighted ? "#e4eaf0" : (parent.parent.hovered ? "#f5f8fa" : "transparent")
                }
            }
        }

        popup: Popup {
            y: control.height + 6
            width: control.width
            padding: 6
            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex
                spacing: 2
            }

            background: Rectangle {
                radius: 14
                color: "#ffffff"
                border.color: "#d2d9e0"
            }
        }
    }

    component HeaderComboBox: ComboBox {
        id: control

        implicitWidth: 124
        implicitHeight: 32
        leftPadding: 12
        rightPadding: 28
        hoverEnabled: true
        focusPolicy: Qt.NoFocus

        contentItem: Text {
            text: control.displayText
            color: control.enabled ? textMain : "#8b95a1"
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        background: Item {
            implicitWidth: control.implicitWidth
            implicitHeight: control.implicitHeight
            clip: true

            Rectangle {
                anchors.fill: parent
                radius: 10
                antialiasing: true
                color: !control.enabled ? "#eef1f4"
                      : control.down ? "#edf1f4"
                      : control.hovered ? "#f7f9fb"
                      : "#fbfcfc"
                border.width: 1
                border.color: !control.enabled ? "#d8dee5"
                              : control.hovered ? "#bec8d0"
                              : "#d2d8df"
            }
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
                context.fillStyle = control.enabled ? "#5f6b78" : "#98a3ae"
                context.fill()
            }
        }

        delegate: ItemDelegate {
            width: control.width
            height: 32
            text: modelData
            highlighted: control.highlightedIndex === index
            hoverEnabled: true
            focusPolicy: Qt.NoFocus

            contentItem: Text {
                text: modelData
                color: textMain
                font.pixelSize: 12
                verticalAlignment: Text.AlignVCenter
                leftPadding: 10
                rightPadding: 10
                elide: Text.ElideRight
            }

            background: Item {
                clip: true
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 2
                    radius: 9
                    color: parent.parent.highlighted ? accentSoft : (parent.parent.hovered ? "#f5f8fa" : "transparent")
                }
            }
        }

        popup: Popup {
            y: control.height + 6
            width: control.width
            padding: 6
            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex
                spacing: 2
            }

            background: Rectangle {
                radius: 12
                color: "#ffffff"
                border.color: "#d2d9e0"
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 90
            color: bgDark
            border.color: "#18202a"
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
                            color: "#f3f5f7"
                            font.pixelSize: 16
                            font.bold: true
                        }

                        Rectangle {
                            width: 1
                            height: 16
                            color: "#6e7884"
                        }

                        Label {
                            text: "当前工程：" + current_workspace
                            color: "#d6dde5"
                            font.pixelSize: 13
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            radius: 4
                            color: "#394554"
                            border.color: "#475667"
                            implicitWidth: 150
                            implicitHeight: 24

                            Label {
                                anchors.centerIn: parent
                                text: "模式：" + appController.current_mode
                                color: "#eef3f7"
                                font.pixelSize: 12
                            }
                        }

                        Rectangle {
                            radius: 4
                            color: "#394554"
                            border.color: "#475667"
                            implicitWidth: 190
                            implicitHeight: 24

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
                    border.color: "#c4ccd5"
                    clip: true

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 7
                        spacing: 7

                        Rectangle {
                            radius: 10
                            color: "#f8f9fa"
                            border.color: "#cfd6de"
                            implicitHeight: 40
                            Layout.preferredWidth: 284
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
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
                                    onClicked: openProjectDialog.open()
                                }

                                HeaderActionButton {
                                    text: "保存"
                                    onClicked: saveProjectDialog.open()
                                }
                            }
                        }

                        Rectangle {
                            radius: 10
                            color: "#f8f9fa"
                            border.color: "#cfd6de"
                            implicitHeight: 40
                            Layout.preferredWidth: 428
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
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
                                    onClicked: { rightPanelVisible = true; materialPopup.open(); shell_status = "已打开材料管理" }
                                }

                                HeaderActionButton {
                                    text: "约束"
                                    onClicked: { rightPanelVisible = true; if (!appController.selected_node_exists) appController.set_node_mode(); shell_status = "请在右侧节点检查器中设置约束" }
                                }

                                HeaderActionButton {
                                    text: "载荷"
                                    onClicked: { rightPanelVisible = true; if (!appController.selected_node_exists) appController.set_node_mode(); shell_status = "请在右侧节点检查器中设置载荷" }
                                }
                            }
                        }

                        Rectangle {
                            radius: 10
                            color: "#f8f9fa"
                            border.color: "#cfd6de"
                            implicitHeight: 40
                            Layout.preferredWidth: 284
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
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
                            radius: 10
                            color: "#f8f9fa"
                            border.color: "#cfd6de"
                            implicitHeight: 40
                            Layout.preferredWidth: 266
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
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
                                    onClicked: {
                                        appController.set_node_mode()
                                        setViewportTool("add")
                                        shell_status = "已切换到节点模式，可在画布中点击添加节点"
                                    }
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
                            radius: 10
                            color: "#f8f9fa"
                            border.color: "#cfd6de"
                            implicitHeight: 40
                            Layout.preferredWidth: 210
                            clip: true

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
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
                SplitView.minimumWidth: leftPanelVisible ? 280 : 0
                SplitView.preferredWidth: leftPanelVisible ? 300 : 0
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#f3f5f7" }
                    GradientStop { position: 1.0; color: bgPanel2 }
                }
                border.color: borderColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 82
                        radius: 14
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "#f7f8fa" }
                            GradientStop { position: 1.0; color: "#edf1f4" }
                        }
                        border.color: borderColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            anchors.topMargin: 10
                            anchors.bottomMargin: 10
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Label {
                                    text: "侧边面板"
                                    color: textMain
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                Rectangle {
                                    Layout.preferredWidth: 6
                                    Layout.preferredHeight: 6
                                    radius: 3
                                    color: accent
                                }

                                Item { Layout.fillWidth: true }

                                Label {
                                    text: leftSectionTabs.currentIndex === 0 ? "编辑" : "查看"
                                    color: textMuted
                                    font.pixelSize: 11
                                }
                            }

                            RowLayout {
                                id: leftSectionTabs
                                Layout.fillWidth: true
                                property int currentIndex: 0
                                spacing: 8

                                PanelTabButton {
                                    Layout.fillWidth: true
                                    text: "模型"
                                    checked: leftSectionTabs.currentIndex === 0
                                    onClicked: leftSectionTabs.currentIndex = 0
                                }
                                PanelTabButton {
                                    Layout.fillWidth: true
                                    text: "结果"
                                    checked: leftSectionTabs.currentIndex === 1
                                    onClicked: leftSectionTabs.currentIndex = 1
                                }
                            }
                        }
                    }

                    StackLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        currentIndex: leftSectionTabs.currentIndex

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            ColumnLayout {
                                width: Math.max(0, leftPanel.width - 28)
                                spacing: 10

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 12
                                    color: bgPanel3
                                    border.color: borderColor
                                    implicitHeight: 244

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 8

                                        Label {
                                            text: "快速操作"
                                            color: textMain
                                            font.pixelSize: 13
                                            font.bold: true
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 1
                                            color: "#dfe5eb"
                                        }

                                        GridLayout {
                                            Layout.fillWidth: true
                                            columns: 2
                                            columnSpacing: 8
                                            rowSpacing: 8

                                            PanelActionButton {
                                                Layout.fillWidth: true
                                                text: "快速新建节点"
                                                emphasized: true
                                                onClicked: {
                                                    appController.set_node_mode()
                                                    setViewportTool("add")
                                                    appController.add_test_node()
                                                    refreshNodeModel()
                                                    syncSelectedNodeEditor()
                                                    shell_status = "已切换到节点模式，并快速新建节点"
                                                }
                                            }

                                            PanelActionButton {
                                                Layout.fillWidth: true
                                                text: "材料管理"
                                                onClicked: {
                                                    materialPopup.open()
                                                    refreshMaterialModel()
                                                    shell_status = "已打开材料管理"
                                                }
                                            }

                                            PanelActionButton {
                                                Layout.fillWidth: true
                                                text: "创建单元"
                                                enabled: appController.selected_element_node_count === 3
                                                onClicked: {
                                                    var ok = appController.create_element_from_selected_nodes()
                                                    shell_status = appController.status_text
                                                    if (ok) {
                                                        refreshElementModel()
                                                    }
                                                }
                                            }

                                            PanelActionButton {
                                                Layout.fillWidth: true
                                                text: "清空选点"
                                                enabled: appController.selected_element_node_count > 0
                                                onClicked: {
                                                    appController.clear_element_node_selection()
                                                    shell_status = appController.status_text
                                                    if (elementCanvas)
                                                        elementCanvas.requestPaint()
                                                }
                                            }
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 32
                                            radius: 4
                                            color: "#fff7e2"
                                            border.color: "#ecd9a2"

                                            Label {
                                                anchors.centerIn: parent
                                                text: "当前单元选点：" + elementSelectionSummary()
                                                color: "#7a5a00"
                                                font.pixelSize: 12
                                                font.bold: appController.selected_element_node_count > 0
                                            }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 12
                                    color: bgPanel3
                                    border.color: borderColor
                                    implicitHeight: 188

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 8

                                        Label {
                                            text: "按坐标添加节点"
                                            color: textMain
                                            font.pixelSize: 13
                                            font.bold: true
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 1
                                            color: "#dfe5eb"
                                        }

                                        GridLayout {
                                            Layout.fillWidth: true
                                            columns: 2
                                            columnSpacing: 8
                                            rowSpacing: 8

                                            Label { text: "X"; color: textMuted }
                                            PanelTextField {
                                                id: addNodeXField
                                                objectName: "addNodeXField"
                                                Layout.fillWidth: true
                                                placeholderText: "输入 X 坐标"
                                            }

                                            Label { text: "Y"; color: textMuted }
                                            PanelTextField {
                                                id: addNodeYField
                                                objectName: "addNodeYField"
                                                Layout.fillWidth: true
                                                placeholderText: "输入 Y 坐标"
                                            }
                                        }

                                        PanelActionButton {
                                            objectName: "addNodeButton"
                                            Layout.fillWidth: true
                                            emphasized: true
                                            text: "新增节点"
                                            onClicked: {
                                                appController.set_node_mode()
                                                setViewportTool("add")
                                                var ok = appController.add_node_by_text(addNodeXField.text, addNodeYField.text)
                                                if (ok) {
                                                    refreshNodeModel()
                                                    syncSelectedNodeEditor()
                                                    shell_status = "已切换到节点模式，并按坐标添加节点"
                                                    addNodeXField.text = ""
                                                    addNodeYField.text = ""
                                                } else {
                                                    shell_status = appController.status_text
                                                }
                                            }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 12
                                    color: bgPanel3
                                    border.color: borderColor
                                    implicitHeight: 470

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 8

                                        RowLayout {
                                            Layout.fillWidth: true

                                            Label {
                                                text: "模型列表"
                                                color: textMain
                                                font.pixelSize: 13
                                                font.bold: true
                                            }

                                            Item { Layout.fillWidth: true }

                                            RowLayout {
                                                id: leftDataTabs
                                                implicitWidth: 180
                                                property int currentIndex: 0
                                                spacing: 8
                                                PanelTabButton {
                                                    Layout.fillWidth: true
                                                    text: "节点"
                                                    checked: leftDataTabs.currentIndex === 0
                                                    onClicked: leftDataTabs.currentIndex = 0
                                                }
                                                PanelTabButton {
                                                    Layout.fillWidth: true
                                                    text: "单元"
                                                    checked: leftDataTabs.currentIndex === 1
                                                    onClicked: leftDataTabs.currentIndex = 1
                                                }
                                            }
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 1
                                            color: "#dfe5eb"
                                        }

                                        StackLayout {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            currentIndex: leftDataTabs.currentIndex

                                            Item {
                                                ColumnLayout {
                                                    anchors.fill: parent
                                                    spacing: 6

                                                    Rectangle {
                                                        Layout.fillWidth: true
                                                        Layout.preferredHeight: 32
                                                        radius: 4
                                                        color: "#f1f3f5"

                                                        RowLayout {
                                                            anchors.fill: parent
                                                            anchors.leftMargin: 8
                                                            anchors.rightMargin: 8
                                                            spacing: 8

                                                            Label { text: "ID"; font.bold: true; Layout.preferredWidth: 42; color: textMain }
                                                            Label { text: "X"; font.bold: true; Layout.preferredWidth: 88; color: textMain }
                                                            Label { text: "Y"; font.bold: true; Layout.preferredWidth: 88; color: textMain }
                                                        }
                                                    }

                                                    Rectangle {
                                                        Layout.fillWidth: true
                                                        Layout.fillHeight: true
                                                        color: "#fbfcfc"
                                                        border.color: "#d4dbe3"
                                                        radius: 4

                                                        ListView {
                                                            id: nodeListView
                                                            objectName: "nodeListView"
                                                            anchors.fill: parent
                                                            anchors.margins: 6
                                                            clip: true
                                                            spacing: 4
                                                            model: nodeListModel

                                                            ScrollBar.vertical: ScrollBar {
                                                                policy: ScrollBar.AlwaysOff
                                                                width: 0
                                                            }

                                                            delegate: Rectangle {
                                                                width: nodeListView.width
                                                                height: 36
                                                                radius: 4
                                                                border.color: appController.is_node_in_element_selection(model.node_id)
                                                                              ? "#d18b00"
                                                                              : (model.node_id === appController.selected_node_id ? accent : "#d4dbe3")
                                                                color: appController.is_node_in_element_selection(model.node_id)
                                                                       ? "#fff1cc"
                                                                       : (model.node_id === appController.selected_node_id
                                                                          ? accentSoft
                                                                          : (index % 2 === 0 ? "#fcfcfc" : "#f5f7f9"))

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
                                                }
                                            }

                                            Item {
                                                ColumnLayout {
                                                    anchors.fill: parent
                                                    spacing: 6

                                                    Rectangle {
                                                        Layout.fillWidth: true
                                                        Layout.preferredHeight: 32
                                                        radius: 4
                                                        color: "#f1f3f5"

                                                        RowLayout {
                                                            anchors.fill: parent
                                                            anchors.leftMargin: 8
                                                            anchors.rightMargin: 8
                                                            spacing: 8

                                                            Label { text: "ID"; font.bold: true; Layout.preferredWidth: 40; color: textMain }
                                                            Label { text: "节点"; font.bold: true; Layout.preferredWidth: 130; color: textMain }
                                                            Label { text: "类型"; font.bold: true; Layout.fillWidth: true; color: textMain }
                                                        }
                                                    }

                                                    Rectangle {
                                                        Layout.fillWidth: true
                                                        Layout.fillHeight: true
                                                        color: "#fbfcfc"
                                                        border.color: "#d4dbe3"
                                                        radius: 4

                                                        ListView {
                                                            id: elementListView
                                                            objectName: "elementListView"
                                                            anchors.fill: parent
                                                            anchors.margins: 6
                                                            clip: true
                                                            spacing: 4
                                                            model: elementRowsCache

                                                            ScrollBar.vertical: ScrollBar {
                                                                policy: ScrollBar.AlwaysOff
                                                                width: 0
                                                            }

                                                            delegate: Rectangle {
                                                                width: elementListView.width
                                                                height: 40
                                                                radius: 4
                                                                property var rowData: modelData

                                                                border.color: rowData && rowData.element_id === appController.selected_element_id ? "#1f5fbf" : "#d4dbe3"
                                                                color: rowData && rowData.element_id === appController.selected_element_id ? "#dbe6fb" : (index % 2 === 0 ? "#fcfcfc" : "#f5f7f9")

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

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            ColumnLayout {
                                width: Math.max(0, leftPanel.width - 28)
                                spacing: 10

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 12
                                    color: bgPanel3
                                    border.color: borderColor
                                    implicitHeight: 230

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 8

                                        Label {
                                            text: "节点结果"
                                            color: textMain
                                            font.pixelSize: 13
                                            font.bold: true
                                        }

                                        Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            color: "#fbfcfc"
                                            border.color: "#d4dbe3"
                                            radius: 4

                                            ListView {
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                clip: true
                                                spacing: 4
                                                model: nodeResultModel

                                                delegate: Rectangle {
                                                    width: ListView.view.width
                                                    height: 30
                                                    radius: 4
                                                    color: index % 2 === 0 ? "#fcfcfc" : "#f5f7f9"
                                                    border.color: "#e1e7ee"

                                                    RowLayout {
                                                        anchors.fill: parent
                                                        anchors.leftMargin: 6
                                                        anchors.rightMargin: 6
                                                        spacing: 8
                                                        Label { text: "N" + model.node_id; Layout.preferredWidth: 44; color: textMain }
                                                        Label { text: "Ux=" + Number(model.ux).toExponential(3); Layout.fillWidth: true; color: textMain }
                                                        Label { text: "Uy=" + Number(model.uy).toExponential(3); Layout.fillWidth: true; color: textMain }
                                                    }
                                                }

                                                footer: nodeResultModel.count === 0 ? emptyNodeResultLabelLeft : null
                                            }

                                            Component {
                                                id: emptyNodeResultLabelLeft
                                                Label {
                                                    width: parent ? parent.width : 200
                                                    text: "暂无节点位移结果"
                                                    horizontalAlignment: Text.AlignHCenter
                                                    color: textMuted
                                                    topPadding: 20
                                                }
                                            }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 12
                                    color: bgPanel3
                                    border.color: borderColor
                                    implicitHeight: 240

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 8

                                        Label {
                                            text: "单元结果"
                                            color: textMain
                                            font.pixelSize: 13
                                            font.bold: true
                                        }

                                        Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            color: "#fbfcfc"
                                            border.color: "#d4dbe3"
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
                                                    color: index % 2 === 0 ? "#fcfcfc" : "#f5f7f9"
                                                    border.color: "#e1e7ee"

                                                    RowLayout {
                                                        anchors.fill: parent
                                                        anchors.leftMargin: 6
                                                        anchors.rightMargin: 6
                                                        spacing: 8
                                                        Label { text: "E" + model.element_id; Layout.preferredWidth: 44; color: textMain }
                                                        Label { text: "σx=" + Number(model.stress_x).toExponential(2); Layout.fillWidth: true; color: textMain }
                                                        Label { text: "σy=" + Number(model.stress_y).toExponential(2); Layout.fillWidth: true; color: textMain }
                                                    }
                                                }

                                                footer: elementResultModel.count === 0 ? emptyElementResultLabelLeft : null
                                            }

                                            Component {
                                                id: emptyElementResultLabelLeft
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

                                Rectangle {
                                    Layout.fillWidth: true
                                    radius: 12
                                    color: bgPanel3
                                    border.color: borderColor
                                    implicitHeight: 152

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 12
                                        spacing: 8

                                        Label {
                                            text: "云图显示"
                                            color: textMain
                                            font.pixelSize: 13
                                            font.bold: true
                                        }

                                        Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8

                                            PanelActionButton {
                                                Layout.fillWidth: true
                                                text: "位移云图"
                                                enabled: appController.solver_has_result && nodeResultModel.count > 0
                                                onClicked: openContourOverlay("displacement")
                                            }

                                            PanelActionButton {
                                                Layout.fillWidth: true
                                                text: "Von Mises"
                                                enabled: appController.solver_has_result && elementResultModel.count > 0
                                                onClicked: openContourOverlay("von_mises")
                                            }
                                        }

                                        Label {
                                            Layout.fillWidth: true
                                            text: "Von Mises 显示模式"
                                            color: textMuted
                                            font.pixelSize: 11
                                        }

                                        Item {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 30
                                            opacity: appController.solver_has_result && elementResultModel.count > 0 ? 1.0 : 0.45

                                            Rectangle {
                                                id: vonMisesModeTrack
                                                anchors.fill: parent
                                                radius: height / 2
                                                color: "#eef3f7"
                                                border.color: "#ccd6df"
                                                border.width: 1

                                                Rectangle {
                                                    width: parent.width / 2 - 4
                                                    height: parent.height - 4
                                                    x: vonMisesContourStyle === "smooth" ? 2 : parent.width / 2 + 2
                                                    y: 2
                                                    radius: height / 2
                                                    color: "#ffffff"
                                                    border.color: "#b8c6d3"
                                                    border.width: 1

                                                    Behavior on x {
                                                        NumberAnimation { duration: 140; easing.type: Easing.OutCubic }
                                                    }
                                                }

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 4
                                                    anchors.rightMargin: 4
                                                    spacing: 0

                                                    Label {
                                                        Layout.fillWidth: true
                                                        horizontalAlignment: Text.AlignHCenter
                                                        verticalAlignment: Text.AlignVCenter
                                                        text: "平滑"
                                                        color: vonMisesContourStyle === "smooth" ? textMain : textMuted
                                                        font.pixelSize: 12
                                                        font.bold: vonMisesContourStyle === "smooth"
                                                    }

                                                    Label {
                                                        Layout.fillWidth: true
                                                        horizontalAlignment: Text.AlignHCenter
                                                        verticalAlignment: Text.AlignVCenter
                                                        text: "可靠"
                                                        color: vonMisesContourStyle === "reliable" ? textMain : textMuted
                                                        font.pixelSize: 12
                                                        font.bold: vonMisesContourStyle === "reliable"
                                                    }
                                                }

                                                MouseArea {
                                                    anchors.fill: parent
                                                    enabled: appController.solver_has_result && elementResultModel.count > 0
                                                    cursorShape: Qt.PointingHandCursor
                                                    onClicked: toggleVonMisesContourStyle()
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
                            color: "#e8ecef"
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
                                        border.color: index === 0 ? accent : "#c9d1d9"

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
                                        color: "#f1f3f5"
                                    }
                                }

                                Repeater {
                                    model: 12
                                    delegate: Rectangle {
                                        x: 0
                                        y: index * (viewport.height / 12)
                                        width: viewport.width
                                        height: 1
                                        color: "#f1f3f5"
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
                                                    fillColor: (modelData && modelData.element_id === appController.selected_element_id)
                                                               ? (modelData.selected_fill_color || "#c9dcffbb")
                                                               : (modelData.fill_color || "#dbe6fb99")
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

                                Item {
                                    id: boundaryOverlay
                                    anchors.fill: parent
                                    z: 2.4

                                    Item {
                                        id: selectedDistributedLoadEdgeHighlight
                                        anchors.fill: parent
                                        visible: appController.selected_element_exists
                                                 && appController.current_mode === "element"
                                                 && selectedElementRow !== null
                                                 && selectedEdgeNodeI !== null
                                                 && selectedEdgeNodeJ !== null

                                        property int visualVersion: boundaryVisualVersion
                                        property var selectedElementRow: appController.selected_element_exists
                                                                     ? findElementRowById(appController.selected_element_id)
                                                                     : null
                                        property var selectedEdgeIds: edgeNodeIdsForElementRow(selectedElementRow, selectedDistributedLoadEdgeIndex)
                                        property var selectedEdgeNodeI: selectedEdgeIds.length === 2 ? findNodeRowById(selectedEdgeIds[0]) : null
                                        property var selectedEdgeNodeJ: selectedEdgeIds.length === 2 ? findNodeRowById(selectedEdgeIds[1]) : null

                                        Shape {
                                            anchors.fill: parent
                                            visible: selectedDistributedLoadEdgeHighlight.visible

                                            ShapePath {
                                                strokeColor: "#f59e0b"
                                                strokeWidth: 5.0
                                                fillColor: "transparent"
                                                capStyle: ShapePath.RoundCap
                                                joinStyle: ShapePath.RoundJoin
                                                startX: selectedDistributedLoadEdgeHighlight.selectedEdgeNodeI !== null ? nodeToViewportX(selectedDistributedLoadEdgeHighlight.selectedEdgeNodeI.node_x) : 0.0
                                                startY: selectedDistributedLoadEdgeHighlight.selectedEdgeNodeI !== null ? nodeToViewportY(selectedDistributedLoadEdgeHighlight.selectedEdgeNodeI.node_y) : 0.0

                                                PathLine {
                                                    x: selectedDistributedLoadEdgeHighlight.selectedEdgeNodeJ !== null ? nodeToViewportX(selectedDistributedLoadEdgeHighlight.selectedEdgeNodeJ.node_x) : 0.0
                                                    y: selectedDistributedLoadEdgeHighlight.selectedEdgeNodeJ !== null ? nodeToViewportY(selectedDistributedLoadEdgeHighlight.selectedEdgeNodeJ.node_y) : 0.0
                                                }
                                            }

                                            ShapePath {
                                                strokeColor: "#fff3c4"
                                                strokeWidth: 2.0
                                                fillColor: "transparent"
                                                capStyle: ShapePath.RoundCap
                                                joinStyle: ShapePath.RoundJoin
                                                startX: selectedDistributedLoadEdgeHighlight.selectedEdgeNodeI !== null ? nodeToViewportX(selectedDistributedLoadEdgeHighlight.selectedEdgeNodeI.node_x) : 0.0
                                                startY: selectedDistributedLoadEdgeHighlight.selectedEdgeNodeI !== null ? nodeToViewportY(selectedDistributedLoadEdgeHighlight.selectedEdgeNodeI.node_y) : 0.0

                                                PathLine {
                                                    x: selectedDistributedLoadEdgeHighlight.selectedEdgeNodeJ !== null ? nodeToViewportX(selectedDistributedLoadEdgeHighlight.selectedEdgeNodeJ.node_x) : 0.0
                                                    y: selectedDistributedLoadEdgeHighlight.selectedEdgeNodeJ !== null ? nodeToViewportY(selectedDistributedLoadEdgeHighlight.selectedEdgeNodeJ.node_y) : 0.0
                                                }
                                            }
                                        }
                                    }

                                    Repeater {
                                        model: distributedLoadRowsCache

                                        delegate: Item {
                                            id: distributedLoadArrowItem
                                            anchors.fill: parent
                                            visible: nodeI !== null && nodeJ !== null && loadMagnitude > 1e-12

                                            property var nodeI: modelData ? findNodeRowById(modelData.node_i_id) : null
                                            property var nodeJ: modelData ? findNodeRowById(modelData.node_j_id) : null
                                            property real qx: modelData ? Number(modelData.qx) : 0.0
                                            property real qy: modelData ? Number(modelData.qy) : 0.0
                                            property real loadMagnitude: Math.sqrt(qx * qx + qy * qy)
                                            property real dirX: loadMagnitude > 1e-12 ? qx / loadMagnitude : 0.0
                                            property real dirY: loadMagnitude > 1e-12 ? -qy / loadMagnitude : 0.0
                                            property real arrowLength: 26.0
                                            property real headLength: 7.0
                                            property real headHalfWidth: 4.2
                                            property int arrowCount: 4
                                            property real x1: nodeI !== null ? nodeToViewportX(nodeI.node_x) : 0.0
                                            property real y1: nodeI !== null ? nodeToViewportY(nodeI.node_y) : 0.0
                                            property real x2: nodeJ !== null ? nodeToViewportX(nodeJ.node_x) : 0.0
                                            property real y2: nodeJ !== null ? nodeToViewportY(nodeJ.node_y) : 0.0
                                            // 均布载荷箭头沿受载边从起点节点覆盖到终点节点。
                                            // 第一个箭头头部贴在 node_i，最后一个箭头头部贴在 node_j。
                                            property real firstArrowT: 0.0
                                            property real lastArrowT: 1.0
                                            property real firstHeadX: x1 + (x2 - x1) * firstArrowT
                                            property real firstHeadY: y1 + (y2 - y1) * firstArrowT
                                            property real lastHeadX: x1 + (x2 - x1) * lastArrowT
                                            property real lastHeadY: y1 + (y2 - y1) * lastArrowT
                                            property real firstTailX: firstHeadX - dirX * arrowLength
                                            property real firstTailY: firstHeadY - dirY * arrowLength
                                            property real lastTailX: lastHeadX - dirX * arrowLength
                                            property real lastTailY: lastHeadY - dirY * arrowLength
                                            property real perpX: -dirY
                                            property real perpY: dirX

                                            Shape {
                                                anchors.fill: parent
                                                visible: distributedLoadArrowItem.visible

                                                ShapePath {
                                                    // 均布载荷的连接线应连接箭尾，而不是连接贴在边界上的箭头。
                                                    // 这样可以同时满足“箭头头部贴边”和“尾部相连”的工程图示习惯。
                                                    strokeColor: "#d93025"
                                                    strokeWidth: 1.4
                                                    fillColor: "transparent"
                                                    capStyle: ShapePath.RoundCap
                                                    joinStyle: ShapePath.RoundJoin
                                                    startX: distributedLoadArrowItem.firstTailX
                                                    startY: distributedLoadArrowItem.firstTailY

                                                    PathLine {
                                                        x: distributedLoadArrowItem.lastTailX
                                                        y: distributedLoadArrowItem.lastTailY
                                                    }
                                                }
                                            }

                                            Repeater {
                                                model: distributedLoadArrowItem.arrowCount

                                                delegate: Shape {
                                                    id: distributedUniformArrowShape
                                                    anchors.fill: parent
                                                    visible: distributedLoadArrowItem.visible

                                                    // 用 index/(count-1) 而不是 (index+0.5)/count，
                                                    // 这样箭头头部会覆盖边的两个端点节点，起止位置更明确。
                                                    property real t: distributedLoadArrowItem.arrowCount > 1 ? index / (distributedLoadArrowItem.arrowCount - 1) : 0.0
                                                    property real endX: distributedLoadArrowItem.x1 + (distributedLoadArrowItem.x2 - distributedLoadArrowItem.x1) * t
                                                    property real endY: distributedLoadArrowItem.y1 + (distributedLoadArrowItem.y2 - distributedLoadArrowItem.y1) * t
                                                    property real startX: endX - distributedLoadArrowItem.dirX * distributedLoadArrowItem.arrowLength
                                                    property real startY: endY - distributedLoadArrowItem.dirY * distributedLoadArrowItem.arrowLength
                                                    property real baseX: endX - distributedLoadArrowItem.dirX * distributedLoadArrowItem.headLength
                                                    property real baseY: endY - distributedLoadArrowItem.dirY * distributedLoadArrowItem.headLength
                                                    property real headX1: baseX + distributedLoadArrowItem.perpX * distributedLoadArrowItem.headHalfWidth
                                                    property real headY1: baseY + distributedLoadArrowItem.perpY * distributedLoadArrowItem.headHalfWidth
                                                    property real headX2: baseX - distributedLoadArrowItem.perpX * distributedLoadArrowItem.headHalfWidth
                                                    property real headY2: baseY - distributedLoadArrowItem.perpY * distributedLoadArrowItem.headHalfWidth

                                                    ShapePath {
                                                        strokeColor: "#d93025"
                                                        strokeWidth: 2.0
                                                        fillColor: "transparent"
                                                        capStyle: ShapePath.RoundCap
                                                        joinStyle: ShapePath.RoundJoin
                                                        startX: distributedUniformArrowShape.startX
                                                        startY: distributedUniformArrowShape.startY

                                                        PathLine {
                                                            x: distributedUniformArrowShape.endX
                                                            y: distributedUniformArrowShape.endY
                                                        }
                                                    }

                                                    ShapePath {
                                                        strokeColor: "#d93025"
                                                        strokeWidth: 2.0
                                                        fillColor: "transparent"
                                                        capStyle: ShapePath.RoundCap
                                                        joinStyle: ShapePath.RoundJoin
                                                        startX: distributedUniformArrowShape.endX
                                                        startY: distributedUniformArrowShape.endY

                                                        PathLine {
                                                            x: distributedUniformArrowShape.headX1
                                                            y: distributedUniformArrowShape.headY1
                                                        }
                                                    }

                                                    ShapePath {
                                                        strokeColor: "#d93025"
                                                        strokeWidth: 2.0
                                                        fillColor: "transparent"
                                                        capStyle: ShapePath.RoundCap
                                                        joinStyle: ShapePath.RoundJoin
                                                        startX: distributedUniformArrowShape.endX
                                                        startY: distributedUniformArrowShape.endY

                                                        PathLine {
                                                            x: distributedUniformArrowShape.headX2
                                                            y: distributedUniformArrowShape.headY2
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }

                                    Repeater {
                                        model: loadRowsCache

                                        delegate: Item {
                                            id: loadArrowItem
                                            anchors.fill: parent
                                            visible: loadNode !== null && loadMagnitude > 1e-12

                                            property var loadNode: modelData ? findNodeRowById(modelData.node_id) : null
                                            property real fx: modelData ? Number(modelData.fx) : 0.0
                                            property real fy: modelData ? Number(modelData.fy) : 0.0
                                            property real loadMagnitude: Math.sqrt(fx * fx + fy * fy)
                                            property real dirX: loadMagnitude > 1e-12 ? fx / loadMagnitude : 0.0
                                            property real dirY: loadMagnitude > 1e-12 ? -fy / loadMagnitude : 0.0
                                            property real arrowLength: 34.0
                                            property real headLength: 9.0
                                            property real headHalfWidth: 5.5
                                            property real startX: loadNode !== null ? nodeToViewportX(loadNode.node_x) : 0.0
                                            property real startY: loadNode !== null ? nodeToViewportY(loadNode.node_y) : 0.0
                                            property real endX: startX + dirX * arrowLength
                                            property real endY: startY + dirY * arrowLength
                                            property real baseX: endX - dirX * headLength
                                            property real baseY: endY - dirY * headLength
                                            property real perpX: -dirY
                                            property real perpY: dirX
                                            property real headX1: baseX + perpX * headHalfWidth
                                            property real headY1: baseY + perpY * headHalfWidth
                                            property real headX2: baseX - perpX * headHalfWidth
                                            property real headY2: baseY - perpY * headHalfWidth

                                            Shape {
                                                anchors.fill: parent
                                                visible: loadArrowItem.visible

                                                ShapePath {
                                                    strokeColor: "#d93025"
                                                    strokeWidth: 2.4
                                                    fillColor: "transparent"
                                                    capStyle: ShapePath.RoundCap
                                                    joinStyle: ShapePath.RoundJoin
                                                    startX: loadArrowItem.startX
                                                    startY: loadArrowItem.startY

                                                    PathLine {
                                                        x: loadArrowItem.endX
                                                        y: loadArrowItem.endY
                                                    }
                                                }

                                                ShapePath {
                                                    strokeColor: "#d93025"
                                                    strokeWidth: 2.4
                                                    fillColor: "transparent"
                                                    capStyle: ShapePath.RoundCap
                                                    joinStyle: ShapePath.RoundJoin
                                                    startX: loadArrowItem.endX
                                                    startY: loadArrowItem.endY

                                                    PathLine {
                                                        x: loadArrowItem.headX1
                                                        y: loadArrowItem.headY1
                                                    }
                                                }

                                                ShapePath {
                                                    strokeColor: "#d93025"
                                                    strokeWidth: 2.4
                                                    fillColor: "transparent"
                                                    capStyle: ShapePath.RoundCap
                                                    joinStyle: ShapePath.RoundJoin
                                                    startX: loadArrowItem.endX
                                                    startY: loadArrowItem.endY

                                                    PathLine {
                                                        x: loadArrowItem.headX2
                                                        y: loadArrowItem.headY2
                                                    }
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
                                        viewportPanActive = false
                                        viewportPanMoved = false

                                        if (!window.viewportPointIsValid(mouse.x, mouse.y))
                                            return

                                        var clickedElementId = elementIdAtViewportPoint(mouse.x, mouse.y)
                                        var clickedBlankInElementMode = appController.current_mode === "element" && clickedElementId === -1
                                        var blankPanInNodeMode = appController.current_mode === "node" && activeViewportTool !== "add"
                                        var forceMoveTool = activeViewportTool === "move"

                                        if (forceMoveTool || clickedBlankInElementMode || blankPanInNodeMode) {
                                            viewportPanActive = true
                                            lastPanMouseX = mouse.x
                                            lastPanMouseY = mouse.y
                                            mouse.accepted = true
                                        }
                                    }

                                    onPositionChanged: function(mouse) {
                                        if (viewportPanActive && pressed) {
                                            var dx = mouse.x - lastPanMouseX
                                            var dy = mouse.y - lastPanMouseY
                                            if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5)
                                                viewportPanMoved = true

                                            viewportPanX += dx
                                            viewportPanY += dy
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

                                    onReleased: function(mouse) {
                                        if (!pressed) {
                                            viewportPanActive = false
                                        }
                                    }

                                    onClicked: function(mouse) {
                                        if (!window.viewportPointIsValid(mouse.x, mouse.y))
                                            return

                                        window.cursorModelX = window.viewportToModelX(mouse.x)
                                        window.cursorModelY = window.viewportToModelY(mouse.y)

                                        if (viewportPanActive && viewportPanMoved) {
                                            viewportPanActive = false
                                            viewportPanMoved = false
                                            return
                                        }

                                        if (appController.current_mode === "element") {
                                            if (selectElementAtViewportPoint(mouse.x, mouse.y)) {
                                                viewportPanActive = false
                                                viewportPanMoved = false
                                                return
                                            }

                                            shell_status = "空白区域：按住并拖动可移动视图"
                                            viewportPanActive = false
                                            viewportPanMoved = false
                                            return
                                        }

                                        if (appController.current_mode === "node") {
                                            if (activeViewportTool !== "add") {
                                                shell_status = "空白区域：按住并拖动可移动视图"
                                                viewportPanActive = false
                                                viewportPanMoved = false
                                                return
                                            }

                                            if (elementIdAtViewportPoint(mouse.x, mouse.y) !== -1) {
                                                shell_status = "当前位置已有单元，请点击空白区域创建新节点"
                                                viewportPanActive = false
                                                viewportPanMoved = false
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

                                            viewportPanActive = false
                                            viewportPanMoved = false
                                            return
                                        }

                                        if (activeViewportTool === "move") {
                                            shell_status = "空白区域：按住并拖动可移动视图"
                                            viewportPanActive = false
                                            viewportPanMoved = false
                                            return
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
                                        text: "节点模式添加工具：点击空白创建节点；单元模式：点击单元面选中单元，点击节点进行建单元选点；空白处拖动移动视图"
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

                                        property bool nodeHasConstraint: boundaryVisualVersion >= 0 && hasConstraintForNode(model.node_id)

                                        Rectangle {
                                            width: 16
                                            height: 16
                                            radius: 8
                                            border.width: nodeHasConstraint ? 3 : 2
                                            border.color: nodeHasConstraint
                                                          ? "#d93025"
                                                          : (appController.is_node_in_element_selection(model.node_id)
                                                             ? "#d18b00"
                                                             : (model.node_id === appController.selected_node_id ? accent : "#6c8197"))
                                            color: appController.is_node_in_element_selection(model.node_id)
                                                   ? "#ffd86b"
                                                   : (model.node_id === appController.selected_node_id ? accent : "#b1bfcb")

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
                            color: "#e8ecef"
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
                SplitView.minimumWidth: rightPanelVisible ? 290 : 0
                SplitView.preferredWidth: rightPanelVisible ? 300 : 0
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#f3f5f7" }
                    GradientStop { position: 1.0; color: bgPanel2 }
                }
                border.color: borderColor

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 42
                        radius: 6
                        color: "#e8ecef"
                        border.color: borderColor

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12
                            anchors.rightMargin: 12
                            spacing: 10

                            Label {
                                text: "检查器"
                                color: accent
                                font.pixelSize: 13
                                font.bold: true
                            }

                            Item { Layout.fillWidth: true }

                            PanelActionButton {
                                text: "材料管理"
                                onClicked: {
                                    materialPopup.open()
                                    refreshMaterialModel()
                                }
                            }
                        }
                    }

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        ColumnLayout {
                            width: Math.max(0, rightPanel.width - 24)
                            spacing: 10

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 12
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 164

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 6

                                    Label {
                                        text: "模型概要"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                    Label { text: "节点：" + appController.node_count + "    单元：" + appController.element_count; color: textMain }
                                    Label { text: "材料：" + appController.material_count + "    约束：" + appController.constraint_count + "    载荷：" + appController.load_count; color: textMain }
                                    Label { text: "当前模式：" + appController.current_mode; color: textMain }
                                    Label { text: "当前选择：" + selection_info; color: textMain }
                                    Label { text: "结果状态：" + (appController.solver_has_result ? "已有结果" : "暂无结果"); color: textMain }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 12
                                color: bgPanel3
                                border.color: borderColor
                                implicitHeight: 154

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "导出相关"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                    Label {
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                        text: appController.solver_has_result ? "当前已有求解结果，可导出 CSV 文件。" : "请先完成求解，再导出节点位移与单元应力应变结果。"
                                        color: textMuted
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "导出节点结果"
                                            enabled: appController.solver_has_result
                                            onClicked: exportNodeResultsDialog.open()
                                        }

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "导出单元结果"
                                            enabled: appController.solver_has_result
                                            onClicked: exportElementResultsDialog.open()
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 12
                                color: bgPanel3
                                border.color: borderColor
                                visible: !appController.selected_node_exists && !appController.selected_element_exists
                                implicitHeight: visible ? 200 : 0

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "当前未选中对象"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                    Label {
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                        text: "先在左侧列表或中央画布中选中节点/单元，再在这里进行对应设置。"
                                        color: textMuted
                                    }

                                    PanelActionButton {
                                        Layout.fillWidth: true
                                        text: "打开材料管理"
                                        onClicked: {
                                            materialPopup.open()
                                            refreshMaterialModel()
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "节点模式"
                                            onClicked: {
                                                appController.set_node_mode()
                                                activeViewportTool = "add"
                                                shell_status = "已切换到节点模式"
                                            }
                                        }

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "单元模式"
                                            onClicked: {
                                                appController.set_element_mode()
                                                activeViewportTool = "move"
                                                shell_status = "已切换到单元模式"
                                            }
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                radius: 12
                                color: bgPanel3
                                border.color: borderColor
                                visible: appController.selected_node_exists && !(appController.selected_element_exists && appController.current_mode === "element")
                                implicitHeight: visible ? 420 : 0

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "节点检查器"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                    RowLayout {
                                        id: nodeInspectorTabs
                                        Layout.fillWidth: true
                                        property int currentIndex: 0
                                        spacing: 8
                                        PanelTabButton {
                                            Layout.fillWidth: true
                                            text: "坐标"
                                            checked: nodeInspectorTabs.currentIndex === 0
                                            onClicked: nodeInspectorTabs.currentIndex = 0
                                        }
                                        PanelTabButton {
                                            Layout.fillWidth: true
                                            text: "约束"
                                            checked: nodeInspectorTabs.currentIndex === 1
                                            onClicked: nodeInspectorTabs.currentIndex = 1
                                        }
                                        PanelTabButton {
                                            Layout.fillWidth: true
                                            text: "载荷"
                                            checked: nodeInspectorTabs.currentIndex === 2
                                            onClicked: nodeInspectorTabs.currentIndex = 2
                                        }
                                    }

                                    StackLayout {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        currentIndex: nodeInspectorTabs.currentIndex

                                        Item {
                                            ColumnLayout {
                                                anchors.fill: parent
                                                spacing: 8

                                                Label { text: "节点编号"; color: textMuted }
                                                Label {
                                                    id: selectedNodeIdValue
                                                    text: "—"
                                                    color: textMain
                                                    font.pixelSize: 14
                                                    font.bold: true
                                                }

                                                Label { text: "X 坐标"; color: textMuted }
                                                PanelTextField {
                                                    id: selectedXField
                                                    objectName: "selectedXField"
                                                    Layout.fillWidth: true
                                                    enabled: appController.selected_node_exists && appController.current_mode !== "element"
                                                    placeholderText: "选中节点 X"
                                                }

                                                Label { text: "Y 坐标"; color: textMuted }
                                                PanelTextField {
                                                    id: selectedYField
                                                    objectName: "selectedYField"
                                                    Layout.fillWidth: true
                                                    enabled: appController.selected_node_exists && appController.current_mode !== "element"
                                                    placeholderText: "选中节点 Y"
                                                }

                                                PanelActionButton {
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

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8

                                                    PanelActionButton {
                                                        objectName: "clearNodeSelectionButton"
                                                        Layout.fillWidth: true
                                                        text: "取消选中"
                                                        onClicked: {
                                                            appController.clear_node_selection()
                                                            syncSelectedNodeEditor()
                                                            shell_status = "已取消节点选中"
                                                        }
                                                    }

                                                    PanelActionButton {
                                                        Layout.fillWidth: true
                                                        text: "删除节点"
                                                        enabled: appController.selected_node_exists && appController.current_mode !== "element"
                                                        onClicked: deleteCurrentNodeFromView()
                                                    }
                                                }
                                            }
                                        }

                                        Item {
                                            ColumnLayout {
                                                anchors.fill: parent
                                                spacing: 8

                                                Label {
                                                    text: "位移约束"
                                                    color: textMain
                                                    font.bold: true
                                                }

                                                PanelCheckBox {
                                                    id: constraintUxCheck
                                                    text: "固定 Ux"
                                                }

                                                PanelTextField {
                                                    id: constraintUxValueField
                                                    Layout.fillWidth: true
                                                    enabled: constraintUxCheck.checked
                                                    placeholderText: "Ux 位移值"
                                                }

                                                PanelCheckBox {
                                                    id: constraintUyCheck
                                                    text: "固定 Uy"
                                                }

                                                PanelTextField {
                                                    id: constraintUyValueField
                                                    Layout.fillWidth: true
                                                    enabled: constraintUyCheck.checked
                                                    placeholderText: "Uy 位移值"
                                                }

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8

                                                    PanelActionButton {
                                                        Layout.fillWidth: true
                                                        text: "应用约束"
                                                        onClicked: {
                                                            var ok = appController.set_selected_node_constraint_by_text(
                                                                        constraintUxCheck.checked,
                                                                        constraintUyCheck.checked,
                                                                        constraintUxValueField.text,
                                                                        constraintUyValueField.text)
                                                            shell_status = appController.status_text
                                                            if (ok) {
                                                                refreshBoundaryModel()
                                                                syncSelectedNodeEditor()
                                                            }
                                                        }
                                                    }

                                                    PanelActionButton {
                                                        Layout.fillWidth: true
                                                        text: "清除约束"
                                                        onClicked: {
                                                            var ok = appController.clear_selected_node_constraint()
                                                            shell_status = appController.status_text
                                                            if (ok) {
                                                                refreshBoundaryModel()
                                                                syncSelectedNodeEditor()
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }

                                        Item {
                                            ColumnLayout {
                                                anchors.fill: parent
                                                spacing: 8

                                                Label {
                                                    text: "集中载荷"
                                                    color: textMain
                                                    font.bold: true
                                                }

                                                Label { text: "Fx"; color: textMuted }
                                                PanelTextField {
                                                    id: loadFxField
                                                    Layout.fillWidth: true
                                                    placeholderText: "节点 Fx"
                                                }

                                                Label { text: "Fy"; color: textMuted }
                                                PanelTextField {
                                                    id: loadFyField
                                                    Layout.fillWidth: true
                                                    placeholderText: "节点 Fy"
                                                }

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 8

                                                    PanelActionButton {
                                                        Layout.fillWidth: true
                                                        text: "应用载荷"
                                                        onClicked: {
                                                            var ok = appController.set_selected_node_load_by_text(loadFxField.text, loadFyField.text)
                                                            shell_status = appController.status_text
                                                            if (ok) {
                                                                refreshBoundaryModel()
                                                                syncSelectedNodeEditor()
                                                            }
                                                        }
                                                    }

                                                    PanelActionButton {
                                                        Layout.fillWidth: true
                                                        text: "清除载荷"
                                                        onClicked: {
                                                            var ok = appController.clear_selected_node_load()
                                                            shell_status = appController.status_text
                                                            if (ok) {
                                                                refreshBoundaryModel()
                                                                syncSelectedNodeEditor()
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
                                radius: 12
                                color: bgPanel3
                                border.color: borderColor
                                visible: appController.selected_element_exists && (!appController.selected_node_exists || appController.current_mode === "element")
                                // 均布载荷面板加入后，单元检查器内容超过原 500px。
                                // 这里增大卡片的隐式高度，让外层 ScrollView 能正确滚到底部。
                                implicitHeight: visible ? 680 : 0

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    spacing: 8

                                    Label {
                                        text: "单元检查器"
                                        color: textMain
                                        font.pixelSize: 13
                                        font.bold: true
                                    }

                                    Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                    Label { text: "单元编号"; color: textMuted }
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

                                    Label { text: "单元类型"; color: textMuted }
                                    Label {
                                        id: selectedElementTypeValue
                                        text: "—"
                                        color: textMain
                                    }

                                    Label { text: "当前材料"; color: textMuted }
                                    Label {
                                        id: selectedElementMaterialValue
                                        text: "—"
                                        color: textMain
                                    }

                                    Label {
                                        id: selectedElementMaterialNameValue
                                        text: "—"
                                        color: textMain
                                    }

                                    Label {
                                        id: selectedElementPlaneModeValue
                                        text: "—"
                                        color: textMuted
                                    }

                                    PanelComboBox {
                                        id: elementMaterialCombo
                                        Layout.fillWidth: true
                                        enabled: appController.selected_element_exists && materialRowsCache.length > 0
                                        model: materialRowsCache.map(function(item) {
                                            return item.material_id + " - " + item.material_name
                                        })
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "分配材料"
                                            enabled: appController.selected_element_exists && elementMaterialCombo.currentIndex >= 0
                                            onClicked: {
                                                var materialId = materialIdAt(elementMaterialCombo.currentIndex)
                                                if (materialId !== -1) {
                                                    var ok = appController.assign_material_to_selected_element(materialId)
                                                    shell_status = appController.status_text
                                                    if (ok) {
                                                        refreshElementModel()
                                                        syncSelectedElementEditor()
                                                    }
                                                }
                                            }
                                        }

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "材料管理"
                                            onClicked: {
                                                materialPopup.open()
                                                refreshMaterialModel()
                                            }
                                        }
                                    }

                                    Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                                    Label {
                                        text: "边界均布载荷"
                                        color: textMain
                                        font.bold: true
                                    }

                                    PanelComboBox {
                                        id: distributedLoadEdgeCombo
                                        Layout.fillWidth: true
                                        enabled: appController.selected_element_exists
                                        model: ["边 0：节点1-节点2", "边 1：节点2-节点3", "边 2：节点3-节点1"]
                                        currentIndex: 0
                                        onCurrentIndexChanged: {
                                            selectedDistributedLoadEdgeIndex = currentIndex >= 0 ? currentIndex : 0
                                            syncSelectedDistributedLoadEditor()
                                            refreshDistributedLoadEdgeHighlight()
                                            shell_status = "正在设置边界均布载荷：" + currentText
                                        }
                                    }

                                    Label { text: "qx"; color: textMuted }
                                    PanelTextField {
                                        id: distributedLoadQxField
                                        Layout.fillWidth: true
                                        placeholderText: "边界均布载荷 qx"
                                    }

                                    Label { text: "qy"; color: textMuted }
                                    PanelTextField {
                                        id: distributedLoadQyField
                                        Layout.fillWidth: true
                                        placeholderText: "边界均布载荷 qy"
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "应用均布载荷"
                                            enabled: appController.selected_element_exists
                                            onClicked: {
                                                var edgeIndex = distributedLoadEdgeCombo.currentIndex >= 0 ? distributedLoadEdgeCombo.currentIndex : 0
                                                var ok = appController.set_selected_element_distributed_load_by_text(edgeIndex, distributedLoadQxField.text, distributedLoadQyField.text)
                                                shell_status = appController.status_text
                                                if (ok) {
                                                    refreshBoundaryModel()
                                                    syncSelectedDistributedLoadEditor()
                                                }
                                            }
                                        }

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "清除该边"
                                            enabled: appController.selected_element_exists
                                            onClicked: {
                                                var edgeIndex = distributedLoadEdgeCombo.currentIndex >= 0 ? distributedLoadEdgeCombo.currentIndex : 0
                                                var ok = appController.clear_selected_element_distributed_load(edgeIndex)
                                                shell_status = appController.status_text
                                                if (ok) {
                                                    refreshBoundaryModel()
                                                    syncSelectedDistributedLoadEditor()
                                                }
                                            }
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "取消选中"
                                            enabled: appController.selected_element_exists
                                            onClicked: {
                                                appController.clear_element_selection()
                                                syncSelectedElementEditor()
                                                shell_status = "已取消单元选中"
                                            }
                                        }

                                        PanelActionButton {
                                            Layout.fillWidth: true
                                            text: "删除单元"
                                            enabled: appController.selected_element_exists
                                            onClicked: deleteCurrentElementFromView()
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
            Layout.preferredHeight: 32
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#e8ecef" }
                GradientStop { position: 1.0; color: "#d7dde5" }
            }
            border.color: "#b8c2cd"

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


    Popup {
        id: materialPopup
        modal: true
        focus: true
        width: 760
        height: 648
        anchors.centerIn: Overlay.overlay
        padding: 0
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        onOpened: refreshMaterialModel()

        background: Rectangle {
            radius: 10
            color: bgPanel3
            border.color: borderColor
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 14
            spacing: 10

            RowLayout {
                Layout.fillWidth: true

                Label {
                    text: "材料管理"
                    color: textMain
                    font.pixelSize: 15
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                PanelActionButton {
                    text: "关闭"
                    onClicked: materialPopup.close()
                }
            }

            Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12

                Rectangle {
                    Layout.preferredWidth: 300
                    Layout.fillHeight: true
                    radius: 6
                    color: "#fbfcfc"
                    border.color: "#d4dbe3"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Label {
                            text: "材料列表"
                            color: textMain
                            font.pixelSize: 13
                            font.bold: true
                        }

                        ListView {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.topMargin: 0
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            spacing: 4
                            model: materialRowsCache

                            delegate: Rectangle {
                                width: ListView.view.width
                                height: 42
                                radius: 4
                                border.color: modelData.material_id === selectedMaterialIdForEdit ? accent : "#d4dbe3"
                                color: modelData.material_id === selectedMaterialIdForEdit ? accentSoft : (index % 2 === 0 ? "#fcfcfc" : "#f5f7f9")

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: fillMaterialEditor(modelData.material_id)
                                }

                                Rectangle {
                                    width: 14
                                    height: 14
                                    radius: 4
                                    anchors.left: parent.left
                                    anchors.leftMargin: 10
                                    anchors.verticalCenter: parent.verticalCenter
                                    color: modelData.material_color || "#AEB8C2"
                                    border.color: "#9aa6b2"
                                }

                                Column {
                                    anchors.fill: parent
                                    anchors.leftMargin: 32
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 2

                                    Label {
                                        text: modelData.material_id + " - " + modelData.material_name
                                        color: textMain
                                        font.bold: modelData.material_id === selectedMaterialIdForEdit
                                    }

                                    Label {
                                        text: "E=" + Number(modelData.young_modulus).toExponential(2) + "   t=" + Number(modelData.thickness).toString()
                                        color: textMuted
                                        font.pixelSize: 11
                                    }
                                }
                            }

                            footer: materialRowsCache.length === 0 ? emptyMaterialFooter : null
                        }

                        Component {
                            id: emptyMaterialFooter
                            Label {
                                width: 220
                                text: "暂无材料"
                                horizontalAlignment: Text.AlignHCenter
                                color: textMuted
                                topPadding: 20
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 6
                    color: "#fbfcfc"
                    border.color: "#d4dbe3"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Label {
                            text: "材料编辑器"
                            color: textMain
                            font.pixelSize: 13
                            font.bold: true
                        }

                        Rectangle { Layout.fillWidth: true; height: 1; color: "#dfe5eb" }

                        Label { text: "材料编号"; color: textMuted }
                        Label {
                            id: materialIdValue
                            text: "—"
                            color: textMain
                            font.pixelSize: 14
                            font.bold: true
                        }

                        Label { text: "名称"; color: textMuted }
                        PanelTextField {
                            id: materialNameField
                            Layout.fillWidth: true
                            placeholderText: "材料名称"
                        }

                        Label { text: "弹性模量 E"; color: textMuted }
                        PanelTextField {
                            id: materialEField
                            Layout.fillWidth: true
                            placeholderText: "例如 210e9"
                        }

                        Label { text: "泊松比 ν"; color: textMuted }
                        PanelTextField {
                            id: materialNuField
                            Layout.fillWidth: true
                            placeholderText: "例如 0.3"
                        }

                        Label { text: "厚度 t"; color: textMuted }
                        PanelTextField {
                            id: materialThicknessField
                            Layout.fillWidth: true
                            placeholderText: "例如 0.01"
                        }

                        Label { text: "平面模式"; color: textMuted }
                        PanelComboBox {
                            id: materialPlaneModeCombo
                            Layout.fillWidth: true
                            model: ["stress"]
                            currentIndex: 0
                        }

                        Item { Layout.fillHeight: true }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            PanelActionButton {
                                Layout.fillWidth: true
                                text: "新建材料"
                                onClicked: {
                                    var ok = appController.add_material_by_text(
                                                materialNameField.text,
                                                materialEField.text,
                                                materialNuField.text,
                                                materialThicknessField.text,
                                                materialPlaneModeCombo.currentText)
                                    shell_status = appController.status_text
                                    if (ok) {
                                        refreshMaterialModel()
                                        if (materialRowsCache.length > 0)
                                            fillMaterialEditor(materialRowsCache[materialRowsCache.length - 1].material_id)
                                    }
                                }
                            }

                            PanelActionButton {
                                Layout.fillWidth: true
                                text: "更新材料"
                                enabled: selectedMaterialIdForEdit !== -1
                                onClicked: {
                                    var ok = appController.update_material_by_text(
                                                selectedMaterialIdForEdit,
                                                materialNameField.text,
                                                materialEField.text,
                                                materialNuField.text,
                                                materialThicknessField.text,
                                                materialPlaneModeCombo.currentText)
                                    shell_status = appController.status_text
                                    if (ok) {
                                        refreshMaterialModel()
                                        fillMaterialEditor(selectedMaterialIdForEdit)
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            PanelActionButton {
                                Layout.fillWidth: true
                                text: "删除材料"
                                enabled: selectedMaterialIdForEdit !== -1
                                onClicked: {
                                    var oldId = selectedMaterialIdForEdit
                                    var ok = appController.delete_material(oldId)
                                    shell_status = appController.status_text
                                    if (ok) {
                                        refreshMaterialModel()
                                        clearMaterialEditor()
                                    }
                                }
                            }

                            PanelActionButton {
                                Layout.fillWidth: true
                                text: "清空编辑"
                                onClicked: clearMaterialEditor()
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        id: contourOverlay
        anchors.fill: parent
        z: 80
        visible: contourOverlayVisible
        color: "#00000066"

        MouseArea {
            anchors.fill: parent
            onClicked: { }
        }

        Rectangle {
            id: contourWindow
            width: Math.min(window.width * 0.82, 1120)
            height: Math.min(window.height * 0.78, 720)
            anchors.centerIn: parent
            radius: 16
            color: "#f7f9fb"
            border.color: "#c3ccd6"
            border.width: 1
            clip: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 48
                    color: "#e8ecef"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 12
                        spacing: 10

                        Label {
                            text: contourTitle
                            color: textMain
                            font.pixelSize: 15
                            font.bold: true
                        }

                        Label {
                            text: "范围：" + Number(contourMinValue).toExponential(3) + " ~ " + Number(contourMaxValue).toExponential(3)
                            color: textMuted
                            font.pixelSize: 11
                        }

                        Item { Layout.fillWidth: true }

                        HeaderActionButton {
                            text: "关闭"
                            onClicked: closeContourOverlay()
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: 14
                    spacing: 12

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 10
                        color: "#ffffff"
                        border.color: "#d4dbe3"
                        clip: true

                        Canvas {
                            id: contourCanvas
                            anchors.fill: parent
                            anchors.margins: 10
                            visible: contourOverlayVisible

                            onPaint: {
                                var ctx = getContext("2d")
                                ctx.reset()
                                ctx.clearRect(0, 0, width, height)

                                ctx.fillStyle = "#fbfcfc"
                                ctx.fillRect(0, 0, width, height)

                                updateContourRange()

                                var subdivisions = 16
                                for (var e = 0; e < elementRowsCache.length; e++) {
                                    var elementRow = elementRowsCache[e]
                                    if (!elementRow || !elementRow.node_ids || elementRow.node_ids.length !== 3)
                                        continue

                                    var n1 = findNodeRowById(elementRow.node_ids[0])
                                    var n2 = findNodeRowById(elementRow.node_ids[1])
                                    var n3 = findNodeRowById(elementRow.node_ids[2])
                                    if (n1 === null || n2 === null || n3 === null)
                                        continue

                                    var v1 = contourValueByNodeId(n1.node_id)
                                    var v2 = contourValueByNodeId(n2.node_id)
                                    var v3 = contourValueByNodeId(n3.node_id)
                                    if (contourMode === "von_mises" && vonMisesContourStyle === "reliable") {
                                        var elementVm = vonMisesByElementId(elementRow.element_id)
                                        v1 = elementVm
                                        v2 = elementVm
                                        v3 = elementVm
                                    }
                                    if (!isFinite(v1) || !isFinite(v2) || !isFinite(v3))
                                        continue

                                    function pointAt(a, b) {
                                        var l1 = 1.0 - a - b
                                        var xModel = l1 * n1.node_x + a * n2.node_x + b * n3.node_x
                                        var yModel = l1 * n1.node_y + a * n2.node_y + b * n3.node_y
                                        var value = l1 * v1 + a * v2 + b * v3
                                        return {
                                            x: contourNodeToCanvasX(xModel, width),
                                            y: contourNodeToCanvasY(yModel, height),
                                            value: value
                                        }
                                    }

                                    function drawSubTriangle(p0, p1, p2) {
                                        var avg = (p0.value + p1.value + p2.value) / 3.0
                                        ctx.beginPath()
                                        ctx.moveTo(p0.x, p0.y)
                                        ctx.lineTo(p1.x, p1.y)
                                        ctx.lineTo(p2.x, p2.y)
                                        ctx.closePath()
                                        ctx.fillStyle = contourColor(avg, 0.92)
                                        ctx.fill()
                                    }

                                    for (var i = 0; i < subdivisions; i++) {
                                        for (var j = 0; j < subdivisions - i; j++) {
                                            var a0 = i / subdivisions
                                            var b0 = j / subdivisions
                                            var a1 = (i + 1) / subdivisions
                                            var b1 = j / subdivisions
                                            var a2 = i / subdivisions
                                            var b2 = (j + 1) / subdivisions

                                            drawSubTriangle(pointAt(a0, b0), pointAt(a1, b1), pointAt(a2, b2))

                                            if (j < subdivisions - i - 1) {
                                                var a3 = (i + 1) / subdivisions
                                                var b3 = (j + 1) / subdivisions
                                                drawSubTriangle(pointAt(a1, b1), pointAt(a3, b3), pointAt(a2, b2))
                                            }
                                        }
                                    }

                                    ctx.beginPath()
                                    ctx.moveTo(contourNodeToCanvasX(n1.node_x, width), contourNodeToCanvasY(n1.node_y, height))
                                    ctx.lineTo(contourNodeToCanvasX(n2.node_x, width), contourNodeToCanvasY(n2.node_y, height))
                                    ctx.lineTo(contourNodeToCanvasX(n3.node_x, width), contourNodeToCanvasY(n3.node_y, height))
                                    ctx.closePath()
                                    ctx.strokeStyle = "rgba(54, 65, 77, 0.35)"
                                    ctx.lineWidth = 1.0
                                    ctx.stroke()
                                }

                                for (var nodeIndex = 0; nodeIndex < nodeListModel.count; nodeIndex++) {
                                    var nodeRow = nodeListModel.get(nodeIndex)
                                    var cx = contourNodeToCanvasX(nodeRow.node_x, width)
                                    var cy = contourNodeToCanvasY(nodeRow.node_y, height)
                                    ctx.beginPath()
                                    ctx.arc(cx, cy, 3.5, 0, Math.PI * 2)
                                    ctx.fillStyle = "rgba(31, 41, 51, 0.86)"
                                    ctx.fill()
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 110
                        Layout.fillHeight: true
                        radius: 10
                        color: "#ffffff"
                        border.color: "#d4dbe3"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Label {
                                text: "图例"
                                color: textMain
                                font.pixelSize: 13
                                font.bold: true
                            }

                            Label {
                                Layout.fillWidth: true
                                text: Number(contourMaxValue).toExponential(2)
                                color: textMuted
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                            }

                            Rectangle {
                                Layout.alignment: Qt.AlignHCenter
                                Layout.preferredWidth: 28
                                Layout.fillHeight: true
                                radius: 5
                                gradient: Gradient {
                                    GradientStop { position: 0.00; color: "#d24138" }
                                    GradientStop { position: 0.25; color: "#f5c442" }
                                    GradientStop { position: 0.50; color: "#4caf50" }
                                    GradientStop { position: 0.75; color: "#28acdc" }
                                    GradientStop { position: 1.00; color: "#2d54b8" }
                                }
                            }

                            Label {
                                Layout.fillWidth: true
                                text: Number(contourMinValue).toExponential(2)
                                color: textMuted
                                font.pixelSize: 10
                                horizontalAlignment: Text.AlignHCenter
                            }

                            Label {
                                Layout.fillWidth: true
                                text: contourMode === "von_mises" ? (vonMisesContourStyle === "reliable" ? "可靠云图：按单元真实 Von Mises 常值显示" : "平滑云图：节点值为相邻单元 Von Mises 平均值") : "节点位移模长插值"
                                color: textMuted
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
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
        color: "#f1f3f5"
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
            onExited: parent.color = "#f1f3f5"

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
        color: "#f1f3f5"
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
            onExited: parent.color = "#f1f3f5"

            onClicked: {
                rightPanelVisible = !rightPanelVisible
                shell_status = rightPanelVisible ? "已展开右侧栏" : "已隐藏右侧栏"
            }
        }
    }
}
