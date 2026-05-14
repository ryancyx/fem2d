from ui.backend.app_controller import AppController


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：实际值={actual!r}，期望值={expected!r}")


def assert_true(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def assert_false(value, message: str) -> None:
    if value:
        raise AssertionError(message)


def main():
    print("开始测试阶段7：约束与载荷后端输入功能 ...")

    controller = AppController()

    # =========================
    # 1. 创建基础节点
    # =========================
    assert_true(controller.add_node_by_coord(0.0, 0.0), "添加节点1失败")
    assert_true(controller.add_node_by_coord(100.0, 0.0), "添加节点2失败")
    assert_true(controller.add_node_by_coord(0.0, 100.0), "添加节点3失败")

    node_rows = controller.get_node_rows()
    assert_equal(len(node_rows), 3, "节点数量应为3")

    print("1) 节点创建通过")

    # =========================
    # 2. 测试设置节点约束
    # =========================
    assert_true(
        controller.set_constraint(
            node_id=1,
            ux_fixed=True,
            uy_fixed=True,
            ux_value=0.0,
            uy_value=0.0,
        ),
        "设置节点1双向约束失败",
    )

    constraint_rows = controller.get_constraint_rows()
    assert_equal(len(constraint_rows), 1, "约束数量应为1")
    assert_equal(constraint_rows[0]["node_id"], 1, "约束应施加在节点1")
    assert_equal(constraint_rows[0]["ux_fixed"], True, "节点1 ux 应固定")
    assert_equal(constraint_rows[0]["uy_fixed"], True, "节点1 uy 应固定")
    assert_equal(constraint_rows[0]["ux_value"], 0.0, "节点1 ux_value 应为0")
    assert_equal(constraint_rows[0]["uy_value"], 0.0, "节点1 uy_value 应为0")

    print("2) 设置节点约束通过")

    # =========================
    # 3. 测试重复设置约束时覆盖，而不是新增重复约束
    # =========================
    assert_true(
        controller.set_constraint(
            node_id=1,
            ux_fixed=True,
            uy_fixed=False,
            ux_value=0.5,
            uy_value=999.0,   # uy_fixed=False 时，后端应自动归零
        ),
        "更新节点1约束失败",
    )

    constraint_rows = controller.get_constraint_rows()
    assert_equal(len(constraint_rows), 1, "重复设置同一节点约束时不应新增记录")
    assert_equal(constraint_rows[0]["node_id"], 1, "约束仍应施加在节点1")
    assert_equal(constraint_rows[0]["ux_fixed"], True, "节点1 ux 应固定")
    assert_equal(constraint_rows[0]["uy_fixed"], False, "节点1 uy 应不固定")
    assert_equal(constraint_rows[0]["ux_value"], 0.5, "节点1 ux_value 应更新为0.5")
    assert_equal(constraint_rows[0]["uy_value"], 0.0, "uy 未固定时 uy_value 应自动归零")

    print("3) 约束覆盖更新通过")

    # =========================
    # 4. 测试非法约束：两个方向都不固定
    # =========================
    assert_false(
        controller.set_constraint(
            node_id=2,
            ux_fixed=False,
            uy_fixed=False,
            ux_value=0.0,
            uy_value=0.0,
        ),
        "两个方向都不固定的约束不应设置成功",
    )

    constraint_rows = controller.get_constraint_rows()
    assert_equal(len(constraint_rows), 1, "非法约束不应改变约束数量")

    print("4) 非法约束拦截通过")

    # =========================
    # 5. 测试设置节点载荷
    # =========================
    assert_true(
        controller.set_load(
            node_id=2,
            fx=1000.0,
            fy=0.0,
        ),
        "设置节点2载荷失败",
    )

    load_rows = controller.get_load_rows()
    assert_equal(len(load_rows), 1, "载荷数量应为1")
    assert_equal(load_rows[0]["node_id"], 2, "载荷应施加在节点2")
    assert_equal(load_rows[0]["fx"], 1000.0, "节点2 fx 应为1000")
    assert_equal(load_rows[0]["fy"], 0.0, "节点2 fy 应为0")
    assert_equal(load_rows[0]["load_type"], "nodal", "载荷类型应为 nodal")

    print("5) 设置节点载荷通过")

    # =========================
    # 6. 测试重复设置载荷时覆盖，而不是新增重复载荷
    # =========================
    assert_true(
        controller.set_load(
            node_id=2,
            fx=-250.0,
            fy=500.0,
        ),
        "更新节点2载荷失败",
    )

    load_rows = controller.get_load_rows()
    assert_equal(len(load_rows), 1, "重复设置同一节点载荷时不应新增记录")
    assert_equal(load_rows[0]["node_id"], 2, "载荷仍应施加在节点2")
    assert_equal(load_rows[0]["fx"], -250.0, "节点2 fx 应更新为 -250")
    assert_equal(load_rows[0]["fy"], 500.0, "节点2 fy 应更新为 500")

    print("6) 载荷覆盖更新通过")

    # =========================
    # 7. 测试非法载荷：fx 和 fy 同时为0
    # =========================
    assert_false(
        controller.set_load(
            node_id=3,
            fx=0.0,
            fy=0.0,
        ),
        "fx 和 fy 同时为0的载荷不应设置成功",
    )

    load_rows = controller.get_load_rows()
    assert_equal(len(load_rows), 1, "非法载荷不应改变载荷数量")

    print("7) 非法载荷拦截通过")

    # =========================
    # 8. 测试选中节点后的边界信息读取
    # =========================
    assert_true(controller.select_node(1), "选中节点1失败")
    node1_boundary = controller.get_selected_node_boundary_info()

    assert_equal(node1_boundary["node_id"], 1, "当前边界信息应对应节点1")
    assert_equal(node1_boundary["has_constraint"], True, "节点1应有约束")
    assert_equal(node1_boundary["has_load"], False, "节点1不应有载荷")

    assert_true(controller.select_node(2), "选中节点2失败")
    node2_boundary = controller.get_selected_node_boundary_info()

    assert_equal(node2_boundary["node_id"], 2, "当前边界信息应对应节点2")
    assert_equal(node2_boundary["has_constraint"], False, "节点2不应有约束")
    assert_equal(node2_boundary["has_load"], True, "节点2应有载荷")
    assert_equal(node2_boundary["fx"], -250.0, "节点2 fx 回填应正确")
    assert_equal(node2_boundary["fy"], 500.0, "节点2 fy 回填应正确")

    print("8) 选中节点边界信息读取通过")

    # =========================
    # 9. 测试清除约束
    # =========================
    assert_true(controller.clear_constraint(1), "清除节点1约束失败")

    constraint_rows = controller.get_constraint_rows()
    assert_equal(len(constraint_rows), 0, "清除后约束数量应为0")

    assert_false(
        controller.clear_constraint(1),
        "重复清除不存在的约束不应成功",
    )

    print("9) 清除约束通过")

    # =========================
    # 10. 测试清除载荷
    # =========================
    assert_true(controller.clear_load(2), "清除节点2载荷失败")

    load_rows = controller.get_load_rows()
    assert_equal(len(load_rows), 0, "清除后载荷数量应为0")

    assert_false(
        controller.clear_load(2),
        "重复清除不存在的载荷不应成功",
    )

    print("10) 清除载荷通过")

    print("\n全部测试通过：阶段7约束与载荷后端输入功能正常。")


if __name__ == "__main__":
    main()