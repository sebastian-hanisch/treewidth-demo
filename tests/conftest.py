"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Die Handrechnungen stehen in den Tests (test_algorithm.py): Pfad P4, Dreieck mit Pendel, Viereck C4, Fünfeck C5, K4, Stern, 3×3-Gitter, Petersen-Graph."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import twd_scenario as S  # noqa: E402


@pytest.fixture
def path4():
    """Pfad 0-1-2-3: ein Baum, Baumweite 1."""
    return S.path_graph(4).adj


@pytest.fixture
def paw():
    """Dreieck 0-1-2 mit Pendel 3 an Knoten 2: chordal, ω = 3, Baumweite 2."""
    return S.triangle_with_pendant().adj


@pytest.fixture
def c4():
    """Viereck: Baumweite 2, nicht chordal (eine Sehne fehlt)."""
    return S.ring_graph(4).adj


@pytest.fixture
def c5():
    """Fünfeck: Baumweite 2, zwei Sehnen fehlen."""
    return S.ring_graph(5).adj


@pytest.fixture
def k4():
    return S.complete_graph(4).adj
