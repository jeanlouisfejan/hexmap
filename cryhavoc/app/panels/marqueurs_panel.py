from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from app.scanner import scanner_marqueurs

class MarqueursPanel(QWidget):
    marqueur_selectionne = pyqtSignal(object)  # Marqueur

    def __init__(self, dossier: Path, parent=None):
        super().__init__(parent)
        self.dossier = Path(dossier)
        self._marqueurs = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.liste = QListWidget()
        self.liste.setIconSize(QSize(48, 48))
        layout.addWidget(self.liste)

        self.liste.itemDoubleClicked.connect(self._on_double_clic)
        self._charger()

    def _charger(self):
        self.liste.clear()
        self._marqueurs = []
        if not self.dossier.exists():
            return
        self._marqueurs = scanner_marqueurs(self.dossier)
        for m in self._marqueurs:
            item = QListWidgetItem(m.nom)
            if Path(m.fichier).exists():
                pix = QPixmap(m.fichier).scaled(
                    48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                item.setIcon(QIcon(pix))
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.liste.addItem(item)

    def _on_double_clic(self, item):
        m = item.data(Qt.ItemDataRole.UserRole)
        if m:
            self.marqueur_selectionne.emit(m)
