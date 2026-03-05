from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter

class BoardView(QGraphicsView):
    ZOOM_FACTOR = 1.15
    ZOOM_MIN = 0.05
    ZOOM_MAX = 10.0

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._zoom_level = 1.0

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        if self._zoom_level * self.ZOOM_FACTOR <= self.ZOOM_MAX:
            self.scale(self.ZOOM_FACTOR, self.ZOOM_FACTOR)
            self._zoom_level *= self.ZOOM_FACTOR

    def zoom_out(self):
        if self._zoom_level / self.ZOOM_FACTOR >= self.ZOOM_MIN:
            self.scale(1 / self.ZOOM_FACTOR, 1 / self.ZOOM_FACTOR)
            self._zoom_level /= self.ZOOM_FACTOR

    def zoom_reset(self):
        self.resetTransform()
        self._zoom_level = 1.0

    def mouseMoveEvent(self, event):
        if self.scene().placement_actif():
            scene_pos = self.mapToScene(event.pos())
            ghost = self.scene()._ghost
            if ghost:
                ghost.setPos(
                    scene_pos.x() - ghost.pixmap().width() / 2,
                    scene_pos.y() - ghost.pixmap().height() / 2
                )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self.scene().placement_actif() and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            sx, sy = self.scene().snap_position(scene_pos.x(), scene_pos.y())
            self.scene()._placement_callback(QPointF(sx, sy))
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.scene().cancel_placement()
        super().keyPressEvent(event)
