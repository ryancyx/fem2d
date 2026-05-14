import csv
import tempfile
from pathlib import Path

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


def read_csv_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.reader(file))


def build_solved_triangle_model(controller: AppController) -> None:
    assert_true(controller.add_node_by_coord(0.0, 0.0), "添加节点1失败")
    assert_true(controller.add_node_by_coord(100.0, 0.0), "添加节点2失败")
    assert_true(controller.add_node_by_coord(0.0, 100.0), "添加节点3失败")

    assert_true(controller.toggle_element_node_selection(1), "选择单元节点1失败")
    assert_true(controller.toggle_element_node_selection(2), "选择单元节点2失败")
    assert_true(controller.toggle_element_node_selection(3), "选择单元节点3失败")
    assert_true(controller.create_element_from_selected_nodes(), "创建单元失败")

    assert_true(controller.set_constraint(1, True, True, 0.0, 0.0), "设置节点1约束失败")
    assert_true(controller.set_constraint(2, False, True, 0.0, 0.0), "设置节点2约束失败")
    assert_true(controller.set_load(3, 1000.0, 0.0), "设置节点3载荷失败")

    assert_true(controller.solve_model(), f"求解失败：{controller.status_text}")


def main() -> None:
    print("开始测试阶段12：结果导出系统 ...")

    controller = AppController()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        node_csv = tmp_path / "node_results.csv"
        element_csv = tmp_path / "element_results.csv"
        empty_node_csv = tmp_path / "empty_node_results.csv"
        empty_element_csv = tmp_path / "empty_element_results.csv"

        # 1. 没有求解结果时，导出应失败
        assert_false(
            controller.export_node_results_to_csv(str(empty_node_csv)),
            "没有求解结果时不应导出节点结果",
        )
        assert_false(
            controller.export_element_results_to_csv(str(empty_element_csv)),
            "没有求解结果时不应导出单元结果",
        )
        assert_false(empty_node_csv.exists(), "失败导出不应生成节点 CSV")
        assert_false(empty_element_csv.exists(), "失败导出不应生成单元 CSV")
        print("1) 无结果导出拦截通过")

        # 2. 构造并求解一个完整三角形模型
        build_solved_triangle_model(controller)
        assert_true(controller.has_solver_result(), "求解后应存在结果")
        print("2) 求解模型构造通过")

        # 3. 导出节点结果
        assert_true(
            controller.export_node_results_to_csv(str(node_csv)),
            f"导出节点结果失败：{controller.status_text}",
        )
        assert_true(node_csv.exists(), "节点结果 CSV 应存在")

        node_rows = read_csv_rows(node_csv)
        assert_equal(
            node_rows[0],
            ["node_id", "ux", "uy", "displacement_magnitude"],
            "节点结果 CSV 表头不正确",
        )
        assert_equal(len(node_rows), 4, "节点结果 CSV 应包含1行表头和3行节点结果")
        print("3) 节点结果 CSV 导出通过")

        # 4. 导出单元结果
        assert_true(
            controller.export_element_results_to_csv(str(element_csv)),
            f"导出单元结果失败：{controller.status_text}",
        )
        assert_true(element_csv.exists(), "单元结果 CSV 应存在")

        element_rows = read_csv_rows(element_csv)
        assert_equal(
            element_rows[0],
            [
                "element_id",
                "strain_x",
                "strain_y",
                "gamma_xy",
                "stress_x",
                "stress_y",
                "tau_xy",
                "von_mises",
            ],
            "单元结果 CSV 表头不正确",
        )
        assert_equal(len(element_rows), 2, "单元结果 CSV 应包含1行表头和1行单元结果")
        print("4) 单元结果 CSV 导出通过")

    print("\n全部测试通过：阶段12结果导出系统正常。")


if __name__ == "__main__":
    main()
