from __future__ import annotations

import numpy as np

from model.fem_model import Constraint, FEMModel, Load, Material, Element, Node
from solver.assembler import build_node_id_to_index_map
from solver.boundary_conditions import apply_displacement_constraints


def assert_close(actual, expected, rtol=1e-9, atol=1e-9, message=""):
    """封装 np.allclose，方便测试失败时打印更清晰的信息。"""
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        raise AssertionError(
            f"{message}\n"
            f"实际值 actual =\n{actual}\n\n"
            f"期望值 expected =\n{expected}"
        )


def build_empty_model_with_constraints(constraints: list[Constraint]) -> FEMModel:
    """
    构造一个最小 FEMModel，只为测试 boundary_conditions 使用。
    这里的 nodes 只负责提供 node_id -> index 映射；
    elements/materials/loads 在本测试中不会真正参与计算。
    """
    return FEMModel(
        nodes=[
            Node(id=10, x=0.0, y=0.0),
            Node(id=20, x=1.0, y=0.0),
            Node(id=30, x=0.0, y=1.0),
        ],
        elements=[],
        materials=[],
        constraints=constraints,
        loads=[],
    )


def manual_apply_single_constraint(
    K: np.ndarray,
    F: np.ndarray,
    dof_index: int,
    prescribed_value: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    手动执行一次“对角元素改1法”，作为参考答案。
    这个函数的逻辑应与 boundary_conditions.py 中的单自由度处理一致。
    """
    K_expected = np.asarray(K, dtype=np.float64).copy()
    F_expected = np.asarray(F, dtype=np.float64).reshape(-1).copy()

    F_expected = F_expected - K_expected[:, dof_index] * prescribed_value
    K_expected[:, dof_index] = 0.0
    K_expected[dof_index, :] = 0.0
    K_expected[dof_index, dof_index] = 1.0
    F_expected[dof_index] = prescribed_value

    return K_expected, F_expected


def main() -> None:
    print("开始测试 boundary_conditions 核心功能 ...\n")

    # --------------------------------------------------
    # 测试 1：单个零位移约束
    # 约束 node 10 的 ux = 0
    #
    # 节点映射:
    #   10 -> index 0
    # 所以约束自由度 dof = 0
    # --------------------------------------------------
    model_1 = build_empty_model_with_constraints(
        constraints=[
            Constraint(
                id=1,
                node_id=10,
                ux_fixed=True,
                uy_fixed=False,
                ux_value=0.0,
                uy_value=0.0,
            )
        ]
    )
    node_id_to_index_1 = build_node_id_to_index_map(model_1)

    K_1 = np.array(
        [
            [10.0,  2.0,  3.0,  0.0,  0.0,  0.0],
            [ 2.0, 20.0,  0.0,  4.0,  0.0,  0.0],
            [ 3.0,  0.0, 30.0,  5.0,  6.0,  0.0],
            [ 0.0,  4.0,  5.0, 40.0,  0.0,  7.0],
            [ 0.0,  0.0,  6.0,  0.0, 50.0,  8.0],
            [ 0.0,  0.0,  0.0,  7.0,  8.0, 60.0],
        ],
        dtype=np.float64,
    )
    F_1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float64)

    K_1_actual, F_1_actual = apply_displacement_constraints(
        K=K_1,
        F=F_1,
        model=model_1,
        node_id_to_index=node_id_to_index_1,
    )

    K_1_expected, F_1_expected = manual_apply_single_constraint(K_1, F_1, dof_index=0, prescribed_value=0.0)

    assert_close(K_1_actual, K_1_expected, atol=1e-12, message="单个零位移约束时 K 修改错误")
    assert_close(F_1_actual, F_1_expected, atol=1e-12, message="单个零位移约束时 F 修改错误")
    print("1) 单个零位移约束通过")

    # --------------------------------------------------
    # 测试 2：单个非零位移约束
    # 约束 node 20 的 uy = 0.5
    #
    # 节点映射:
    #   20 -> index 1
    # 所以 uy 自由度 dof = 2*1+1 = 3
    # --------------------------------------------------
    model_2 = build_empty_model_with_constraints(
        constraints=[
            Constraint(
                id=2,
                node_id=20,
                ux_fixed=False,
                uy_fixed=True,
                ux_value=0.0,
                uy_value=0.5,
            )
        ]
    )
    node_id_to_index_2 = build_node_id_to_index_map(model_2)

    K_2 = np.array(
        [
            [12.0,  1.0,  2.0,  3.0,  0.0,  0.0],
            [ 1.0, 15.0,  4.0,  5.0,  0.0,  0.0],
            [ 2.0,  4.0, 18.0,  6.0,  7.0,  0.0],
            [ 3.0,  5.0,  6.0, 21.0,  8.0,  9.0],
            [ 0.0,  0.0,  7.0,  8.0, 24.0, 10.0],
            [ 0.0,  0.0,  0.0,  9.0, 10.0, 27.0],
        ],
        dtype=np.float64,
    )
    F_2 = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0], dtype=np.float64)

    K_2_actual, F_2_actual = apply_displacement_constraints(
        K=K_2,
        F=F_2,
        model=model_2,
        node_id_to_index=node_id_to_index_2,
    )

    K_2_expected, F_2_expected = manual_apply_single_constraint(K_2, F_2, dof_index=3, prescribed_value=0.5)

    assert_close(K_2_actual, K_2_expected, atol=1e-12, message="单个非零位移约束时 K 修改错误")
    assert_close(F_2_actual, F_2_expected, atol=1e-12, message="单个非零位移约束时 F 修改错误")
    print("2) 单个非零位移约束通过")

    # --------------------------------------------------
    # 测试 3：同一个约束对象同时固定 ux 和 uy
    # 约束 node 30: ux = 0, uy = -0.25
    #
    # 节点映射:
    #   30 -> index 2
    # dof:
    #   ux -> 4
    #   uy -> 5
    # --------------------------------------------------
    model_3 = build_empty_model_with_constraints(
        constraints=[
            Constraint(
                id=3,
                node_id=30,
                ux_fixed=True,
                uy_fixed=True,
                ux_value=0.0,
                uy_value=-0.25,
            )
        ]
    )
    node_id_to_index_3 = build_node_id_to_index_map(model_3)

    K_3 = np.array(
        [
            [11.0,  1.0,  2.0,  0.0,  3.0,  0.0],
            [ 1.0, 12.0,  0.0,  4.0,  0.0,  5.0],
            [ 2.0,  0.0, 13.0,  6.0,  7.0,  0.0],
            [ 0.0,  4.0,  6.0, 14.0,  0.0,  8.0],
            [ 3.0,  0.0,  7.0,  0.0, 15.0,  9.0],
            [ 0.0,  5.0,  0.0,  8.0,  9.0, 16.0],
        ],
        dtype=np.float64,
    )
    F_3 = np.array([1.0, 3.0, 5.0, 7.0, 9.0, 11.0], dtype=np.float64)

    K_3_expected, F_3_expected = manual_apply_single_constraint(K_3, F_3, dof_index=4, prescribed_value=0.0)
    K_3_expected, F_3_expected = manual_apply_single_constraint(K_3_expected, F_3_expected, dof_index=5, prescribed_value=-0.25)

    K_3_actual, F_3_actual = apply_displacement_constraints(
        K=K_3,
        F=F_3,
        model=model_3,
        node_id_to_index=node_id_to_index_3,
    )

    assert_close(K_3_actual, K_3_expected, atol=1e-12, message="同时固定 ux, uy 时 K 修改错误")
    assert_close(F_3_actual, F_3_expected, atol=1e-12, message="同时固定 ux, uy 时 F 修改错误")
    print("3) 同时固定 ux 和 uy 通过")

    # --------------------------------------------------
    # 测试 4：重复施加同一个自由度的相同约束
    # 这是允许的，不应报错
    # --------------------------------------------------
    model_4 = build_empty_model_with_constraints(
        constraints=[
            Constraint(
                id=4,
                node_id=10,
                ux_fixed=True,
                uy_fixed=False,
                ux_value=0.0,
                uy_value=0.0,
            ),
            Constraint(
                id=5,
                node_id=10,
                ux_fixed=True,
                uy_fixed=False,
                ux_value=0.0,
                uy_value=0.0,
            ),
        ]
    )
    node_id_to_index_4 = build_node_id_to_index_map(model_4)

    K_4 = np.eye(6, dtype=np.float64)
    F_4 = np.arange(1.0, 7.0, dtype=np.float64)

    K_4_actual, F_4_actual = apply_displacement_constraints(
        K=K_4,
        F=F_4,
        model=model_4,
        node_id_to_index=node_id_to_index_4,
    )

    K_4_expected, F_4_expected = manual_apply_single_constraint(K_4, F_4, dof_index=0, prescribed_value=0.0)

    assert_close(K_4_actual, K_4_expected, atol=1e-12, message="重复相同约束时 K 修改错误")
    assert_close(F_4_actual, F_4_expected, atol=1e-12, message="重复相同约束时 F 修改错误")
    print("4) 重复相同约束通过")

    # --------------------------------------------------
    # 测试 5：重复施加同一个自由度的冲突约束
    # 这是不允许的，必须报错
    # --------------------------------------------------
    model_5 = build_empty_model_with_constraints(
        constraints=[
            Constraint(
                id=6,
                node_id=20,
                ux_fixed=True,
                uy_fixed=False,
                ux_value=0.0,
                uy_value=0.0,
            ),
            Constraint(
                id=7,
                node_id=20,
                ux_fixed=True,
                uy_fixed=False,
                ux_value=1.0,
                uy_value=0.0,
            ),
        ]
    )
    node_id_to_index_5 = build_node_id_to_index_map(model_5)

    K_5 = np.eye(6, dtype=np.float64)
    F_5 = np.zeros(6, dtype=np.float64)

    conflict_raised = False
    try:
        apply_displacement_constraints(
            K=K_5,
            F=F_5,
            model=model_5,
            node_id_to_index=node_id_to_index_5,
        )
    except ValueError as exc:
        conflict_raised = True
        if "冲突" not in str(exc):
            raise AssertionError(f"冲突约束确实报错了，但报错信息不符合预期: {exc}")

    if not conflict_raised:
        raise AssertionError("冲突约束没有报错，但它应该报错。")
    print("5) 冲突约束报错通过")

    # --------------------------------------------------
    # 测试 6：原始 K 和 F 不应被外部修改
    # 因为 apply_displacement_constraints 内部应复制后再处理
    # --------------------------------------------------
    model_6 = build_empty_model_with_constraints(
        constraints=[
            Constraint(
                id=8,
                node_id=10,
                ux_fixed=False,
                uy_fixed=True,
                ux_value=0.0,
                uy_value=2.0,
            )
        ]
    )
    node_id_to_index_6 = build_node_id_to_index_map(model_6)

    K_6 = np.array(
        [
            [2.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 3.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 4.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 5.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 6.0, 1.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 7.0],
        ],
        dtype=np.float64,
    )
    F_6 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float64)

    K_6_before = K_6.copy()
    F_6_before = F_6.copy()

    _K_6_actual, _F_6_actual = apply_displacement_constraints(
        K=K_6,
        F=F_6,
        model=model_6,
        node_id_to_index=node_id_to_index_6,
    )

    assert_close(K_6, K_6_before, atol=1e-12, message="原始 K 被意外修改")
    assert_close(F_6, F_6_before, atol=1e-12, message="原始 F 被意外修改")
    print("6) 原始 K 和 F 不被外部修改通过")

    print("\n全部测试通过：boundary_conditions.py 的位移约束处理逻辑正确。")


if __name__ == "__main__":
    main()