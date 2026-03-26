from model.constraint import Constraint

constraint = Constraint(
    id=1,
    node_id=1,
    ux_fixed=True,
    uy_fixed=True
)

print(constraint)
print(constraint.to_dict())