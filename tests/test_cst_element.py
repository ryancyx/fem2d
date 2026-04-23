from __future__ import annotations

import numpy as np

from solver.cst_element import (
    triangle_area,
    compute_b_c,
    constitutive_matrix,
    strain_displacement_matrix,
    element_stiffness,
)


def assert_close(actual, expected, rtol=1e-9, atol=1e-9, message=""):
    """简单封装一下 allclose，失败时给出更清晰的报错。"""
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        raise AssertionError(
            f"{message}\n"
            f"实际值 actual =\n{actual}\n\n"
            f"期望值 expected =\n{expected}"
        )


def main() -> None:
    # -----------------------------
    # 1. 构造一个最简单、最经典的测试单元
    # 节点按逆时针顺序:
    # i = (0,0), j = (1,0), k = (0,1)
    # -----------------------------
    coords = np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        dtype=np.float64,
    )

    E = 210e9
    nu = 0.3
    thickness = 0.01

    print("开始测试 CST 单元核心计算 ...\n")

    # -----------------------------
    # 2. 测试面积
    # -----------------------------
    area = triangle_area(coords)
    expected_area = 0.5
    assert_close(area, expected_area, atol=1e-12, message="triangle_area 计算错误")
    print("1) triangle_area 通过")

    # -----------------------------
    # 3. 测试 b, c 系数
    # 对于该单元:
    # b = [y_j-y_k, y_k-y_i, y_i-y_j] = [-1, 1, 0]
    # c = [x_k-x_j, x_i-x_k, x_j-x_i] = [-1, 0, 1]
    # -----------------------------
    b, c = compute_b_c(coords)

    expected_b = np.array([-1.0, 1.0, 0.0], dtype=np.float64)
    expected_c = np.array([-1.0, 0.0, 1.0], dtype=np.float64)

    assert_close(b, expected_b, atol=1e-12, message="compute_b_c 中 b 计算错误")
    assert_close(c, expected_c, atol=1e-12, message="compute_b_c 中 c 计算错误")
    print("2) compute_b_c 通过")

    # -----------------------------
    # 4. 测试应变矩阵 B
    # 由于 2A = 1，所以这里 B 会非常简洁
    # -----------------------------
    B = strain_displacement_matrix(coords)

    expected_B = np.array(
        [
            [-1.0,  0.0,  1.0,  0.0,  0.0,  0.0],
            [ 0.0, -1.0,  0.0,  0.0,  0.0,  1.0],
            [-1.0, -1.0,  0.0,  1.0,  1.0,  0.0],
        ],
        dtype=np.float64,
    )

    assert_close(B, expected_B, atol=1e-12, message="strain_displacement_matrix 计算错误")
    print("3) strain_displacement_matrix 通过")

    # -----------------------------
    # 5. 测试平面应力弹性矩阵 D
    # -----------------------------
    D = constitutive_matrix(E, nu, plane_mode="stress")

    expected_D = (E / (1.0 - nu**2)) * np.array(
        [
            [1.0, nu, 0.0],
            [nu, 1.0, 0.0],
            [0.0, 0.0, (1.0 - nu) / 2.0],
        ],
        dtype=np.float64,
    )

    assert_close(D, expected_D, rtol=1e-12, atol=1e-6, message="constitutive_matrix(stress) 计算错误")
    print("4) constitutive_matrix (plane stress) 通过")

    # -----------------------------
    # 6. 测试单元刚度矩阵 Ke
    # 这里用该标准单元的参考结果做对照
    # -----------------------------
    Ke = element_stiffness(coords, E, nu, thickness, plane_mode="stress")

    expected_Ke = np.array(
        [
            [ 1.557692307692e+09,  7.500000000000e+08, -1.153846153846e+09, -4.038461538462e+08, -4.038461538462e+08, -3.461538461538e+08],
            [ 7.500000000000e+08,  1.557692307692e+09, -3.461538461538e+08, -4.038461538462e+08, -4.038461538462e+08, -1.153846153846e+09],
            [-1.153846153846e+09, -3.461538461538e+08,  1.153846153846e+09,  0.000000000000e+00,  0.000000000000e+00,  3.461538461538e+08],
            [-4.038461538462e+08, -4.038461538462e+08,  0.000000000000e+00,  4.038461538462e+08,  4.038461538462e+08,  0.000000000000e+00],
            [-4.038461538462e+08, -4.038461538462e+08,  0.000000000000e+00,  4.038461538462e+08,  4.038461538462e+08,  0.000000000000e+00],
            [-3.461538461538e+08, -1.153846153846e+09,  3.461538461538e+08,  0.000000000000e+00,  0.000000000000e+00,  1.153846153846e+09],
        ],
        dtype=np.float64,
    )

    assert Ke.shape == (6, 6), f"Ke 形状错误，当前为 {Ke.shape}，应为 (6, 6)"
    assert_close(Ke, expected_Ke, rtol=1e-9, atol=1e-3, message="element_stiffness 计算错误")
    print("5) element_stiffness 数值结果通过")

    # -----------------------------
    # 7. 测试对称性
    # 单元刚度矩阵应该对称
    # -----------------------------
    assert_close(Ke, Ke.T, rtol=1e-12, atol=1e-6, message="Ke 不是对称矩阵")
    print("6) Ke 对称性通过")

    # -----------------------------
    # 8. 测试刚体模态
    # 单个二维三角形单元应有 3 个刚体模态:
    # - x方向整体平移
    # - y方向整体平移
    # - 平面内刚体转动
    # 它们代入 Ke 后应接近 0
    # -----------------------------
    rigid_tx = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 0.0], dtype=np.float64)
    rigid_ty = np.array([0.0, 1.0, 0.0, 1.0, 0.0, 1.0], dtype=np.float64)

    # 对于节点:
    # (0,0), (1,0), (0,1)
    # 刚体转动位移可取 u=-y, v=x
    rigid_rot = np.array([0.0, 0.0, 0.0, 1.0, -1.0, 0.0], dtype=np.float64)

    assert_close(Ke @ rigid_tx, np.zeros(6), atol=1e-6, message="Ke 未通过 x 向刚体平移测试")
    assert_close(Ke @ rigid_ty, np.zeros(6), atol=1e-6, message="Ke 未通过 y 向刚体平移测试")
    assert_close(Ke @ rigid_rot, np.zeros(6), atol=1e-6, message="Ke 未通过刚体转动测试")
    print("7) 刚体模态测试通过")

    # -----------------------------
    # 9. 测试特征值性质
    # 理论上:
    # - 3 个接近 0（刚体模态）
    # - 3 个正特征值（真实变形模态）
    # -----------------------------
    eigenvalues = np.linalg.eigvalsh(Ke)

    zero_mode_count = np.sum(np.abs(eigenvalues) < 1e-4)
    positive_mode_count = np.sum(eigenvalues > 1e-4)

    if zero_mode_count != 3:
        raise AssertionError(
            f"Ke 的零模态数量不对，应为 3，当前为 {zero_mode_count}。\n特征值 = {eigenvalues}"
        )

    if positive_mode_count != 3:
        raise AssertionError(
            f"Ke 的正特征值数量不对，应为 3，当前为 {positive_mode_count}。\n特征值 = {eigenvalues}"
        )

    print("8) 特征值性质通过")

    print("\n全部测试通过：CST 单元面积、B矩阵、D矩阵、Ke矩阵及核心力学性质均正确。")


if __name__ == "__main__":
    main()
    