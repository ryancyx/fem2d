from model.material import Material

material = Material(
    id=1,
    name="Steel",
    young_modulus=2.1e11,
    poisson_ratio=0.3,
    thickness=0.01
)

print(material)
print(material.to_dict())