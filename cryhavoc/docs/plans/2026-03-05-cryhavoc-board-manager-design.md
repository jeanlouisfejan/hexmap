# Cry Havoc Board Manager — Design v1

## Contexte

Application PyQt6 de gestion de plateau pour wargame hot-seat.
Jeu : Cry Havoc (type médiéval, maps illustrées, pions individuels).

---

## Architecture générale

`QMainWindow` mono-fenêtre avec `QSplitter` horizontal :
- **Panneau gauche** : `QTabWidget` (Maps, Pions, Marqueurs, Aide)
- **Panneau droit** : `QGraphicsView` + `QGraphicsScene`

Tout synchrone sur le thread principal. Pas de multi-fenêtre, pas de threads.

---

## Convention de nommage des fichiers

```
nom.jpg           # sain, à pied
nom_b.jpg         # blessé, à pied
nom_s.jpg         # sonné, à pied
nom_m.jpg         # mort, à pied
nom_c.jpg         # sain, monté
nom_bc.jpg        # blessé, monté
nom_sc.jpg        # sonné, monté
```

Détection automatique des états disponibles par scan du dossier `pions/`.
Tous les fichiers sont en `.jpg`. Les marqueurs (`marqueurs/`) ont une image unique par marqueur.

---

## Modèle de données

```python
@dataclass
class Pion:
    nom: str
    états_disponibles: list[str]   # sous-ensemble de ["", "_b", "_s", "_m"]
    peut_monter: bool              # True si fichiers *c.jpg détectés
    état: str                      # état courant : "" | "_b" | "_s" | "_m"
    monté: bool                    # True si actuellement monté
    x: float
    y: float

@dataclass
class ConfigGrille:
    cell_w: int
    cell_h: int
    offset_x: int
    offset_y: int
    rotation: int                  # 0 ou 90

@dataclass
class MapItem:
    fichier: str
    x: float
    y: float
    grille: ConfigGrille
```

---

## Panneau gauche — Onglets

### Onglet Maps
- Liste des fichiers dans `./maps/` (jpg, bmp, png)
- Double-clic → ajoute la map à la scène (positionnée à droite de la dernière)
- Bouton "Supprimer de la scène" pour retirer une map

### Onglet Pions
- Liste avec miniature de tous les pions détectés dans `./pions/`
- Double-clic → active le mode placement (Option C) :
  - Le pion suit le curseur sur la scène (preview à 50% d'opacité)
  - Clic gauche sur la scène → pose le pion
  - Échap → annule

### Onglet Marqueurs
- Identique à Pions, sans gestion d'états ni montage

### Onglet Aide
- Liste des fichiers `.html` / `.txt` dans `./aide/`
- Affichage dans un `QTextBrowser` (HTML ou texte brut)

---

## Scène de jeu

### Maps
- Chaque map est un `QGraphicsPixmapItem` déplaçable
- Positionnement initial : côte à côte sur l'axe X
- Taille des pions : proportionnelle à la taille de la map (ratio configurable, défaut ~5% de la largeur map)

### Pions et marqueurs
- `QGraphicsPixmapItem` superposés aux maps
- `ItemIsMovable` : clic-glisser pour déplacer
- Rubber-band selection : cliquer-glisser sur zone vide → sélection multiple déplaçable
- Clic droit → menu contextuel :
  - Changer état (sain / blessé / sonné / mort) — seulement états disponibles
  - Monter / Démonter (si `peut_monter`)
  - Retirer (remet dans le panneau)
  - Supprimer

### Zoom
- Molette souris : zoom centré sur le curseur
- Menu Vue : Zoom+ / Zoom- / Réinitialiser

---

## Grille overlay

- Dessinée dans `QGraphicsScene.drawBackground()` → zoomable et déplaçable automatiquement
- Toggle via menu Vue → "Afficher grille"
- Configurée par map via un dialog "Config grille" :
  - `cell_w`, `cell_h` : taille d'une cellule (px)
  - `offset_x`, `offset_y` : décalage pour aligner avec les lignes imprimées
  - Bouton "Pivoter 90°" : permute `cell_w` ↔ `cell_h`
- Snapping optionnel (toggle) : au dépôt d'un pion, centre sur la cellule la plus proche
- Config sauvegardée par map dans le JSON

---

## Menus

```
Fichier
  Nouveau plateau
  Ouvrir plateau...     (.json)
  Enregistrer
  Enregistrer sous...
  Quitter

Édition
  Annuler     (Ctrl+Z)
  Refaire     (Ctrl+Y)
  Supprimer sélection

Vue
  Zoom +      (Ctrl++)
  Zoom -      (Ctrl+-)
  Zoom réinitialiser
  Afficher grille (toggle)
  Snapping grille (toggle)
  Config grille...

Aide
  À propos
```

---

## Format de sauvegarde JSON

```json
{
  "maps": [
    {
      "fichier": "maps/Crossroads.jpg",
      "x": 0,
      "y": 0,
      "grille": {
        "cell_w": 64,
        "cell_h": 64,
        "offset_x": 0,
        "offset_y": 0,
        "rotation": 0
      }
    }
  ],
  "pions": [
    {
      "nom": "tybalt",
      "état": "_b",
      "monté": true,
      "x": 320,
      "y": 150
    }
  ]
}
```

---

## Placement de pions — Option C

1. Double-clic sur un pion dans le panneau
2. Le curseur change (CrossCursor)
3. Un `QGraphicsPixmapItem` fantôme (opacité 0.5) suit le curseur sur la scène
4. Clic gauche → le pion est posé à cette position (opacité 1.0)
5. Échap → annulation, fantôme supprimé

---

## Notes techniques

- Python 3.10+, PyQt6
- Undo/Redo via `QUndoStack` (commandes : AddPion, MovePion, RemovePion, ChangeEtat)
- Chargement paresseux des images maps (ne charger que lors du premier affichage)
- Dossiers attendus : `maps/`, `pions/`, `marqueurs/`, `aide/` (créés si absents)

---

## Hors scope v1

- Système de tours
- Log d'actions
- Résolution de combats DBU
- Réseau / multijoueur distant
