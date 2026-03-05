from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QColor, QPen

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

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        if not self.grille_visible:
            return
        pen = QPen(QColor(100, 100, 200, 80))
        pen.setWidth(0)  # cosmetic pen (1px à l'écran peu importe le zoom)
        painter.setPen(pen)

        cw, ch = self._cell_w, self._cell_h
        ox, oy = self._offset_x, self._offset_y

        # Première ligne/colonne visible
        left = ox + ((rect.left() - ox) // cw) * cw
        top = oy + ((rect.top() - oy) // ch) * ch

        x = left
        while x <= rect.right() + cw:
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += cw
        y = top
        while y <= rect.bottom() + ch:
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += ch

    def snap_position(self, x: float, y: float) -> tuple[float, float]:
        if not self.snap_actif:
            return x, y
        cw, ch = self._cell_w, self._cell_h
        ox, oy = self._offset_x, self._offset_y
        col = round((x - ox) / cw)
        row = round((y - oy) / ch)
        return ox + col * cw + cw / 2, oy + row * ch + ch / 2

    def activer_placement(self, pixmap, callback):
        self.cancel_placement()
        ghost = QGraphicsPixmapItem(pixmap)
        ghost.setOpacity(0.5)
        ghost.setZValue(100)
        ghost.setPos(-9999, -9999)
        self.addItem(ghost)
        self._ghost = ghost
        self._placement_callback = callback
        self._mode_placement = True

    def cancel_placement(self):
        if self._ghost:
            self.removeItem(self._ghost)
            self._ghost = None
        self._mode_placement = False
        self._placement_callback = None

    def placement_actif(self) -> bool:
        return bool(self._mode_placement)
