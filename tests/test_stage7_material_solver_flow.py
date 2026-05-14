from ui.backend.app_controller import AppController


def assert_true(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def assert_false(value, message: str) -> None:
    if value:
        raise AssertionError(message)


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：实际值={actual!r}，期望值={expected!r}")


def assert_almost_equal(actual, expected, message: str, tol: float = 1e-12) -> None:
    if abs(actual - expected) > tol:
        raise AssertionError(f"{message}：实际值={actual!r}，期望值={expected!r}")


def get_material_rows(controller: AppController):
    if hasattr(controller, "get_material_rows"):
        return controller.get_material_rows()
    return controller.get_materials()


def get_element_rows(controller: AppController):
    return controller.get_element_rows()


def build_basic_triangle_model(controller: AppController) -> None:
    assert_true(controller.add_node_by_coord(0.0, 0.0), "添加节点1失败")
    assert_true(controller.add_node_by_coord(100.0, 0.0), "添加节点2失败")
    assert_true(controller.add_node_by_coord(0.0, 100.0), "添加节点3失败")

    assert_true(controller.toggle_element_node_selection(1), "选择单元节点1失败")
    assert_true(controller.toggle_element_node_selection(2), "选择单元节点2失败")
    assert_true(controller.toggle_element_node_selection(3), "选择单元节点3失败")

    assert_true(controller.create_element_from_selected_nodes(), "创建三角形单元失败")

    node_rows = controller.get_node_rows()
    element_rows = controller.get_element_rows()

    assert_equal(len(node_rows), 3, "节点数量应为3")
    assert_equal(len(element_rows), 1, "单元数量应为1")


def main():
    print("开始测试阶段7：材料管理、材料分配与求解链路 ...")

    controller = AppController()

    # =========================
    # 1. 创建基础三角形模型
    # =========================
    build_basic_triangle_model(controller)

    element_rows = get_element_rows(controller)
    assert_equal(element_rows[0]["id"], 1, "第一个单元编号应为1")
    assert_equal(element_rows[0]["node_ids"], [1, 2, 3], "单元节点连接关系应为 [1, 2, 3]")

    print("1) 基础三角形模型创建通过")

    # =========================
    # 2. 检查创建单元时是否已有默认材料
    # =========================
    material_rows = get_material_rows(controller)
    assert_true(len(material_rows) >= 1, "创建单元后应至少存在一个默认材料")

    default_material_id = material_rows[0]["id"]
    assert_equal(default_material_id, 1, "默认材料 id 应为1")

    print("2) 默认材料检查通过")

    # =========================
    # 3. 新增第二个材料
    # =========================
    assert_true(
        controller.add_material(
            "测试铝材",
            70_000_000_000.0,
            0.33,
            0.02,
            "stress",
        ),
        "新增测试铝材失败",
    )

    material_rows = get_material_rows(controller)
    assert_equal(len(material_rows), 2, "新增材料后材料数量应为2")

    material_2 = material_rows[1]
    assert_equal(material_2["id"], 2, "新增材料 id 应为2")
    assert_equal(material_2["name"], "测试铝材", "新增材料名称不正确")
    assert_almost_equal(material_2["young_modulus"], 70_000_000_000.0, "新增材料弹性模量不正确")
    assert_almost_equal(material_2["poisson_ratio"], 0.33, "新增材料泊松比不正确")
    assert_almost_equal(material_2["thickness"], 0.02, "新增材料厚度不正确")
    assert_equal(material_2["plane_mode"], "stress", "新增材料平面模式应为 stress")

    print("3) 新增材料通过")

    # =========================
    # 4. 更新第二个材料
    # =========================
    assert_true(
        controller.update_material(
            2,
            "更新后的测试铝材",
            72_000_000_000.0,
            0.31,
            0.015,
            "stress",
        ),
        "更新材料失败",
    )

    material_rows = get_material_rows(controller)
    updated_material = [item for item in material_rows if item["id"] == 2][0]

    assert_equal(updated_material["name"], "更新后的测试铝材", "材料名称更新失败")
    assert_almost_equal(updated_material["young_modulus"], 72_000_000_000.0, "材料弹性模量更新失败")
    assert_almost_equal(updated_material["poisson_ratio"], 0.31, "材料泊松比更新失败")
    assert_almost_equal(updated_material["thickness"], 0.015, "材料厚度更新失败")

    print("4) 更新材料通过")

    # =========================
    # 5. 非法材料参数拦截
    # =========================
    assert_false(
        controller.add_material(
            "非法材料-负弹性模量",
            -1.0,
            0.3,
            0.01,
            "stress",
        ),
        "负弹性模量材料不应创建成功",
    )

    assert_false(
        controller.add_material(
            "非法材料-平面应变",
            210_000_000_000.0,
            0.3,
            0.01,
            "strain",
        ),
        "当前版本暂不支持 strain，不能创建成功",
    )

    material_rows = get_material_rows(controller)
    assert_equal(len(material_rows), 2, "非法材料不应改变材料数量")

    print("5) 非法材料拦截通过")

    # =========================
    # 6. 给单元分配第二个材料
    # =========================
    assert_true(
        controller.assign_material_to_element(1, 2),
        "给单元1分配材料2失败",
    )

    element_rows = get_element_rows(controller)
    assert_equal(element_rows[0]["material_id"], 2, "单元1应已分配材料2")

    controller.select_element(1)
    selected_material_info = controller.get_selected_element_material_info()

    assert_equal(selected_material_info["element_id"], 1, "选中单元材料信息的 element_id 应为1")
    assert_equal(selected_material_info["material_id"], 2, "选中单元材料信息的 material_id 应为2")
    assert_equal(selected_material_info["material_name"], "更新后的测试铝材", "选中单元材料名称回填不正确")

    print("6) 单元材料分配通过")

    # =========================
    # 7. 被引用材料不允许删除
    # =========================
    assert_false(
        controller.delete_material(2),
        "正在被单元引用的材料不应删除成功",
    )

    material_rows = get_material_rows(controller)
    assert_equal(len(material_rows), 2, "删除被引用材料失败后，材料数量应仍为2")

    print("7) 被引用材料删除保护通过")

    # =========================
    # 8. 未使用材料允许删除
    # =========================
    assert_true(
        controller.delete_material(1),
        "未被引用的默认材料应允许删除",
    )

    material_rows = get_material_rows(controller)
    assert_equal(len(material_rows), 1, "删除未使用材料后，材料数量应为1")
    assert_equal(material_rows[0]["id"], 2, "剩余材料应为材料2")

    print("8) 未使用材料删除通过")

    # =========================
    # 9. 设置足够边界条件与载荷
    #    节点1：ux, uy 固定
    #    节点2：uy 固定，防止刚体转动
    #    节点3：施加 x 方向载荷
    # =========================
    assert_true(
        controller.set_constraint(1, True, True, 0.0, 0.0),
        "设置节点1双向约束失败",
    )

    assert_true(
        controller.set_constraint(2, False, True, 0.0, 0.0),
        "设置节点2 y向约束失败",
    )

    assert_true(
        controller.set_load(3, 1000.0, 0.0),
        "设置节点3载荷失败",
    )

    constraint_rows = controller.get_constraint_rows()
    load_rows = controller.get_load_rows()

    assert_equal(len(constraint_rows), 2, "约束数量应为2")
    assert_equal(len(load_rows), 1, "载荷数量应为1")

    print("9) 求解前边界条件与载荷设置通过")

    # =========================
    # 10. 求解完整模型
    # =========================
    solve_ok = controller.solve_model()

    if not solve_ok:
        raise AssertionError(f"完整模型求解失败，状态信息：{controller.status_text}")

    assert_true(controller.has_solver_result(), "求解后应存在求解结果")

    node_result_rows = controller.get_node_result_rows()
    element_result_rows = controller.get_element_result_rows()

    assert_equal(len(node_result_rows), 3, "应得到3个节点位移结果")
    assert_equal(len(element_result_rows), 1, "应得到1个单元应力应变结果")

    print("10) 完整求解链路通过")

    print("\n全部测试通过：阶段7材料管理、材料分配、约束载荷输入与求解链路正常。")


if __name__ == "__main__":
    main()