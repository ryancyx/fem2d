"""
多 CST 单元参考算例对比测试

用途：
1. 用当前 AppController / solver 跑一个双 CST 单元模型；
2. 用本文件内独立 NumPy 公式重新组装整体刚度矩阵并求解；
3. 对比节点位移、单元应变、单元应力、Von Mises 应力；
4. 同时覆盖：多单元组装、共享节点、集中载荷、边界均布载荷等效节点力。

放置位置：tests/test_multi_cst_reference_case.py
运行方式：python tests/test_multi_cst_reference_case.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np


# 允许从 tests/ 目录直接运行时导入项目模块
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.backend.app_controller import AppController  # noqa: E402


# =========================
# 算例定义：两个 CST 单元组成一个 1x1 正方形
# =========================

E = 70_000_000_000.0
NU = 0.25
THICKNESS = 0.02

NODES: Dict[int, Tuple[float, float]] = {
    1: (0.0, 0.0),
    2: (1.0, 0.0),
    3: (1.0, 1.0),
    4: (0.0, 1.0),
}

# 两个单元均为逆时针节点顺序
ELEMENTS: Dict[int, List[int]] = {
    1: [1, 2, 4],
    2: [2, 3, 4],
}

# 左边界固定：节点1、节点4 的 ux/uy 均固定
FIXED_DOF_VALUES: Dict[Tuple[int, str], float] = {
    (1, "ux"): 0.0,
    (1, "uy"): 0.0,
    (4, "ux"): 0.0,
    (4, "uy"): 0.0,
}

# 右侧两个节点施加集中力
NODAL_LOADS: Dict[int, Tuple[float, float]] = {
    2: (500.0, 100.0),
    3: (300.0, -50.0),
}

# 在单元2的边0，即 node_ids[0] -> node_ids[1]，也就是节点2 -> 节点3 上施加边界均布载荷
DISTRIBUTED_LOADS = [
    {
        "element_id": 2,
        "local_edge_index": 0,
        "qx": 8000.0,
        "qy": -3000.0,
    }
]


# =========================
# 工具函数：独立 CST 计算
# =========================

def node_dof_indices(node_id: int) -> Tuple[int, int]:
    base = (node_id - 1) * 2
    return base, base + 1


def element_dof_indices(node_ids: Iterable[int]) -> List[int]:
    indices: List[int] = []
    for node_id in node_ids:
        ux_i, uy_i = node_dof_indices(node_id)
        indices.extend([ux_i, uy_i])
    return indices


def plane_stress_D(E_value: float, nu_value: float) -> np.ndarray:
    factor = E_value / (1.0 - nu_value * nu_value)
    return factor * np.array(
        [
            [1.0, nu_value, 0.0],
            [nu_value, 1.0, 0.0],
            [0.0, 0.0, (1.0 - nu_value) / 2.0],
        ],
        dtype=float,
    )


def cst_B_and_area(coords: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    coords shape = (3, 2)，节点顺序为 i, j, k。
    返回 CST 单元 B 矩阵与面积 A。
    """
    xi, yi = coords[0]
    xj, yj = coords[1]
    xk, yk = coords[2]

    twice_area = (xj - xi) * (yk - yi) - (xk - xi) * (yj - yi)
    area = 0.5 * twice_area
    if area <= 0.0:
        raise ValueError(f"CST 单元面积必须为正，当前 A={area}")

    b_i = yj - yk
    b_j = yk - yi
    b_k = yi - yj

    c_i = xk - xj
    c_j = xi - xk
    c_k = xj - xi

    B = (1.0 / (2.0 * area)) * np.array(
        [
            [b_i, 0.0, b_j, 0.0, b_k, 0.0],
            [0.0, c_i, 0.0, c_j, 0.0, c_k],
            [c_i, b_i, c_j, b_j, c_k, b_k],
        ],
        dtype=float,
    )
    return B, area


def edge_node_ids_for_element(node_ids: List[int], local_edge_index: int) -> Tuple[int, int]:
    if local_edge_index == 0:
        return node_ids[0], node_ids[1]
    if local_edge_index == 1:
        return node_ids[1], node_ids[2]
    if local_edge_index == 2:
        return node_ids[2], node_ids[0]
    raise ValueError("local_edge_index must be 0, 1 or 2")


def add_equivalent_distributed_loads(F: np.ndarray) -> None:
    for item in DISTRIBUTED_LOADS:
        element_id = int(item["element_id"])
        edge_index = int(item["local_edge_index"])
        qx = float(item["qx"])
        qy = float(item["qy"])

        node_ids = ELEMENTS[element_id]
        node_i_id, node_j_id = edge_node_ids_for_element(node_ids, edge_index)
        xi, yi = NODES[node_i_id]
        xj, yj = NODES[node_j_id]
        edge_length = math.hypot(xj - xi, yj - yi)

        half_fx = 0.5 * edge_length * THICKNESS * qx
        half_fy = 0.5 * edge_length * THICKNESS * qy

        for node_id in (node_i_id, node_j_id):
            ux_i, uy_i = node_dof_indices(node_id)
            F[ux_i] += half_fx
            F[uy_i] += half_fy


def build_reference_solution() -> dict:
    node_count = len(NODES)
    dof_count = node_count * 2
    K = np.zeros((dof_count, dof_count), dtype=float)
    F = np.zeros(dof_count, dtype=float)
    D = plane_stress_D(E, NU)

    element_matrices: Dict[int, dict] = {}

    for element_id, node_ids in ELEMENTS.items():
        coords = np.array([NODES[node_id] for node_id in node_ids], dtype=float)
        B, area = cst_B_and_area(coords)
        Ke = THICKNESS * area * (B.T @ D @ B)
        dofs = element_dof_indices(node_ids)

        for local_r, global_r in enumerate(dofs):
            for local_c, global_c in enumerate(dofs):
                K[global_r, global_c] += Ke[local_r, local_c]

        element_matrices[element_id] = {
            "B": B,
            "area": area,
            "node_ids": node_ids,
            "dofs": dofs,
        }

    # 集中节点载荷
    for node_id, (fx, fy) in NODAL_LOADS.items():
        ux_i, uy_i = node_dof_indices(node_id)
        F[ux_i] += fx
        F[uy_i] += fy

    # 边界均布载荷等效节点力
    add_equivalent_distributed_loads(F)

    # 位移边界条件：对角线置 1 法，支持非零约束值
    K_bc = K.copy()
    F_bc = F.copy()
    constrained: Dict[int, float] = {}
    for (node_id, dof_name), value in FIXED_DOF_VALUES.items():
        ux_i, uy_i = node_dof_indices(node_id)
        dof = ux_i if dof_name == "ux" else uy_i
        constrained[dof] = float(value)

    for dof, value in constrained.items():
        for row in range(dof_count):
            if row != dof:
                F_bc[row] -= K_bc[row, dof] * value
        K_bc[dof, :] = 0.0
        K_bc[:, dof] = 0.0
        K_bc[dof, dof] = 1.0
        F_bc[dof] = value

    displacement = np.linalg.solve(K_bc, F_bc)

    element_results = {}
    for element_id, info in element_matrices.items():
        dofs = info["dofs"]
        B = info["B"]
        delta_e = displacement[dofs]
        strain = B @ delta_e
        stress = D @ strain
        von_mises = von_mises_plane_stress(stress[0], stress[1], stress[2])
        element_results[element_id] = {
            "strain": strain,
            "stress": stress,
            "von_mises": von_mises,
        }

    node_displacements = {
        node_id: np.array(displacement[list(node_dof_indices(node_id))], dtype=float)
        for node_id in NODES
    }

    return {
        "K": K,
        "F": F,
        "displacement": displacement,
        "node_displacements": node_displacements,
        "element_results": element_results,
    }


def von_mises_plane_stress(stress_x: float, stress_y: float, tau_xy: float) -> float:
    value = stress_x * stress_x - stress_x * stress_y + stress_y * stress_y + 3.0 * tau_xy * tau_xy
    return math.sqrt(max(value, 0.0))


# =========================
# AppController 建模与结果读取
# =========================

def build_app_case() -> AppController:
    app = AppController()

    for node_id in sorted(NODES):
        x, y = NODES[node_id]
        assert app.add_node_by_coord(x, y), f"添加节点 {node_id} 失败：{app.status_text}"

    assert app.add_material("多单元测试材料", E, NU, THICKNESS, "stress"), app.status_text

    # 用当前 AppController 的单元创建接口创建两个 CST 单元
    for element_id in sorted(ELEMENTS):
        app.clear_element_node_selection()
        for node_id in ELEMENTS[element_id]:
            assert app.toggle_element_node_selection(node_id), app.status_text
        assert app.create_element_from_selected_nodes(), app.status_text

    # 设置约束
    assert app.set_constraint(1, True, True, 0.0, 0.0), app.status_text
    assert app.set_constraint(4, True, True, 0.0, 0.0), app.status_text

    # 设置集中载荷
    for node_id, (fx, fy) in NODAL_LOADS.items():
        assert app.set_load(node_id, fx, fy), app.status_text

    # 设置边界均布载荷
    for item in DISTRIBUTED_LOADS:
        assert app.set_distributed_load(
            int(item["element_id"]),
            int(item["local_edge_index"]),
            float(item["qx"]),
            float(item["qy"]),
        ), app.status_text

    return app


def app_node_displacements(app: AppController) -> Dict[int, np.ndarray]:
    rows = app.get_node_result_rows()
    result: Dict[int, np.ndarray] = {}
    for row in rows:
        result[int(row["node_id"])] = np.array([float(row["ux"]), float(row["uy"])], dtype=float)
    return result


def app_element_results(app: AppController) -> Dict[int, dict]:
    rows = app.get_element_result_rows()
    result: Dict[int, dict] = {}
    for row in rows:
        stress = np.array(
            [
                float(row["stress_x"]),
                float(row["stress_y"]),
                float(row["tau_xy"]),
            ],
            dtype=float,
        )
        strain = np.array(
            [
                float(row["strain_x"]),
                float(row["strain_y"]),
                float(row["gamma_xy"]),
            ],
            dtype=float,
        )
        result[int(row["element_id"])] = {
            "strain": strain,
            "stress": stress,
            "von_mises": von_mises_plane_stress(stress[0], stress[1], stress[2]),
        }
    return result


# =========================
# 对比与输出
# =========================

def assert_close_array(name: str, actual: np.ndarray, expected: np.ndarray, rtol: float = 1e-8, atol: float = 1e-11) -> None:
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        diff = actual - expected
        raise AssertionError(
            f"{name} 不一致\n"
            f"actual   = {actual}\n"
            f"expected = {expected}\n"
            f"diff     = {diff}\n"
        )


def print_node_displacements(title: str, values: Dict[int, np.ndarray]) -> None:
    print(title)
    for node_id in sorted(values):
        ux, uy = values[node_id]
        print(f"  节点 {node_id}: ux={ux:.12e}, uy={uy:.12e}")


def print_element_results(title: str, values: Dict[int, dict]) -> None:
    print(title)
    for element_id in sorted(values):
        strain = values[element_id]["strain"]
        stress = values[element_id]["stress"]
        von_mises = values[element_id]["von_mises"]
        print(
            f"  单元 {element_id}: "
            f"strain=[{strain[0]:.12e}, {strain[1]:.12e}, {strain[2]:.12e}], "
            f"stress=[{stress[0]:.12e}, {stress[1]:.12e}, {stress[2]:.12e}], "
            f"von_mises={von_mises:.12e}"
        )


def main() -> None:
    print("开始测试：多 CST 单元整体求解参考算例 ...")

    app = build_app_case()

    distributed_rows = app.get_distributed_load_rows()
    assert len(distributed_rows) == 1, f"均布载荷记录数量应为 1，当前为 {len(distributed_rows)}"
    assert distributed_rows[0]["node_i_id"] == 2 and distributed_rows[0]["node_j_id"] == 3
    print("1) 多单元模型、集中载荷、均布载荷建模通过")

    assert app.solve_model(), app.status_text
    print("2) AppController / solver 求解成功")

    reference = build_reference_solution()
    print("3) 独立 NumPy CST 参考解计算完成")

    actual_nodes = app_node_displacements(app)
    expected_nodes = reference["node_displacements"]

    for node_id in sorted(NODES):
        assert_close_array(
            f"节点 {node_id} 位移",
            actual_nodes[node_id],
            expected_nodes[node_id],
        )
    print("4) 节点位移与独立参考解一致")

    actual_elements = app_element_results(app)
    expected_elements = reference["element_results"]

    for element_id in sorted(ELEMENTS):
        assert_close_array(
            f"单元 {element_id} 应变",
            actual_elements[element_id]["strain"],
            expected_elements[element_id]["strain"],
        )
        assert_close_array(
            f"单元 {element_id} 应力",
            actual_elements[element_id]["stress"],
            expected_elements[element_id]["stress"],
            rtol=1e-8,
            atol=1e-6,
        )
        actual_vm = actual_elements[element_id]["von_mises"]
        expected_vm = expected_elements[element_id]["von_mises"]
        if not math.isclose(actual_vm, expected_vm, rel_tol=1e-8, abs_tol=1e-6):
            raise AssertionError(
                f"单元 {element_id} Von Mises 不一致：actual={actual_vm}, expected={expected_vm}"
            )
    print("5) 单元应变、应力、Von Mises 与独立参考解一致")

    print()
    print_node_displacements("App 求解节点位移：", actual_nodes)
    print_element_results("App 求解单元结果：", actual_elements)

    print()
    print("全部测试通过：多 CST 单元整体组装、共享节点、集中载荷、均布载荷和后处理结果可靠。")


if __name__ == "__main__":
    main()
