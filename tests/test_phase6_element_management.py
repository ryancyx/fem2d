from ui.backend.app_controller import AppController


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def print_step(title: str) -> None:
    print(f"\n[TEST] {title}")


def build_one_element(controller: AppController) -> None:
    expect(controller.add_node_by_coord(0.0, 0.0) is True, "节点1添加失败")
    expect(controller.add_node_by_coord(1.0, 0.0) is True, "节点2添加失败")
    expect(controller.add_node_by_coord(0.0, 1.0) is True, "节点3添加失败")

    expect(controller.toggle_element_node_selection(1) is True, "选择节点1失败")
    expect(controller.toggle_element_node_selection(2) is True, "选择节点2失败")
    expect(controller.toggle_element_node_selection(3) is True, "选择节点3失败")

    expect(controller.create_element_from_selected_nodes() is True, "创建单元失败")


def test_select_element() -> None:
    print_step("选中单元")
    controller = AppController()
    build_one_element(controller)

    expect(controller.selected_element_exists is True, "创建后应自动选中单元")
    expect(controller.selected_element_id == 1, "当前选中单元应为1")

    row = controller.get_selected_element_row()
    expect(row["id"] == 1, "单元id错误")
    expect(row["node_ids"] == [1, 2, 3], "单元节点错误")
    expect(row["material_id"] == 1, "材料id错误")
    expect(row["element_type"] == "CST", "单元类型错误")

    expect(controller.selected_element_node_ids_info == [1, 2, 3], "属性中的单元节点列表错误")
    expect(controller.selected_element_material_id == 1, "属性中的材料id错误")
    expect(controller.selected_element_type == "CST", "属性中的单元类型错误")

    print("通过：选中单元正确")


def test_clear_element_selection() -> None:
    print_step("清空单元选中")
    controller = AppController()
    build_one_element(controller)

    controller.clear_element_selection()
    expect(controller.selected_element_exists is False, "清空后不应仍有选中单元")
    expect(controller.selected_element_id == -1, "清空后 selected_element_id 应为 -1")
    expect(controller.get_selected_element_row() == {}, "清空后当前选中单元行应为空")

    print("通过：清空单元选中正确")


def test_delete_selected_element() -> None:
    print_step("删除当前选中单元")
    controller = AppController()
    build_one_element(controller)

    expect(controller.element_count == 1, "删除前单元数应为1")
    expect(controller.delete_selected_element() is True, "删除当前选中单元失败")
    expect(controller.element_count == 0, "删除后单元数应为0")
    expect(controller.selected_element_exists is False, "删除后不应仍有选中单元")
    expect(controller.selected_element_id == -1, "删除后 selected_element_id 应为 -1")

    rows = controller.get_element_rows()
    expect(rows == [], "删除后单元列表应为空")

    print("通过：删除当前选中单元正确")


def test_delete_nonexistent_element() -> None:
    print_step("删除不存在的单元")
    controller = AppController()

    ok = controller.delete_element(999)
    expect(ok is False, "不存在的单元不应删除成功")
    expect("不存在编号为 999 的单元" in controller.status_text, "状态提示不正确")

    print("通过：删除不存在单元的处理正确")


def test_select_nonexistent_element() -> None:
    print_step("选中不存在的单元")
    controller = AppController()

    ok = controller.select_element(999)
    expect(ok is False, "不存在的单元不应选中成功")
    expect("不存在编号为 999 的单元" in controller.status_text, "状态提示不正确")

    print("通过：选中不存在单元的处理正确")


def main() -> None:
    print("开始测试：阶段6 单元管理")

    test_select_element()
    test_clear_element_selection()
    test_delete_selected_element()
    test_delete_nonexistent_element()
    test_select_nonexistent_element()

    print("\n全部测试通过：阶段6 单元管理逻辑正常。")


if __name__ == "__main__":
    main()