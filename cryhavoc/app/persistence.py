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
