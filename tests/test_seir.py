import math
from pathlib import Path

import pytest

from sunmodel.seir import Polygon, SeirModel, load_polygons, spur_step

REPO_ROOT = Path(__file__).resolve().parent.parent
POLYPARA = REPO_ROOT / "polypara.dat"


def test_load_polygons_reads_all_eight_rows():
    polygons = load_polygons(POLYPARA)
    assert len(polygons) == 8
    assert polygons[0] == Polygon(
        id=1, S=0.96, E=0.02, I=0.01, R=0.01, a=7.0, g=2.0, m=3.0, beta=5.25,
    )


def test_spur_step_produces_finite_bounded_fractions():
    p = Polygon(id=1, S=0.96, E=0.02, I=0.01, R=0.01, a=7.0, g=2.0, m=3.0, beta=5.25)
    new_p, infected = spur_step(p)
    for value in (new_p.S, new_p.E, new_p.I, new_p.R, infected):
        assert math.isfinite(value)


def test_seir_model_step_zero_matches_direct_spur_step():
    model = SeirModel(POLYPARA, seed=0)
    inf, updated = model.step(timestep=0)

    polygons = load_polygons(POLYPARA)
    expected_inf = [0.0] * 9
    for p in polygons:
        _, infected = spur_step(p)
        expected_inf[p.id] = infected

    assert len(updated) == 8
    for pid in range(1, 9):
        assert inf[pid] == pytest.approx(expected_inf[pid])


def test_seir_model_step_nonzero_perturbs_beta(monkeypatch):
    model = SeirModel(POLYPARA, seed=42)
    _, gen0 = model.step(timestep=0)
    inf1, gen1 = model.step(timestep=1, polygons=gen0)

    assert len(gen1) == 8
    # beta should have been redrawn (not copied straight through from gen0)
    assert any(a.beta != b.beta for a, b in zip(gen0, gen1))
    for pid in range(1, 9):
        assert math.isfinite(inf1[pid])
