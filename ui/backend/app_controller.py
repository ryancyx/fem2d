from PySide6.QtCore import QObject, Property, Signal, Slot

from model.constraint import Constraint
from model.element import Element
from model.fem_model import FEMModel
from model.load import Load
from model.material import Material
from model.node import Node


class AppController(QObject):
    status_text_changed = Signal()
    current_mode_changed = Signal()
    model_stats_changed = Signal()

    def __init__(self):
        super().__init__()
        self._status_text = "就绪"
        self._current_mode = "none"
        self._model = FEMModel()

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

    @Slot()
    def new_model(self) -> None:
        self._model = FEMModel()
        self.set_current_mode("none")
        self.set_status_text("已新建空模型")
        self.notify_model_stats_changed()

    @Slot()
    def set_node_mode(self) -> None:
        self.set_current_mode("node")
        self.set_status_text("已切换到节点模式")

    @Slot()
    def set_element_mode(self) -> None:
        self.set_current_mode("element")
        self.set_status_text("已切换到单元模式")

    @Slot()
    def add_test_node(self) -> None:
        node_id = self._next_id(self._model.nodes)

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

        node = Node(id=node_id, x=x, y=y)
        self._model.nodes.append(node)

        self.set_current_mode("node")
        self.set_status_text(f"已添加测试节点 {node_id} ({x:.1f}, {y:.1f})")
        self.notify_model_stats_changed()

    @Slot()
    def add_test_material(self) -> None:
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
