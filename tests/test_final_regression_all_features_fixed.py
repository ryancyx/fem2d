"""
FEM2D Studio 最终功能回归测试

运行位置：项目根目录
推荐路径：tests/test_final_regression_all_features.py
运行命令：python tests/test_final_regression_all_features.py

说明：
1. 本测试主要覆盖 AppController 后端主流程与数据导出：
   - 节点 / 单元 / 材料
   - 材料颜色字段
   - 约束 / 集中载荷
   - 边界均布载荷记录与等效求解
   - 求解结果生成
   - 节点 / 单元 CSV 导出
   - 工程保存 / 打开
   - 模型修改后结果失效
2. QML 里的红框、红箭头、云图窗口、PNG 云图导出属于界面渲染层，
   建议继续用人工测试确认；本脚本负责确认其依赖的数据接口正常。
"""

from __future__ import annotations

import csv
import math
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.backend.app_controller import AppController  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_close(a: float, b: float, tol: float = 1e-9, message: str = "") -> None:
    if abs(a - b) > tol:
        raise AssertionError(message or f"数值不一致：{a} != {b}")


def assert_finite(value: float, message: str) -> None:
    if not math.isfinite(float(value)):
        raise AssertionError(message)


def create_square_two_triangle_model(app: AppController) -> None:
    """创建一个两三角形方形模型，用于综合回归测试。"""
    app.new_model()

    # 节点：正方形四角
    assert_true(app.add_node_by_coord(0.0, 0.0), "添加节点1失败")
    assert_true(app.add_node_by_coord(1.0, 0.0), "添加节点2失败")
    assert_true(app.add_node_by_coord(0.0, 1.0), "添加节点3失败")
    assert_true(app.add_node_by_coord(1.0, 1.0), "添加节点4失败")

    assert_true(app.node_count == 4, "节点数量应为4")

    # 单元1：1-2-3，逆时针
    assert_true(app.toggle_element_node_selection(1), "选择单元1节点1失败")
    assert_true(app.toggle_element_node_selection(2), "选择单元1节点2失败")
    assert_true(app.toggle_element_node_selection(3), "选择单元1节点3失败")
    assert_true(app.create_element_from_selected_nodes(), "创建单元1失败")

    # 单元2：2-4-3，逆时针
    assert_true(app.toggle_element_node_selection(2), "选择单元2节点2失败")
    assert_true(app.toggle_element_node_selection(4), "选择单元2节点4失败")
    assert_true(app.toggle_element_node_selection(3), "选择单元2节点3失败")
    assert_true(app.create_element_from_selected_nodes(), "创建单元2失败")

    assert_true(app.element_count == 2, "单元数量应为2")

    # 默认材料由创建单元时自动创建，更新为钢材参数。
    assert_true(
        app.update_material(1, "测试钢材", 210_000_000_000.0, 0.30, 0.01, "stress"),
        "更新默认材料失败",
    )

    # 添加第二种材料并分配给单元2。
    assert_true(
        app.add_material("测试铝材", 70_000_000_000.0, 0.33, 0.01, "stress"),
        "添加第二种材料失败",
    )
    assert_true(app.material_count == 2, "材料数量应为2")
    assert_true(app.assign_material_to_element(2, 2), "给单元2分配材料失败")


def test_material_color_rows(app: AppController) -> None:
    material_rows = app.get_material_rows()
    element_rows = app.get_element_rows()

    assert_true(len(material_rows) == 2, "材料行数量应为2")
    assert_true(len(element_rows) == 2, "单元行数量应为2")

    for row in material_rows:
        assert_true("color" in row, "材料行缺少 color 字段")
        assert_true(str(row["color"]).startswith("#"), "材料颜色应为 #RRGGBB 格式")

    for row in element_rows:
        assert_true("fill_color" in row, "单元行缺少 fill_color 字段")
        assert_true("selected_fill_color" in row, "单元行缺少 selected_fill_color 字段")
        assert_true(str(row["fill_color"]).startswith("#"), "单元填充色格式异常")

    print("1) 材料颜色与单元颜色数据接口通过")


def test_boundary_conditions_and_loads(app: AppController) -> None:
    # 约束：固定左下角，限制右下角 y，限制左上角 x。
    assert_true(app.set_constraint(1, True, True, 0.0, 0.0), "设置节点1约束失败")
    assert_true(app.set_constraint(2, False, True, 0.0, 0.0), "设置节点2约束失败")
    assert_true(app.set_constraint(3, True, False, 0.0, 0.0), "设置节点3约束失败")

    constraint_rows = app.get_constraint_rows()
    assert_true(len(constraint_rows) == 3, "约束数量应为3")
    assert_true(any(row["node_id"] == 1 and row["ux_fixed"] and row["uy_fixed"] for row in constraint_rows), "节点1约束异常")

    # 集中载荷：右上角施加斜向力。
    assert_true(app.set_load(4, 1000.0, -500.0), "设置节点4集中载荷失败")
    load_rows = app.get_load_rows()
    assert_true(len(load_rows) == 1, "集中载荷数量应为1")
    assert_true(load_rows[0]["node_id"] == 4, "集中载荷节点应为4")

    # 均布载荷：单元2的边0，也就是节点2 -> 节点4。
    assert_true(app.set_distributed_load(2, 0, 0.0, -1000.0), "设置边界均布载荷失败")
    distributed_rows = app.get_distributed_load_rows()
    assert_true(len(distributed_rows) == 1, "均布载荷数量应为1")
    row = distributed_rows[0]
    assert_true(row["element_id"] == 2, "均布载荷单元编号应为2")
    assert_true(row["local_edge_index"] == 0, "均布载荷边编号应为0")
    assert_true(row["node_i_id"] == 2 and row["node_j_id"] == 4, "均布载荷起终点节点应为2->4")
    assert_close(row["qy"], -1000.0, message="均布载荷 qy 异常")

    # 非法均布载荷：qx/qy 同时为0，应拒绝。
    assert_true(not app.set_distributed_load(2, 1, 0.0, 0.0), "qx/qy 同时为0时应拒绝")

    print("2) 约束、集中载荷、边界均布载荷接口通过")


def test_solver_and_exports(app: AppController, temp_dir: Path) -> None:
    assert_true(app.solve_model(), f"求解失败：{app.status_text}")
    assert_true(app.has_solver_result(), "求解后应存在结果")
    assert_true(app.current_mode == "result", "求解成功后模式应为 result")

    node_result_rows = app.get_node_result_rows()
    element_result_rows = app.get_element_result_rows()
    assert_true(len(node_result_rows) == 4, "节点结果数量应为4")
    assert_true(len(element_result_rows) == 2, "单元结果数量应为2")

    for row in node_result_rows:
        assert_finite(row["ux"], f"节点{row['node_id']} ux 非有限数")
        assert_finite(row["uy"], f"节点{row['node_id']} uy 非有限数")

    for row in element_result_rows:
        for key in ["strain_x", "strain_y", "gamma_xy", "stress_x", "stress_y", "tau_xy"]:
            assert_finite(row[key], f"单元{row['element_id']} {key} 非有限数")

    node_csv = temp_dir / "node_results.csv"
    element_csv = temp_dir / "element_results.csv"
    assert_true(app.export_node_results_to_csv(str(node_csv)), "导出节点结果CSV失败")
    assert_true(app.export_element_results_to_csv(str(element_csv)), "导出单元结果CSV失败")
    assert_true(node_csv.exists() and node_csv.stat().st_size > 0, "节点结果CSV未生成")
    assert_true(element_csv.exists() and element_csv.stat().st_size > 0, "单元结果CSV未生成")

    with node_csv.open("r", encoding="utf-8-sig", newline="") as f:
        header = next(csv.reader(f))
        assert_true(header == ["node_id", "ux", "uy", "displacement_magnitude"], "节点CSV表头异常")

    with element_csv.open("r", encoding="utf-8-sig", newline="") as f:
        header = next(csv.reader(f))
        assert_true("von_mises" in header, "单元CSV表头应包含 von_mises")

    print("3) 求解、节点结果导出、单元结果导出通过")


def test_project_save_load(app: AppController, temp_dir: Path) -> None:
    project_path = temp_dir / "regression_project.json"
    assert_true(app.save_project_to_file(str(project_path)), "保存工程失败")
    assert_true(project_path.exists() and project_path.stat().st_size > 0, "工程文件未生成")

    loaded = AppController()
    assert_true(loaded.load_project_from_file(str(project_path)), f"打开工程失败：{loaded.status_text}")

    assert_true(loaded.node_count == 4, "打开工程后节点数量应为4")
    assert_true(loaded.element_count == 2, "打开工程后单元数量应为2")
    assert_true(loaded.material_count == 2, "打开工程后材料数量应为2")
    assert_true(loaded.constraint_count == 3, "打开工程后约束数量应为3")
    assert_true(loaded.load_count == 2, "打开工程后载荷总数应为2：1个集中载荷 + 1个均布载荷")
    assert_true(len(loaded.get_distributed_load_rows()) == 1, "打开工程后均布载荷应恢复")

    assert_true(loaded.solve_model(), f"打开工程后重新求解失败：{loaded.status_text}")
    assert_true(len(loaded.get_node_result_rows()) == 4, "打开工程后节点结果数量异常")
    assert_true(len(loaded.get_element_result_rows()) == 2, "打开工程后单元结果数量异常")

    print("4) 工程保存、打开、均布载荷恢复、重新求解通过")


def test_result_invalidation(app: AppController) -> None:
    assert_true(app.has_solver_result(), "失效测试前应已有求解结果")
    assert_true(app.add_node_by_coord(2.0, 2.0), "添加节点用于结果失效测试失败")
    assert_true(not app.has_solver_result(), "模型修改后求解结果应失效")
    # 当前 AppController 的设计是：模型修改后必须清除旧求解结果；
    # 但 current_mode 会根据具体操作保持为 node / element / edit，
    # 例如 add_node_by_coord() 会把模式切到 node。
    # 因此这里不强制要求 current_mode == "edit"，只要求不再停留在 result。
    assert_true(app.current_mode != "result", "模型修改后不应继续停留在 result 模式")
    assert_true(app.current_mode in {"node", "element", "edit", "none"}, "模型修改后模式应处于可编辑相关状态")
    print("5) 模型修改后结果失效逻辑通过")


def main() -> None:
    print("开始最终功能回归测试 ...")
    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        app = AppController()

        create_square_two_triangle_model(app)
        test_material_color_rows(app)
        test_boundary_conditions_and_loads(app)
        test_solver_and_exports(app, temp_dir)
        test_project_save_load(app, temp_dir)
        test_result_invalidation(app)

    print("\n全部通过：FEM2D Studio 当前核心功能回归测试正常。")


if __name__ == "__main__":
    main()
