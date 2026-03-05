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
    """Placeholder — sera completé en Task 9."""
    pass


class MarqueurGraphicsItem(QGraphicsPixmapItem):
    """Placeholder — sera completé en Task 9."""
    pass
