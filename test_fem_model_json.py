from model.node import Node
from model.element import Element
from model.material import Material
from model.constraint import Constraint
from model.load import Load
from model.fem_model import FEMModel

# 这里的导入方式可能需要根据你的 json_io.py 实际函数名微调
# 如果下面这一行报错，再看我后面的“接口名不一致时怎么改”
from project_io.json_io import save_model_to_json, load_model_from_json


def build_demo_model() -> FEMModel:
    """构造一个最小可用的 FEMModel，用于综合测试。"""
    nodes = [
        Node(id=1, x=0.0, y=0.0),
        Node(id=2, x=1.0, y=0.0),
        Node(id=3, x=0.0, y=1.0),
    ]

    elements = [
        Element(
            id=1,
            node_ids=[1, 2, 3],
            material_id=1,
            element_type="CST"
        )
    ]

    materials = [
        Material(
            id=1,
            name="Steel",
            young_modulus=210e9,
            poisson_ratio=0.3,
            thickness=0.01,
            plane_mode="stress"
        )
    ]

    constraints = [
        Constraint(
            id=1,
            node_id=1,
            ux_fixed=True,
            uy_fixed=True,
            ux_value=0.0,
            uy_value=0.0
        )
    ]

    loads = [
        Load(
            id=1,
            node_id=2,
            fx=1000.0,
            fy=0.0,
            load_type="nodal"
        )
    ]

    model = FEMModel(
        nodes=nodes,
        elements=elements,
        materials=materials,
        constraints=constraints,
        loads=loads
    )

    return model


def check_model_basic_data(model: FEMModel) -> None:
    """检查模型关键字段是否正确。"""
    assert len(model.nodes) == 3, "节点数量应为 3"
    assert len(model.elements) == 1, "单元数量应为 1"
    assert len(model.materials) == 1, "材料数量应为 1"
    assert len(model.constraints) == 1, "约束数量应为 1"
    assert len(model.loads) == 1, "载荷数量应为 1"

    # 节点检查
    assert model.nodes[0].id == 1
    assert model.nodes[0].x == 0.0
    assert model.nodes[0].y == 0.0

    assert model.nodes[1].id == 2
    assert model.nodes[1].x == 1.0
    assert model.nodes[1].y == 0.0

    # 单元检查
    assert model.elements[0].id == 1
    assert model.elements[0].node_ids == [1, 2, 3]
    assert model.elements[0].material_id == 1
    assert model.elements[0].element_type == "CST"

    # 材料检查
    assert model.materials[0].id == 1
    assert model.materials[0].name == "Steel"
    assert model.materials[0].young_modulus == 210e9
    assert model.materials[0].poisson_ratio == 0.3
    assert model.materials[0].thickness == 0.01
    assert model.materials[0].plane_mode == "stress"

    # 约束检查
    assert model.constraints[0].id == 1
    assert model.constraints[0].node_id == 1
    assert model.constraints[0].ux_fixed is True
    assert model.constraints[0].uy_fixed is True
    assert model.constraints[0].ux_value == 0.0
    assert model.constraints[0].uy_value == 0.0

    # 载荷检查
    assert model.loads[0].id == 1
    assert model.loads[0].node_id == 2
    assert model.loads[0].fx == 1000.0
    assert model.loads[0].fy == 0.0
    assert model.loads[0].load_type == "nodal"


def test_build_and_json_io():
    """综合测试：建模 -> 保存 JSON -> 读取 JSON -> 校验一致性"""
    model = build_demo_model()

    # 先检查原始模型本身没问题
    check_model_basic_data(model)

    test_file = "demo_model.json"

    # 保存到 JSON
    save_model_to_json(model, test_file)

    # 从 JSON 读取
    loaded_model = load_model_from_json(test_file)

    # 检查读取后的模型
    check_model_basic_data(loaded_model)

    print("test_build_and_json_io passed.")


if __name__ == "__main__":
    test_build_and_json_io()