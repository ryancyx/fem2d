"""
CST 单元理论算例对比测试

运行位置：项目根目录
推荐路径：tests/test_cst_reference_case.py
运行命令：python tests/test_cst_reference_case.py

题目：
一个平面应力 CST 三角形单元，节点逆时针排列：
    节点1: (0, 0)
    节点2: (1, 0)
    节点3: (0, 1)
材料：
    E = 210 GPa
    nu = 0.30
    t = 0.01 m
边界条件：
    节点1: ux = 0, uy = 0
    节点2: uy = 0
    节点3: ux = 0
载荷：
    节点2: Fx = 1000 N, Fy = 0
    单元边2，即节点3 -> 节点1: qx = 0, qy = -2000

说明：
边界均布载荷按当前程序定义，在进入求解器前等效为两端节点集中力：
    Fi = 1/2 * l * t * q
    Fj = 1/2 * l * t * q
本脚本会：
1. 用 AppController 调用你的软件求解流程；
2. 用独立 NumPy CST 公式直接计算；
3. 对比节点位移、单元应变、单元应力、Von Mises 应力。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.backend.app_controller import AppController  # noqa: E402


E = 210_000_000_000.0
NU = 0.30
THICKNESS = 0.01


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def von_mises_plane_stress(stress: np.ndarray) -> float:
    sx, sy, txy = [float(x) for x in stress]
    return math.sqrt(max(sx * sx - sx * sy + sy * sy + 3.0 * txy * txy, 0.0))


def build_app_model() -> AppController:
    app = AppController()
    app.new_model()

    # 几何
    assert_true(app.add_node_by_coord(0.0, 0.0), "添加节点1失败")
    assert_true(app.add_node_by_coord(1.0, 0.0), "添加节点2失败")
    assert_true(app.add_node_by_coord(0.0, 1.0), "添加节点3失败")

    # 单元 1-2-3，逆时针
    assert_true(app.toggle_element_node_selection(1), "选择节点1失败")
    assert_true(app.toggle_element_node_selection(2), "选择节点2失败")
    assert_true(app.toggle_element_node_selection(3), "选择节点3失败")
    assert_true(app.create_element_from_selected_nodes(), "创建CST单元失败")

    # 更新默认材料
    assert_true(
        app.update_material(1, "Reference Steel", E, NU, THICKNESS, "stress"),
        "更新材料失败",
    )

    # 边界条件
    assert_true(app.set_constraint(1, True, True, 0.0, 0.0), "节点1约束失败")
    assert_true(app.set_constraint(2, False, True, 0.0, 0.0), "节点2约束失败")
    assert_true(app.set_constraint(3, True, False, 0.0, 0.0), "节点3约束失败")

    # 载荷
    assert_true(app.set_load(2, 1000.0, 0.0), "节点2集中载荷失败")
    assert_true(app.set_distributed_load(1, 2, 0.0, -2000.0), "边2均布载荷失败")

    return app


def independent_cst_solution() -> dict:
    coords = np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        dtype=float,
    )

    xi, yi = coords[0]
    xj, yj = coords[1]
    xk, yk = coords[2]

    signed_twice_area = np.linalg.det(
        np.array(
            [
                [1.0, xi, yi],
                [1.0, xj, yj],
                [1.0, xk, yk],
            ],
            dtype=float,
        )
    )
    area = signed_twice_area / 2.0
    assert_true(area > 0.0, "理论算例单元节点顺序应为逆时针")

    b_i = yj - yk
    b_j = yk - yi
    b_k = yi - yj

    c_i = -xj + xk
    c_j = -xk + xi
    c_k = -xi + xj

    B = (1.0 / (2.0 * area)) * np.array(
        [
            [b_i, 0.0, b_j, 0.0, b_k, 0.0],
            [0.0, c_i, 0.0, c_j, 0.0, c_k],
            [c_i, b_i, c_j, b_j, c_k, b_k],
        ],
        dtype=float,
    )

    D = (E / (1.0 - NU * NU)) * np.array(
        [
            [1.0, NU, 0.0],
            [NU, 1.0, 0.0],
            [0.0, 0.0, (1.0 - NU) / 2.0],
        ],
        dtype=float,
    )

    K = THICKNESS * area * (B.T @ D @ B)

    # 全局载荷向量，DOF 顺序：[u1, v1, u2, v2, u3, v3]
    F = np.zeros(6, dtype=float)

    # 节点2集中力 Fx = 1000
    F[2] += 1000.0

    # 边2：节点3 -> 节点1，长度为1，q = (0, -2000)
    edge_length = 1.0
    half_fx = 0.5 * edge_length * THICKNESS * 0.0
    half_fy = 0.5 * edge_length * THICKNESS * (-2000.0)

    # 节点3贡献
    F[4] += half_fx
    F[5] += half_fy
    # 节点1贡献
    F[0] += half_fx
    F[1] += half_fy

    # 位移边界：u1, v1, v2, u3 固定为0
    fixed_dofs = [0, 1, 3, 4]
    K_mod = K.copy()
    F_mod = F.copy()

    for dof in fixed_dofs:
        # 固定位移为0，因此不需要对其他载荷项扣除 K[:, dof] * value
        K_mod[dof, :] = 0.0
        K_mod[:, dof] = 0.0
        K_mod[dof, dof] = 1.0
        F_mod[dof] = 0.0

    displacement = np.linalg.solve(K_mod, F_mod)
    strain = B @ displacement
    stress = D @ strain
    vm = von_mises_plane_stress(stress)

    return {
        "K": K,
        "F": F,
        "displacement": displacement,
        "strain": strain,
        "stress": stress,
        "von_mises": vm,
    }


def software_solution(app: AppController) -> dict:
    assert_true(app.solve_model(), f"软件求解失败：{app.status_text}")

    node_rows = {int(row["node_id"]): row for row in app.get_node_result_rows()}
    element_rows = {int(row["element_id"]): row for row in app.get_element_result_rows()}

    displacement = np.array(
        [
            node_rows[1]["ux"],
            node_rows[1]["uy"],
            node_rows[2]["ux"],
            node_rows[2]["uy"],
            node_rows[3]["ux"],
            node_rows[3]["uy"],
        ],
        dtype=float,
    )

    element = element_rows[1]
    strain = np.array(
        [
            element["strain_x"],
            element["strain_y"],
            element["gamma_xy"],
        ],
        dtype=float,
    )
    stress = np.array(
        [
            element["stress_x"],
            element["stress_y"],
            element["tau_xy"],
        ],
        dtype=float,
    )
    vm = von_mises_plane_stress(stress)

    return {
        "displacement": displacement,
        "strain": strain,
        "stress": stress,
        "von_mises": vm,
    }


def print_vector(name: str, value: np.ndarray) -> None:
    text = np.array2string(value, precision=12, suppress_small=False)
    print(f"{name}: {text}")


def compare_results(expected: dict, actual: dict) -> None:
    print("\n=== 独立理论计算结果 ===")
    print_vector("节点位移 [u1, v1, u2, v2, u3, v3]", expected["displacement"])
    print_vector("单元应变 [eps_x, eps_y, gamma_xy]", expected["strain"])
    print_vector("单元应力 [sigma_x, sigma_y, tau_xy]", expected["stress"])
    print(f"Von Mises: {expected['von_mises']:.12e}")

    print("\n=== 软件求解结果 ===")
    print_vector("节点位移 [u1, v1, u2, v2, u3, v3]", actual["displacement"])
    print_vector("单元应变 [eps_x, eps_y, gamma_xy]", actual["strain"])
    print_vector("单元应力 [sigma_x, sigma_y, tau_xy]", actual["stress"])
    print(f"Von Mises: {actual['von_mises']:.12e}")

    np.testing.assert_allclose(
        actual["displacement"],
        expected["displacement"],
        rtol=1e-9,
        atol=1e-12,
        err_msg="节点位移与独立CST计算不一致",
    )
    np.testing.assert_allclose(
        actual["strain"],
        expected["strain"],
        rtol=1e-9,
        atol=1e-12,
        err_msg="单元应变与独立CST计算不一致",
    )
    np.testing.assert_allclose(
        actual["stress"],
        expected["stress"],
        rtol=1e-9,
        atol=1e-6,
        err_msg="单元应力与独立CST计算不一致",
    )
    np.testing.assert_allclose(
        actual["von_mises"],
        expected["von_mises"],
        rtol=1e-9,
        atol=1e-6,
        err_msg="Von Mises 应力与独立CST计算不一致",
    )


def main() -> None:
    print("开始 CST 单元理论算例对比测试 ...")
    print("题目：单个右三角形 CST 单元，含集中载荷与边界均布载荷。")

    app = build_app_model()
    expected = independent_cst_solution()
    actual = software_solution(app)
    compare_results(expected, actual)

    print("\n全部通过：软件求解结果与独立 CST 理论计算结果一致。")


if __name__ == "__main__":
    main()
