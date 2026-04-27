import os
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from ui.backend.app_controller import AppController


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def print_step(title: str) -> None:
    print(f"\n[TEST] {title}")


def load_qml_with_controller() -> tuple[QGuiApplication, QQmlApplicationEngine, AppController]:
    # 让测试在没有桌面的环境里也更容易运行
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([])

    engine = QQmlApplicationEngine()
    controller = AppController()
    engine.rootContext().setContextProperty("appController", controller)

    qml_file = Path(__file__).resolve().parents[1] / "ui" / "qml" / "main.qml"
    print("QML file path:", qml_file)
    print("QML exists:", qml_file.exists())

    expect(qml_file.exists(), "main.qml 不存在")

    engine.load(str(qml_file))
    QCoreApplication.processEvents()

    root_objects = engine.rootObjects()
    print("Root objects count:", len(root_objects))
    expect(len(root_objects) > 0, "QML 加载失败：rootObjects 为空")

    return app, engine, controller


def test_qml_load() -> AppController:
    print_step("QML 加载冒烟测试")

    _, _, controller = load_qml_with_controller()

    expect(controller.status_text in ["就绪", "已新建空模型"], "AppController 初始状态异常")
    print("通过：QML 可正常加载，AppController 已成功注入")
    return controller


def test_node_flow(controller: AppController) -> None:
    print_step("节点新增 / 选中 / 修改流程")

    controller.new_model()

    ok = controller.add_node_by_coord(0.0, 0.0)
    expect(ok is True, "节点1添加失败")

    ok = controller.add_node_by_coord(100.0, 0.0)
    expect(ok is True, "节点2添加失败")

    ok = controller.add_node_by_text("0", "100")
    expect(ok is True, "节点3文本添加失败")

    expect(controller.node_count == 3, "节点数应为 3")
    expect(controller.selected_node_exists is True, "应存在选中节点")
    expect(controller.selected_node_id == 3, "最后添加的节点应自动被选中")

    rows = controller.get_node_rows()
    expect(len(rows) == 3, "get_node_rows 返回数量不正确")

    ok = controller.select_node(2)
    expect(ok is True, "选中节点2失败")
    expect(controller.selected_node_id == 2, "当前应选中节点2")

    ok = controller.update_selected_node_position(120.5, 20.25)
    expect(ok is True, "节点2坐标修改失败")

    row = controller.get_selected_node_row()
    expect(row["id"] == 2, "选中节点行 id 错误")
    expect(abs(row["x"] - 120.5) < 1e-9, "选中节点行 x 错误")
    expect(abs(row["y"] - 20.25) < 1e-9, "选中节点行 y 错误")

    print("通过：节点编辑流程正常")


def test_solver_flow(controller: AppController) -> None:
    print_step("求解流程测试")

    controller.new_model()

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

    ok = controller.solve_model()
    expect(ok is True, "求解失败")
    expect(controller.solver_has_result is True, "求解后应有结果")

    node_rows = controller.get_node_result_rows()
    element_rows = controller.get_element_result_rows()

    expect(len(node_rows) > 0, "节点结果为空")
    expect(len(element_rows) > 0, "单元结果为空")

    print("通过：求解流程正常")


def test_result_invalidation(controller: AppController) -> None:
    print_step("结果失效逻辑测试")

    expect(controller.solver_has_result is True, "执行本测试前应已有求解结果")

    ok = controller.select_node(3)
    expect(ok is True, "选中节点3失败")

    ok = controller.update_selected_node_position(10.0, 110.0)
    expect(ok is True, "修改节点3坐标失败")

    expect(controller.solver_has_result is False, "模型修改后旧结果应自动失效")

    print("通过：结果失效逻辑正常")


def main() -> None:
    print("开始测试：QML 加载 + AppController 联调流程 ...")

    controller = test_qml_load()
    test_node_flow(controller)
    test_solver_flow(controller)
    test_result_invalidation(controller)

    print("\n全部测试通过：QML 可加载，节点编辑、求解与结果失效逻辑正常。")


if __name__ == "__main__":
    main()