from model.node import Node


class CanvasController:
    """阶段4：负责画布坐标变换与节点创建。"""

    def __init__(self) -> None:
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._next_node_id = 1
        self._nodes: list[Node] = []

    def set_view(self, zoom: float, pan_x: float, pan_y: float) -> None:
        if zoom <= 0:
            raise ValueError("zoom 必须大于 0。")
        self.zoom = zoom
        self.pan_x = pan_x
        self.pan_y = pan_y

    def screen_to_model(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        model_x = (screen_x - self.pan_x) / self.zoom
        model_y = (screen_y - self.pan_y) / self.zoom
        return model_x, model_y

    def model_to_screen(self, model_x: float, model_y: float) -> tuple[float, float]:
        screen_x = model_x * self.zoom + self.pan_x
        screen_y = model_y * self.zoom + self.pan_y
        return screen_x, screen_y

    def add_node_at_screen_pos(self, screen_x: float, screen_y: float) -> Node:
        model_x, model_y = self.screen_to_model(screen_x, screen_y)
        node = Node(id=self._next_node_id, x=model_x, y=model_y)
        self._nodes.append(node)
        self._next_node_id += 1
        return node

    def get_nodes(self) -> list[Node]:
        return list(self._nodes)

    def get_nodes_for_qml(self) -> list[dict[str, float | int]]:
        items: list[dict[str, float | int]] = []

        for node in self._nodes:
            screen_x, screen_y = self.model_to_screen(node.x, node.y)
            items.append(
                {
                    "id": node.id,
                    "model_x": node.x,
                    "model_y": node.y,
                    "screen_x": screen_x,
                    "screen_y": screen_y,
                }
            )

        return items

    def clear_nodes(self) -> None:
        self._nodes.clear()
        self._next_node_id = 1