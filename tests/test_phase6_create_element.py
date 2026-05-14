from ui.backend.app_controller import AppController


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def print_step(title: str) -> None:
    print(f"\n[TEST] {title}")


def build_triangle_nodes(controller: AppController) -> None:
    expect(controller.add_node_by_coord(0.0, 0.0) is True, "节点1添加失败")
    expect(controller.add_node_by_coord(1.0, 0.0) is True, "节点2添加失败")
    expect(controller.add_node_by_coord(0.0, 1.0) is True, "节点3添加失败")


def build_collinear_nodes(controller: AppController) -> None:
    expect(controller.add_node_by_coord(0.0, 0.0) is True, "节点1添加失败")
    expect(controller.add_node_by_coord(1.0, 0.0) is True, "节点2添加失败")
    expect(controller.add_node_by_coord(2.0, 0.0) is True, "节点3添加失败")


def select_nodes(controller: AppController, node_ids: list[int]) -> None:
    for node_id in node_ids:
        ok = controller.toggle_element_node_selection(node_id)
        expect(ok is True, f"选择节点 {node_id} 失败")


def test_create_element_success() -> None:
    print_step("成功创建单元")

    controller = AppController()
    build_triangle_nodes(controller)
    select_nodes(controller, [1, 2, 3])

    ok = controller.create_element_from_selected_nodes()
    expect(ok is True, "创建单元应成功")
    expect(controller.element_count == 1, "创建后单元数应为 1")
    expect(controller.material_count == 1, "创建单元时应自动补默认材料")
    expect(controller.selected_element_node_ids == [], "创建成功后应清空临时选点")
    expect(controller.selected_element_node_count == 0, "创建成功后临时选点数量应为 0")
    expect(controller.current_mode == "element", "创建成功后当前模式应为 element")

    rows = controller.get_element_rows()
    expect(len(rows) == 1, "单元列表应有 1 个元素")
    expect(rows[0]["id"] == 1, "第一个单元 ID 应为 1")
    expect(rows[0]["node_ids"] == [1, 2, 3], "单元节点顺序应为 [1, 2, 3]")
    expect(rows[0]["material_id"] == 1, "默认材料 ID 应为 1")
    expect(rows[0]["element_type"] == "CST", "单元类型应为 CST")

    print("通过：成功创建单元")


def test_need_exactly_three_nodes() -> None:
    print_step("必须恰好选择3个节点")

    controller = AppController()
    build_triangle_nodes(controller)
    select_nodes(controller, [1, 2])

    ok = controller.create_element_from_selected_nodes()
    expect(ok is False, "只选2个节点时不应创建成功")
    expect(controller.element_count == 0, "失败后单元数应仍为 0")
    expect("必须恰好选择 3 个节点" in controller.status_text, "状态应提示必须选择3个节点")

    print("通过：节点数不足时被正确阻止")


def test_collinear_nodes_blocked() -> None:
    print_step("共线节点禁止创建单元")

    controller = AppController()
    build_collinear_nodes(controller)
    select_nodes(controller, [1, 2, 3])

    ok = controller.create_element_from_selected_nodes()
    expect(ok is False, "共线节点不应创建成功")
    expect(controller.element_count == 0, "失败后单元数应仍为 0")
    expect(controller.selected_element_node_ids == [1, 2, 3], "创建失败后临时选点应保留")
    expect("共线" in controller.status_text, "状态应提示节点共线")

    print("通过：共线节点被正确阻止")


def test_duplicate_element_blocked() -> None:
    print_step("重复单元禁止创建")

    controller = AppController()
    build_triangle_nodes(controller)

    select_nodes(controller, [1, 2, 3])
    expect(controller.create_element_from_selected_nodes() is True, "第一次创建单元失败")
    expect(controller.element_count == 1, "第一次创建后单元数应为 1")

    select_nodes(controller, [3, 2, 1])
    ok = controller.create_element_from_selected_nodes()
    expect(ok is False, "重复单元不应创建成功")
    expect(controller.element_count == 1, "重复创建失败后单元数应保持为 1")
    expect("已存在" in controller.status_text, "状态应提示相同节点组合已存在")

    print("通过：重复单元被正确阻止")


def test_invalidate_solver_result_after_element_creation() -> None:
    print_step("创建单元后求解结果自动失效")

    controller = AppController()

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
    expect(ok is True, "求解应成功")
    expect(controller.solver_has_result is True, "求解后应存在结果")

    expect(controller.add_node_by_coord(50.0, 50.0) is True, "节点4添加失败")
    select_nodes(controller, [1, 2, 4])

    ok = controller.create_element_from_selected_nodes()
    expect(ok is True, "创建第二个单元应成功")
    expect(controller.solver_has_result is False, "模型变化后旧求解结果应自动失效")

    print("通过：创建单元后求解结果自动失效")


def main() -> None:
    print("开始测试：阶段6 创建单元")

    test_create_element_success()
    test_need_exactly_three_nodes()
    test_collinear_nodes_blocked()
    test_duplicate_element_blocked()
    test_invalidate_solver_result_after_element_creation()

    print("\n全部测试通过：阶段6 创建单元逻辑正常。")


if __name__ == "__main__":
    main()