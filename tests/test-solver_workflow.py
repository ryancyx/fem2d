from __future__ import annotations

import numpy as np

from model.fem_model import Constraint, Element, FEMModel, Load, Material, Node
from solver.solver import solve_linear_static


def main() -> None:
    print("开始测试 solver 总流程 ...\n")

    model = FEMModel(
        nodes=[
            Node(id=1, x=0.0, y=0.0),
            Node(id=2, x=1.0, y=0.0),
            Node(id=3, x=0.0, y=1.0),
        ],
        elements=[
            Element(id=1, node_ids=[1, 2, 3], material_id=1, element_type="CST"),
        ],
        materials=[
            Material(
                id=1,
                name="Steel",
                young_modulus=210e9,
                poisson_ratio=0.3,
                thickness=0.01,
                plane_mode="stress",
            ),
        ],
        constraints=[
            Constraint(
                id=1,
                node_id=1,
                ux_fixed=True,
                uy_fixed=True,
                ux_value=0.0,
                uy_value=0.0,
            ),
            Constraint(
                id=2,
                node_id=2,
                ux_fixed=False,
                uy_fixed=True,
                ux_value=0.0,
                uy_value=0.0,
            ),
        ],
        loads=[
            Load(
                id=1,
                node_id=3,
                fx=1000.0,
                fy=0.0,
                load_type="nodal",
            ),
        ],
    )

    result = solve_linear_static(model)

    np.set_printoptions(precision=6, suppress=True)

    print("=== 原始整体刚度矩阵 K ===")
    print(result.global_stiffness)
    print()

    print("=== 原始整体载荷向量 F ===")
    print(result.global_load)
    print()

    print("=== 约束后整体刚度矩阵 K_bc ===")
    print(result.constrained_stiffness)
    print()

    print("=== 约束后整体载荷向量 F_bc ===")
    print(result.constrained_load)
    print()

    print("=== 整体位移向量 u ===")
    print(result.displacement)
    print()

    print("=== 节点位移 ===")
    for node_id, (ux, uy) in result.node_displacements.items():
        print(f"Node {node_id}: ux={ux:.12e}, uy={uy:.12e}")
    print()

    print("=== 单元结果 ===")
    for elem_result in result.element_results:
        print(f"Element {elem_result.element_id}")
        print("u_e =", elem_result.displacement_vector)
        print("strain =", elem_result.strain)
        print("stress =", elem_result.stress)
        print()

    # -----------------------------
    # 基本正确性检查
    # -----------------------------
    assert result.global_stiffness.shape == (6, 6)
    assert result.global_load.shape == (6,)
    assert result.constrained_stiffness.shape == (6, 6)
    assert result.constrained_load.shape == (6,)
    assert result.displacement.shape == (6,)

    # 约束自由度应满足：
    # node 1: ux = 0, uy = 0
    # node 2: uy = 0
    assert np.isclose(result.node_displacements[1][0], 0.0)
    assert np.isclose(result.node_displacements[1][1], 0.0)
    assert np.isclose(result.node_displacements[2][1], 0.0)

    # 应至少有 1 个单元结果
    assert len(result.element_results) == 1

    # 应变和应力都应为有限值
    elem_result = result.element_results[0]
    assert np.all(np.isfinite(elem_result.strain))
    assert np.all(np.isfinite(elem_result.stress))

    print("测试通过：solver 总流程可运行，结果结构正确。")


if __name__ == "__main__":
    main()