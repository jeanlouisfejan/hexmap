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
        from app.panels.maps_panel import MapsPanel
        from app.panels.pions_panel import PionsPanel
        from app.panels.marqueurs_panel import MarqueursPanel
        from app.panels.aide_panel import AidePanel

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

        base = Path(__file__).parent.parent

        self.maps_panel = MapsPanel(base / "maps")
        self.maps_panel.map_demandee.connect(self._ajouter_map)
        self.tabs.addTab(self.maps_panel, "Maps")

        self.pions_panel = PionsPanel(base / "pions")
        self.pions_panel.pion_selectionne.connect(self._activer_placement_pion)
        self.tabs.addTab(self.pions_panel, "Pions")

        self.marqueurs_panel = MarqueursPanel(base / "marqueurs")
        self.marqueurs_panel.marqueur_selectionne.connect(self._activer_placement_marqueur)
        self.tabs.addTab(self.marqueurs_panel, "Marqueurs")

        aide_path = base / "aide"
        aide_path.mkdir(exist_ok=True)
        self.aide_panel = AidePanel(aide_path)
        self.tabs.addTab(self.aide_panel, "Aide")

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

    # --- Slots fichier ---
    def _nouveau(self):
        self.scene.clear()
        self._maps_modeles.clear()
        self._map_items.clear()
        self._pions_modeles.clear()
        self._pion_items.clear()
        self._marqueurs_modeles.clear()
        self._marqueur_items.clear()
        self._fichier_sauvegarde = None
        self.setWindowTitle("Cry Havoc Board Manager")

    def _ouvrir(self):
        from PyQt6.QtWidgets import QFileDialog
        from app.persistence import charger
        from app.items import MapGraphicsItem, PionGraphicsItem, MarqueurGraphicsItem
        from PyQt6.QtGui import QPixmap
        f, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un plateau", "", "Plateau Cry Havoc (*.json)"
        )
        if not f:
            return
        self._nouveau()
        base = Path(__file__).parent.parent
        maps, pions, marqueurs = charger(Path(f))

        for m in maps:
            pix = QPixmap(m.fichier)
            if not pix.isNull():
                gi = MapGraphicsItem(m, pix)
                self.scene.addItem(gi)
                self._maps_modeles.append(m)
                self._map_items.append(gi)

        for p in pions:
            img = str(base / "pions" / f"{p.image_key()}.jpg")
            pix = QPixmap(img)
            if not pix.isNull():
                pix = self._scaler_pion(pix)
                gi = PionGraphicsItem(p, pix, str(base / "pions"))
                gi.setPos(p.x, p.y)
                self.scene.addItem(gi)
                self._pions_modeles.append(p)
                self._pion_items.append(gi)

        for m in marqueurs:
            pix = QPixmap(m.fichier)
            if not pix.isNull():
                pix = self._scaler_pion(pix)
                gi = MarqueurGraphicsItem(m, pix)
                gi.setPos(m.x, m.y)
                self.scene.addItem(gi)
                self._marqueurs_modeles.append(m)
                self._marqueur_items.append(gi)

        self._fichier_sauvegarde = f
        self.statusBar().showMessage(f"Ouvert : {f}", 3000)
        self.setWindowTitle(f"Cry Havoc — {Path(f).name}")

    def _enregistrer(self):
        if self._fichier_sauvegarde:
            self._faire_sauvegarde(self._fichier_sauvegarde)
        else:
            self._enregistrer_sous()

    def _enregistrer_sous(self):
        from PyQt6.QtWidgets import QFileDialog
        f, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le plateau", "", "Plateau Cry Havoc (*.json)"
        )
        if f:
            self._fichier_sauvegarde = f
            self._faire_sauvegarde(f)

    def _faire_sauvegarde(self, fichier: str):
        from app.persistence import sauvegarder
        sauvegarder(
            Path(fichier),
            self._maps_modeles,
            self._pions_modeles,
            self._marqueurs_modeles,
        )
        self.statusBar().showMessage(f"Sauvegardé : {fichier}", 3000)
        self.setWindowTitle(f"Cry Havoc — {Path(fichier).name}")

    def _annuler(self): pass
    def _refaire(self): pass
    def _supprimer_selection(self): pass
    def _toggle_grille(self):
        self.scene.set_grille_visible(self.grille_action.isChecked())
    def _toggle_snap(self):
        self.scene.snap_actif = self.snap_action.isChecked()
    def _config_grille(self):
        from app.dialogs.grid_config import GridConfigDialog
        from app.models import ConfigGrille
        from PyQt6.QtWidgets import QDialog
        config = ConfigGrille(
            cell_w=self.scene._cell_w,
            cell_h=self.scene._cell_h,
            offset_x=self.scene._offset_x,
            offset_y=self.scene._offset_y,
        )
        dlg = GridConfigDialog(config, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            c = dlg.get_config()
            self.scene.set_grille_config(c.cell_w, c.cell_h, c.offset_x, c.offset_y)
    def _a_propos(self): pass
    def _activer_placement_pion(self, pion):
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        from pathlib import Path
        import copy
        base = Path(__file__).parent.parent
        img = str(base / "pions" / f"{pion.nom}.jpg")
        pix = QPixmap(img)
        if pix.isNull():
            return
        pix = self._scaler_pion(pix)

        def placer(scene_pos):
            from app.items import PionGraphicsItem
            nouveau = copy.copy(pion)
            nouveau.x = scene_pos.x() - pix.width() / 2
            nouveau.y = scene_pos.y() - pix.height() / 2
            gi = PionGraphicsItem(nouveau, pix, str(base / "pions"))
            gi.setPos(nouveau.x, nouveau.y)
            self.scene.addItem(gi)
            self._pions_modeles.append(nouveau)
            self._pion_items.append(gi)
            self.scene.cancel_placement()
            self.view.unsetCursor()

        self.scene.activer_placement(pix, placer)
        self.view.setFocus()
        self.view.setCursor(Qt.CursorShape.CrossCursor)

    def _activer_placement_marqueur(self, marqueur):
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        import copy
        pix = QPixmap(marqueur.fichier)
        if pix.isNull():
            return
        pix = self._scaler_pion(pix)

        def placer(scene_pos):
            from app.items import MarqueurGraphicsItem
            m = copy.copy(marqueur)
            m.x = scene_pos.x() - pix.width() / 2
            m.y = scene_pos.y() - pix.height() / 2
            gi = MarqueurGraphicsItem(m, pix)
            gi.setPos(m.x, m.y)
            self.scene.addItem(gi)
            self._marqueurs_modeles.append(m)
            self._marqueur_items.append(gi)
            self.scene.cancel_placement()
            self.view.unsetCursor()

        self.scene.activer_placement(pix, placer)
        self.view.setFocus()
        self.view.setCursor(Qt.CursorShape.CrossCursor)
    def _ajouter_map(self, fichier: str):
        from PyQt6.QtGui import QPixmap
        from app.models import MapItem
        from app.items import MapGraphicsItem
        x = 0.0
        for item in self.scene.items():
            if isinstance(item, MapGraphicsItem):
                x = max(x, item.pos().x() + item.pixmap().width())
        pix = QPixmap(fichier)
        if pix.isNull():
            return
        map_model = MapItem(fichier=fichier, x=x, y=0.0)
        gi = MapGraphicsItem(map_model, pix)
        self.scene.addItem(gi)
        self._maps_modeles.append(map_model)
        self._map_items.append(gi)
    def _scaler_pion(self, pix):
        from PyQt6.QtCore import Qt
        return pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
