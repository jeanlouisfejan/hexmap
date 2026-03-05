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
