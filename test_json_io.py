from model.node import Node
from model.element import Element
from model.material import Material
from model.constraint import Constraint
from model.load import Load
from model.fem_model import FEMModel
from project_io.json_io import save_model_to_json, load_model_from_json


model = FEMModel()

model.add_node(Node(id=1, x=0.0, y=0.0))
model.add_node(Node(id=2, x=1.0, y=0.0))
model.add_node(Node(id=3, x=0.0, y=1.0))

model.add_material(
    Material(
        id=1,
        name="Steel",
        young_modulus=2.1e11,
        poisson_ratio=0.3,
        thickness=0.01,
        plane_mode="stress"
    )
)

model.add_element(Element(id=1, node_ids=[1, 2, 3], material_id=1))
model.add_constraint(Constraint(id=1, node_id=1, ux_fixed=True, uy_fixed=True))
model.add_load(Load(id=1, node_id=2, fx=1000.0, fy=0.0))

save_model_to_json(model, "demo_model.json")

loaded_model = load_model_from_json("demo_model.json")

print("原模型：")
print(model)

print("\n读取后模型：")
print(loaded_model)

print("\n读取后的字典：")
print(loaded_model.to_dict())
