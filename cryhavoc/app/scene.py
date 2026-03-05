from PyQt6.QtWidgets import QGraphicsScene

class BoardScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.grille_visible = False
        self.snap_actif = False
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self._cell_w = 64
        self._cell_h = 64
        self._offset_x = 0
        self._offset_y = 0
        self._ghost = None
        self._mode_placement = False
        self._placement_callback = None

    def set_grille_visible(self, visible: bool):
        self.grille_visible = visible
        self.update()

    def set_grille_config(self, cell_w, cell_h, offset_x, offset_y):
        self._cell_w = cell_w
        self._cell_h = cell_h
        self._offset_x = offset_x
        self._offset_y = offset_y
        self.update()

    def placement_actif(self) -> bool:
        return bool(self._mode_placement)

    def cancel_placement(self):
        if self._ghost:
            self.removeItem(self._ghost)
            self._ghost = None
        self._mode_placement = False
        self._placement_callback = None

    def activer_placement(self, pixmap, callback):
        pass

    def snap_position(self, x, y):
        return x, y
