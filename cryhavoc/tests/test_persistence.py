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
