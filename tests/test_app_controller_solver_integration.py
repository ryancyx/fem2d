from __future__ import annotations

import numpy as np

from model.constraint import Constraint
from model.element import Element
from model.fem_model import FEMModel
from model.load import Load
from model.material import Material
from model.node import Node
from ui.backend.app_controller import AppController


def assert_close(actual, expected, rtol=1e-9, atol=1e-9, message=""):
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        raise AssertionError(
            f"{message}\n"
            f"actual = {actual}\n"
            f"expected = {expected}"
        )


def build_minimal_solvable_model() -> FEMModel:
    """
    构造一个与前面 solver 总流程测试一致的最小可解模型：
    - 1 个 CST 单元
    - 3 个节点
    - 1 个材料
    - 2 条约束（共约束 3 个自由度）
    - 1 个节点集中力
    """
    return FEMModel(
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


def test_solve_success() -> None:
    controller = AppController()

    # 这里是白盒联调测试：直接把一个最小可解模型塞进控制器
    controller._model = build_minimal_solvable_model()

    ok = controller.solve_model()
    if not ok:
        raise AssertionError(f"solve_model() 返回 False，status_text = {controller.status_text}")

    if not controller.has_solver_result():
        raise AssertionError("求解成功后 has_solver_result() 仍为 False")

    if controller.current_mode != "result":
        raise AssertionError(f"求解成功后 current_mode 错误: {controller.current_mode}")

    if controller.status_text != "求解完成":
        raise AssertionError(f"求解成功后 status_text 错误: {controller.status_text}")

    node_rows = controller.get_node_result_rows()
    element_rows = controller.get_element_result_rows()

    if len(node_rows) != 3:
        raise AssertionError(f"节点结果数量错误: {len(node_rows)}")

    if len(element_rows) != 1:
        raise AssertionError(f"单元结果数量错误: {len(element_rows)}")

    # 转成便于检查的字典
    node_map = {row["node_id"]: row for row in node_rows}
    elem = element_rows[0]

    # 节点 1、2 受约束，自位移应为 0
    assert_close(node_map[1]["ux"], 0.0, atol=1e-15, message="节点 1 ux 错误")
    assert_close(node_map[1]["uy"], 0.0, atol=1e-15, message="节点 1 uy 错误")
    assert_close(node_map[2]["uy"], 0.0, atol=1e-15, message="节点 2 uy 错误")

    # 节点 3 的 x 位移应与前面总流程测试一致
    assert_close(node_map[3]["ux"], 2.476190476190476e-06, atol=1e-12, message="节点 3 ux 错误")
    assert_close(node_map[3]["uy"], 0.0, atol=1e-15, message="节点 3 uy 错误")

    # 单元应变 / 应力
    assert_close(elem["strain_x"], 0.0, atol=1e-15, message="strain_x 错误")
    assert_close(elem["strain_y"], 0.0, atol=1e-15, message="strain_y 错误")
    assert_close(elem["gamma_xy"], 2.476190476190476e-06, atol=1e-12, message="gamma_xy 错误")

    assert_close(elem["stress_x"], 0.0, atol=1e-9, message="stress_x 错误")
    assert_close(elem["stress_y"], 0.0, atol=1e-9, message="stress_y 错误")
    assert_close(elem["tau_xy"], 200000.0, atol=1e-3, message="tau_xy 错误")

    print("1) AppController 求解成功联调通过")


def test_result_invalidation_after_model_change() -> None:
    controller = AppController()
    controller._model = build_minimal_solvable_model()

    ok = controller.solve_model()
    if not ok:
        raise AssertionError("预求解失败，无法继续测试结果失效逻辑")

    if not controller.has_solver_result():
        raise AssertionError("预求解后没有结果")

    # 修改模型：添加一个测试节点
    controller.add_test_node()

    if controller.has_solver_result():
        raise AssertionError("模型修改后，旧结果没有被清空")

    if controller.current_mode != "edit" and controller.current_mode != "node":
        raise AssertionError(
            f"模型修改后模式异常，当前为 {controller.current_mode}"
        )

    print("2) 模型修改后结果失效逻辑通过")


def main() -> None:
    print("开始测试 AppController 与求解器联调 ...\n")

    test_solve_success()
    test_result_invalidation_after_model_change()

    print("\n全部测试通过：AppController 已成功接入 solver，且结果缓存/失效逻辑正常。")


if __name__ == "__main__":
    main()