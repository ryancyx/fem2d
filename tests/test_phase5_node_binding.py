from ui.backend.app_controller import AppController


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def print_step(title: str) -> None:
    print(f"\n[TEST] {title}")


def test_initial_state(controller: AppController) -> None:
    print_step("初始状态")
    expect(controller.node_count == 0, "初始节点数应为 0")
    expect(controller.selected_node_exists is False, "初始不应有选中节点")
    print("通过：初始状态正确")


def test_add_node_by_coord(controller: AppController) -> None:
    print_step("按坐标添加节点")
    ok = controller.add_node_by_coord(0.0, 0.0)
    expect(ok is True, "按坐标添加节点失败")
    expect(controller.node_count == 1, "添加后节点数应为 1")
    expect(controller.selected_node_exists is True, "添加后应自动选中新节点")
    expect(controller.selected_node_id == 1, "第一个节点 ID 应为 1")
    print("通过：按坐标添加节点正确")


def test_add_node_by_text(controller: AppController) -> None:
    print_step("按文本添加节点")
    ok = controller.add_node_by_text("1.5", "2.5")
    expect(ok is True, "按文本添加节点失败")
    expect(controller.node_count == 2, "添加后节点数应为 2")
    expect(controller.selected_node_id == 2, "第二个节点应被自动选中")
    row = controller.get_selected_node_row()
    expect(abs(row["x"] - 1.5) < 1e-9, "节点 x 坐标错误")
    expect(abs(row["y"] - 2.5) < 1e-9, "节点 y 坐标错误")
    print("通过：按文本添加节点正确")


def test_select_node(controller: AppController) -> None:
    print_step("选中节点")
    ok = controller.select_node(1)
    expect(ok is True, "选中节点 1 失败")
    expect(controller.selected_node_id == 1, "当前选中节点应为 1")
    print("通过：选中节点正确")


def test_update_selected_node(controller: AppController) -> None:
    print_step("修改选中节点坐标")
    ok = controller.update_selected_node_position(3.0, 4.0)
    expect(ok is True, "修改选中节点坐标失败")
    row = controller.get_selected_node_row()
    expect(abs(row["x"] - 3.0) < 1e-9, "修改后 x 坐标错误")
    expect(abs(row["y"] - 4.0) < 1e-9, "修改后 y 坐标错误")
    print("通过：修改选中节点坐标正确")


def test_delete_unreferenced_node(controller: AppController) -> None:
    print_step("删除未引用节点")
    ok = controller.select_node(2)
    expect(ok is True, "选中节点 2 失败")
    ok = controller.delete_selected_node()
    expect(ok is True, "删除未引用节点失败")
    expect(controller.node_count == 1, "删除后节点数应为 1")
    print("通过：删除未引用节点正确")


def test_invalid_input(controller: AppController) -> None:
    print_step("非法输入测试")

    old_count = controller.node_count

    ok = controller.add_node_by_text("", "10")
    expect(ok is False, "空 X 不应添加成功")
    expect(controller.node_count == old_count, "非法输入后节点数不应变化")

    ok = controller.add_node_by_text("abc", "10")
    expect(ok is False, "非法 X 文本不应添加成功")
    expect(controller.node_count == old_count, "非法输入后节点数不应变化")

    ok = controller.add_node_by_text("1", "")
    expect(ok is False, "空 Y 不应添加成功")
    expect(controller.node_count == old_count, "非法输入后节点数不应变化")

    print("通过：非法输入处理正确")


def test_clear_selection(controller: AppController) -> None:
    print_step("清除选中测试")

    ok = controller.select_node(1)
    expect(ok is True, "清除选中前应能先选中节点 1")
    expect(controller.selected_node_exists is True, "选中节点后 selected_node_exists 应为 True")

    controller.clear_node_selection()
    expect(controller.selected_node_exists is False, "清除选中后不应仍有选中节点")
    expect(controller.selected_node_id == -1, "清除选中后 selected_node_id 应为 -1")

    row = controller.get_selected_node_row()
    expect(row == {}, "清除选中后 get_selected_node_row() 应返回空字典")

    print("通过：清除选中逻辑正确")


def test_solver_result_invalidation(controller: AppController) -> None:
    print_step("求解结果失效测试")

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
    expect(controller.solver_has_result is True, "求解后应存在结果")

    ok = controller.select_node(3)
    expect(ok is True, "选中节点 3 失败")

    ok = controller.update_selected_node_position(10.0, 110.0)
    expect(ok is True, "修改节点 3 坐标失败")

    expect(controller.solver_has_result is False, "模型修改后旧求解结果应自动失效")

    print("通过：求解结果失效逻辑正确")


def test_delete_referenced_node_blocked(controller: AppController) -> None:
    print_step("被引用节点禁止删除测试")

    controller.new_model()

    expect(controller.add_node_by_coord(0.0, 0.0) is True, "节点1添加失败")
    expect(controller.add_node_by_coord(1.0, 0.0) is True, "节点2添加失败")
    expect(controller.add_node_by_coord(0.0, 1.0) is True, "节点3添加失败")

    controller.add_test_material()
    controller.add_test_element()

    expect(controller.node_count == 3, "测试前节点数应为 3")
    expect(controller.element_count == 1, "测试前单元数应为 1")

    ok = controller.select_node(1)
    expect(ok is True, "选中节点 1 失败")

    ok = controller.delete_selected_node()
    expect(ok is False, "被单元引用的节点不应允许删除")
    expect(controller.node_count == 3, "删除失败后节点数不应变化")
    expect("不能删除" in controller.status_text, "状态信息应提示不能删除")

    print("通过：被引用节点删除保护正确")

def main() -> None:
    print("开始测试：阶段 5 节点绑定")

    controller = AppController()

    test_initial_state(controller)
    test_add_node_by_coord(controller)
    test_add_node_by_text(controller)
    test_select_node(controller)
    test_update_selected_node(controller)
    test_delete_unreferenced_node(controller)

    test_invalid_input(controller)
    test_clear_selection(controller)
    test_solver_result_invalidation(controller)
    test_delete_referenced_node_blocked(controller)

    print("\n全部测试通过：阶段 5 节点绑定逻辑正常。")


if __name__ == "__main__":
    main()