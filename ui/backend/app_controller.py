from PySide6.QtCore import QObject, Signal, Slot, Property


class AppController(QObject):
    status_text_changed = Signal()
    current_mode_changed = Signal()

    def __init__(self):
        super().__init__()
        self._status_text = "Ready"
        self._current_mode = "none"

    @Property(str, notify=status_text_changed)
    def status_text(self):
        return self._status_text

    @Property(str, notify=current_mode_changed)
    def current_mode(self):
        return self._current_mode

    def set_status_text(self, text: str) -> None:
        if self._status_text != text:
            self._status_text = text
            self.status_text_changed.emit()

    def set_current_mode(self, mode: str) -> None:
        if self._current_mode != mode:
            self._current_mode = mode
            self.current_mode_changed.emit()

    @Slot()
    def new_model(self) -> None:
        self.set_status_text("已创建空模型")
        self.set_current_mode("none")

    @Slot()
    def set_node_mode(self) -> None:
        self.set_current_mode("node")
        self.set_status_text("已切换到节点模式")

    @Slot()
    def set_element_mode(self) -> None:
        self.set_current_mode("element")
        self.set_status_text("已切换到单元模式")