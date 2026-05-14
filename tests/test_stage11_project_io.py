from pathlib import Path
from tempfile import TemporaryDirectory

from ui.backend.app_controller import AppController


def assert_true(value, message: str) -> None:
    if not value:
        raise AssertionError(message)


def assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：实际值={actual!r}，期望值={expected!r}")


def build_sample_project(controller: AppController) -> None:
    assert_true(controller.add_node_by_coord(0.0, 0.0), "添加节点1失败")
    assert_true(controller.add_node_by_coord(100.0, 0.0), "添加节点2失败")
    assert_true(controller.add_node_by_coord(0.0, 100.0), "添加节点3失败")

    assert_true(controller.toggle_element_node_selection(1), "选择单元节点1失败")
    assert_true(controller.toggle_element_node_selection(2), "选择单元节点2失败")
    assert_true(controller.toggle_element_node_selection(3), "选择单元节点3失败")
    assert_true(controller.create_element_from_selected_nodes(), "创建三角形单元失败")

    assert_true(controller.add_material("测试材料", 210_000_000_000.0, 0.3, 0.01, "stress"), "添加材料失败")
    assert_true(controller.assign_material_to_element(1, 2), "给单元分配材料失败")

    assert_true(controller.set_constraint(1, True, True, 0.0, 0.0), "设置节点1约束失败")
    assert_true(controller.set_constraint(2, False, True, 0.0, 0.0), "设置节点2约束失败")
    assert_true(controller.set_load(3, 1000.0, 0.0), "设置节点3载荷失败")


def main() -> None:
    print("开始测试阶段11：工程文件保存与打开 ...")

    with TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "stage11_project.json"

        controller = AppController()
        build_sample_project(controller)

        assert_true(controller.save_project_to_file(str(project_path)), "保存工程文件失败")
        assert_true(project_path.exists(), "工程文件应已生成")
        print("1) 工程保存通过")

        loaded = AppController()
        assert_true(loaded.load_project_from_file(str(project_path)), "打开工程文件失败")
        print("2) 工程打开通过")

        assert_equal(len(loaded.get_node_rows()), 3, "恢复后节点数量应为3")
        assert_equal(len(loaded.get_element_rows()), 1, "恢复后单元数量应为1")
        assert_equal(len(loaded.get_material_rows()), 2, "恢复后材料数量应为2")
        assert_equal(len(loaded.get_constraint_rows()), 2, "恢复后约束数量应为2")
        assert_equal(len(loaded.get_load_rows()), 1, "恢复后载荷数量应为1")
        print("3) 模型数据恢复通过")

        element = loaded.get_element_rows()[0]
        assert_equal(element["node_ids"], [1, 2, 3], "恢复后的单元节点连接关系不正确")
        assert_equal(element["material_id"], 2, "恢复后的单元材料编号不正确")

        load = loaded.get_load_rows()[0]
        assert_equal(load["node_id"], 3, "恢复后的载荷节点编号不正确")
        assert_equal(load["fx"], 1000.0, "恢复后的 fx 不正确")
        assert_equal(load["fy"], 0.0, "恢复后的 fy 不正确")
        print("4) 关键字段校验通过")

        assert_true(loaded.solve_model(), f"恢复工程后应能正常求解，状态：{loaded.status_text}")
        assert_true(loaded.has_solver_result(), "恢复工程求解后应存在结果")
        print("5) 打开工程后求解通过")

    print("\n全部测试通过：阶段11工程文件保存与打开功能正常。")


if __name__ == "__main__":
    main()
