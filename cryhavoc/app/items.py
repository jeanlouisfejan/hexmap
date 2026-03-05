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

    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()

        # Actions changer état
        labels_état = {"": "Sain", "_b": "Blessé", "_s": "Sonné", "_m": "Mort"}
        for état in self.pion.états_disponibles:
            label = labels_état.get(état, état)
            a = menu.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.pion.état == état)
            a.setData(("état", état))

        # Monter/Démonter si applicable
        if self.pion.peut_monter:
            menu.addSeparator()
            if self.pion.monté:
                a = menu.addAction("Démonter")
                a.setData(("monter", False))
            else:
                a = menu.addAction("Monter")
                a.setData(("monter", True))

        menu.addSeparator()
        a_retirer = menu.addAction("Retirer")
        a_retirer.setData(("retirer",))
        a_supprimer = menu.addAction("Supprimer")
        a_supprimer.setData(("supprimer",))

        action = menu.exec(event.screenPos().toPoint())
        if not action:
            return
        data = action.data()
        if not data:
            return

        if data[0] == "état":
            self.pion.état = data[1]
            self.rafraichir_image()
        elif data[0] == "monter":
            self.pion.monté = data[1]
            self.rafraichir_image()
        elif data[0] == "retirer":
            self.scene().removeItem(self)
        elif data[0] == "supprimer":
            self.scene().removeItem(self)


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
