from PyQt6.QtWidgets import QGraphicsPixmapItem

class MapGraphicsItem(QGraphicsPixmapItem):
    def __init__(self, map_item, pixmap):
        super().__init__(pixmap)
        self.map_item = map_item
        self.setFlags(
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPos(map_item.x, map_item.y)

    def itemChange(self, change, value):
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            self.map_item.x = value.x()
            self.map_item.y = value.y()
        return super().itemChange(change, value)


class PionGraphicsItem(QGraphicsPixmapItem):
    def __init__(self, pion, pixmap, dossier_pions):
        super().__init__(pixmap)
        self.pion = pion
        self.dossier_pions = dossier_pions
        self.setFlags(
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(10)

    def itemChange(self, change, value):
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            self.pion.x = value.x()
            self.pion.y = value.y()
        return super().itemChange(change, value)

    def _chemin_image(self) -> str:
        from pathlib import Path
        key = self.pion.image_key()
        return str(Path(self.dossier_pions) / f"{key}.jpg")

    def rafraichir_image(self):
        from PyQt6.QtGui import QPixmap
        pix = QPixmap(self._chemin_image())
        if not pix.isNull():
            self.setPixmap(pix)


class MarqueurGraphicsItem(QGraphicsPixmapItem):
    def __init__(self, marqueur, pixmap):
        super().__init__(pixmap)
        self.marqueur = marqueur
        self.setFlags(
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsPixmapItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(10)

    def itemChange(self, change, value):
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            self.marqueur.x = value.x()
            self.marqueur.y = value.y()
        return super().itemChange(change, value)
