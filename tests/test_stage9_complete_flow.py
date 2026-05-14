from ui.backend.app_controller import AppController


def assert_true(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：实际值={actual!r}，期望值={expected!r}")


def assert_positive(value, message: str) -> None:
    if value <= 0:
        raise AssertionError(f"{message}：实际值={value!r}，应大于0")


def build_solvable_triangle(controller: AppController) -> None:
    assert_true(controller.add_node_by_coord(0.0, 0.0), "添加节点1失败")
    assert_true(controller.add_node_by_coord(100.0, 0.0), "添加节点2失败")
    assert_true(controller.add_node_by_coord(0.0, 100.0), "添加节点3失败")

    assert_true(controller.toggle_element_node_selection(1), "选择节点1失败")
    assert_true(controller.toggle_element_node_selection(2), "选择节点2失败")
    assert_true(controller.toggle_element_node_selection(3), "选择节点3失败")
    assert_true(controller.create_element_from_selected_nodes(), "创建单元失败")

    # create_element_from_selected_nodes 会自动确保默认材料存在并分配给单元。
    assert_equal(len(controller.get_material_rows()), 1, "应自动创建默认材料")
    assert_equal(controller.get_element_rows()[0]["material_id"], 1, "单元应分配默认材料1")

    # 节点1固定ux/uy，节点2固定uy，节点3施加x向载荷。
    assert_true(controller.set_constraint(1, True, True, 0.0, 0.0), "设置节点1约束失败")
    assert_true(controller.set_constraint(2, False, True, 0.0, 0.0), "设置节点2约束失败")
    assert_true(controller.set_load(3, 1000.0, 0.0), "设置节点3载荷失败")


def main() -> None:
    print("开始测试阶段9：结果显示与后处理数据接口 ...")

    controller = AppController()
    build_solvable_triangle(controller)

    assert_true(controller.solve_model(), f"求解失败：{controller.status_text}")
    assert_true(controller.has_solver_result(), "求解后应存在结果")

    node_rows = controller.get_node_result_rows()
    element_rows = controller.get_element_result_rows()

    assert_equal(len(node_rows), 3, "应得到3条节点位移结果")
    assert_equal(len(element_rows), 1, "应得到1条单元结果")

    print("1) 求解结果基础表通过")

    node_result = controller.get_node_result_by_id(3)
    assert_true(node_result["has_result"], "节点3应能读取位移结果")
    assert_equal(node_result["node_id"], 3, "节点结果编号应为3")
    assert_true("ux" in node_result and "uy" in node_result, "节点结果应包含ux/uy")
    assert_true("u_magnitude" in node_result, "节点结果应包含位移模长")

    missing_node = controller.get_node_result_by_id(999)
    assert_true(not missing_node["has_result"], "不存在的节点结果应返回has_result=False")

    print("2) 节点详细结果读取通过")

    element_result = controller.get_element_result_by_id(1)
    assert_true(element_result["has_result"], "单元1应能读取应力应变结果")
    assert_equal(element_result["element_id"], 1, "单元结果编号应为1")
    for key in ["strain_x", "strain_y", "gamma_xy", "stress_x", "stress_y", "tau_xy", "von_mises"]:
        assert_true(key in element_result, f"单元结果应包含 {key}")

    missing_element = controller.get_element_result_by_id(999)
    assert_true(not missing_element["has_result"], "不存在的单元结果应返回has_result=False")

    print("3) 单元详细结果读取通过")

    summary = controller.get_result_summary()
    assert_true(summary["has_result"], "结果摘要应显示已有结果")
    assert_equal(summary["node_result_count"], 3, "结果摘要节点数量应为3")
    assert_equal(summary["element_result_count"], 1, "结果摘要单元数量应为1")
    assert_true(summary["max_displacement_node_id"] in [1, 2, 3], "最大位移节点编号应有效")
    assert_equal(summary["max_von_mises_element_id"], 1, "最大等效应力单元编号应为1")

    print("4) 后处理结果摘要通过")

    assert_true(controller.clear_solver_results_from_view(), "清除求解结果失败")
    assert_true(not controller.has_solver_result(), "清除后不应再存在求解结果")
    assert_equal(len(controller.get_node_result_rows()), 0, "清除后节点结果应为空")
    assert_equal(len(controller.get_element_result_rows()), 0, "清除后单元结果应为空")

    print("5) 结果清除接口通过")

    print("\n全部测试通过：阶段9结果显示与后处理数据接口正常。")


if __name__ == "__main__":
    main()
