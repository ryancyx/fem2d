import csv
import json
import math
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl

from model.constraint import Constraint
from model.element import Element
from model.fem_model import FEMModel
from model.load import Load
from model.material import Material
from model.node import Node

from solver.solver import SolverResult, solve_linear_static


class AppController(QObject):
    status_text_changed = Signal()
    current_mode_changed = Signal()
    model_stats_changed = Signal()
    solver_results_changed = Signal()

    node_data_changed = Signal()
    selected_node_changed = Signal()

    # 阶段6：单元相关信号
    element_selection_changed = Signal()
    element_data_changed = Signal()
    selected_element_changed = Signal()

    # 阶段7：材料 / 约束 / 载荷相关信号
    material_data_changed = Signal()
    boundary_data_changed = Signal()

    def __init__(self):
        super().__init__()
        self._status_text = "就绪"
        self._current_mode = "none"
        self._current_project_path: str | None = None
        self._model = FEMModel()

        self._solver_result: SolverResult | None = None
        self._node_result_rows: list[dict] = []
        self._element_result_rows: list[dict] = []

        self._selected_node_id: int | None = None

        # 阶段6：用于创建单元时暂存被选中的3个节点
        self._selected_element_node_ids: list[int] = []

        # 阶段6：当前选中的单元
        self._selected_element_id: int | None = None

    @Property(str, notify=status_text_changed)
    def status_text(self):
        return self._status_text

    @Property(str, notify=current_mode_changed)
    def current_mode(self):
        return self._current_mode

    @Property(int, notify=model_stats_changed)
    def node_count(self):
        return len(self._model.nodes)

    @Property(int, notify=model_stats_changed)
    def element_count(self):
        return len(self._model.elements)

    @Property(int, notify=model_stats_changed)
    def material_count(self):
        return len(self._model.materials)

    @Property(int, notify=model_stats_changed)
    def constraint_count(self):
        return len(self._model.constraints)

    @Property(int, notify=model_stats_changed)
    def load_count(self):
        return len(self._model.loads)

    @Property(bool, notify=solver_results_changed)
    def solver_has_result(self):
        return self._solver_result is not None

    @Property(bool, notify=selected_node_changed)
    def selected_node_exists(self):
        return self._get_selected_node() is not None

    @Property(int, notify=selected_node_changed)
    def selected_node_id(self):
        node = self._get_selected_node()
        if node is None:
            return -1
        return node.id

    @Property(float, notify=selected_node_changed)
    def selected_node_x(self):
        node = self._get_selected_node()
        if node is None:
            return 0.0
        return float(node.x)

    @Property(float, notify=selected_node_changed)
    def selected_node_y(self):
        node = self._get_selected_node()
        if node is None:
            return 0.0
        return float(node.y)

    # 阶段6：当前单元临时选点数量
    @Property(int, notify=element_selection_changed)
    def selected_element_node_count(self):
        return len(self._selected_element_node_ids)

    # 阶段6：当前单元临时选点列表
    @Property("QVariantList", notify=element_selection_changed)
    def selected_element_node_ids(self):
        return list(self._selected_element_node_ids)

    # 阶段6：当前选中单元信息
    @Property(bool, notify=selected_element_changed)
    def selected_element_exists(self):
        return self._get_selected_element() is not None

    @Property(int, notify=selected_element_changed)
    def selected_element_id(self):
        element = self._get_selected_element()
        if element is None:
            return -1
        return element.id

    @Property("QVariantList", notify=selected_element_changed)
    def selected_element_node_ids_info(self):
        element = self._get_selected_element()
        if element is None:
            return []
        return list(element.node_ids)

    @Property(int, notify=selected_element_changed)
    def selected_element_material_id(self):
        element = self._get_selected_element()
        if element is None or element.material_id is None:
            return -1
        return int(element.material_id)

    @Property(str, notify=selected_element_changed)
    def selected_element_type(self):
        element = self._get_selected_element()
        if element is None:
            return ""
        return str(element.element_type)

    def set_status_text(self, text: str) -> None:
        if self._status_text != text:
            self._status_text = text
            self.status_text_changed.emit()

    def set_current_mode(self, mode: str) -> None:
        if self._current_mode != mode:
            self._current_mode = mode
            self.current_mode_changed.emit()

    def notify_model_stats_changed(self) -> None:
        self.model_stats_changed.emit()

    def _notify_solver_results_changed(self) -> None:
        self.solver_results_changed.emit()

    def _notify_node_data_changed(self) -> None:
        self.node_data_changed.emit()

    def _notify_selected_node_changed(self) -> None:
        self.selected_node_changed.emit()

    def _notify_element_selection_changed(self) -> None:
        self.element_selection_changed.emit()

    def _notify_element_data_changed(self) -> None:
        self.element_data_changed.emit()

    def _notify_selected_element_changed(self) -> None:
        self.selected_element_changed.emit()

    def _notify_material_data_changed(self) -> None:
        self.material_data_changed.emit()

    def _notify_boundary_data_changed(self) -> None:
        self.boundary_data_changed.emit()

    def _notify_all_model_data_changed(self) -> None:
        self.notify_model_stats_changed()
        self._notify_node_data_changed()
        self._notify_selected_node_changed()
        self._notify_element_selection_changed()
        self._notify_element_data_changed()
        self._notify_selected_element_changed()
        self._notify_material_data_changed()
        self._notify_boundary_data_changed()
        self._notify_solver_results_changed()

    def _path_from_qml(self, file_path, default_suffix: str) -> Path:
        if file_path is None:
            raise ValueError("文件路径为空")

        if isinstance(file_path, QUrl):
            raw = file_path.toLocalFile() or file_path.toString()
        else:
            raw = str(file_path).strip()

        if raw == "":
            raise ValueError("文件路径为空")

        if raw.startswith("file:"):
            local_path = QUrl(raw).toLocalFile()
            if local_path:
                raw = local_path

        path = Path(raw).expanduser()
        if path.suffix == "":
            path = path.with_suffix(default_suffix)

        return path

    def _project_path_from_qml(self, file_path) -> Path:
        return self._path_from_qml(file_path, ".json")

    def _csv_path_from_qml(self, file_path) -> Path:
        return self._path_from_qml(file_path, ".csv")

    def _reset_runtime_state_after_project_change(self) -> None:
        self._selected_node_id = None
        self._selected_element_id = None
        self._selected_element_node_ids = []
        self._clear_solver_results()
        self.set_current_mode("none")

    def _next_id(self, items) -> int:
        if not items:
            return 1
        return max(item.id for item in items) + 1

    def _ensure_default_material(self) -> int:
        if self._model.materials:
            return self._model.materials[0].id

        material_id = self._next_id(self._model.materials)
        material = Material(
            id=material_id,
            name=f"材料-{material_id}",
            young_modulus=210000000000.0,
            poisson_ratio=0.3,
            thickness=0.01,
            plane_mode="stress",
        )
        self._model.materials.append(material)
        self._notify_material_data_changed()
        return material_id

    def _clear_solver_results(self) -> None:
        self._solver_result = None
        self._node_result_rows = []
        self._element_result_rows = []
        self._notify_solver_results_changed()

    def _invalidate_results_after_model_change(self) -> None:
        if self._solver_result is not None:
            self._clear_solver_results()
            self.set_current_mode("edit")

    def _build_node_result_rows(self, solver_result: SolverResult) -> list[dict]:
        rows: list[dict] = []

        for node_id, (ux, uy) in solver_result.node_displacements.items():
            rows.append(
                {
                    "node_id": int(node_id),
                    "ux": float(ux),
                    "uy": float(uy),
                }
            )

        rows.sort(key=lambda item: item["node_id"])
        return rows

    def _build_element_result_rows(self, solver_result: SolverResult) -> list[dict]:
        rows: list[dict] = []

        for item in solver_result.element_results:
            rows.append(
                {
                    "element_id": int(item.element_id),
                    "strain_x": float(item.strain[0]),
                    "strain_y": float(item.strain[1]),
                    "gamma_xy": float(item.strain[2]),
                    "stress_x": float(item.stress[0]),
                    "stress_y": float(item.stress[1]),
                    "tau_xy": float(item.stress[2]),
                }
            )

        rows.sort(key=lambda item: item["element_id"])
        return rows

    def _build_node_rows(self) -> list[dict]:
        rows: list[dict] = []

        for node in self._model.nodes:
            rows.append(
                {
                    "id": int(node.id),
                    "x": float(node.x),
                    "y": float(node.y),
                }
            )

        rows.sort(key=lambda item: item["id"])
        return rows

    def _build_element_rows(self) -> list[dict]:
        rows: list[dict] = []

        for element in self._model.elements:
            rows.append(
                {
                    "id": int(element.id),
                    "node_ids": list(element.node_ids),
                    "material_id": -1 if element.material_id is None else int(element.material_id),
                    "element_type": str(element.element_type),
                }
            )

        rows.sort(key=lambda item: item["id"])
        return rows

    def _build_material_rows(self) -> list[dict]:
        rows: list[dict] = []

        for material in self._model.materials:
            rows.append(
                {
                    "id": int(material.id),
                    "name": str(material.name),
                    "young_modulus": float(material.young_modulus),
                    "poisson_ratio": float(material.poisson_ratio),
                    "thickness": float(material.thickness),
                    "plane_mode": str(material.plane_mode),
                }
            )

        rows.sort(key=lambda item: item["id"])
        return rows

    def _build_constraint_rows(self) -> list[dict]:
        rows: list[dict] = []

        for constraint in self._model.constraints:
            rows.append(
                {
                    "id": int(constraint.id),
                    "node_id": int(constraint.node_id),
                    "ux_fixed": bool(constraint.ux_fixed),
                    "uy_fixed": bool(constraint.uy_fixed),
                    "ux_value": float(constraint.ux_value),
                    "uy_value": float(constraint.uy_value),
                }
            )

        rows.sort(key=lambda item: item["id"])
        return rows

    def _build_load_rows(self) -> list[dict]:
        rows: list[dict] = []

        for load in self._model.loads:
            rows.append(
                {
                    "id": int(load.id),
                    "node_id": int(load.node_id),
                    "fx": float(load.fx),
                    "fy": float(load.fy),
                    "load_type": str(load.load_type),
                }
            )

        rows.sort(key=lambda item: item["id"])
        return rows

    def _find_node_by_id(self, node_id: int) -> Node | None:
        for node in self._model.nodes:
            if node.id == node_id:
                return node
        return None

    def _find_element_by_id(self, element_id: int) -> Element | None:
        for element in self._model.elements:
            if element.id == element_id:
                return element
        return None

    def _find_material_by_id(self, material_id: int) -> Material | None:
        for material in self._model.materials:
            if material.id == material_id:
                return material
        return None

    def _find_constraint_by_node_id(self, node_id: int) -> Constraint | None:
        for constraint in self._model.constraints:
            if constraint.node_id == node_id:
                return constraint
        return None

    def _find_load_by_node_id(self, node_id: int) -> Load | None:
        for load in self._model.loads:
            if load.node_id == node_id:
                return load
        return None

    def _set_selected_node_id(self, node_id: int | None) -> None:
        if self._selected_node_id != node_id:
            self._selected_node_id = node_id
            self._notify_selected_node_changed()
            self._notify_boundary_data_changed()

    def _set_selected_element_id(self, element_id: int | None) -> None:
        if self._selected_element_id != element_id:
            self._selected_element_id = element_id
            self._notify_selected_element_changed()
            self._notify_material_data_changed()

    def _get_selected_node(self) -> Node | None:
        if self._selected_node_id is None:
            return None
        return self._find_node_by_id(self._selected_node_id)

    def _get_selected_element(self) -> Element | None:
        if self._selected_element_id is None:
            return None
        return self._find_element_by_id(self._selected_element_id)

    def _validate_coordinate(self, value: float, name: str) -> float:
        if not math.isfinite(value):
            raise ValueError(f"{name} 不是有效数字")
        return float(value)

    def _validate_finite_number(self, value: float, name: str) -> float:
        if not math.isfinite(value):
            raise ValueError(f"{name} 不是有效数字")
        return float(value)

    def _parse_coordinate_text(self, text: str, name: str) -> float:
        stripped = text.strip()
        if stripped == "":
            raise ValueError(f"{name} 不能为空")

        try:
            value = float(stripped)
        except ValueError as exc:
            raise ValueError(f"{name} 不是合法数字") from exc

        return self._validate_coordinate(value, name)

    def _parse_float_text(self, text: str, name: str) -> float:
        stripped = text.strip()
        if stripped == "":
            raise ValueError(f"{name} 不能为空")

        try:
            value = float(stripped)
        except ValueError as exc:
            raise ValueError(f"{name} 不是合法数字") from exc

        return self._validate_finite_number(value, name)

    def _normalize_plane_mode(self, plane_mode: str) -> str:
        raw = plane_mode.strip().lower()
        mapping = {
            "stress": "stress",
            "plane_stress": "stress",
            "plane stress": "stress",
            "strain": "strain",
            "plane_strain": "strain",
            "plane strain": "strain",
        }

        if raw not in mapping:
            raise ValueError("平面模式必须为 stress 或 strain")

        normalized = mapping[raw]
        if normalized != "stress":
            raise ValueError("当前版本暂仅支持平面应力（stress）")

        return normalized

    def _node_is_referenced(self, node_id: int) -> tuple[bool, str]:
        for element in self._model.elements:
            if node_id in element.node_ids:
                return True, f"节点 {node_id} 已被单元 {element.id} 引用，不能删除"

        return False, ""

    def _get_node_coords_by_id(self, node_id: int) -> tuple[float, float]:
        node = self._find_node_by_id(node_id)
        if node is None:
            raise ValueError(f"不存在编号为 {node_id} 的节点")
        return float(node.x), float(node.y)

    def _signed_twice_area_by_node_ids(self, node_ids: list[int]) -> float:
        if len(node_ids) != 3:
            raise ValueError("面积计算必须传入3个节点")

        x1, y1 = self._get_node_coords_by_id(node_ids[0])
        x2, y2 = self._get_node_coords_by_id(node_ids[1])
        x3, y3 = self._get_node_coords_by_id(node_ids[2])

        return (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)

    def _are_three_nodes_collinear(self, node_ids: list[int]) -> bool:
        twice_area = self._signed_twice_area_by_node_ids(node_ids)
        return abs(twice_area) < 1e-12

    def _normalize_element_node_order_to_ccw(self, node_ids: list[int]) -> list[int]:
        """
        将三角形单元节点顺序统一修正为逆时针。

        CST 单元的面积公式采用有向面积，若节点顺序为顺时针，面积为负，
        后续刚度矩阵计算会失败。因此这里在创建/读取工程时统一做一次规范化。
        """
        if len(node_ids) != 3:
            raise ValueError("CST 单元必须包含3个节点")

        twice_area = self._signed_twice_area_by_node_ids(node_ids)
        if abs(twice_area) < 1e-12:
            raise ValueError("所选 3 个节点共线，不能构成三角形单元")

        normalized = list(node_ids)
        if twice_area < 0.0:
            normalized[1], normalized[2] = normalized[2], normalized[1]

        return normalized

    def _normalize_all_element_node_orders_to_ccw(self) -> int:
        fixed_count = 0

        for element in self._model.elements:
            original = list(element.node_ids)
            normalized = self._normalize_element_node_order_to_ccw(original)
            if normalized != original:
                element.node_ids = normalized
                fixed_count += 1

        return fixed_count

    def _element_with_same_nodes_exists(self, node_ids: list[int]) -> bool:
        target = tuple(sorted(node_ids))
        for element in self._model.elements:
            if tuple(sorted(element.node_ids)) == target:
                return True
        return False

    def _material_is_used_by_elements(self, material_id: int) -> list[int]:
        used_element_ids: list[int] = []

        for element in self._model.elements:
            if element.material_id == material_id:
                used_element_ids.append(element.id)

        return used_element_ids

    def _validate_model_before_solve(self) -> None:
        for element in self._model.elements:
            if element.material_id is None:
                raise ValueError(f"单元 {element.id} 尚未分配材料")

            material = self._find_material_by_id(element.material_id)
            if material is None:
                raise ValueError(f"单元 {element.id} 引用了不存在的材料 {element.material_id}")

            if material.plane_mode != "stress":
                raise ValueError("当前版本求解器暂仅支持平面应力（stress）")

    @Slot("QVariant", result=bool)
    @Slot(str, result=bool)
    def save_project_to_file(self, file_path) -> bool:
        try:
            path = self._project_path_from_qml(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            project_data = {
                "file_type": "fem2d_project",
                "version": 1,
                "model": self._model.to_dict(),
            }

            path.write_text(
                json.dumps(project_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            self._current_project_path = str(path)
            self.set_status_text(f"已保存工程：{path.name}")
            return True

        except Exception as exc:
            self.set_status_text(f"保存工程失败：{exc}")
            return False

    @Slot("QVariant", result=bool)
    @Slot(str, result=bool)
    def load_project_from_file(self, file_path) -> bool:
        try:
            path = self._project_path_from_qml(file_path)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在：{path}")

            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("工程文件格式错误：根对象必须是字典")

            model_data = data.get("model", data)
            if not isinstance(model_data, dict):
                raise ValueError("工程文件格式错误：model 字段必须是字典")

            loaded_model = FEMModel.from_dict(model_data)

            self._model = loaded_model
            fixed_count = self._normalize_all_element_node_orders_to_ccw()
            self._current_project_path = str(path)
            self._reset_runtime_state_after_project_change()
            if fixed_count > 0:
                self.set_status_text(f"已打开工程：{path.name}，并自动修正 {fixed_count} 个单元节点顺序")
            else:
                self.set_status_text(f"已打开工程：{path.name}")
            self._notify_all_model_data_changed()
            return True

        except Exception as exc:
            self.set_status_text(f"打开工程失败：{exc}")
            return False

    @Slot()
    def new_model(self) -> None:
        self._model = FEMModel()
        self._current_project_path = None
        self._selected_node_id = None
        self._selected_element_id = None
        self._selected_element_node_ids = []
        self._clear_solver_results()
        self.set_current_mode("none")
        self.set_status_text("已新建空模型")
        self.notify_model_stats_changed()
        self._notify_node_data_changed()
        self._notify_selected_node_changed()
        self._notify_element_selection_changed()
        self._notify_element_data_changed()
        self._notify_selected_element_changed()
        self._notify_material_data_changed()
        self._notify_boundary_data_changed()

    @Slot()
    def set_node_mode(self) -> None:
        self.set_current_mode("node")
        self.set_status_text("已切换到节点模式")

    @Slot()
    def set_element_mode(self) -> None:
        self.set_current_mode("element")
        self.set_status_text("已切换到单元模式")

    @Slot(result="QVariantList")
    def get_node_rows(self):
        return self._build_node_rows()

    @Slot(result="QVariantList")
    def get_element_rows(self):
        return self._build_element_rows()

    @Slot(result="QVariantList")
    def get_material_rows(self):
        return self._build_material_rows()

    @Slot(result="QVariantList")
    def get_constraint_rows(self):
        return self._build_constraint_rows()

    @Slot(result="QVariantList")
    def get_load_rows(self):
        return self._build_load_rows()

    @Slot(result="QVariantList")
    def get_materials(self):
        return self._build_material_rows()

    @Slot(result="QVariantList")
    def get_constraints(self):
        return self._build_constraint_rows()

    @Slot(result="QVariantList")
    def get_loads(self):
        return self._build_load_rows()

    @Slot(result="QVariantMap")
    def get_selected_node_row(self):
        node = self._get_selected_node()
        if node is None:
            return {}

        return {
            "id": int(node.id),
            "x": float(node.x),
            "y": float(node.y),
        }

    @Slot(result="QVariantMap")
    def get_selected_element_row(self):
        element = self._get_selected_element()
        if element is None:
            return {}

        return {
            "id": int(element.id),
            "node_ids": list(element.node_ids),
            "material_id": -1 if element.material_id is None else int(element.material_id),
            "element_type": str(element.element_type),
        }

    @Slot(result="QVariantMap")
    def get_selected_node_boundary_info(self):
        node = self._get_selected_node()
        if node is None:
            return {}

        constraint = self._find_constraint_by_node_id(node.id)
        load = self._find_load_by_node_id(node.id)

        return {
            "node_id": int(node.id),
            "has_constraint": constraint is not None,
            "ux_fixed": False if constraint is None else bool(constraint.ux_fixed),
            "uy_fixed": False if constraint is None else bool(constraint.uy_fixed),
            "ux_value": 0.0 if constraint is None else float(constraint.ux_value),
            "uy_value": 0.0 if constraint is None else float(constraint.uy_value),
            "has_load": load is not None,
            "fx": 0.0 if load is None else float(load.fx),
            "fy": 0.0 if load is None else float(load.fy),
            "load_type": "" if load is None else str(load.load_type),
        }

    @Slot(result="QVariantMap")
    def get_selected_element_material_info(self):
        element = self._get_selected_element()
        if element is None:
            return {}

        material = None
        if element.material_id is not None:
            material = self._find_material_by_id(element.material_id)

        return {
            "element_id": int(element.id),
            "material_id": -1 if element.material_id is None else int(element.material_id),
            "has_material": material is not None,
            "material_name": "" if material is None else str(material.name),
            "young_modulus": 0.0 if material is None else float(material.young_modulus),
            "poisson_ratio": 0.0 if material is None else float(material.poisson_ratio),
            "thickness": 0.0 if material is None else float(material.thickness),
            "plane_mode": "" if material is None else str(material.plane_mode),
        }

    @Slot(int, result=bool)
    def select_node(self, node_id: int) -> bool:
        node = self._find_node_by_id(node_id)
        if node is None:
            self.set_status_text(f"选中节点失败：不存在编号为 {node_id} 的节点")
            return False

        self._set_selected_node_id(node.id)
        self.set_current_mode("node")
        self.set_status_text(f"已选中节点 {node.id}")
        return True

    @Slot()
    def clear_node_selection(self) -> None:
        self._set_selected_node_id(None)
        self.set_status_text("已取消节点选中")

    @Slot(int, result=bool)
    def select_element(self, element_id: int) -> bool:
        element = self._find_element_by_id(element_id)
        if element is None:
            self.set_status_text(f"选中单元失败：不存在编号为 {element_id} 的单元")
            return False

        self._set_selected_element_id(element.id)
        self.set_current_mode("element")
        self.set_status_text(f"已选中单元 {element.id}")
        return True

    @Slot()
    def clear_element_selection(self) -> None:
        self._set_selected_element_id(None)
        self.set_status_text("已取消单元选中")

    @Slot(float, float, result=bool)
    def add_node_by_coord(self, x: float, y: float) -> bool:
        try:
            x = self._validate_coordinate(x, "X")
            y = self._validate_coordinate(y, "Y")
        except ValueError as exc:
            self.set_status_text(f"添加节点失败：{exc}")
            return False

        self._invalidate_results_after_model_change()

        node_id = self._next_id(self._model.nodes)
        node = Node(id=node_id, x=x, y=y)
        self._model.nodes.append(node)

        self._set_selected_node_id(node.id)
        self.set_current_mode("node")
        self.set_status_text(f"已添加节点 {node.id} ({x:.3f}, {y:.3f})")
        self.notify_model_stats_changed()
        self._notify_node_data_changed()
        return True

    @Slot(str, str, result=bool)
    def add_node_by_text(self, x_text: str, y_text: str) -> bool:
        try:
            x = self._parse_coordinate_text(x_text, "X")
            y = self._parse_coordinate_text(y_text, "Y")
        except ValueError as exc:
            self.set_status_text(f"添加节点失败：{exc}")
            return False

        return self.add_node_by_coord(x, y)

    @Slot(float, float, result=bool)
    def update_selected_node_position(self, x: float, y: float) -> bool:
        node = self._get_selected_node()
        if node is None:
            self.set_status_text("修改节点失败：当前没有选中任何节点")
            return False

        try:
            x = self._validate_coordinate(x, "X")
            y = self._validate_coordinate(y, "Y")
        except ValueError as exc:
            self.set_status_text(f"修改节点失败：{exc}")
            return False

        self._invalidate_results_after_model_change()

        node.x = x
        node.y = y

        self.set_current_mode("node")
        self.set_status_text(f"已更新节点 {node.id} 坐标为 ({x:.3f}, {y:.3f})")
        self._notify_node_data_changed()
        self._notify_selected_node_changed()
        return True

    @Slot(str, str, result=bool)
    def update_selected_node_position_by_text(self, x_text: str, y_text: str) -> bool:
        try:
            x = self._parse_coordinate_text(x_text, "X")
            y = self._parse_coordinate_text(y_text, "Y")
        except ValueError as exc:
            self.set_status_text(f"修改节点失败：{exc}")
            return False

        return self.update_selected_node_position(x, y)

    @Slot(int, result=bool)
    def delete_node(self, node_id: int) -> bool:
        node = self._find_node_by_id(node_id)
        if node is None:
            self.set_status_text(f"删除节点失败：不存在编号为 {node_id} 的节点")
            return False

        referenced, message = self._node_is_referenced(node_id)
        if referenced:
            self.set_status_text(f"删除节点失败：{message}")
            return False

        self._invalidate_results_after_model_change()

        self._model.nodes = [item for item in self._model.nodes if item.id != node_id]
        self._model.constraints = [item for item in self._model.constraints if item.node_id != node_id]
        self._model.loads = [item for item in self._model.loads if item.node_id != node_id]

        if self._selected_node_id == node_id:
            self._set_selected_node_id(None)

        if node_id in self._selected_element_node_ids:
            self._selected_element_node_ids.remove(node_id)
            self._notify_element_selection_changed()

        self.set_current_mode("node")
        self.set_status_text(f"已删除节点 {node_id}")
        self.notify_model_stats_changed()
        self._notify_node_data_changed()
        self._notify_boundary_data_changed()
        return True

    @Slot(result=bool)
    def delete_selected_node(self) -> bool:
        node = self._get_selected_node()
        if node is None:
            self.set_status_text("删除节点失败：当前没有选中任何节点")
            return False

        return self.delete_node(node.id)

    @Slot(int, result=bool)
    def delete_element(self, element_id: int) -> bool:
        element = self._find_element_by_id(element_id)
        if element is None:
            self.set_status_text(f"删除单元失败：不存在编号为 {element_id} 的单元")
            return False

        self._invalidate_results_after_model_change()

        self._model.elements = [item for item in self._model.elements if item.id != element_id]

        if self._selected_element_id == element_id:
            self._set_selected_element_id(None)

        self.set_current_mode("element")
        self.set_status_text(f"已删除单元 {element_id}")
        self.notify_model_stats_changed()
        self._notify_element_data_changed()
        return True

    @Slot(result=bool)
    def delete_selected_element(self) -> bool:
        element = self._get_selected_element()
        if element is None:
            self.set_status_text("删除单元失败：当前没有选中任何单元")
            return False

        return self.delete_element(element.id)

    # =========================
    # 阶段6：单元临时选点相关接口
    # =========================

    @Slot()
    def clear_element_node_selection(self) -> None:
        self._selected_element_node_ids = []
        self._notify_element_selection_changed()
        self.set_status_text("已清空单元节点选择")

    @Slot(int, result=bool)
    def toggle_element_node_selection(self, node_id: int) -> bool:
        node = self._find_node_by_id(node_id)
        if node is None:
            self.set_status_text(f"单元选点失败：不存在编号为 {node_id} 的节点")
            return False

        if node_id in self._selected_element_node_ids:
            self._selected_element_node_ids.remove(node_id)
            self._notify_element_selection_changed()
            self.set_status_text(f"已取消单元节点 {node_id}")
            return True

        if len(self._selected_element_node_ids) >= 3:
            self.set_status_text("单元选点失败：最多只能选择 3 个节点")
            return False

        self._selected_element_node_ids.append(node_id)
        self._notify_element_selection_changed()
        self.set_status_text(
            f"已选择单元节点 {node_id}（{len(self._selected_element_node_ids)}/3）"
        )
        return True

    @Slot(int, result=bool)
    def is_node_in_element_selection(self, node_id: int) -> bool:
        return node_id in self._selected_element_node_ids

    @Slot(result=bool)
    def create_element_from_selected_nodes(self) -> bool:
        if len(self._selected_element_node_ids) != 3:
            self.set_status_text("创建单元失败：必须恰好选择 3 个节点")
            return False

        node_ids = list(self._selected_element_node_ids)

        try:
            node_ids = self._normalize_element_node_order_to_ccw(node_ids)
        except ValueError as exc:
            self.set_status_text(f"创建单元失败：{exc}")
            return False

        if self._element_with_same_nodes_exists(node_ids):
            self.set_status_text("创建单元失败：相同节点组合的单元已存在")
            return False

        self._invalidate_results_after_model_change()

        material_id = self._ensure_default_material()
        element_id = self._next_id(self._model.elements)

        element = Element(
            id=element_id,
            node_ids=node_ids,
            material_id=material_id,
            element_type="CST",
        )
        self._model.elements.append(element)

        self._selected_element_node_ids = []
        self._set_selected_element_id(element.id)

        self._notify_element_selection_changed()
        self._notify_element_data_changed()
        self.notify_model_stats_changed()

        self.set_current_mode("element")
        self.set_status_text(
            f"已创建单元 {element_id}，连接节点 {node_ids[0]}-{node_ids[1]}-{node_ids[2]}"
        )
        return True

    # =========================
    # 阶段7：材料管理接口
    # =========================

    @Slot(str, float, float, float, str, result=bool)
    def add_material(
        self,
        name: str,
        young_modulus: float,
        poisson_ratio: float,
        thickness: float,
        plane_mode: str,
    ) -> bool:
        try:
            normalized_name = name.strip()
            if normalized_name == "":
                raise ValueError("材料名称不能为空")

            young_modulus = self._validate_finite_number(young_modulus, "弹性模量")
            poisson_ratio = self._validate_finite_number(poisson_ratio, "泊松比")
            thickness = self._validate_finite_number(thickness, "厚度")
            plane_mode = self._normalize_plane_mode(plane_mode)

            material = Material(
                id=self._next_id(self._model.materials),
                name=normalized_name,
                young_modulus=young_modulus,
                poisson_ratio=poisson_ratio,
                thickness=thickness,
                plane_mode=plane_mode,
            )
        except ValueError as exc:
            self.set_status_text(f"添加材料失败：{exc}")
            return False

        self._invalidate_results_after_model_change()
        self._model.materials.append(material)

        self.notify_model_stats_changed()
        self._notify_material_data_changed()
        self._notify_selected_element_changed()
        self.set_status_text(f"已添加材料 {material.id}：{material.name}")
        return True

    @Slot(str, str, str, str, str, result=bool)
    def add_material_by_text(
        self,
        name: str,
        young_modulus_text: str,
        poisson_ratio_text: str,
        thickness_text: str,
        plane_mode: str,
    ) -> bool:
        try:
            young_modulus = self._parse_float_text(young_modulus_text, "弹性模量")
            poisson_ratio = self._parse_float_text(poisson_ratio_text, "泊松比")
            thickness = self._parse_float_text(thickness_text, "厚度")
        except ValueError as exc:
            self.set_status_text(f"添加材料失败：{exc}")
            return False

        return self.add_material(name, young_modulus, poisson_ratio, thickness, plane_mode)

    @Slot(int, str, float, float, float, str, result=bool)
    def update_material(
        self,
        material_id: int,
        name: str,
        young_modulus: float,
        poisson_ratio: float,
        thickness: float,
        plane_mode: str,
    ) -> bool:
        material = self._find_material_by_id(material_id)
        if material is None:
            self.set_status_text(f"更新材料失败：不存在编号为 {material_id} 的材料")
            return False

        try:
            normalized_name = name.strip()
            if normalized_name == "":
                raise ValueError("材料名称不能为空")

            young_modulus = self._validate_finite_number(young_modulus, "弹性模量")
            poisson_ratio = self._validate_finite_number(poisson_ratio, "泊松比")
            thickness = self._validate_finite_number(thickness, "厚度")
            plane_mode = self._normalize_plane_mode(plane_mode)

            if young_modulus <= 0:
                raise ValueError("Young modulus must be greater than zero")
            if thickness <= 0:
                raise ValueError("Thickness must be greater than zero")
            if not (-1.0 <= poisson_ratio <= 0.5):
                raise ValueError("Poisson ratio must be between -1 and 0.5")
        except ValueError as exc:
            self.set_status_text(f"更新材料失败：{exc}")
            return False

        self._invalidate_results_after_model_change()

        material.name = normalized_name
        material.young_modulus = young_modulus
        material.poisson_ratio = poisson_ratio
        material.thickness = thickness
        material.plane_mode = plane_mode

        self._notify_material_data_changed()
        self._notify_selected_element_changed()
        self.set_status_text(f"已更新材料 {material.id}：{material.name}")
        return True

    @Slot(int, str, str, str, str, result=bool)
    def update_material_by_text(
        self,
        material_id: int,
        name: str,
        young_modulus_text: str,
        poisson_ratio_text: str,
        thickness_text: str,
        plane_mode: str,
    ) -> bool:
        try:
            young_modulus = self._parse_float_text(young_modulus_text, "弹性模量")
            poisson_ratio = self._parse_float_text(poisson_ratio_text, "泊松比")
            thickness = self._parse_float_text(thickness_text, "厚度")
        except ValueError as exc:
            self.set_status_text(f"更新材料失败：{exc}")
            return False

        return self.update_material(
            material_id,
            name,
            young_modulus,
            poisson_ratio,
            thickness,
            plane_mode,
        )

    @Slot(int, result=bool)
    def delete_material(self, material_id: int) -> bool:
        material = self._find_material_by_id(material_id)
        if material is None:
            self.set_status_text(f"删除材料失败：不存在编号为 {material_id} 的材料")
            return False

        used_element_ids = self._material_is_used_by_elements(material_id)
        if used_element_ids:
            joined_ids = ", ".join(str(item) for item in used_element_ids)
            self.set_status_text(
                f"删除材料失败：材料 {material_id} 正被单元 {joined_ids} 引用"
            )
            return False

        self._invalidate_results_after_model_change()
        self._model.materials = [item for item in self._model.materials if item.id != material_id]

        self.notify_model_stats_changed()
        self._notify_material_data_changed()
        self._notify_selected_element_changed()
        self.set_status_text(f"已删除材料 {material_id}")
        return True

    @Slot(int, int, result=bool)
    def assign_material_to_element(self, element_id: int, material_id: int) -> bool:
        element = self._find_element_by_id(element_id)
        if element is None:
            self.set_status_text(f"分配材料失败：不存在编号为 {element_id} 的单元")
            return False

        material = self._find_material_by_id(material_id)
        if material is None:
            self.set_status_text(f"分配材料失败：不存在编号为 {material_id} 的材料")
            return False

        self._invalidate_results_after_model_change()
        element.material_id = material.id

        self._notify_element_data_changed()
        self._notify_selected_element_changed()
        self.set_status_text(f"已为单元 {element.id} 分配材料 {material.id}：{material.name}")
        return True

    @Slot(int, result=bool)
    def assign_material_to_selected_element(self, material_id: int) -> bool:
        element = self._get_selected_element()
        if element is None:
            self.set_status_text("分配材料失败：当前没有选中任何单元")
            return False

        return self.assign_material_to_element(element.id, material_id)

    # =========================
    # 阶段7：约束管理接口
    # =========================

    @Slot(int, bool, bool, float, float, result=bool)
    def set_constraint(
        self,
        node_id: int,
        ux_fixed: bool,
        uy_fixed: bool,
        ux_value: float,
        uy_value: float,
    ) -> bool:
        node = self._find_node_by_id(node_id)
        if node is None:
            self.set_status_text(f"设置约束失败：不存在编号为 {node_id} 的节点")
            return False

        try:
            ux_value = self._validate_finite_number(ux_value, "ux_value")
            uy_value = self._validate_finite_number(uy_value, "uy_value")

            if not ux_fixed:
                ux_value = 0.0
            if not uy_fixed:
                uy_value = 0.0

            if not ux_fixed and not uy_fixed:
                raise ValueError("Constraint must fix at least one direction(ux or uy)")
        except ValueError as exc:
            self.set_status_text(f"设置约束失败：{exc}")
            return False

        self._invalidate_results_after_model_change()

        constraint = self._find_constraint_by_node_id(node_id)
        if constraint is None:
            constraint = Constraint(
                id=self._next_id(self._model.constraints),
                node_id=node_id,
                ux_fixed=ux_fixed,
                uy_fixed=uy_fixed,
                ux_value=ux_value,
                uy_value=uy_value,
            )
            self._model.constraints.append(constraint)
        else:
            constraint.ux_fixed = ux_fixed
            constraint.uy_fixed = uy_fixed
            constraint.ux_value = ux_value
            constraint.uy_value = uy_value

        self.notify_model_stats_changed()
        self._notify_boundary_data_changed()
        if self._selected_node_id == node_id:
            self._notify_selected_node_changed()
        self.set_status_text(f"已设置节点 {node_id} 约束")
        return True

    @Slot(int, bool, bool, str, str, result=bool)
    def set_constraint_by_text(
        self,
        node_id: int,
        ux_fixed: bool,
        uy_fixed: bool,
        ux_value_text: str,
        uy_value_text: str,
    ) -> bool:
        try:
            ux_value = 0.0 if not ux_fixed else self._parse_float_text(ux_value_text, "ux_value")
            uy_value = 0.0 if not uy_fixed else self._parse_float_text(uy_value_text, "uy_value")
        except ValueError as exc:
            self.set_status_text(f"设置约束失败：{exc}")
            return False

        return self.set_constraint(node_id, ux_fixed, uy_fixed, ux_value, uy_value)

    @Slot(bool, bool, float, float, result=bool)
    def set_selected_node_constraint(
        self,
        ux_fixed: bool,
        uy_fixed: bool,
        ux_value: float,
        uy_value: float,
    ) -> bool:
        node = self._get_selected_node()
        if node is None:
            self.set_status_text("设置约束失败：当前没有选中任何节点")
            return False

        return self.set_constraint(node.id, ux_fixed, uy_fixed, ux_value, uy_value)

    @Slot(bool, bool, str, str, result=bool)
    def set_selected_node_constraint_by_text(
        self,
        ux_fixed: bool,
        uy_fixed: bool,
        ux_value_text: str,
        uy_value_text: str,
    ) -> bool:
        node = self._get_selected_node()
        if node is None:
            self.set_status_text("设置约束失败：当前没有选中任何节点")
            return False

        return self.set_constraint_by_text(
            node.id,
            ux_fixed,
            uy_fixed,
            ux_value_text,
            uy_value_text,
        )

    @Slot(int, result=bool)
    def clear_constraint(self, node_id: int) -> bool:
        if self._find_node_by_id(node_id) is None:
            self.set_status_text(f"清除约束失败：不存在编号为 {node_id} 的节点")
            return False

        old_count = len(self._model.constraints)
        self._model.constraints = [item for item in self._model.constraints if item.node_id != node_id]

        if len(self._model.constraints) == old_count:
            self.set_status_text(f"清除约束失败：节点 {node_id} 当前没有约束")
            return False

        self._invalidate_results_after_model_change()

        self.notify_model_stats_changed()
        self._notify_boundary_data_changed()
        if self._selected_node_id == node_id:
            self._notify_selected_node_changed()
        self.set_status_text(f"已清除节点 {node_id} 约束")
        return True

    @Slot(result=bool)
    def clear_selected_node_constraint(self) -> bool:
        node = self._get_selected_node()
        if node is None:
            self.set_status_text("清除约束失败：当前没有选中任何节点")
            return False

        return self.clear_constraint(node.id)

    # =========================
    # 阶段7：载荷管理接口
    # =========================

    @Slot(int, float, float, result=bool)
    def set_load(self, node_id: int, fx: float, fy: float) -> bool:
        node = self._find_node_by_id(node_id)
        if node is None:
            self.set_status_text(f"设置载荷失败：不存在编号为 {node_id} 的节点")
            return False

        try:
            fx = self._validate_finite_number(fx, "fx")
            fy = self._validate_finite_number(fy, "fy")
            if abs(fx) < 1e-15 and abs(fy) < 1e-15:
                raise ValueError("Fx & Fy must not both be zero")
        except ValueError as exc:
            self.set_status_text(f"设置载荷失败：{exc}")
            return False

        self._invalidate_results_after_model_change()

        load = self._find_load_by_node_id(node_id)
        if load is None:
            load = Load(
                id=self._next_id(self._model.loads),
                node_id=node_id,
                fx=fx,
                fy=fy,
                load_type="nodal",
            )
            self._model.loads.append(load)
        else:
            load.fx = fx
            load.fy = fy
            load.load_type = "nodal"

        self.notify_model_stats_changed()
        self._notify_boundary_data_changed()
        if self._selected_node_id == node_id:
            self._notify_selected_node_changed()
        self.set_status_text(f"已设置节点 {node_id} 载荷")
        return True

    @Slot(int, str, str, result=bool)
    def set_load_by_text(self, node_id: int, fx_text: str, fy_text: str) -> bool:
        try:
            fx = self._parse_float_text(fx_text, "fx")
            fy = self._parse_float_text(fy_text, "fy")
        except ValueError as exc:
            self.set_status_text(f"设置载荷失败：{exc}")
            return False

        return self.set_load(node_id, fx, fy)

    @Slot(float, float, result=bool)
    def set_selected_node_load(self, fx: float, fy: float) -> bool:
        node = self._get_selected_node()
        if node is None:
            self.set_status_text("设置载荷失败：当前没有选中任何节点")
            return False

        return self.set_load(node.id, fx, fy)

    @Slot(str, str, result=bool)
    def set_selected_node_load_by_text(self, fx_text: str, fy_text: str) -> bool:
        node = self._get_selected_node()
        if node is None:
            self.set_status_text("设置载荷失败：当前没有选中任何节点")
            return False

        return self.set_load_by_text(node.id, fx_text, fy_text)

    @Slot(int, result=bool)
    def clear_load(self, node_id: int) -> bool:
        if self._find_node_by_id(node_id) is None:
            self.set_status_text(f"清除载荷失败：不存在编号为 {node_id} 的节点")
            return False

        old_count = len(self._model.loads)
        self._model.loads = [item for item in self._model.loads if item.node_id != node_id]

        if len(self._model.loads) == old_count:
            self.set_status_text(f"清除载荷失败：节点 {node_id} 当前没有载荷")
            return False

        self._invalidate_results_after_model_change()

        self.notify_model_stats_changed()
        self._notify_boundary_data_changed()
        if self._selected_node_id == node_id:
            self._notify_selected_node_changed()
        self.set_status_text(f"已清除节点 {node_id} 载荷")
        return True

    @Slot(result=bool)
    def clear_selected_node_load(self) -> bool:
        node = self._get_selected_node()
        if node is None:
            self.set_status_text("清除载荷失败：当前没有选中任何节点")
            return False

        return self.clear_load(node.id)

    @Slot()
    def add_test_node(self) -> None:
        preset_coords = [
            (0.0, 0.0),
            (100.0, 0.0),
            (0.0, 100.0),
            (100.0, 100.0),
            (200.0, 0.0),
            (200.0, 100.0),
        ]

        if len(self._model.nodes) < len(preset_coords):
            x, y = preset_coords[len(self._model.nodes)]
        else:
            index = len(self._model.nodes)
            x = float((index % 4) * 100.0)
            y = float((index // 4) * 100.0)

        self.add_node_by_coord(x, y)

    @Slot()
    def add_test_material(self) -> None:
        self.add_material(
            "测试钢材",
            210000000000.0,
            0.3,
            0.01,
            "stress",
        )

    @Slot()
    def add_test_element(self) -> None:
        if len(self._model.nodes) < 3:
            self.set_status_text("创建测试单元失败：至少需要 3 个节点")
            return

        self._invalidate_results_after_model_change()

        material_id = self._ensure_default_material()
        element_id = self._next_id(self._model.elements)

        last_three_nodes = self._model.nodes[-3:]
        node_ids = [node.id for node in last_three_nodes]

        try:
            node_ids = self._normalize_element_node_order_to_ccw(node_ids)
        except ValueError as exc:
            self.set_status_text(f"创建测试单元失败：{exc}")
            return

        element = Element(
            id=element_id,
            node_ids=node_ids,
            material_id=material_id,
            element_type="CST",
        )
        self._model.elements.append(element)

        self._set_selected_element_id(element.id)
        self._notify_element_data_changed()
        self.set_current_mode("element")
        self.set_status_text(
            f"已添加测试单元 {element_id}，连接节点 {node_ids[0]}-{node_ids[1]}-{node_ids[2]}"
        )
        self.notify_model_stats_changed()

    @Slot()
    def add_test_constraint(self) -> None:
        if not self._model.nodes:
            self.set_status_text("添加测试约束失败：请先创建节点")
            return

        target_node = None
        for node in self._model.nodes:
            if self._find_constraint_by_node_id(node.id) is None:
                target_node = node
                break

        if target_node is None:
            self.set_status_text("添加测试约束失败：所有节点都已有约束")
            return

        self.set_constraint(target_node.id, True, True, 0.0, 0.0)

    @Slot()
    def add_test_load(self) -> None:
        if not self._model.nodes:
            self.set_status_text("添加测试载荷失败：请先创建节点")
            return

        target_node = None
        for node in self._model.nodes:
            if self._find_load_by_node_id(node.id) is None:
                target_node = node
                break

        if target_node is None:
            self.set_status_text("添加测试载荷失败：所有节点都已有载荷")
            return

        self.set_load(target_node.id, 1000.0, 0.0)


    def _von_mises_plane_stress(self, stress_x: float, stress_y: float, tau_xy: float) -> float:
        value = stress_x * stress_x - stress_x * stress_y + stress_y * stress_y + 3.0 * tau_xy * tau_xy
        return math.sqrt(max(value, 0.0))

    @Slot("QVariant", result=bool)
    @Slot(str, result=bool)
    def export_node_results_to_csv(self, file_path) -> bool:
        try:
            if self._solver_result is None or not self._node_result_rows:
                raise ValueError("当前没有节点位移结果可导出，请先完成求解")

            path = self._csv_path_from_qml(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["node_id", "ux", "uy", "displacement_magnitude"])

                for row in sorted(self._node_result_rows, key=lambda item: int(item.get("node_id", -1))):
                    node_id = int(row.get("node_id", -1))
                    ux = float(row.get("ux", 0.0))
                    uy = float(row.get("uy", 0.0))
                    magnitude = math.sqrt(ux * ux + uy * uy)
                    writer.writerow([node_id, ux, uy, magnitude])

            self.set_status_text(f"已导出节点结果：{path.name}")
            return True

        except Exception as exc:
            self.set_status_text(f"导出节点结果失败：{exc}")
            return False

    @Slot("QVariant", result=bool)
    @Slot(str, result=bool)
    def export_element_results_to_csv(self, file_path) -> bool:
        try:
            if self._solver_result is None or not self._element_result_rows:
                raise ValueError("当前没有单元应力应变结果可导出，请先完成求解")

            path = self._csv_path_from_qml(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "element_id",
                    "strain_x",
                    "strain_y",
                    "gamma_xy",
                    "stress_x",
                    "stress_y",
                    "tau_xy",
                    "von_mises",
                ])

                for row in sorted(self._element_result_rows, key=lambda item: int(item.get("element_id", -1))):
                    element_id = int(row.get("element_id", -1))
                    strain_x = float(row.get("strain_x", 0.0))
                    strain_y = float(row.get("strain_y", 0.0))
                    gamma_xy = float(row.get("gamma_xy", 0.0))
                    stress_x = float(row.get("stress_x", 0.0))
                    stress_y = float(row.get("stress_y", 0.0))
                    tau_xy = float(row.get("tau_xy", 0.0))
                    von_mises = self._von_mises_plane_stress(stress_x, stress_y, tau_xy)

                    writer.writerow([
                        element_id,
                        strain_x,
                        strain_y,
                        gamma_xy,
                        stress_x,
                        stress_y,
                        tau_xy,
                        von_mises,
                    ])

            self.set_status_text(f"已导出单元结果：{path.name}")
            return True

        except Exception as exc:
            self.set_status_text(f"导出单元结果失败：{exc}")
            return False

    @Slot(result=bool)
    def solve_model(self) -> bool:
        try:
            fixed_count = self._normalize_all_element_node_orders_to_ccw()
            if fixed_count > 0:
                self._notify_element_data_changed()
            self._validate_model_before_solve()
            solver_result = solve_linear_static(self._model)

            self._solver_result = solver_result
            self._node_result_rows = self._build_node_result_rows(solver_result)
            self._element_result_rows = self._build_element_result_rows(solver_result)

            self.set_current_mode("result")
            self.set_status_text("求解完成")
            self._notify_solver_results_changed()
            return True

        except Exception as exc:
            self._clear_solver_results()
            self.set_current_mode("edit")
            self.set_status_text(f"求解失败：{exc}")
            return False

    @Slot(result=bool)
    def has_solver_result(self) -> bool:
        return self._solver_result is not None

    @Slot(result="QVariantList")
    def get_node_result_rows(self):
        return list(self._node_result_rows)

    @Slot(result="QVariantList")
    def get_element_result_rows(self):
        return list(self._element_result_rows)
