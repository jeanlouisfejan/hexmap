from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTabWidget,
    QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cry Havoc Board Manager")
        self.resize(1400, 900)

        # Créer les dossiers attendus
        base = Path(__file__).parent.parent
        for d in ["maps", "pions", "marqueurs", "aide"]:
            (base / d).mkdir(exist_ok=True)

        # Listes de suivi des éléments de scène
        self._maps_modeles = []
        self._map_items = []
        self._pions_modeles = []
        self._pion_items = []
        self._marqueurs_modeles = []
        self._marqueur_items = []
        self._fichier_sauvegarde = None

        self._setup_ui()
        self._setup_menus()

    def _setup_ui(self):
        from app.view import BoardView
        from app.scene import BoardScene

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(220)
        self.tabs.setMaximumWidth(320)
        splitter.addWidget(self.tabs)

        self.scene = BoardScene()
        self.view = BoardView(self.scene)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(1, 1)

        # Les onglets seront ajoutés dans les tâches suivantes
        # Pour l'instant, juste un placeholder
        from PyQt6.QtWidgets import QLabel
        placeholder = QLabel("Onglets à venir...")
        self.tabs.addTab(placeholder, "Maps")

    def _setup_menus(self):
        mb = self.menuBar()

        # Fichier
        fichier = mb.addMenu("Fichier")
        fichier.addAction(self._action("Nouveau plateau", self._nouveau, "Ctrl+N"))
        fichier.addAction(self._action("Ouvrir...", self._ouvrir, "Ctrl+O"))
        fichier.addSeparator()
        fichier.addAction(self._action("Enregistrer", self._enregistrer, "Ctrl+S"))
        fichier.addAction(self._action("Enregistrer sous...", self._enregistrer_sous, "Ctrl+Shift+S"))
        fichier.addSeparator()
        fichier.addAction(self._action("Quitter", self.close, "Ctrl+Q"))

        # Édition
        edition = mb.addMenu("Édition")
        self.undo_action = self._action("Annuler", self._annuler, "Ctrl+Z")
        self.redo_action = self._action("Refaire", self._refaire, "Ctrl+Y")
        edition.addAction(self.undo_action)
        edition.addAction(self.redo_action)
        edition.addSeparator()
        edition.addAction(self._action("Supprimer sélection", self._supprimer_selection, "Delete"))

        # Vue
        vue = mb.addMenu("Vue")
        vue.addAction(self._action("Zoom +", self.view.zoom_in, "Ctrl++"))
        vue.addAction(self._action("Zoom -", self.view.zoom_out, "Ctrl+-"))
        vue.addAction(self._action("Zoom réinitialiser", self.view.zoom_reset, "Ctrl+0"))
        vue.addSeparator()
        self.grille_action = self._action("Afficher grille", self._toggle_grille, "Ctrl+G")
        self.grille_action.setCheckable(True)
        vue.addAction(self.grille_action)
        self.snap_action = self._action("Snapping grille", self._toggle_snap, "Ctrl+Shift+G")
        self.snap_action.setCheckable(True)
        vue.addAction(self.snap_action)
        vue.addSeparator()
        vue.addAction(self._action("Config grille...", self._config_grille))

        # Aide
        aide_menu = mb.addMenu("Aide")
        aide_menu.addAction(self._action("À propos", self._a_propos))

        self.setStatusBar(QStatusBar())

    def _action(self, texte, slot=None, shortcut=None) -> QAction:
        a = QAction(texte, self)
        if slot:
            a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        return a

    # --- Slots placeholder ---
    def _nouveau(self): pass
    def _ouvrir(self): pass
    def _enregistrer(self): pass
    def _enregistrer_sous(self): pass
    def _annuler(self): pass
    def _refaire(self): pass
    def _supprimer_selection(self): pass
    def _toggle_grille(self):
        self.scene.set_grille_visible(self.grille_action.isChecked())
    def _toggle_snap(self):
        self.scene.snap_actif = self.snap_action.isChecked()
    def _config_grille(self): pass
    def _a_propos(self): pass
    def _activer_placement_pion(self, pion): pass
    def _activer_placement_marqueur(self, marqueur): pass
    def _ajouter_map(self, fichier: str): pass
    def _scaler_pion(self, pix): return pix
