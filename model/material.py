from dataclasses import dataclass, asdict


@dataclass
class Material:
    id: int
    name: str
    young_modulus: float
    poisson_ratio: float
    thickness: float
    plane_mode: str = "stress"

    def __post_init__(self) -> None:
        if self.young_modulus <= 0:
            raise ValueError("Young modulus must be greater than zero")
        if self.thickness <= 0:
            raise ValueError("Thickness must be greater than zero")
        if not (-1.0 <= self.poisson_ratio <= 0.5):
            raise ValueError("Poisson ratio must be between -1 and 0.5")
        if self.plane_mode != "stress":
            raise ValueError("Plane mode must be stress")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Material":
        return Material(**data)
