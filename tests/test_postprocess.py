from __future__ import annotations

import numpy as np

from model.fem_model import FEMModel, Node, Element, Material
from solver.postprocess import (
    extract_element_displacement_vector,
    compute_element_result,
    compute_all_element_results,
    extract_node_displacements,
)
from solver.assembler import (
    build_node_id_to_index_map,
    build_node_id_to_node_map,
)


def assert_close(actual, expected, rtol=1e-9, atol=1e-9, message=""):
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        raise AssertionError(
            f"{message}\n"
            f"实际值 actual =\n{actual}\n\n"
            f"期望值 expected =\n{expected}"
        )


def build_test_model() -> FEMModel:
    return FEMModel(
        nodes=[
            Node(id=10, x=0.0, y=0.0),
            Node(id=20, x=1.0, y=0.0),
            Node(id=30, x=0.0, y=1.0),
        ],
        elements=[
            Element(id=1, node_ids=[10, 20, 30], material_id=100, element_type="CST"),
        ],
        materials=[
            Material(
                id=100,
                name="Steel",
                young_modulus=210e9,
                poisson_ratio=0.3,
                thickness=0.01,
                plane_mode="stress",
            )
        ],
        constraints=[],
        loads=[],
    )


def main() -> None:
    print("开始测试 postprocess 核心功能 ...\n")

    model = build_test_model()
    node_id_to_index = build_node_id_to_index_map(model)
    node_id_to_node = build_node_id_to_node_map(model)

    element = model.elements[0]
    material = model.materials[0]

    # --------------------------------------------------
    # 人工给定一个整体位移向量
    #
    # 节点顺序:
    #   10 -> index 0
    #   20 -> index 1
    #   30 -> index 2
    #
    # 因此整体位移向量顺序为:
    # [u10, v10, u20, v20, u30, v30]
    # --------------------------------------------------
    global_u = np.array(
        [0.0, 0.0, 0.1, 0.0, 0.0, 0.2],
        dtype=np.float64,
    )

    # --------------------------------------------------
    # 测试 1：提取单元局部位移向量
    # 对于唯一单元 [10,20,30]，其局部位移应与 global_u 完全一致
    # --------------------------------------------------
    u_e = extract_element_displacement_vector(global_u, element, node_id_to_index)
    expected_u_e = np.array([0.0, 0.0, 0.1, 0.0, 0.0, 0.2], dtype=np.float64)

    assert_close(u_e, expected_u_e, atol=1e-12, message="extract_element_displacement_vector 错误")
    print("1) extract_element_displacement_vector 通过")

    # --------------------------------------------------
    # 测试 2：单元应变、应力
    #
    # 对于标准三角形:
    #   (0,0), (1,0), (0,1)
    #
    # B = [
    #   [-1,  0,  1,  0,  0,  0]
    #   [ 0, -1,  0,  0,  0,  1]
    #   [-1, -1,  0,  1,  1,  0]
    # ]
    #
    # u_e = [0,0,0.1,0,0,0.2]^T
    #
    # 所以：
    #   strain = [0.1, 0.2, 0.0]^T
    # --------------------------------------------------
    element_result = compute_element_result(
        element=element,
        material=material,
        global_displacement=global_u,
        node_id_to_index=node_id_to_index,
        node_id_to_node=node_id_to_node,
    )

    expected_strain = np.array([0.1, 0.2, 0.0], dtype=np.float64)

    D = (material.young_modulus / (1.0 - material.poisson_ratio ** 2)) * np.array(
        [
            [1.0, material.poisson_ratio, 0.0],
            [material.poisson_ratio, 1.0, 0.0],
            [0.0, 0.0, (1.0 - material.poisson_ratio) / 2.0],
        ],
        dtype=np.float64,
    )
    expected_stress = D @ expected_strain

    assert element_result.element_id == 1, f"element_id 错误: {element_result.element_id}"
    assert_close(element_result.displacement_vector, expected_u_e, atol=1e-12, message="单元位移向量错误")
    assert_close(element_result.strain, expected_strain, atol=1e-12, message="单元应变错误")
    assert_close(element_result.stress, expected_stress, atol=1e-6, message="单元应力错误")
    print("2) compute_element_result 通过")

    # --------------------------------------------------
    # 测试 3：全模型单元结果
    # 当前模型只有一个单元，所以结果列表长度应为 1
    # --------------------------------------------------
    all_results = compute_all_element_results(model, global_u)

    if len(all_results) != 1:
        raise AssertionError(f"compute_all_element_results 结果长度错误: {len(all_results)}")

    assert_close(all_results[0].strain, expected_strain, atol=1e-12, message="全模型单元应变错误")
    assert_close(all_results[0].stress, expected_stress, atol=1e-6, message="全模型单元应力错误")
    print("3) compute_all_element_results 通过")

    # --------------------------------------------------
    # 测试 4：节点位移提取
    # --------------------------------------------------
    node_displacements = extract_node_displacements(model, global_u)

    expected_node_displacements = {
        10: (0.0, 0.0),
        20: (0.1, 0.0),
        30: (0.0, 0.2),
    }

    if node_displacements != expected_node_displacements:
        raise AssertionError(
            f"extract_node_displacements 错误。\n"
            f"实际值 = {node_displacements}\n"
            f"期望值 = {expected_node_displacements}"
        )
    print("4) extract_node_displacements 通过")

    print("\n全部测试通过：postprocess.py 的节点位移、单元应变、单元应力计算逻辑正确。")


if __name__ == "__main__":
    main()