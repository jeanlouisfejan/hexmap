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
