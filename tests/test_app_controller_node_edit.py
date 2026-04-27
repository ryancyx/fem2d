from ui.backend.app_controller import AppController


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def print_step(title: str) -> None:
    print(f"\n[TEST] {title}")


def test_initial_state(controller: AppController) -> None:
    print_step("初始状态")

    expect(controller.status_text == "就绪", "初始状态栏文字应为“就绪”")
    expect(controller.current_mode == "none", "初始模式应为 none")
    expect(controller.node_count == 0, "初始节点数应为 0")
    expect(controller.element_count == 0, "初始单元数应为 0")
    expect(controller.material_count == 0, "初始材料数应为 0")
    expect(controller.constraint_count == 0, "初始约束数应为 0")
    expect(controller.load_count == 0, "初始载荷数应为 0")
    expect(controller.solver_has_result is False, "初始不应有求解结果")
    expect(controller.selected_node_exists is False, "初始不应有选中节点")

    print("通过：初始状态正确")


def test_add_nodes(controller: AppController) -> None:
    print_step("按坐标添加节点")

    ok1 = controller.add_node_by_coord(0.0, 0.0)
    ok2 = controller.add_node_by_coord(100.0, 0.0)
    ok3 = controller.add_node_by_text("0", "100")

    expect(ok1 is True, "第1个节点添加失败")
    expect(ok2 is True, "第2个节点添加失败")
    expect(ok3 is True, "第3个节点文本添加失败")

    expect(controller.node_count == 3, "节点数应为 3")
    expect(controller.current_mode == "node", "添加节点后模式应为 node")
    expect(controller.selected_node_exists is True, "添加节点后应自动选中新节点")
    expect(controller.selected_node_id == 3, "最后添加的节点应被选中，ID 应为 3")

    rows = controller.get_node_rows()
    expect(len(rows) == 3, "get_node_rows() 返回数量错误")
    expect(rows[0]["id"] == 1 and rows[0]["x"] == 0.0 and rows[0]["y"] == 0.0, "节点1数据错误")
    expect(rows[1]["id"] == 2 and rows[1]["x"] == 100.0 and rows[1]["y"] == 0.0, "节点2数据错误")
    expect(rows[2]["id"] == 3 and rows[2]["x"] == 0.0 and rows[2]["y"] == 100.0, "节点3数据错误")

    print("通过：节点添加与列表读取正确")


def test_select_and_update_node(controller: AppController) -> None:
    print_step("选中并修改节点坐标")

    ok = controller.select_node(2)
    expect(ok is True, "选中节点 2 失败")
    expect(controller.selected_node_id == 2, "当前选中节点应为 2")
    expect(controller.selected_node_x == 100.0, "节点2初始 x 错误")
    expect(controller.selected_node_y == 0.0, "节点2初始 y 错误")

    ok = controller.update_selected_node_position(120.5, 20.25)
    expect(ok is True, "修改节点2坐标失败")
    expect(abs(controller.selected_node_x - 120.5) < 1e-9, "修改后 x 不正确")
    expect(abs(controller.selected_node_y - 20.25) < 1e-9, "修改后 y 不正确")

    row = controller.get_selected_node_row()
    expect(row["id"] == 2, "当前选中节点行的 id 错误")
    expect(abs(row["x"] - 120.5) < 1e-9, "当前选中节点行的 x 错误")
    expect(abs(row["y"] - 20.25) < 1e-9, "当前选中节点行的 y 错误")

    print("通过：节点选中与坐标修改正确")


def test_invalid_input(controller: AppController) -> None:
    print_step("非法输入测试")

    old_count = controller.node_count

    ok = controller.add_node_by_text("", "10")
    expect(ok is False, "空 X 不应添加成功")
    expect(controller.node_count == old_count, "非法输入后节点数不应变化")

    ok = controller.add_node_by_text("abc", "10")
    expect(ok is False, "非法 X 文本不应添加成功")
    expect(controller.node_count == old_count, "非法输入后节点数不应变化")

    controller.clear_node_selection()
    expect(controller.selected_node_exists is False, "取消选中后不应仍有选中节点")

    ok = controller.update_selected_node_position_by_text("1", "2")
    expect(ok is False, "未选中节点时不应允许修改成功")

    print("通过：非法输入与边界情况处理正确")


def test_solver_and_invalidation(controller: AppController) -> None:
    print_step("求解与结果失效逻辑")

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
    expect(controller.solver_has_result is True, "求解成功后应有结果")

    node_rows = controller.get_node_result_rows()
    element_rows = controller.get_element_result_rows()

    expect(len(node_rows) > 0, "求解后应有节点结果")
    expect(len(element_rows) > 0, "求解后应有单元结果")

    expect(controller.select_node(3) is True, "选中节点3失败")
    expect(controller.update_selected_node_position(10.0, 110.0) is True, "修改节点3失败")

    expect(controller.solver_has_result is False, "模型修改后，旧求解结果应自动失效")

    print("通过：求解与结果失效逻辑正确")


def main() -> None:
    print("开始测试 AppController 节点编辑接口 ...")

    controller = AppController()

    test_initial_state(controller)
    test_add_nodes(controller)
    test_select_and_update_node(controller)
    test_invalid_input(controller)
    test_solver_and_invalidation(controller)

    print("\n全部测试通过：AppController 的节点编辑接口、求解流程与结果失效逻辑正常。")


if __name__ == "__main__":
    main()