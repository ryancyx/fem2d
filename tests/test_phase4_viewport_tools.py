import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QPoint, Qt, QObject, QMetaObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest

from ui.backend.app_controller import AppController


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def print_step(title: str) -> None:
    print(f"\n[TEST] {title}")


def process_events(delay_ms: int = 80) -> None:
    QCoreApplication.processEvents()
    QTest.qWait(delay_ms)
    QCoreApplication.processEvents()


def get_num_prop(obj: QObject, name: str, default: float = 0.0) -> float:
    value = obj.property(name)
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_bool_prop(obj: QObject, name: str, default: bool = False) -> bool:
    value = obj.property(name)
    if value is None:
        return default

    return bool(value)


def get_str_prop(obj: QObject, name: str, default: str = "") -> str:
    value = obj.property(name)
    if value is None:
        return default

    return str(value)


def set_text_field(text_item: QObject, value: str) -> None:
    text_item.setProperty("text", value)
    process_events(40)

    actual = get_str_prop(text_item, "text")
    expect(actual == value, f"文本框赋值失败：期望 {value}，实际 {actual}")


def find_required_object(root: QObject, name: str) -> QObject:
    if root.objectName() == name:
        return root

    found = root.findChild(QObject, name)
    if found is not None:
        return found

    for child in root.findChildren(QObject):
        if child.objectName() == name:
            return child

    raise AssertionError(f"未找到 objectName = {name} 的对象")


def get_item_geometry_in_window(item: QObject, window: QObject) -> tuple[float, float, float, float]:
    x = 0.0
    y = 0.0
    current = item

    while current is not None and current != window:
        x += get_num_prop(current, "x", 0.0)
        y += get_num_prop(current, "y", 0.0)
        current = current.parent()

    width = get_num_prop(item, "width", 0.0)
    height = get_num_prop(item, "height", 0.0)

    return x, y, width, height


def item_center_click(window: QObject, item: QObject) -> None:
    x, y, width, height = get_item_geometry_in_window(item, window)
    expect(width > 0 and height > 0, f"控件尺寸无效：width={width}, height={height}")

    pos = QPoint(int(x + width / 2), int(y + height / 2))
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, pos)
    process_events()


def item_offset_click(window: QObject, item: QObject, offset_x: float, offset_y: float) -> None:
    x, y, width, height = get_item_geometry_in_window(item, window)
    expect(width > 0 and height > 0, f"控件尺寸无效：width={width}, height={height}")

    pos = QPoint(int(x + offset_x), int(y + offset_y))
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, pos)
    process_events()


def try_reset_viewport_transform(window: QObject) -> None:
    """
    优先调用 QML 里的 resetViewportTransform()。
    如果当前 PySide6 环境不能直接 invoke QML 函数，则退回直接设置属性。
    """
    try:
        QMetaObject.invokeMethod(window, "resetViewportTransform", Qt.DirectConnection)
        process_events(60)
    except Exception:
        window.setProperty("viewportZoom", 1.0)
        window.setProperty("viewportPanX", 0.0)
        window.setProperty("viewportPanY", 0.0)
        process_events(60)


def load_qml():
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    controller = AppController()
    engine.rootContext().setContextProperty("appController", controller)

    qml_file = Path(__file__).resolve().parents[1] / "ui" / "qml" / "main.qml"
    print("QML file path:", qml_file)
    expect(qml_file.exists(), "main.qml 不存在")

    engine.load(str(qml_file))
    process_events(150)

    roots = engine.rootObjects()
    print("Root objects count:", len(roots))
    expect(len(roots) > 0, "QML 加载失败：rootObjects 为空")

    window = roots[0]
    window.show()
    process_events(180)

    return app, engine, controller, window


def test_qml_load_and_find_objects(window: QObject) -> dict[str, QObject]:
    print_step("QML 加载与关键对象查找")

    names = [
        "mainWindow",
        "nodeModeButton",
        "solveHeaderButton",
        "viewportRect",
        "viewportMouseArea",
        "addNodeXField",
        "addNodeYField",
        "addNodeButton",
        "nodeListView",
        "selectedXField",
        "selectedYField",
        "applyNodeEditButton",
        "clearNodeSelectionButton",
        "solveTaskButton",
    ]

    objects = {}
    for name in names:
        objects[name] = find_required_object(window, name)

    print("通过：关键 QML 对象均可找到")
    return objects


def test_panel_visibility_state(window: QObject) -> None:
    print_step("左右侧栏折叠状态属性")

    expect(get_bool_prop(window, "leftPanelVisible") is True, "初始左侧栏应显示")
    expect(get_bool_prop(window, "rightPanelVisible") is True, "初始右侧栏应显示")

    window.setProperty("leftPanelVisible", False)
    process_events()
    expect(get_bool_prop(window, "leftPanelVisible") is False, "左侧栏隐藏状态设置失败")

    window.setProperty("leftPanelVisible", True)
    process_events()
    expect(get_bool_prop(window, "leftPanelVisible") is True, "左侧栏显示状态恢复失败")

    window.setProperty("rightPanelVisible", False)
    process_events()
    expect(get_bool_prop(window, "rightPanelVisible") is False, "右侧栏隐藏状态设置失败")

    window.setProperty("rightPanelVisible", True)
    process_events()
    expect(get_bool_prop(window, "rightPanelVisible") is True, "右侧栏显示状态恢复失败")

    print("通过：左右侧栏折叠状态属性正常")


def test_viewport_zoom_state(window: QObject) -> None:
    print_step("视口缩放参数与重置逻辑")

    min_zoom = get_num_prop(window, "minViewportZoom")
    max_zoom = get_num_prop(window, "maxViewportZoom")

    expect(abs(min_zoom - 0.1) < 1e-9, "最小缩放倍率应为 0.1")
    expect(abs(max_zoom - 20.0) < 1e-9, "最大缩放倍率应为 20.0")

    window.setProperty("viewportZoom", 5.0)
    window.setProperty("viewportPanX", 123.0)
    window.setProperty("viewportPanY", -45.0)
    process_events()

    expect(abs(get_num_prop(window, "viewportZoom") - 5.0) < 1e-9, "视口缩放属性设置失败")
    expect(abs(get_num_prop(window, "viewportPanX") - 123.0) < 1e-9, "视口 PanX 设置失败")
    expect(abs(get_num_prop(window, "viewportPanY") + 45.0) < 1e-9, "视口 PanY 设置失败")

    try_reset_viewport_transform(window)

    expect(abs(get_num_prop(window, "viewportZoom") - 1.0) < 1e-9, "重置后 viewportZoom 应为 1")
    expect(abs(get_num_prop(window, "viewportPanX")) < 1e-9, "重置后 viewportPanX 应为 0")
    expect(abs(get_num_prop(window, "viewportPanY")) < 1e-9, "重置后 viewportPanY 应为 0")

    print("通过：视口缩放范围与重置逻辑正常")


def test_viewport_click_create_nodes(window: QObject, controller: AppController, objects: dict[str, QObject]) -> None:
    print_step("视口点击创建节点")

    controller.new_model()
    process_events()

    node_mode_button = objects["nodeModeButton"]
    viewport_mouse_area = objects["viewportMouseArea"]

    item_center_click(window, node_mode_button)
    expect(controller.current_mode == "node", "点击节点模式按钮后，当前模式应为 node")

    window.setProperty("activeViewportTool", "add")
    process_events()

    item_offset_click(window, viewport_mouse_area, 140, 120)
    item_offset_click(window, viewport_mouse_area, 280, 120)
    item_offset_click(window, viewport_mouse_area, 220, 240)

    expect(controller.node_count == 3, "视口点击后应创建 3 个节点")
    expect(controller.selected_node_exists is True, "创建节点后应自动选中最后一个节点")
    expect(controller.selected_node_id == 3, "最后创建的节点 ID 应为 3")

    rows = controller.get_node_rows()
    expect(len(rows) == 3, "节点列表数量应为 3")

    print("通过：视口点击创建节点正常")


def test_add_node_by_text(window: QObject, controller: AppController, objects: dict[str, QObject]) -> None:
    print_step("左侧坐标输入创建节点")

    add_x = objects["addNodeXField"]
    add_y = objects["addNodeYField"]
    add_button = objects["addNodeButton"]

    set_text_field(add_x, "0")
    set_text_field(add_y, "1")
    item_center_click(window, add_button)

    expect(controller.node_count == 4, "坐标输入新增节点后，节点数应为 4")
    expect(controller.selected_node_id == 4, "坐标输入新增节点后，应自动选中新节点 4")

    row = controller.get_selected_node_row()
    expect(row["id"] == 4, "当前选中节点 ID 应为 4")
    expect(abs(row["x"] - 0.0) < 1e-9, "新增节点 x 坐标错误")
    expect(abs(row["y"] - 1.0) < 1e-9, "新增节点 y 坐标错误")

    print("通过：左侧坐标输入创建节点正常")


def test_edit_selected_node(window: QObject, controller: AppController, objects: dict[str, QObject]) -> None:
    print_step("右侧属性编辑器修改节点坐标")

    controller.select_node(2)
    process_events()

    selected_x = objects["selectedXField"]
    selected_y = objects["selectedYField"]
    apply_button = objects["applyNodeEditButton"]

    set_text_field(selected_x, "1")
    set_text_field(selected_y, "1")
    item_center_click(window, apply_button)

    row = controller.get_selected_node_row()
    expect(row["id"] == 2, "当前选中节点应为 2")
    expect(abs(row["x"] - 1.0) < 1e-9, "节点 2 修改后 x 坐标错误")
    expect(abs(row["y"] - 1.0) < 1e-9, "节点 2 修改后 y 坐标错误")

    print("通过：右侧属性编辑器修改节点坐标正常")


def test_delete_selected_node_by_view_tool(window: QObject, controller: AppController, objects: dict[str, QObject]) -> None:
    print_step("删除工具删除当前选中节点")

    expect(controller.node_count >= 4, "执行删除测试前，应至少有 4 个节点")

    controller.select_node(4)
    process_events()

    window.setProperty("activeViewportTool", "delete")
    process_events()

    viewport_mouse_area = objects["viewportMouseArea"]

    item_offset_click(window, viewport_mouse_area, 180, 180)

    expect(controller.node_count == 3, "删除选中节点后，节点数应回到 3")
    expect(controller.selected_node_exists is False, "删除当前选中节点后，不应继续存在选中节点")

    rows = controller.get_node_rows()
    ids = [row["id"] for row in rows]
    expect(4 not in ids, "节点 4 应已被删除")

    print("通过：删除工具可以删除当前选中节点")


def test_delete_referenced_node_is_blocked(controller: AppController) -> None:
    print_step("禁止删除被引用节点")

    controller.new_model()

    expect(controller.add_node_by_coord(0.0, 0.0) is True, "节点1添加失败")
    expect(controller.add_node_by_coord(1.0, 0.0) is True, "节点2添加失败")
    expect(controller.add_node_by_coord(0.0, 1.0) is True, "节点3添加失败")

    controller.add_test_material()
    controller.add_test_element()

    expect(controller.node_count == 3, "引用删除测试中节点数应为 3")
    expect(controller.element_count == 1, "引用删除测试中单元数应为 1")

    expect(controller.select_node(1) is True, "选中节点 1 失败")

    ok = controller.delete_selected_node()

    expect(ok is False, "被单元引用的节点不应允许删除")
    expect(controller.node_count == 3, "删除失败后节点数不应变化")
    expect("不能删除" in controller.status_text, "状态信息应提示不能删除")

    print("通过：被单元引用的节点会被阻止删除")


def test_solve_and_result_invalidation(window: QObject, controller: AppController, objects: dict[str, QObject]) -> None:
    print_step("求解与结果失效逻辑")

    controller.new_model()
    process_events()

    solve_button = objects["solveHeaderButton"]

    expect(controller.add_node_by_coord(0.0, 0.0) is True, "节点1添加失败")
    expect(controller.add_node_by_coord(100.0, 0.0) is True, "节点2添加失败")
    expect(controller.add_node_by_coord(0.0, 100.0) is True, "节点3添加失败")

    controller.add_test_material()
    controller.add_test_element()

    controller.add_test_constraint()
    controller.add_test_constraint()

    controller.add_test_load()
    controller.add_test_load()
    controller.add_test_load()

    process_events()

    item_center_click(window, solve_button)

    if controller.solver_has_result is False:
        print("求解失败状态文本：", controller.status_text)

    expect(controller.solver_has_result is True, "求解后应有结果")
    expect(len(controller.get_node_result_rows()) > 0, "求解后节点结果不应为空")
    expect(len(controller.get_element_result_rows()) > 0, "求解后单元结果不应为空")

    expect(controller.select_node(3) is True, "选中节点3失败")
    expect(controller.update_selected_node_position(10.0, 110.0) is True, "修改节点3坐标失败")

    expect(controller.solver_has_result is False, "修改模型后旧求解结果应自动失效")

    print("通过：求解与结果失效逻辑正常")


def main() -> int:
    print("开始测试：阶段4 视口工具、折叠侧栏、节点编辑、删除与求解流程 ...")

    app, engine, controller, window = load_qml()
    objects = test_qml_load_and_find_objects(window)

    test_panel_visibility_state(window)
    test_viewport_zoom_state(window)
    test_viewport_click_create_nodes(window, controller, objects)
    test_add_node_by_text(window, controller, objects)
    test_edit_selected_node(window, controller, objects)
    test_delete_selected_node_by_view_tool(window, controller, objects)
    test_delete_referenced_node_is_blocked(controller)
    test_solve_and_result_invalidation(window, controller, objects)

    print("\n全部测试通过：阶段4 视口工具、侧栏折叠、节点编辑、删除、求解与结果失效逻辑正常。")

    process_events(100)
    return 0


if __name__ == "__main__":
    sys.exit(main())