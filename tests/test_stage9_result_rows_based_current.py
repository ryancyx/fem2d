from ui.backend.app_controller import AppController


def assert_true(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：实际值={actual!r}，期望值={expected!r}")


def assert_has_keys(row: dict, keys: list[str], label: str) -> None:
    for key in keys:
        if key not in row:
            raise AssertionError(f"{label} 缺少字段：{key}")


def build_solvable_triangle(controller: AppController) -> None:
    assert_true(controller.add_node_by_coord(0.0, 0.0), "添加节点1失败")
    assert_true(controller.add_node_by_coord(100.0, 0.0), "添加节点2失败")
    assert_true(controller.add_node_by_coord(0.0, 100.0), "添加节点3失败")

    assert_true(controller.toggle_element_node_selection(1), "选择节点1失败")
    assert_true(controller.toggle_element_node_selection(2), "选择节点2失败")
    assert_true(controller.toggle_element_node_selection(3), "选择节点3失败")
    assert_true(controller.create_element_from_selected_nodes(), "创建单元失败")

    material_rows = controller.get_material_rows() if hasattr(controller, "get_material_rows") else controller.get_materials()
    assert_true(len(material_rows) >= 1, "创建单元后应存在默认材料")

    assert_true(controller.set_constraint(1, True, True, 0.0, 0.0), "节点1双向约束失败")
    assert_true(controller.set_constraint(2, False, True, 0.0, 0.0), "节点2 y 向约束失败")
    assert_true(controller.set_load(3, 1000.0, 0.0), "节点3载荷失败")


def main() -> None:
    print("开始测试阶段9：求解结果数据行输出 ...")

    controller = AppController()
    build_solvable_triangle(controller)

    assert_true(controller.solve_model(), f"求解失败：{controller.status_text}")
    assert_true(controller.has_solver_result(), "求解后应存在结果")

    node_rows = controller.get_node_result_rows()
    element_rows = controller.get_element_result_rows()

    assert_equal(len(node_rows), 3, "节点位移结果数量应为3")
    assert_equal(len(element_rows), 1, "单元结果数量应为1")

    for row in node_rows:
        assert_has_keys(row, ["node_id", "ux", "uy"], "节点结果行")
        assert_true(isinstance(row["node_id"], int), "node_id 应为整数")
        float(row["ux"])
        float(row["uy"])

    for row in element_rows:
        assert_has_keys(
            row,
            [
                "element_id",
                "strain_x",
                "strain_y",
                "gamma_xy",
                "stress_x",
                "stress_y",
                "tau_xy",
            ],
            "单元结果行",
        )
        assert_true(isinstance(row["element_id"], int), "element_id 应为整数")
        float(row["strain_x"])
        float(row["strain_y"])
        float(row["gamma_xy"])
        float(row["stress_x"])
        float(row["stress_y"])
        float(row["tau_xy"])

    print("1) 节点位移结果行字段检查通过")
    print("2) 单元应力/应变结果行字段检查通过")
    print("\n全部测试通过：阶段9结果数据可以被 QML 结果面板稳定读取。")


if __name__ == "__main__":
    main()
