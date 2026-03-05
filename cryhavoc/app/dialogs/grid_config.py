from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QPushButton,
    QDialogButtonBox, QVBoxLayout
)
from app.models import ConfigGrille

class GridConfigDialog(QDialog):
    def __init__(self, config: ConfigGrille, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration de la grille")
        self.config = config
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.sb_cell_w = QSpinBox()
        self.sb_cell_w.setRange(4, 2000)
        self.sb_cell_w.setValue(config.cell_w)
        form.addRow("Largeur cellule (px):", self.sb_cell_w)

        self.sb_cell_h = QSpinBox()
        self.sb_cell_h.setRange(4, 2000)
        self.sb_cell_h.setValue(config.cell_h)
        form.addRow("Hauteur cellule (px):", self.sb_cell_h)

        self.sb_offset_x = QSpinBox()
        self.sb_offset_x.setRange(-2000, 2000)
        self.sb_offset_x.setValue(config.offset_x)
        form.addRow("Décalage X (px):", self.sb_offset_x)

        self.sb_offset_y = QSpinBox()
        self.sb_offset_y.setRange(-2000, 2000)
        self.sb_offset_y.setValue(config.offset_y)
        form.addRow("Décalage Y (px):", self.sb_offset_y)

        layout.addLayout(form)

        btn_pivot = QPushButton("Pivoter 90°")
        btn_pivot.clicked.connect(self._pivoter)
        layout.addWidget(btn_pivot)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _pivoter(self):
        w = self.sb_cell_w.value()
        h = self.sb_cell_h.value()
        self.sb_cell_w.setValue(h)
        self.sb_cell_h.setValue(w)

    def get_config(self) -> ConfigGrille:
        return ConfigGrille(
            cell_w=self.sb_cell_w.value(),
            cell_h=self.sb_cell_h.value(),
            offset_x=self.sb_offset_x.value(),
            offset_y=self.sb_offset_y.value(),
            rotation=self.config.rotation,
        )
