from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QPainter

class BoardView(QGraphicsView):
    ZOOM_FACTOR = 1.15

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._zoom_level = 1.0

    def zoom_in(self):
        self.scale(self.ZOOM_FACTOR, self.ZOOM_FACTOR)
        self._zoom_level *= self.ZOOM_FACTOR

    def zoom_out(self):
        self.scale(1 / self.ZOOM_FACTOR, 1 / self.ZOOM_FACTOR)
        self._zoom_level /= self.ZOOM_FACTOR

    def zoom_reset(self):
        self.resetTransform()
        self._zoom_level = 1.0
