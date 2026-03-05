# Cry Havoc Board Manager — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Application PyQt6 de gestion de plateau wargame hot-seat avec maps assemblées, pions déplaçables, états multiples, grille overlay configurable et sauvegarde JSON.

**Architecture:** QMainWindow avec QSplitter (panneau gauche = QTabWidget, panneau droit = QGraphicsView/QGraphicsScene). Modèles de données en dataclasses Python. Undo/Redo via QUndoStack.

**Tech Stack:** Python 3.10+, PyQt6, pytest, pytest-qt, dataclasses, json

---

## Structure des fichiers

```
cryhavoc/
  main.py
  requirements.txt
  app/
    __init__.py
    models.py
    scanner.py           # détection pions par scan dossier
    persistence.py       # save/load JSON
    undo_commands.py     # QUndoCommand subclasses
    scene.py             # BoardScene(QGraphicsScene)
    view.py              # BoardView(QGraphicsView)
    main_window.py       # MainWindow(QMainWindow)
    panels/
      __init__.py
      maps_panel.py
      pions_panel.py
      marqueurs_panel.py
      aide_panel.py
    dialogs/
      __init__.py
      grid_config.py
  tests/
    conftest.py
    test_models.py
    test_scanner.py
    test_persistence.py
```

---

### Task 1 : Setup projet

**Files:**
- Create: `requirements.txt`
- Create: `main.py`
- Create: `app/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Créer requirements.txt**

```
PyQt6>=6.6.0
pytest>=8.0.0
pytest-qt>=4.4.0
```

**Step 2: Créer main.py**

```python
import sys
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Cry Havoc Board Manager")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Step 3: Créer app/__init__.py vide**

```python
```

**Step 4: Créer tests/conftest.py**

```python
import pytest
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
```

**Step 5: Installer les dépendances**

Run: `pip install -r requirements.txt`
Expected: installation sans erreur

**Step 6: Commit**

```bash
git add requirements.txt main.py app/__init__.py tests/conftest.py
git commit -m "feat: project setup with PyQt6 and pytest"
```

---

### Task 2 : Modèles de données

**Files:**
- Create: `app/models.py`
- Create: `tests/test_models.py`

**Step 1: Écrire les tests**

```python
# tests/test_models.py
from app.models import Pion, MapItem, ConfigGrille

def test_pion_defaults():
    p = Pion(nom="tybalt", états_disponibles=["", "_b", "_s", "_m"],
             peut_monter=True)
    assert p.état == ""
    assert p.monté is False
    assert p.x == 0.0
    assert p.y == 0.0

def test_pion_image_key_unmounted():
    p = Pion(nom="tybalt", états_disponibles=["", "_b"], peut_monter=False)
    p.état = "_b"
    assert p.image_key() == "tybalt_b"

def test_pion_image_key_mounted():
    p = Pion(nom="tybalt", états_disponibles=["", "_b"], peut_monter=True)
    p.état = "_b"
    p.monté = True
    assert p.image_key() == "tybalt_bc"

def test_pion_image_key_sain_mounted():
    p = Pion(nom="guy", états_disponibles=["", "_b"], peut_monter=True)
    p.monté = True
    assert p.image_key() == "guy_c"

def test_config_grille_defaults():
    g = ConfigGrille()
    assert g.cell_w == 64
    assert g.cell_h == 64
    assert g.rotation == 0

def test_config_grille_pivot():
    g = ConfigGrille(cell_w=64, cell_h=48)
    g.pivoter()
    assert g.cell_w == 48
    assert g.cell_h == 64
    assert g.rotation == 90

def test_map_item_defaults():
    m = MapItem(fichier="maps/test.jpg")
    assert m.x == 0.0
    assert m.y == 0.0
    assert m.grille is not None
```

**Step 2: Run pour vérifier l'échec**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — ModuleNotFoundError

**Step 3: Implémenter app/models.py**

```python
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class ConfigGrille:
    cell_w: int = 64
    cell_h: int = 64
    offset_x: int = 0
    offset_y: int = 0
    rotation: int = 0  # 0 ou 90

    def pivoter(self):
        self.cell_w, self.cell_h = self.cell_h, self.cell_w
        self.rotation = 90 if self.rotation == 0 else 0

@dataclass
class Pion:
    nom: str
    états_disponibles: list[str]
    peut_monter: bool = False
    état: str = ""
    monté: bool = False
    x: float = 0.0
    y: float = 0.0

    def image_key(self) -> str:
        """Retourne le nom de fichier sans extension."""
        suffix = self.état.lstrip("_")  # "" | "b" | "s" | "m"
        monture = "c" if self.monté else ""
        if suffix:
            return f"{self.nom}_{suffix}{monture}"
        elif monture:
            return f"{self.nom}_{monture}"
        else:
            return self.nom

@dataclass
class MapItem:
    fichier: str
    x: float = 0.0
    y: float = 0.0
    grille: ConfigGrille = field(default_factory=ConfigGrille)

@dataclass
class Marqueur:
    nom: str
    fichier: str
    x: float = 0.0
    y: float = 0.0
```

**Step 4: Run tests**

Run: `pytest tests/test_models.py -v`
Expected: tous PASS

**Step 5: Commit**

```bash
git add app/models.py tests/test_models.py
git commit -m "feat: data models Pion, MapItem, ConfigGrille"
```

---

### Task 3 : Scanner de pions

**Files:**
- Create: `app/scanner.py`
- Create: `tests/test_scanner.py`

**Step 1: Écrire les tests**

```python
# tests/test_scanner.py
import os, tempfile, pytest
from pathlib import Path
from app.scanner import scanner_pions, scanner_marqueurs

@pytest.fixture
def dossier_pions(tmp_path):
    """Crée un dossier temporaire avec des fichiers pions factices."""
    fichiers = [
        "tybalt.jpg", "tybalt_b.jpg", "tybalt_s.jpg", "tybalt_m.jpg",
        "tybalt_c.jpg", "tybalt_bc.jpg",
        "ceol.jpg", "ceol_b.jpg",
    ]
    for f in fichiers:
        (tmp_path / f).touch()
    return tmp_path

def test_scanner_detecte_noms(dossier_pions):
    pions = scanner_pions(dossier_pions)
    noms = [p.nom for p in pions]
    assert "tybalt" in noms
    assert "ceol" in noms

def test_scanner_detecte_etats(dossier_pions):
    pions = {p.nom: p for p in scanner_pions(dossier_pions)}
    assert pions["tybalt"].états_disponibles == ["", "_b", "_s", "_m"]
    assert pions["ceol"].états_disponibles == ["", "_b"]

def test_scanner_detecte_montage(dossier_pions):
    pions = {p.nom: p for p in scanner_pions(dossier_pions)}
    assert pions["tybalt"].peut_monter is True
    assert pions["ceol"].peut_monter is False

@pytest.fixture
def dossier_marqueurs(tmp_path):
    for f in ["fleche.jpg", "feu.jpg"]:
        (tmp_path / f).touch()
    return tmp_path

def test_scanner_marqueurs(dossier_marqueurs):
    marqueurs = scanner_marqueurs(dossier_marqueurs)
    noms = [m.nom for m in marqueurs]
    assert "fleche" in noms
    assert "feu" in noms
```

**Step 2: Run pour vérifier l'échec**

Run: `pytest tests/test_scanner.py -v`
Expected: FAIL — ModuleNotFoundError

**Step 3: Implémenter app/scanner.py**

```python
from pathlib import Path
from app.models import Pion, Marqueur

ÉTATS = ["", "_b", "_s", "_m"]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

def scanner_pions(dossier: Path) -> list[Pion]:
    dossier = Path(dossier)
    # Collecter tous les stems (noms sans extension)
    stems = {f.stem for f in dossier.iterdir() if f.suffix.lower() in EXTENSIONS}

    # Identifier les noms de base (sans suffixe état ni 'c')
    suffixes_connus = {"_b", "_s", "_m", "_c", "_bc", "_sc", "_mc"}
    noms_base = set()
    for stem in stems:
        est_base = True
        for suf in suffixes_connus:
            if stem.endswith(suf):
                est_base = False
                break
        if est_base:
            noms_base.add(stem)

    pions = []
    for nom in sorted(noms_base):
        états = [e for e in ÉTATS if (dossier / f"{nom}{e.lstrip('_') and '_' + e.lstrip('_') or ''}.jpg").exists()
                 or (dossier / f"{nom}{e}.jpg").exists()]
        # Simplification : chercher les fichiers existants
        états_dispo = []
        for e in ÉTATS:
            fname = f"{nom}{e}.jpg" if e else f"{nom}.jpg"
            if (dossier / fname).exists():
                états_dispo.append(e)
        peut_monter = (dossier / f"{nom}_c.jpg").exists() or (dossier / f"{nom}c.jpg").exists()
        pions.append(Pion(nom=nom, états_disponibles=états_dispo, peut_monter=peut_monter))
    return pions

def scanner_marqueurs(dossier: Path) -> list[Marqueur]:
    dossier = Path(dossier)
    marqueurs = []
    for f in sorted(dossier.iterdir()):
        if f.suffix.lower() in EXTENSIONS:
            marqueurs.append(Marqueur(nom=f.stem, fichier=str(f)))
    return marqueurs
```

**Step 4: Run tests**

Run: `pytest tests/test_scanner.py -v`
Expected: tous PASS

**Step 5: Corriger si nécessaire**

Si les tests de détection d'états échouent, vérifier la logique de construction du nom de fichier dans `scanner_pions`. Les fichiers `.touch()` sont vides mais existent — `.exists()` retourne True.

**Step 6: Commit**

```bash
git add app/scanner.py tests/test_scanner.py
git commit -m "feat: pion and marker file scanner"
```

---

### Task 4 : Persistance JSON

**Files:**
- Create: `app/persistence.py`
- Create: `tests/test_persistence.py`

**Step 1: Écrire les tests**

```python
# tests/test_persistence.py
import json, tempfile
from pathlib import Path
from app.models import Pion, MapItem, ConfigGrille, Marqueur
from app.persistence import sauvegarder, charger

def plateau_test():
    maps = [MapItem(fichier="maps/test.jpg", x=0, y=0,
                    grille=ConfigGrille(cell_w=64, cell_h=48, offset_x=5, offset_y=3))]
    pions = [Pion(nom="tybalt", états_disponibles=["", "_b"], peut_monter=True,
                  état="_b", monté=True, x=100.0, y=200.0)]
    marqueurs = [Marqueur(nom="feu", fichier="marqueurs/feu.jpg", x=50.0, y=60.0)]
    return maps, pions, marqueurs

def test_roundtrip(tmp_path):
    maps, pions, marqueurs = plateau_test()
    fichier = tmp_path / "plateau.json"
    sauvegarder(fichier, maps, pions, marqueurs)
    maps2, pions2, marqueurs2 = charger(fichier)

    assert len(maps2) == 1
    assert maps2[0].fichier == "maps/test.jpg"
    assert maps2[0].grille.cell_w == 64
    assert maps2[0].grille.cell_h == 48
    assert maps2[0].grille.offset_x == 5

    assert len(pions2) == 1
    assert pions2[0].nom == "tybalt"
    assert pions2[0].état == "_b"
    assert pions2[0].monté is True
    assert pions2[0].x == 100.0

    assert len(marqueurs2) == 1
    assert marqueurs2[0].nom == "feu"
```

**Step 2: Run pour vérifier l'échec**

Run: `pytest tests/test_persistence.py -v`
Expected: FAIL — ModuleNotFoundError

**Step 3: Implémenter app/persistence.py**

```python
import json
from pathlib import Path
from app.models import Pion, MapItem, ConfigGrille, Marqueur

def sauvegarder(fichier: Path, maps: list[MapItem],
                pions: list[Pion], marqueurs: list[Marqueur]):
    data = {
        "maps": [
            {
                "fichier": m.fichier, "x": m.x, "y": m.y,
                "grille": {
                    "cell_w": m.grille.cell_w, "cell_h": m.grille.cell_h,
                    "offset_x": m.grille.offset_x, "offset_y": m.grille.offset_y,
                    "rotation": m.grille.rotation,
                }
            }
            for m in maps
        ],
        "pions": [
            {
                "nom": p.nom, "état": p.état, "monté": p.monté,
                "x": p.x, "y": p.y,
                "états_disponibles": p.états_disponibles,
                "peut_monter": p.peut_monter,
            }
            for p in pions
        ],
        "marqueurs": [
            {"nom": m.nom, "fichier": m.fichier, "x": m.x, "y": m.y}
            for m in marqueurs
        ],
    }
    Path(fichier).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def charger(fichier: Path) -> tuple[list[MapItem], list[Pion], list[Marqueur]]:
    data = json.loads(Path(fichier).read_text(encoding="utf-8"))
    maps = [
        MapItem(
            fichier=m["fichier"], x=m["x"], y=m["y"],
            grille=ConfigGrille(
                cell_w=m["grille"]["cell_w"], cell_h=m["grille"]["cell_h"],
                offset_x=m["grille"]["offset_x"], offset_y=m["grille"]["offset_y"],
                rotation=m["grille"]["rotation"],
            )
        )
        for m in data.get("maps", [])
    ]
    pions = [
        Pion(
            nom=p["nom"], états_disponibles=p["états_disponibles"],
            peut_monter=p["peut_monter"], état=p["état"],
            monté=p["monté"], x=p["x"], y=p["y"],
        )
        for p in data.get("pions", [])
    ]
    marqueurs = [
        Marqueur(nom=m["nom"], fichier=m["fichier"], x=m["x"], y=m["y"])
        for m in data.get("marqueurs", [])
    ]
    return maps, pions, marqueurs
```

**Step 4: Run tests**

Run: `pytest tests/test_persistence.py -v`
Expected: tous PASS

**Step 5: Commit**

```bash
git add app/persistence.py tests/test_persistence.py
git commit -m "feat: JSON save/load with maps, pions, marqueurs"
```

---

### Task 5 : Fenêtre principale — squelette

**Files:**
- Create: `app/main_window.py`
- Create: `app/panels/__init__.py`

**Step 1: Créer app/panels/__init__.py vide**

```python
```

**Step 2: Implémenter app/main_window.py (squelette)**

```python
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QTabWidget, QWidget,
    QMenuBar, QStatusBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cry Havoc Board Manager")
        self.resize(1400, 900)
        self._setup_ui()
        self._setup_menus()

    def _setup_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # Panneau gauche
        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(220)
        self.tabs.setMaximumWidth(320)
        splitter.addWidget(self.tabs)

        # Panneau droit (placeholder pour l'instant)
        from app.view import BoardView
        from app.scene import BoardScene
        self.scene = BoardScene()
        self.view = BoardView(self.scene)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(1, 1)

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
        aide = mb.addMenu("Aide")
        aide.addAction(self._action("À propos", self._a_propos))

        self.setStatusBar(QStatusBar())

    def _action(self, texte, slot=None, shortcut=None) -> QAction:
        a = QAction(texte, self)
        if slot:
            a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        return a

    # Slots placeholder
    def _nouveau(self): pass
    def _ouvrir(self): pass
    def _enregistrer(self): pass
    def _enregistrer_sous(self): pass
    def _annuler(self): pass
    def _refaire(self): pass
    def _supprimer_selection(self): pass
    def _toggle_grille(self): pass
    def _toggle_snap(self): pass
    def _config_grille(self): pass
    def _a_propos(self): pass
```

**Step 3: Vérifier que l'app se lance**

Run: `python main.py`
Expected: fenêtre vide avec menus s'affiche sans erreur

**Step 4: Commit**

```bash
git add app/main_window.py app/panels/__init__.py
git commit -m "feat: main window skeleton with menus"
```

---

### Task 6 : Scene et View

**Files:**
- Create: `app/scene.py`
- Create: `app/view.py`

**Step 1: Implémenter app/scene.py**

```python
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen

class BoardScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.grille_visible = False
        self.snap_actif = False
        self.setSceneRect(-5000, -5000, 10000, 10000)
        # Config grille globale (par défaut, chaque map peut avoir la sienne)
        self._cell_w = 64
        self._cell_h = 64
        self._offset_x = 0
        self._offset_y = 0

    def set_grille_visible(self, visible: bool):
        self.grille_visible = visible
        self.update()

    def set_grille_config(self, cell_w, cell_h, offset_x, offset_y):
        self._cell_w = cell_w
        self._cell_h = cell_h
        self._offset_x = offset_x
        self._offset_y = offset_y
        self.update()

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        if not self.grille_visible:
            return
        pen = QPen(QColor(100, 100, 200, 80))
        pen.setWidth(0)  # cosmetic pen (1px à l'écran)
        painter.setPen(pen)

        cw, ch = self._cell_w, self._cell_h
        ox, oy = self._offset_x, self._offset_y

        left = rect.left() - ((rect.left() - ox) % cw)
        top = rect.top() - ((rect.top() - oy) % ch)

        x = left
        while x <= rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += cw
        y = top
        while y <= rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += ch

    def snap_position(self, x: float, y: float) -> tuple[float, float]:
        """Retourne la position snappée au centre de la cellule la plus proche."""
        if not self.snap_actif:
            return x, y
        cw, ch = self._cell_w, self._cell_h
        ox, oy = self._offset_x, self._offset_y
        col = round((x - ox) / cw)
        row = round((y - oy) / ch)
        return ox + col * cw + cw / 2, oy + row * ch + ch / 2
```

**Step 2: Implémenter app/view.py**

```python
from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
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

    def mousePressEvent(self, event):
        # Déléguer au mode placement si actif (géré par main_window)
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.scene().cancel_placement()
        super().keyPressEvent(event)
```

**Step 3: Ajouter cancel_placement à BoardScene**

Dans `app/scene.py`, ajouter à `BoardScene` :

```python
    def cancel_placement(self):
        """Annule le mode placement (géré dans Task 9)."""
        pass
```

**Step 4: Lancer l'app et vérifier**

Run: `python main.py`
Expected: fenêtre avec vue vide, zoom à la molette fonctionne

**Step 5: Commit**

```bash
git add app/scene.py app/view.py
git commit -m "feat: BoardScene with grid overlay and BoardView with zoom"
```

---

### Task 7 : Onglet Maps

**Files:**
- Create: `app/panels/maps_panel.py`
- Modify: `app/main_window.py`
- Create: `app/items.py` (QGraphicsItems custom)

**Step 1: Créer app/items.py**

```python
from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtCore import Qt

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
```

**Step 2: Créer app/panels/maps_panel.py**

```python
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton
)
from PyQt6.QtCore import pyqtSignal

EXTENSIONS_MAPS = {".jpg", ".jpeg", ".png", ".bmp"}

class MapsPanel(QWidget):
    map_demandee = pyqtSignal(str)  # fichier absolu

    def __init__(self, dossier: Path, parent=None):
        super().__init__(parent)
        self.dossier = Path(dossier)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.liste = QListWidget()
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
                self.liste.addItem(QListWidgetItem(f.name))

    def _on_double_clic(self, item):
        self.map_demandee.emit(str(self.dossier / item.text()))

    def _ajouter(self):
        item = self.liste.currentItem()
        if item:
            self.map_demandee.emit(str(self.dossier / item.text()))
```

**Step 3: Connecter MapsPanel dans main_window.py**

Dans `_setup_ui`, après création de `self.scene` et `self.view` :

```python
        from app.panels.maps_panel import MapsPanel
        from app.panels.pions_panel import PionsPanel      # Task 8
        from app.panels.marqueurs_panel import MarqueursPanel  # Task 8
        from app.panels.aide_panel import AidePanel        # Task 8
        from pathlib import Path

        base = Path(__file__).parent.parent

        self.maps_panel = MapsPanel(base / "maps")
        self.maps_panel.map_demandee.connect(self._ajouter_map)
        self.tabs.addTab(self.maps_panel, "Maps")
```

Ajouter à `MainWindow` :

```python
    def _ajouter_map(self, fichier: str):
        from PyQt6.QtGui import QPixmap
        from app.models import MapItem, ConfigGrille
        from app.items import MapGraphicsItem
        # Calculer position X (à droite de la dernière map)
        x = 0
        for item in self.scene.items():
            if isinstance(item, MapGraphicsItem):
                x = max(x, item.pos().x() + item.pixmap().width())
        pix = QPixmap(fichier)
        if pix.isNull():
            return
        map_model = MapItem(fichier=fichier, x=x, y=0)
        gi = MapGraphicsItem(map_model, pix)
        self.scene.addItem(gi)
        self._maps_modeles.append(map_model)
        self._map_items.append(gi)
```

Ajouter dans `__init__` de `MainWindow` après `_setup_ui()` :

```python
        self._maps_modeles = []
        self._map_items = []
        self._pions_modeles = []
        self._pion_items = []
        self._marqueurs_modeles = []
        self._marqueur_items = []
        self._fichier_sauvegarde = None
```

**Step 4: Tester manuellement**

Run: `python main.py`
Expected: onglet Maps liste les fichiers du dossier maps/, double-clic ajoute la map à la scène

**Step 5: Commit**

```bash
git add app/items.py app/panels/maps_panel.py app/main_window.py
git commit -m "feat: maps panel with add-to-scene"
```

---

### Task 8 : Onglets Pions, Marqueurs, Aide

**Files:**
- Create: `app/panels/pions_panel.py`
- Create: `app/panels/marqueurs_panel.py`
- Create: `app/panels/aide_panel.py`
- Create: `app/dialogs/__init__.py`

**Step 1: Créer app/dialogs/__init__.py vide**

```python
```

**Step 2: Créer app/panels/pions_panel.py**

```python
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from app.scanner import scanner_pions
from app.models import Pion

class PionsPanel(QWidget):
    pion_selectionne = pyqtSignal(object)  # Pion

    def __init__(self, dossier: Path, parent=None):
        super().__init__(parent)
        self.dossier = Path(dossier)
        self._pions: list[Pion] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.liste = QListWidget()
        self.liste.setIconSize(QSize(48, 48))
        layout.addWidget(self.liste)

        self.liste.itemDoubleClicked.connect(self._on_double_clic)
        self._charger()

    def _charger(self):
        self.liste.clear()
        self._pions = []
        if not self.dossier.exists():
            return
        self._pions = scanner_pions(self.dossier)
        for pion in self._pions:
            item = QListWidgetItem(pion.nom)
            img_path = self.dossier / f"{pion.nom}.jpg"
            if img_path.exists():
                pix = QPixmap(str(img_path)).scaled(
                    48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                item.setIcon(QIcon(pix))
            item.setData(Qt.ItemDataRole.UserRole, pion)
            self.liste.addItem(item)

    def _on_double_clic(self, item):
        pion = item.data(Qt.ItemDataRole.UserRole)
        if pion:
            self.pion_selectionne.emit(pion)
```

**Step 3: Créer app/panels/marqueurs_panel.py**

```python
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from app.scanner import scanner_marqueurs
from app.models import Marqueur

class MarqueursPanel(QWidget):
    marqueur_selectionne = pyqtSignal(object)  # Marqueur

    def __init__(self, dossier: Path, parent=None):
        super().__init__(parent)
        self.dossier = Path(dossier)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.liste = QListWidget()
        self.liste.setIconSize(QSize(48, 48))
        layout.addWidget(self.liste)
        self.liste.itemDoubleClicked.connect(self._on_double_clic)
        self._charger()

    def _charger(self):
        self.liste.clear()
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
```

**Step 4: Créer app/panels/aide_panel.py**

```python
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
```

**Step 5: Connecter les onglets dans main_window.py**

Remplacer le bloc commenté `# Task 8` dans `_setup_ui` par les vrais imports et connexions :

```python
        from app.panels.pions_panel import PionsPanel
        from app.panels.marqueurs_panel import MarqueursPanel
        from app.panels.aide_panel import AidePanel

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
```

Ajouter slots placeholder dans `MainWindow` :

```python
    def _activer_placement_pion(self, pion): pass
    def _activer_placement_marqueur(self, marqueur): pass
```

**Step 6: Créer les dossiers manquants au démarrage**

Dans `__init__` de `MainWindow`, avant `_setup_ui()` :

```python
        from pathlib import Path
        base = Path(__file__).parent.parent
        for d in ["maps", "pions", "marqueurs", "aide"]:
            (base / d).mkdir(exist_ok=True)
```

**Step 7: Tester manuellement**

Run: `python main.py`
Expected: 4 onglets visibles, Pions liste les pions avec miniatures

**Step 8: Commit**

```bash
git add app/panels/pions_panel.py app/panels/marqueurs_panel.py \
        app/panels/aide_panel.py app/dialogs/__init__.py app/main_window.py
git commit -m "feat: pions, marqueurs and aide panels"
```

---

### Task 9 : Mode placement — Option C

**Files:**
- Create: `app/items.py` (étoffer)
- Modify: `app/scene.py`
- Modify: `app/view.py`
- Modify: `app/main_window.py`

**Step 1: Ajouter PionGraphicsItem dans app/items.py**

```python
from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtCore import Qt

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
        self.setZValue(10)  # pions au-dessus des maps

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
```

**Step 2: Ajouter mode placement dans BoardScene**

Dans `app/scene.py`, ajouter attributs et méthodes à `BoardScene` :

```python
    def __init__(self):
        # ... existant ...
        self._ghost = None          # QGraphicsPixmapItem fantôme
        self._mode_placement = None  # "pion" | "marqueur" | None
        self._placement_callback = None

    def activer_placement(self, pixmap, callback):
        """Active le mode placement. callback(scene_pos) appelé au clic."""
        from PyQt6.QtWidgets import QGraphicsPixmapItem
        self.cancel_placement()
        ghost = QGraphicsPixmapItem(pixmap)
        ghost.setOpacity(0.5)
        ghost.setZValue(100)
        ghost.setPos(-9999, -9999)
        self.addItem(ghost)
        self._ghost = ghost
        self._placement_callback = callback
        self._mode_placement = True

    def cancel_placement(self):
        if self._ghost:
            self.removeItem(self._ghost)
            self._ghost = None
        self._mode_placement = False
        self._placement_callback = None

    def placement_actif(self) -> bool:
        return bool(self._mode_placement)
```

**Step 3: Gérer le mouvement du fantôme dans BoardView**

Dans `app/view.py`, surcharger `mouseMoveEvent` et `mousePressEvent` :

```python
    def mouseMoveEvent(self, event):
        if self.scene().placement_actif():
            scene_pos = self.mapToScene(event.pos())
            ghost = self.scene()._ghost
            if ghost:
                # Centrer le fantôme sur le curseur
                ghost.setPos(
                    scene_pos.x() - ghost.pixmap().width() / 2,
                    scene_pos.y() - ghost.pixmap().height() / 2
                )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        from PyQt6.QtCore import Qt
        if self.scene().placement_actif() and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            sx, sy = self.scene().snap_position(scene_pos.x(), scene_pos.y())
            from PyQt6.QtCore import QPointF
            self.scene()._placement_callback(QPointF(sx, sy))
            event.accept()
            return
        super().mousePressEvent(event)
```

**Step 4: Implémenter _activer_placement_pion dans main_window.py**

```python
    def _activer_placement_pion(self, pion):
        from PyQt6.QtGui import QPixmap
        from pathlib import Path
        import copy
        base = Path(__file__).parent.parent
        img = str(base / "pions" / f"{pion.nom}.jpg")
        pix = QPixmap(img)
        if pix.isNull():
            return
        # Redimensionner proportionnellement (environ 5% de la largeur de la première map)
        pix = self._scaler_pion(pix)

        def placer(scene_pos):
            from app.models import Pion
            from app.items import PionGraphicsItem
            import copy
            nouveau = copy.copy(pion)
            nouveau.x = scene_pos.x() - pix.width() / 2
            nouveau.y = scene_pos.y() - pix.height() / 2
            gi = PionGraphicsItem(nouveau, pix, str(base / "pions"))
            gi.setPos(nouveau.x, nouveau.y)
            self.scene.addItem(gi)
            self._pions_modeles.append(nouveau)
            self._pion_items.append(gi)
            self.scene.cancel_placement()

        self.scene.activer_placement(pix, placer)
        self.view.setFocus()
        self.view.setCursor(Qt.CursorShape.CrossCursor)

    def _scaler_pion(self, pix):
        from PyQt6.QtCore import Qt
        # Taille cible : ~60px (ajustable)
        return pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)

    def _activer_placement_marqueur(self, marqueur):
        from PyQt6.QtGui import QPixmap
        from pathlib import Path
        pix = QPixmap(marqueur.fichier)
        if pix.isNull():
            return
        pix = self._scaler_pion(pix)

        def placer(scene_pos):
            from app.items import MarqueurGraphicsItem
            import copy
            m = copy.copy(marqueur)
            m.x = scene_pos.x() - pix.width() / 2
            m.y = scene_pos.y() - pix.height() / 2
            gi = MarqueurGraphicsItem(m, pix)
            gi.setPos(m.x, m.y)
            self.scene.addItem(gi)
            self._marqueurs_modeles.append(m)
            self._marqueur_items.append(gi)
            self.scene.cancel_placement()

        self.scene.activer_placement(pix, placer)
        self.view.setFocus()
```

**Step 5: Ajouter MarqueurGraphicsItem dans app/items.py**

```python
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
```

**Step 6: Tester manuellement**

Run: `python main.py`
Expected: double-clic sur un pion → pion fantôme suit le curseur → clic → pion posé → Échap annule

**Step 7: Commit**

```bash
git add app/scene.py app/view.py app/items.py app/main_window.py
git commit -m "feat: placement mode option C with ghost preview"
```

---

### Task 10 : Menu contextuel des pions

**Files:**
- Modify: `app/items.py`

**Step 1: Ajouter contextMenuEvent à PionGraphicsItem**

```python
    def contextMenuEvent(self, event):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu = QMenu()

        # Changer état
        for état in self.pion.états_disponibles:
            label = {
                "": "Sain", "_b": "Blessé", "_s": "Sonné", "_m": "Mort"
            }.get(état, état)
            a = menu.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.pion.état == état)
            a.setData(("état", état))

        # Monter/Démonter
        if self.pion.peut_monter:
            menu.addSeparator()
            if self.pion.monté:
                menu.addAction("Démonter").setData(("monter", False))
            else:
                menu.addAction("Monter").setData(("monter", True))

        menu.addSeparator()
        menu.addAction("Retirer").setData(("retirer",))
        menu.addAction("Supprimer").setData(("supprimer",))

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
```

**Step 2: Tester manuellement**

Run: `python main.py`
Expected: clic droit sur un pion → menu avec états disponibles, monter/démonter si applicable

**Step 3: Commit**

```bash
git add app/items.py
git commit -m "feat: context menu for pions (state change, mount, remove)"
```

---

### Task 11 : Dialog config grille

**Files:**
- Create: `app/dialogs/grid_config.py`
- Modify: `app/main_window.py`

**Step 1: Créer app/dialogs/grid_config.py**

```python
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QSpinBox, QPushButton,
    QDialogButtonBox, QHBoxLayout, QVBoxLayout, QLabel
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
```

**Step 2: Connecter dans main_window.py**

Remplacer `_config_grille`, `_toggle_grille`, `_toggle_snap` :

```python
    def _toggle_grille(self):
        self.scene.set_grille_visible(self.grille_action.isChecked())

    def _toggle_snap(self):
        self.scene.snap_actif = self.snap_action.isChecked()

    def _config_grille(self):
        from app.dialogs.grid_config import GridConfigDialog
        from app.models import ConfigGrille
        config = ConfigGrille(
            cell_w=self.scene._cell_w,
            cell_h=self.scene._cell_h,
            offset_x=self.scene._offset_x,
            offset_y=self.scene._offset_y,
        )
        dlg = GridConfigDialog(config, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            c = dlg.get_config()
            self.scene.set_grille_config(c.cell_w, c.cell_h, c.offset_x, c.offset_y)
```

**Step 3: Tester manuellement**

Run: `python main.py`
Expected: Vue → Config grille → dialog s'ouvre → OK applique la grille → toggle l'affiche

**Step 4: Commit**

```bash
git add app/dialogs/grid_config.py app/main_window.py
git commit -m "feat: grid config dialog with pivot and snap toggle"
```

---

### Task 12 : Save / Load plateau complet

**Files:**
- Modify: `app/main_window.py`

**Step 1: Implémenter _enregistrer, _enregistrer_sous, _ouvrir, _nouveau**

```python
    def _enregistrer(self):
        if self._fichier_sauvegarde:
            self._faire_sauvegarde(self._fichier_sauvegarde)
        else:
            self._enregistrer_sous()

    def _enregistrer_sous(self):
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path
        f, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le plateau", "", "Plateau Cry Havoc (*.json)"
        )
        if f:
            self._fichier_sauvegarde = f
            self._faire_sauvegarde(f)

    def _faire_sauvegarde(self, fichier: str):
        from app.persistence import sauvegarder
        from pathlib import Path
        sauvegarder(
            Path(fichier),
            self._maps_modeles,
            self._pions_modeles,
            self._marqueurs_modeles,
        )
        self.statusBar().showMessage(f"Sauvegardé : {fichier}", 3000)

    def _ouvrir(self):
        from PyQt6.QtWidgets import QFileDialog
        from app.persistence import charger
        from app.items import MapGraphicsItem, PionGraphicsItem, MarqueurGraphicsItem
        from PyQt6.QtGui import QPixmap
        from pathlib import Path
        f, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un plateau", "", "Plateau Cry Havoc (*.json)"
        )
        if not f:
            return
        self._nouveau()
        maps, pions, marqueurs = charger(Path(f))
        base = Path(__file__).parent.parent

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

    def _nouveau(self):
        self.scene.clear()
        self._maps_modeles.clear()
        self._map_items.clear()
        self._pions_modeles.clear()
        self._pion_items.clear()
        self._marqueurs_modeles.clear()
        self._marqueur_items.clear()
        self._fichier_sauvegarde = None
```

**Step 2: Tester roundtrip**

Run: `python main.py`
Expected:
1. Ajouter maps + pions
2. Fichier → Enregistrer sous... → sauvegarder
3. Fichier → Nouveau → scène vide
4. Fichier → Ouvrir... → plateau restauré à l'identique

**Step 3: Commit**

```bash
git add app/main_window.py
git commit -m "feat: save/load JSON plateau with maps and pions"
```

---

### Task 13 : Supprimer sélection + finitions

**Files:**
- Modify: `app/main_window.py`

**Step 1: Implémenter _supprimer_selection**

```python
    def _supprimer_selection(self):
        from app.items import MapGraphicsItem, PionGraphicsItem, MarqueurGraphicsItem
        for item in self.scene.selectedItems():
            if isinstance(item, MapGraphicsItem):
                self._maps_modeles.remove(item.map_item)
                self._map_items.remove(item)
            elif isinstance(item, PionGraphicsItem):
                if item.pion in self._pions_modeles:
                    self._pions_modeles.remove(item.pion)
                if item in self._pion_items:
                    self._pion_items.remove(item)
            elif isinstance(item, MarqueurGraphicsItem):
                if item.marqueur in self._marqueurs_modeles:
                    self._marqueurs_modeles.remove(item.marqueur)
                if item in self._marqueur_items:
                    self._marqueur_items.remove(item)
            self.scene.removeItem(item)
```

**Step 2: Titre de fenêtre dynamique**

Dans `_faire_sauvegarde` et `_ouvrir`, ajouter :

```python
        from pathlib import Path
        self.setWindowTitle(f"Cry Havoc — {Path(fichier).name}")
```

Dans `_nouveau` :

```python
        self.setWindowTitle("Cry Havoc Board Manager")
```

**Step 3: Run tests unitaires complets**

Run: `pytest tests/ -v`
Expected: tous PASS

**Step 4: Commit final**

```bash
git add app/main_window.py
git commit -m "feat: delete selection and dynamic window title"
```

---

## Résumé des commits attendus

1. `feat: project setup with PyQt6 and pytest`
2. `feat: data models Pion, MapItem, ConfigGrille`
3. `feat: pion and marker file scanner`
4. `feat: JSON save/load with maps, pions, marqueurs`
5. `feat: main window skeleton with menus`
6. `feat: BoardScene with grid overlay and BoardView with zoom`
7. `feat: maps panel with add-to-scene`
8. `feat: pions, marqueurs and aide panels`
9. `feat: placement mode option C with ghost preview`
10. `feat: context menu for pions (state change, mount, remove)`
11. `feat: grid config dialog with pivot and snap toggle`
12. `feat: save/load JSON plateau with maps and pions`
13. `feat: delete selection and dynamic window title`
