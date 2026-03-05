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
