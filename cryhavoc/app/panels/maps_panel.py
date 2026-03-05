from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap

EXTENSIONS_MAPS = {".jpg", ".jpeg", ".png", ".bmp"}
THUMB_W, THUMB_H = 120, 80

class MapsPanel(QWidget):
    map_demandee = pyqtSignal(str)  # chemin absolu du fichier

    def __init__(self, dossier: Path, parent=None):
        super().__init__(parent)
        self.dossier = Path(dossier)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.liste = QListWidget()
        self.liste.setIconSize(QSize(THUMB_W, THUMB_H))
        self.liste.setGridSize(QSize(THUMB_W + 8, THUMB_H + 24))
        self.liste.setViewMode(QListWidget.ViewMode.IconMode)
        self.liste.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.liste.setWordWrap(True)
        layout.addWidget(self.liste)

        btn = QPushButton("Ajouter à la scène")
        btn.clicked.connect(self._ajouter)
        layout.addWidget(btn)

        self.liste.itemDoubleClicked.connect(self._on_double_clic)
        self._charger()

    def _charger(self):
        self.liste.clear()
        if not self.dossier.exists():
            return
        for f in sorted(self.dossier.iterdir()):
            if f.suffix.lower() in EXTENSIONS_MAPS:
                item = QListWidgetItem(f.name)
                pix = QPixmap(str(f))
                if not pix.isNull():
                    thumb = pix.scaled(THUMB_W, THUMB_H,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                    item.setIcon(QIcon(thumb))
                self.liste.addItem(item)

    def _on_double_clic(self, item):
        self.map_demandee.emit(str(self.dossier / item.text()))

    def _ajouter(self):
        item = self.liste.currentItem()
        if item:
            self.map_demandee.emit(str(self.dossier / item.text()))
