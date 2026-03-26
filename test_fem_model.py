from model.node import Node
from model.element import Element
from model.material import Material
from model.constraint import Constraint
from model.load import Load
from model.fem_model import FEMModel


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

print(model)
print(model.to_dict())
print(model.get_node_by_id(2))
print(model.get_material_by_id(1))