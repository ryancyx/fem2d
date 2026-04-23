from __future__ import annotations

import numpy as np

from model.fem_model import FEMModel, Node, Element, Material, Constraint, Load
from solver.assembler import (
    build_node_id_to_index_map,
    build_node_id_to_node_map,
    build_material_id_to_material_map,
    get_element_coords,
    element_dof_indices,
    assemble_global_stiffness,
    assemble_global_load_vector,
)
from solver.cst_element import element_stiffness


def assert_close(actual, expected, rtol=1e-9, atol=1e-9, message=""):
    """封装 np.allclose，方便测试失败时打印更清楚的信息。"""
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        raise AssertionError(
            f"{message}\n"
            f"实际值 actual =\n{actual}\n\n"
            f"期望值 expected =\n{expected}"
        )


def build_test_model() -> FEMModel:
    """
    构造一个两单元测试模型。
    节点编号故意不连续，用来验证 node_id -> index 映射是否正确。

    节点：
        10 -> (0, 0)
        20 -> (1, 0)
        30 -> (0, 1)
        40 -> (1, 1)

    单元：
        e1 = [10, 20, 30]
        e2 = [20, 40, 30]

    两个三角形拼成一个正方形，并共享边 (20, 30)。
    """
    return FEMModel(
        nodes=[
            Node(id=10, x=0.0, y=0.0),
            Node(id=20, x=1.0, y=0.0),
            Node(id=30, x=0.0, y=1.0),
            Node(id=40, x=1.0, y=1.0),
        ],
        elements=[
            Element(id=1, node_ids=[10, 20, 30], material_id=100, element_type="CST"),
            Element(id=2, node_ids=[20, 40, 30], material_id=100, element_type="CST"),
        ],
        materials=[
            Material(
                id=100,
                name="Steel",
                young_modulus=210e9,
                poisson_ratio=0.3,
                thickness=0.01,
                plane_mode="stress",
            ),
        ],
        constraints=[],
        loads=[
            Load(id=1, node_id=20, fx=100.0, fy=-50.0, load_type="nodal"),
            Load(id=2, node_id=30, fx=0.0, fy=-200.0, load_type="nodal"),
            Load(id=3, node_id=20, fx=25.0, fy=10.0, load_type="nodal"),
        ],
    )


def manually_assemble_expected_K(model: FEMModel) -> np.ndarray:
    """
    手动按映射关系装配整体刚度矩阵，用来作为 assemble_global_stiffness 的对照答案。
    这里“手动”的意思是：
    - 自己先算每个单元的 Ke
    - 自己按 dof 映射叠加到 K_expected
    """
    node_id_to_index = build_node_id_to_index_map(model)
    node_id_to_node = build_node_id_to_node_map(model)
    material_id_to_material = build_material_id_to_material_map(model)

    total_dofs = 2 * len(model.nodes)
    K_expected = np.zeros((total_dofs, total_dofs), dtype=np.float64)

    for element in model.elements:
        material = material_id_to_material[element.material_id]
        coords = get_element_coords(element, node_id_to_node)
        dofs = element_dof_indices(element, node_id_to_index)

        Ke = element_stiffness(
            coords=coords,
            E=material.young_modulus,
            nu=material.poisson_ratio,
            thickness=material.thickness,
            plane_mode=material.plane_mode,
        )

        for i_local, i_global in enumerate(dofs):
            for j_local, j_global in enumerate(dofs):
                K_expected[i_global, j_global] += Ke[i_local, j_local]

    return K_expected


def main() -> None:
    model = build_test_model()

    print("开始测试 assembler 核心功能 ...\n")

    # --------------------------------------------------
    # 1. 测试 节点ID -> 顺序索引 映射
    # --------------------------------------------------
    node_id_to_index = build_node_id_to_index_map(model)
    expected_node_id_to_index = {
        10: 0,
        20: 1,
        30: 2,
        40: 3,
    }
    assert node_id_to_index == expected_node_id_to_index, (
        f"build_node_id_to_index_map 错误。\n"
        f"实际值 = {node_id_to_index}\n"
        f"期望值 = {expected_node_id_to_index}"
    )
    print("1) build_node_id_to_index_map 通过")

    # --------------------------------------------------
    # 2. 测试 节点ID -> 节点对象 映射
    # --------------------------------------------------
    node_id_to_node = build_node_id_to_node_map(model)
    assert node_id_to_node[10].x == 0.0 and node_id_to_node[10].y == 0.0
    assert node_id_to_node[40].x == 1.0 and node_id_to_node[40].y == 1.0
    print("2) build_node_id_to_node_map 通过")

    # --------------------------------------------------
    # 3. 测试 材料ID -> 材料对象 映射
    # --------------------------------------------------
    material_id_to_material = build_material_id_to_material_map(model)
    assert material_id_to_material[100].young_modulus == 210e9
    assert material_id_to_material[100].poisson_ratio == 0.3
    print("3) build_material_id_to_material_map 通过")

    # --------------------------------------------------
    # 4. 测试单元坐标提取
    # 第一个单元 e1 = [10, 20, 30]
    # --------------------------------------------------
    e1 = model.elements[0]
    coords_e1 = get_element_coords(e1, node_id_to_node)
    expected_coords_e1 = np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        dtype=np.float64,
    )
    assert_close(coords_e1, expected_coords_e1, atol=1e-12, message="get_element_coords(e1) 错误")
    print("4) get_element_coords 通过")

    # --------------------------------------------------
    # 5. 测试单元自由度编号
    # 节点顺序索引:
    #   10 -> 0
    #   20 -> 1
    #   30 -> 2
    #   40 -> 3
    #
    # 所以:
    #   e1 = [10,20,30] -> [0,1,2,3,4,5]
    #   e2 = [20,40,30] -> [2,3,6,7,4,5]
    # --------------------------------------------------
    e2 = model.elements[1]

    dofs_e1 = element_dof_indices(e1, node_id_to_index)
    dofs_e2 = element_dof_indices(e2, node_id_to_index)

    assert dofs_e1 == [0, 1, 2, 3, 4, 5], f"element_dof_indices(e1) 错误: {dofs_e1}"
    assert dofs_e2 == [2, 3, 6, 7, 4, 5], f"element_dof_indices(e2) 错误: {dofs_e2}"
    print("5) element_dof_indices 通过")

    # --------------------------------------------------
    # 6. 测试整体刚度矩阵装配
    # --------------------------------------------------
    K_actual = assemble_global_stiffness(model)
    K_expected = manually_assemble_expected_K(model)

    assert K_actual.shape == (8, 8), f"整体刚度矩阵形状错误: {K_actual.shape}"
    assert_close(
        K_actual,
        K_expected,
        rtol=1e-9,
        atol=1e-3,
        message="assemble_global_stiffness 结果错误",
    )
    print("6) assemble_global_stiffness 数值装配通过")

    # --------------------------------------------------
    # 7. 测试整体刚度矩阵对称性
    # --------------------------------------------------
    assert_close(K_actual, K_actual.T, atol=1e-6, message="整体刚度矩阵 K 不对称")
    print("7) 整体刚度矩阵对称性通过")

    # --------------------------------------------------
    # 8. 测试整体载荷向量组装
    #
    # 载荷:
    #   node 20: (100, -50)
    #   node 30: (0, -200)
    #   node 20: (25, 10)
    #
    # 节点索引:
    #   20 -> 1 -> dof [2, 3]
    #   30 -> 2 -> dof [4, 5]
    #
    # 所以总载荷向量应为:
    #   [0, 0, 125, -40, 0, -200, 0, 0]
    # --------------------------------------------------
    F_actual = assemble_global_load_vector(model)
    F_expected = np.array([0.0, 0.0, 125.0, -40.0, 0.0, -200.0, 0.0, 0.0], dtype=np.float64)

    assert F_actual.shape == (8,), f"整体载荷向量形状错误: {F_actual.shape}"
    assert_close(F_actual, F_expected, atol=1e-12, message="assemble_global_load_vector 结果错误")
    print("8) assemble_global_load_vector 通过")

    print("\n全部测试通过：assembler.py 的映射、自由度编号、整体刚度装配、整体载荷组装均正确。")


if __name__ == "__main__":
    main()