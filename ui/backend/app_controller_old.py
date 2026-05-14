import math

from PySide6.QtCore import QObject, Property, Signal, Slot

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

    def __init__(self):
        super().__init__()
        self._status_text = "就绪"
        self._current_mode = "none"
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
        if element is None:
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
                    "material_id": int(element.material_id),
                    "element_type": str(element.element_type),
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

    def _set_selected_node_id(self, node_id: int | None) -> None:
        if self._selected_node_id != node_id:
            self._selected_node_id = node_id
            self._notify_selected_node_changed()

    def _set_selected_element_id(self, element_id: int | None) -> None:
        if self._selected_element_id != element_id:
            self._selected_element_id = element_id
            self._notify_selected_element_changed()

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

    def _parse_coordinate_text(self, text: str, name: str) -> float:
        stripped = text.strip()
        if stripped == "":
            raise ValueError(f"{name} 不能为空")

        try:
            value = float(stripped)
        except ValueError as exc:
            raise ValueError(f"{name} 不是合法数字") from exc

        return self._validate_coordinate(value, name)

    def _node_is_referenced(self, node_id: int) -> tuple[bool, str]:
        for element in self._model.elements:
            if node_id in element.node_ids:
                return True, f"节点 {node_id} 已被单元 {element.id} 引用，不能删除"

        for constraint in self._model.constraints:
            if constraint.node_id == node_id:
                return True, f"节点 {node_id} 已被约束 {constraint.id} 引用，不能删除"

        for load in self._model.loads:
            if load.node_id == node_id:
                return True, f"节点 {node_id} 已被载荷 {load.id} 引用，不能删除"

        return False, ""

    def _get_node_coords_by_id(self, node_id: int) -> tuple[float, float]:
        node = self._find_node_by_id(node_id)
        if node is None:
            raise ValueError(f"不存在编号为 {node_id} 的节点")
        return float(node.x), float(node.y)

    def _are_three_nodes_collinear(self, node_ids: list[int]) -> bool:
        if len(node_ids) != 3:
            raise ValueError("共线检查必须传入3个节点")

        x1, y1 = self._get_node_coords_by_id(node_ids[0])
        x2, y2 = self._get_node_coords_by_id(node_ids[1])
        x3, y3 = self._get_node_coords_by_id(node_ids[2])

        twice_area = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
        return abs(twice_area) < 1e-12

    def _element_with_same_nodes_exists(self, node_ids: list[int]) -> bool:
        target = tuple(sorted(node_ids))
        for element in self._model.elements:
            if tuple(sorted(element.node_ids)) == target:
                return True
        return False

    @Slot()
    def new_model(self) -> None:
        self._model = FEMModel()
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
            "material_id": int(element.material_id),
            "element_type": str(element.element_type),
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

        if self._selected_node_id == node_id:
            self._selected_node_id = None

        if node_id in self._selected_element_node_ids:
            self._selected_element_node_ids.remove(node_id)
            self._notify_element_selection_changed()

        self.set_current_mode("node")
        self.set_status_text(f"已删除节点 {node_id}")
        self.notify_model_stats_changed()
        self._notify_node_data_changed()
        self._notify_selected_node_changed()
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
            self._selected_element_id = None

        self.set_current_mode("element")
        self.set_status_text(f"已删除单元 {element_id}")
        self.notify_model_stats_changed()
        self._notify_element_data_changed()
        self._notify_selected_element_changed()
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

        if self._are_three_nodes_collinear(node_ids):
            self.set_status_text("创建单元失败：所选 3 个节点共线，不能构成三角形单元")
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
        self._invalidate_results_after_model_change()

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

        self.set_status_text(f"已添加测试材料 {material.name}")
        self.notify_model_stats_changed()

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

        self._invalidate_results_after_model_change()

        index = min(len(self._model.constraints), len(self._model.nodes) - 1)
        target_node = self._model.nodes[index]
        constraint_id = self._next_id(self._model.constraints)

        constraint = Constraint(
            id=constraint_id,
            node_id=target_node.id,
            ux_fixed=True,
            uy_fixed=True,
            ux_value=0.0,
            uy_value=0.0,
        )
        self._model.constraints.append(constraint)

        self.set_status_text(f"已在节点 {target_node.id} 上添加测试约束")
        self.notify_model_stats_changed()

    @Slot()
    def add_test_load(self) -> None:
        if not self._model.nodes:
            self.set_status_text("添加测试载荷失败：请先创建节点")
            return

        self._invalidate_results_after_model_change()

        index = min(len(self._model.loads), len(self._model.nodes) - 1)
        target_node = self._model.nodes[index]
        load_id = self._next_id(self._model.loads)

        load = Load(
            id=load_id,
            node_id=target_node.id,
            fx=1000.0,
            fy=0.0,
            load_type="nodal",
        )
        self._model.loads.append(load)

        self.set_status_text(f"已在节点 {target_node.id} 上添加测试载荷")
        self.notify_model_stats_changed()

    @Slot(result=bool)
    def solve_model(self) -> bool:
        try:
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