from ui.backend.app_controller import AppController


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def print_step(title: str) -> None:
    print(f"\n[TEST] {title}")


def build_basic_nodes(controller: AppController) -> None:
    expect(controller.add_node_by_coord(0.0, 0.0) is True, "节点1添加失败")
    expect(controller.add_node_by_coord(1.0, 0.0) is True, "节点2添加失败")
    expect(controller.add_node_by_coord(0.0, 1.0) is True, "节点3添加失败")
    expect(controller.add_node_by_coord(1.0, 1.0) is True, "节点4添加失败")


def test_initial_element_selection_state(controller: AppController) -> None:
    print_step("初始单元选点状态")

    expect(controller.selected_element_node_count == 0, "初始单元选点数量应为 0")
    expect(controller.selected_element_node_ids == [], "初始单元选点列表应为空")

    print("通过：初始单元选点状态正确")


def test_toggle_element_selection(controller: AppController) -> None:
    print_step("单元选点切换")

    ok = controller.toggle_element_node_selection(1)
    expect(ok is True, "选择节点1失败")
    expect(controller.selected_element_node_ids == [1], "当前应选中 [1]")
    expect(controller.selected_element_node_count == 1, "当前选点数量应为 1")
    expect(controller.is_node_in_element_selection(1) is True, "节点1应在单元选点中")

    ok = controller.toggle_element_node_selection(2)
    expect(ok is True, "选择节点2失败")
    expect(controller.selected_element_node_ids == [1, 2], "当前应选中 [1, 2]")
    expect(controller.selected_element_node_count == 2, "当前选点数量应为 2")

    ok = controller.toggle_element_node_selection(3)
    expect(ok is True, "选择节点3失败")
    expect(controller.selected_element_node_ids == [1, 2, 3], "当前应选中 [1, 2, 3]")
    expect(controller.selected_element_node_count == 3, "当前选点数量应为 3")

    print("通过：单元选点切换正确")


def test_select_fourth_node_blocked(controller: AppController) -> None:
    print_step("第4个节点禁止加入单元选点")

    ok = controller.toggle_element_node_selection(4)
    expect(ok is False, "第4个节点不应允许加入")
    expect(controller.selected_element_node_ids == [1, 2, 3], "选点列表不应变化")
    expect(controller.selected_element_node_count == 3, "选点数量仍应为 3")
    expect("最多只能选择 3 个节点" in controller.status_text, "状态信息应提示最多3个节点")

    print("通过：第4个节点被正确阻止")


def test_deselect_node(controller: AppController) -> None:
    print_step("取消单个单元选点")

    ok = controller.toggle_element_node_selection(2)
    expect(ok is True, "取消节点2失败")
    expect(controller.selected_element_node_ids == [1, 3], "取消后应剩 [1, 3]")
    expect(controller.selected_element_node_count == 2, "取消后选点数量应为 2")
    expect(controller.is_node_in_element_selection(2) is False, "节点2不应仍在单元选点中")

    print("通过：取消单个单元选点正确")


def test_clear_element_selection(controller: AppController) -> None:
    print_step("清空全部单元选点")

    controller.clear_element_node_selection()
    expect(controller.selected_element_node_ids == [], "清空后选点列表应为空")
    expect(controller.selected_element_node_count == 0, "清空后选点数量应为 0")

    print("通过：清空全部单元选点正确")


def test_invalid_node_selection(controller: AppController) -> None:
    print_step("非法节点编号单元选点")

    ok = controller.toggle_element_node_selection(999)
    expect(ok is False, "不存在的节点不应选点成功")
    expect(controller.selected_element_node_ids == [], "非法选点后列表应保持为空")
    expect("不存在编号为 999 的节点" in controller.status_text, "状态信息应提示节点不存在")

    print("通过：非法节点编号处理正确")


def test_delete_node_cleans_element_selection(controller: AppController) -> None:
    print_step("删除节点时自动清理单元选点")

    expect(controller.toggle_element_node_selection(1) is True, "选择节点1失败")
    expect(controller.toggle_element_node_selection(2) is True, "选择节点2失败")
    expect(controller.selected_element_node_ids == [1, 2], "当前应选中 [1, 2]")

    expect(controller.delete_node(2) is True, "删除未引用节点2失败")
    expect(controller.selected_element_node_ids == [1], "删除节点2后，单元选点应自动变为 [1]")
    expect(controller.selected_element_node_count == 1, "删除节点后选点数量应自动更新")

    print("通过：删除节点时自动清理单元选点正确")


def test_new_model_clears_element_selection(controller: AppController) -> None:
    print_step("新建模型时清空单元选点")

    expect(controller.toggle_element_node_selection(1) is True, "选择节点1失败")
    expect(controller.selected_element_node_count == 1, "当前选点数量应为 1")

    controller.new_model()
    expect(controller.selected_element_node_ids == [], "新建模型后单元选点应为空")
    expect(controller.selected_element_node_count == 0, "新建模型后选点数量应为 0")
    expect(controller.node_count == 0, "新建模型后节点数应为 0")

    print("通过：新建模型时清空单元选点正确")


def main() -> None:
    print("开始测试：阶段6 单元临时选点机制")

    controller = AppController()

    test_initial_element_selection_state(controller)

    build_basic_nodes(controller)
    test_toggle_element_selection(controller)
    test_select_fourth_node_blocked(controller)
    test_deselect_node(controller)
    test_clear_element_selection(controller)
    test_invalid_node_selection(controller)

    controller = AppController()
    build_basic_nodes(controller)
    test_delete_node_cleans_element_selection(controller)

    controller = AppController()
    build_basic_nodes(controller)
    test_new_model_clears_element_selection(controller)

    print("\n全部测试通过：阶段6 单元临时选点机制正常。")


if __name__ == "__main__":
    main()