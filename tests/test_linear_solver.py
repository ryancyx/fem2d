from __future__ import annotations

import numpy as np

from solver.linear_solver import solve_linear_system


def assert_close(actual, expected, rtol=1e-9, atol=1e-9, message=""):
    """封装 np.allclose，便于输出更清晰的报错。"""
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        raise AssertionError(
            f"{message}\n"
            f"实际值 actual =\n{actual}\n\n"
            f"期望值 expected =\n{expected}"
        )


def main() -> None:
    print("开始测试 linear_solver 核心功能 ...\n")

    # --------------------------------------------------
    # 测试 1：一个最基本的 2x2 可解线性系统
    # --------------------------------------------------
    K_1 = np.array(
        [
            [2.0, 1.0],
            [1.0, 3.0],
        ],
        dtype=np.float64,
    )
    F_1 = np.array([1.0, 2.0], dtype=np.float64)

    u_1 = solve_linear_system(K_1, F_1)
    u_1_expected = np.linalg.solve(K_1, F_1)

    assert_close(u_1, u_1_expected, atol=1e-12, message="2x2 系统求解错误")
    assert_close(K_1 @ u_1, F_1, atol=1e-12, message="2x2 系统求解结果不满足 K u = F")
    print("1) 基本 2x2 线性系统通过")

    # --------------------------------------------------
    # 测试 2：一个 6x6 的可解系统
    # 更接近 FEM 中的自由度规模
    # --------------------------------------------------
    K_2 = np.array(
        [
            [10.0,  2.0,  0.0,  0.0,  0.0,  0.0],
            [ 2.0, 11.0,  3.0,  0.0,  0.0,  0.0],
            [ 0.0,  3.0, 12.0,  4.0,  0.0,  0.0],
            [ 0.0,  0.0,  4.0, 13.0,  5.0,  0.0],
            [ 0.0,  0.0,  0.0,  5.0, 14.0,  6.0],
            [ 0.0,  0.0,  0.0,  0.0,  6.0, 15.0],
        ],
        dtype=np.float64,
    )
    F_2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.float64)

    u_2 = solve_linear_system(K_2, F_2)
    u_2_expected = np.linalg.solve(K_2, F_2)

    assert_close(u_2, u_2_expected, atol=1e-12, message="6x6 系统求解错误")
    assert_close(K_2 @ u_2, F_2, atol=1e-12, message="6x6 系统求解结果不满足 K u = F")
    print("2) 6x6 线性系统通过")

    # --------------------------------------------------
    # 测试 3：F 可以不是一维输入，也能被 reshape 成正确形式
    # --------------------------------------------------
    K_3 = np.array(
        [
            [4.0, 1.0],
            [1.0, 2.0],
        ],
        dtype=np.float64,
    )
    F_3 = np.array([[9.0], [8.0]], dtype=np.float64)  # 刻意写成列向量

    u_3 = solve_linear_system(K_3, F_3)
    F_3_flat = np.array([9.0, 8.0], dtype=np.float64)
    u_3_expected = np.linalg.solve(K_3, F_3_flat)

    assert_close(u_3, u_3_expected, atol=1e-12, message="列向量右端输入求解错误")
    print("3) 列向量右端输入通过")

    # --------------------------------------------------
    # 测试 4：K 不是方阵时应报错
    # --------------------------------------------------
    K_4 = np.array(
        [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
        ],
        dtype=np.float64,
    )
    F_4 = np.array([1.0, 2.0], dtype=np.float64)

    non_square_raised = False
    try:
        solve_linear_system(K_4, F_4)
    except ValueError as exc:
        non_square_raised = True
        if "方阵" not in str(exc):
            raise AssertionError(f"K 非方阵时虽然报错，但报错信息不符合预期: {exc}")

    if not non_square_raised:
        raise AssertionError("K 非方阵时没有报错，但应该报错。")
    print("4) K 非方阵报错通过")

    # --------------------------------------------------
    # 测试 5：F 长度与 K 维度不匹配时应报错
    # --------------------------------------------------
    K_5 = np.eye(3, dtype=np.float64)
    F_5 = np.array([1.0, 2.0], dtype=np.float64)

    size_mismatch_raised = False
    try:
        solve_linear_system(K_5, F_5)
    except ValueError as exc:
        size_mismatch_raised = True
        if "长度必须与 K 的维度一致" not in str(exc):
            raise AssertionError(f"F 维度不匹配时虽然报错，但报错信息不符合预期: {exc}")

    if not size_mismatch_raised:
        raise AssertionError("F 维度不匹配时没有报错，但应该报错。")
    print("5) F 维度不匹配报错通过")

    # --------------------------------------------------
    # 测试 6：奇异矩阵应报错
    # --------------------------------------------------
    K_6 = np.array(
        [
            [1.0, 2.0],
            [2.0, 4.0],
        ],
        dtype=np.float64,
    )  # 第二行是第一行的 2 倍，奇异
    F_6 = np.array([1.0, 2.0], dtype=np.float64)

    singular_raised = False
    try:
        solve_linear_system(K_6, F_6)
    except ValueError as exc:
        singular_raised = True
        if "奇异" not in str(exc):
            raise AssertionError(f"奇异矩阵虽然报错，但报错信息不符合预期: {exc}")

    if not singular_raised:
        raise AssertionError("奇异矩阵没有报错，但应该报错。")
    print("6) 奇异矩阵报错通过")

    print("\n全部测试通过：linear_solver.py 的线性方程组求解逻辑正确。")


if __name__ == "__main__":
    main()