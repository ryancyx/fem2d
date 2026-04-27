import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QPoint, Qt, QObject
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


def get_str_prop(obj: QObject, name: str, default: str = "") -> str:
    value = obj.property(name)
    if value is None:
        return default
    return str(value)


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


def send_char_to_window(window: QObject, ch: str) -> None:
    if ch.isdigit():
        key = getattr(Qt, f"Key_{ch}")
        QTest.keyClick(window, key)
    elif ch == ".":
        QTest.keyClick(window, Qt.Key_Period)
    elif ch == "-":
        QTest.keyClick(window, Qt.Key_Minus)
    elif ch == " ":
        QTest.keyClick(window, Qt.Key_Space)
    else:
        raise AssertionError(f"测试脚本暂不支持输入字符: {ch}")

    process_events(10)


def type_text_via_window(window: QObject, value: str) -> None:
    for ch in value:
        send_char_to_window(window, ch)


def clear_and_type(window: QObject, text_item: QObject, value: str) -> None:
    """
    先点击文本框使其获得焦点，再把按键逐个发送给 window。
    真正拥有焦点的是 QML TextField，因此按键会路由到它。
    """
    item_center_click(window, text_item)

    if hasattr(text_item, "forceActiveFocus"):
        text_item.forceActiveFocus()
        process_events(30)

    current_text = get_str_prop(text_item, "text", "")

    # 尽量清空现有文本
    if current_text:
        for _ in range(len(current_text) + 2):
            QTest.keyClick(window, Qt.Key_Backspace)
            process_events(10)

    if value:
        type_text_via_window(window, value)
        process_events(60)

    final_text = get_str_prop(text_item, "text", "")
    expect(final_text == value, f"文本输入失败：期望 '{value}'，实际 '{final_text}'")


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
    process_events(120)

    roots = engine.rootObjects()
    print("Root objects count:", len(roots))
    expect(len(roots) > 0, "QML 加载失败：rootObjects 为空")

    window = roots[0]
    window.show()
    process_events(150)

    return app, engine, controller, window


def test_qml_load_and_find_objects(window):
    print_step("QML 加载与对象查找")

    names = [
        "mainWindow",
        "nodeModeButton",
        "viewportRect",
        "viewportMouseArea",
        "addNodeXField",
        "addNodeYField",
        "addNodeButton",
        "selectedXField",
        "selectedYField",
        "applyNodeEditButton",
        "solveHeaderButton",
    ]

    found = {}
    for name in names:
        found[name] = find_required_object(window, name)

    print("通过：关键对象都已找到")
    return found


def test_click_create_nodes(window, controller, objects):
    print_step("视口点击创建节点")

    node_mode_button = objects["nodeModeButton"]
    viewport_mouse_area = objects["viewportMouseArea"]

    item_center_click(window, node_mode_button)
    expect(controller.current_mode == "node", "点击节点模式按钮后模式应为 node")

    item_offset_click(window, viewport_mouse_area, 140, 120)
    item_offset_click(window, viewport_mouse_area, 280, 120)
    item_offset_click(window, viewport_mouse_area, 220, 240)

    expect(controller.node_count == 3, "视口点击后应创建 3 个节点")
    expect(controller.selected_node_exists is True, "创建节点后应自动选中最后一个节点")
    expect(controller.selected_node_id == 3, "最后创建节点应为 3")

    rows = controller.get_node_rows()
    expect(len(rows) == 3, "节点列表数量不正确")

    print("通过：可通过视口点击创建节点")


def test_add_node_by_text(window, controller, objects):
    print_step("左侧坐标输入创建节点")

    add_x = objects["addNodeXField"]
    add_y = objects["addNodeYField"]
    add_button = objects["addNodeButton"]

    clear_and_type(window, add_x, "50")
    clear_and_type(window, add_y, "150")
    item_center_click(window, add_button)

    expect(controller.node_count == 4, "坐标输入新增节点后节点数应为 4")
    expect(controller.selected_node_id == 4, "文本新增后应自动选中新节点 4")

    row = controller.get_selected_node_row()
    expect(abs(row["x"] - 50.0) < 1e-9, "新增节点 x 错误")
    expect(abs(row["y"] - 150.0) < 1e-9, "新增节点 y 错误")

    print("通过：可通过左侧输入框创建节点")


def test_edit_selected_node(window, controller, objects):
    print_step("右侧属性编辑器修改节点坐标")

    controller.select_node(2)
    process_events()

    selected_x = objects["selectedXField"]
    selected_y = objects["selectedYField"]
    apply_button = objects["applyNodeEditButton"]

    clear_and_type(window, selected_x, "135.5")
    clear_and_type(window, selected_y, "25.25")
    item_center_click(window, apply_button)

    row = controller.get_selected_node_row()
    expect(row["id"] == 2, "当前选中节点应为 2")
    expect(abs(row["x"] - 135.5) < 1e-9, "节点 2 修改后 x 错误")
    expect(abs(row["y"] - 25.25) < 1e-9, "节点 2 修改后 y 错误")

    print("通过：右侧属性编辑器可修改选中节点坐标")


def test_solve_and_invalidate(window, controller, objects):
    print_step("求解与结果失效逻辑")

    controller.new_model()
    process_events()

    solve_button = objects["solveHeaderButton"]

    # 使用确定的标准三角形模型，避免视口点击坐标影响求解稳定性
    expect(controller.add_node_by_coord(0.0, 0.0) is True, "节点1添加失败")
    expect(controller.add_node_by_coord(100.0, 0.0) is True, "节点2添加失败")
    expect(controller.add_node_by_coord(0.0, 100.0) is True, "节点3添加失败")
    process_events()

    expect(controller.node_count == 3, "求解前应有 3 个节点")

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
    expect(len(controller.get_node_result_rows()) > 0, "节点结果不应为空")
    expect(len(controller.get_element_result_rows()) > 0, "单元结果不应为空")

    controller.select_node(3)
    process_events()
    controller.update_selected_node_position(10.0, 110.0)
    process_events()

    expect(controller.solver_has_result is False, "修改节点后旧结果应自动失效")

    print("通过：求解与结果失效逻辑正常")


def main():
    print("开始测试：QML 视口点击创建节点 + 属性编辑 + 求解流程 ...")

    app, engine, controller, window = load_qml()
    objects = test_qml_load_and_find_objects(window)
    test_click_create_nodes(window, controller, objects)
    test_add_node_by_text(window, controller, objects)
    test_edit_selected_node(window, controller, objects)
    test_solve_and_invalidate(window, controller, objects)

    print("\n全部测试通过：QML 视口点击、节点编辑、求解与结果失效逻辑正常。")

    process_events(100)
    return 0


if __name__ == "__main__":
    sys.exit(main())