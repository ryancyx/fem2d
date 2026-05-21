"""
test_distributed_load_current_controller.py

用途：
    基于当前版本 ui/backend/app_controller.py 与 main.qml 中实际使用的接口，
    测试“边界均布载荷”的数据记录、QML 调用接口、等效节点力计算与清除逻辑。

放置位置：
    tests/test_distributed_load_current_controller.py

运行方式：
    在项目根目录运行：
        python tests/test_distributed_load_current_controller.py

说明：
    本测试不加载 QML 界面，但严格使用 main.qml 当前调用的 AppController 接口：
        - set_selected_element_distributed_load_by_text(...)
        - get_selected_element_distributed_load_info(...)
        - get_distributed_load_rows()
        - clear_selected_element_distributed_load(...)
    同时调用 AppController 内部的 _build_solver_model_with_distributed_loads()
    来验证均布载荷是否被正确等效成节点集中力。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.backend.app_controller import AppController  # noqa: E402


def assert_close(actual: float, expected: float, name: str, rel_tol: float = 1e-9, abs_tol: float = 1e-9) -> None:
    if not math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol):
        raise AssertionError(f"{name} 不正确：actual={actual}, expected={expected}")


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def build_basic_controller() -> AppController:
    """
    建立一个最小三角形模型：

        node 3: (0, 100)
          *
          |\
          | \
          |  \
          *---*
        node1  node2
       (0,0) (100,0)

    单元 1 的边编号与当前 AppController 定义一致：
        edge 0: node_ids[0] -> node_ids[1]，即 1 -> 2
        edge 1: node_ids[1] -> node_ids[2]，即 2 -> 3
        edge 2: node_ids[2] -> node_ids[0]，即 3 -> 1
    """
    app = AppController()

    assert_true(app.add_node_by_coord(0.0, 0.0), "添加节点 1 失败")
    assert_true(app.add_node_by_coord(100.0, 0.0), "添加节点 2 失败")
    assert_true(app.add_node_by_coord(0.0, 100.0), "添加节点 3 失败")

    assert_true(app.toggle_element_node_selection(1), "选择单元节点 1 失败")
    assert_true(app.toggle_element_node_selection(2), "选择单元节点 2 失败")
    assert_true(app.toggle_element_node_selection(3), "选择单元节点 3 失败")
    assert_true(app.create_element_from_selected_nodes(), "创建三角形单元失败")

    assert_true(app.selected_element_exists, "创建单元后应自动选中该单元")
    assert_true(app.selected_element_id == 1, "当前测试假设第一个单元 id 为 1")
    assert_true(app.material_count == 1, "创建单元时应自动创建默认材料")

    return app


def sum_loads_by_node(solver_model) -> dict[int, tuple[float, float]]:
    """
    把 solver_model.loads 中的载荷按节点编号求和。
    这样即使后续同一节点上有多个等效节点力，本测试也能稳定检查总量。
    """
    result: dict[int, list[float]] = {}

    for load in solver_model.loads:
        node_id = int(load.node_id)
        if node_id not in result:
            result[node_id] = [0.0, 0.0]
        result[node_id][0] += float(load.fx)
        result[node_id][1] += float(load.fy)

    return {node_id: (values[0], values[1]) for node_id, values in result.items()}


def test_qml_exposed_api_exists(app: AppController) -> None:
    """
    检查 main.qml 当前依赖的 AppController 接口是否存在。
    这一步能提前发现“QML 还在调用旧接口，但 Python 后端改名了”的问题。
    """
    required_methods = [
        "get_distributed_load_rows",
        "get_selected_element_distributed_load_info",
        "set_selected_element_distributed_load_by_text",
        "clear_selected_element_distributed_load",
    ]

    for method_name in required_methods:
        method = getattr(app, method_name, None)
        if method is None or not callable(method):
            raise AssertionError(f"缺少 QML 所需接口：{method_name}")


def test_edge0_downward_load(app: AppController) -> None:
    """
    测试 edge 0: node 1 -> node 2，长度 l = 100，默认厚度 t = 0.01。
    qx = 0, qy = -1000。

    根据公式：
        每个端点 Fy = 1/2 * l * t * qy
                  = 0.5 * 100 * 0.01 * (-1000)
                  = -500
    """
    assert_true(
        app.set_selected_element_distributed_load_by_text(0, "0", "-1000"),
        f"设置 edge 0 向下均布载荷失败：{app.status_text}",
    )

    rows = app.get_distributed_load_rows()
    assert_true(len(rows) == 1, f"应有 1 条均布载荷记录，实际为 {len(rows)}")
    row = rows[0]

    assert_true(row["element_id"] == 1, "均布载荷 element_id 应为 1")
    assert_true(row["local_edge_index"] == 0, "均布载荷边编号应为 0")
    assert_true(row["node_i_id"] == 1 and row["node_j_id"] == 2, "edge 0 应对应节点 1 -> 2")
    assert_close(float(row["qx"]), 0.0, "edge 0 qx")
    assert_close(float(row["qy"]), -1000.0, "edge 0 qy")

    info = app.get_selected_element_distributed_load_info(0)
    assert_true(info["has_load"] is True, "edge 0 应显示已有均布载荷")
    assert_true(info["node_i_id"] == 1 and info["node_j_id"] == 2, "edge 0 编辑信息中的起终点节点错误")
    assert_close(float(info["qx"]), 0.0, "edge 0 编辑信息 qx")
    assert_close(float(info["qy"]), -1000.0, "edge 0 编辑信息 qy")

    solver_model = app._build_solver_model_with_distributed_loads()
    load_sum = sum_loads_by_node(solver_model)

    assert_true(set(load_sum.keys()) == {1, 2}, f"edge 0 等效节点应为 1、2，实际为 {sorted(load_sum.keys())}")
    assert_close(load_sum[1][0], 0.0, "node 1 Fx")
    assert_close(load_sum[1][1], -500.0, "node 1 Fy")
    assert_close(load_sum[2][0], 0.0, "node 2 Fx")
    assert_close(load_sum[2][1], -500.0, "node 2 Fy")


def test_edge1_horizontal_load_after_clear_edge0(app: AppController) -> None:
    """
    先清除 edge 0，再测试 edge 1: node 2 -> node 3。
    node2=(100,0)，node3=(0,100)，边长 l=sqrt(100^2+100^2)。

    qx = 2000, qy = 0，默认厚度 t = 0.01。

    每个端点 Fx = 1/2 * l * t * qx
                = 0.5 * sqrt(20000) * 0.01 * 2000
                = sqrt(20000) * 10
                ≈ 1414.213562
    """
    assert_true(
        app.clear_selected_element_distributed_load(0),
        f"清除 edge 0 均布载荷失败：{app.status_text}",
    )

    assert_true(len(app.get_distributed_load_rows()) == 0, "清除 edge 0 后，均布载荷列表应为空")

    assert_true(
        app.set_selected_element_distributed_load_by_text(1, "2000", "0"),
        f"设置 edge 1 水平均布载荷失败：{app.status_text}",
    )

    rows = app.get_distributed_load_rows()
    assert_true(len(rows) == 1, f"应有 1 条均布载荷记录，实际为 {len(rows)}")
    row = rows[0]

    assert_true(row["local_edge_index"] == 1, "均布载荷边编号应为 1")
    assert_true(row["node_i_id"] == 2 and row["node_j_id"] == 3, "edge 1 应对应节点 2 -> 3")
    assert_close(float(row["qx"]), 2000.0, "edge 1 qx")
    assert_close(float(row["qy"]), 0.0, "edge 1 qy")

    expected_fx_each = 0.5 * math.hypot(100.0, 100.0) * 0.01 * 2000.0

    solver_model = app._build_solver_model_with_distributed_loads()
    load_sum = sum_loads_by_node(solver_model)

    assert_true(set(load_sum.keys()) == {2, 3}, f"edge 1 等效节点应为 2、3，实际为 {sorted(load_sum.keys())}")
    assert_close(load_sum[2][0], expected_fx_each, "node 2 Fx")
    assert_close(load_sum[2][1], 0.0, "node 2 Fy")
    assert_close(load_sum[3][0], expected_fx_each, "node 3 Fx")
    assert_close(load_sum[3][1], 0.0, "node 3 Fy")


def test_reject_zero_distributed_load(app: AppController) -> None:
    """
    qx 和 qy 同时为 0 应被拒绝。
    当前 AppController.set_distributed_load 中明确禁止 qx 与 qy 同时为 0。
    """
    old_rows = app.get_distributed_load_rows()

    ok = app.set_selected_element_distributed_load_by_text(2, "0", "0")
    assert_true(ok is False, "qx=qy=0 的均布载荷应被拒绝")

    new_rows = app.get_distributed_load_rows()
    assert_true(new_rows == old_rows, "被拒绝的零均布载荷不应改变已有均布载荷列表")


def test_clear_remaining_load(app: AppController) -> None:
    """
    清除 edge 1 后，均布载荷列表应为空；
    再构造 solver_model 时，不应产生任何等效节点载荷。
    """
    assert_true(
        app.clear_selected_element_distributed_load(1),
        f"清除 edge 1 均布载荷失败：{app.status_text}",
    )

    rows = app.get_distributed_load_rows()
    assert_true(len(rows) == 0, f"清除后均布载荷列表应为空，实际为 {len(rows)}")

    solver_model = app._build_solver_model_with_distributed_loads()
    assert_true(len(solver_model.loads) == 0, "清除全部均布载荷后，不应生成等效节点载荷")


def main() -> None:
    # 给 PySide6 的 QObject/Signal 一个最小 Qt Core 环境，便于 PyCharm 直接运行。
    qt_app = QCoreApplication.instance()
    if qt_app is None:
        qt_app = QCoreApplication([])

    print("开始测试：基于当前 AppController/QML 接口的边界均布载荷功能 ...")

    app = build_basic_controller()

    test_qml_exposed_api_exists(app)
    print("1) QML 依赖接口存在性检查通过")

    test_edge0_downward_load(app)
    print("2) edge 0 向下均布载荷记录与等效节点力通过")

    test_edge1_horizontal_load_after_clear_edge0(app)
    print("3) edge 1 水平均布载荷记录与等效节点力通过")

    test_reject_zero_distributed_load(app)
    print("4) qx/qy 同时为 0 的非法输入拒绝逻辑通过")

    test_clear_remaining_load(app)
    print("5) 均布载荷清除逻辑通过")

    print()
    print("全部测试通过：当前 AppController/QML 接口下，边界均布载荷功能正常。")


if __name__ == "__main__":
    main()
