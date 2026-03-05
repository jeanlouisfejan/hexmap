from pathlib import Path
from app.models import Pion, Marqueur

ÉTATS = ["", "_b", "_s", "_m"]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
SUFFIXES_NON_BASE = {"_b", "_s", "_m", "_c", "_bc", "_sc", "_mc"}

def _est_nom_base(stem: str) -> bool:
    """Retourne True si le stem est un nom de base (pas un variant d'état/montage)."""
    for suf in SUFFIXES_NON_BASE:
        if stem.endswith(suf):
            return False
    return True

def scanner_pions(dossier: Path) -> list[Pion]:
    dossier = Path(dossier)
    if not dossier.exists():
        return []

    stems = {f.stem for f in dossier.iterdir() if f.suffix.lower() in EXTENSIONS}
    noms_base = sorted(s for s in stems if _est_nom_base(s))

    pions = []
    for nom in noms_base:
        états_dispo = []
        for état in ÉTATS:
            if état == "":
                fname = f"{nom}.jpg"
            else:
                fname = f"{nom}{état}.jpg"
            if (dossier / fname).exists():
                états_dispo.append(état)

        peut_monter = (dossier / f"{nom}_c.jpg").exists()
        pions.append(Pion(nom=nom, états_disponibles=états_dispo, peut_monter=peut_monter))

    return pions

def scanner_marqueurs(dossier: Path) -> list[Marqueur]:
    dossier = Path(dossier)
    if not dossier.exists():
        return []
    marqueurs = []
    for f in sorted(dossier.iterdir()):
        if f.suffix.lower() in EXTENSIONS:
            marqueurs.append(Marqueur(nom=f.stem, fichier=str(f)))
    return marqueurs
