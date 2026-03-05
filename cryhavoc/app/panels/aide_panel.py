from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QTextBrowser

class AidePanel(QWidget):
    def __init__(self, dossier: Path, parent=None):
        super().__init__(parent)
        self.dossier = Path(dossier)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.liste = QListWidget()
        self.liste.setMaximumHeight(120)
        layout.addWidget(self.liste)

        self.browser = QTextBrowser()
        layout.addWidget(self.browser)

        self.liste.itemClicked.connect(self._afficher)
        self._charger()

    def _charger(self):
        self.liste.clear()
        if not self.dossier.exists():
            return
        for f in sorted(self.dossier.iterdir()):
            if f.suffix.lower() in {".html", ".txt"}:
                self.liste.addItem(QListWidgetItem(f.name))

    def _afficher(self, item):
        path = self.dossier / item.text()
        texte = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".html":
            self.browser.setHtml(texte)
        else:
            self.browser.setPlainText(texte)
