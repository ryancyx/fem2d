import json
from pathlib import Path

from model.fem_model import FEMModel


def save_model_to_json(model: FEMModel, file_path: str | Path) -> None:
    path = Path(file_path)

    with path.open("w", encoding="utf-8") as f:
        json.dump(model.to_dict(), f, ensure_ascii=False, indent=4)


def load_model_from_json(file_path: str | Path) -> FEMModel:
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return FEMModel.from_dict(data)
