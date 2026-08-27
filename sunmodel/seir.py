"""SEIR (Susceptible/Exposed/Infected/Removed) submodel of solar-disk
"polygon" regions.

Port of the SPUR, ZCELLS and MOVES subroutines and the ran2 random
number generator in sun.f. The original SPUR routine is a numerical
relaxation of an SEIR system, borrowed wholesale from Olsen & Schaffer's
disease-spread model and repurposed here to represent 8 solar-disk
"polygon" regions.

Differences from the original FORTRAN:
  * State is kept in memory as a list of Polygon objects instead of
    being ping-ponged through TIMENEW.DAT/TIMEOLD.DAT.
  * The SAV/EAV/IAV/RAV history arrays are dropped: in the original they
    only feed a WRITE statement that is commented out (dead code), so
    only the state after the final (50th) relaxation step is ever used.
  * ran2's hand-rolled linear-congruential generator is replaced with
    Python's random.Random. Pass a seed to SeirModel for reproducible
    runs; the numeric stream will not match the original FORTRAN
    bit-for-bit.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

N_POLYGONS = 8  # 'icell' in the original
_RELAXATION_STEPS = 50  # 'J' in SPUR
_TIME_STEP = 0.002  # 'DELT' in SPUR
_CONVERGE_PCT = 0.00001  # 'CRIT' in SPUR
_AVG_LIFESPAN_MONTHS = 144.0  # 'MONTHS' in SPUR


@dataclass(frozen=True)
class Polygon:
    """One solar-disk region tracked by the SEIR submodel.

    S, E, I, R are the Susceptible/Exposed/Infected/Removed fractions;
    a, g, m are the model's latency/infectious/lifespan rate constants;
    beta is the contact-rate seed ('BETAB'/'B' in the original).
    """
    id: int
    S: float
    E: float
    I: float
    R: float
    a: float
    g: float
    m: float
    beta: float


def load_polygons(path: Path | str) -> List[Polygon]:
    """Read initial polygon parameters from polypara.dat.

    Whitespace-separated, one polygon per row after a title row:
    id, S, E, I, R, a, g, m, beta.

    Only the first N_POLYGONS rows are read, matching the original's
    "DO 22 K = 1, icell" loop (icell=8) -- any extra rows in the file
    (polypara.dat ships with 14) are left unread, same as in sun.f.
    """
    polygons: List[Polygon] = []
    with open(path) as f:
        next(f)  # title row
        for line in f:
            if len(polygons) == N_POLYGONS:
                break
            line = line.strip()
            if not line:
                continue
            pid, s, e, i, r, a, g, m, beta = line.split()
            polygons.append(Polygon(
                id=int(pid), S=float(s), E=float(e), I=float(i), R=float(r),
                a=float(a), g=float(g), m=float(m), beta=float(beta),
            ))
    return polygons


def spur_step(p: Polygon) -> Tuple[Polygon, float]:
    """Advance one polygon's SEIR state by one SPUR relaxation.

    Port of SUBROUTINE SPUR (minus the unused SAV/EAV/IAV/RAV history --
    see module docstring). Returns (new_polygon_state, infected_fraction).
    """
    latent = p.a / p.m
    infect = p.g / p.m
    life_expectancy = abs(_AVG_LIFESPAN_MONTHS - p.m / 30.0)

    s1, e1, i1, r1 = p.S, p.E, p.I, p.R
    s2, e2_, i2, r2 = 1.1 * s1, 1.1 * e1, 1.1 * i1, 1.1 * r1
    beta = p.beta * 100.0

    s_bar = e_bar = i_bar = r_bar = 0.0
    for _ in range(_RELAXATION_STEPS):
        while True:
            s_bar = (s1 + s2) / 2
            e_bar = (e1 + e2_) / 2
            i_bar = (i1 + i2) / 2
            r_bar = (r1 + r2) / 2
            total = s_bar + e_bar + i_bar + r_bar

            s_hat = s1 + (total / life_expectancy
                          - s_bar * (1 / life_expectancy + beta * i_bar)) * _TIME_STEP
            e_hat = e1 + (beta * s_bar * i_bar
                          - e_bar * (1 / life_expectancy + 1 / latent)) * _TIME_STEP
            i_hat = i1 + (e_bar / latent
                          - i_bar * (1 / life_expectancy + 1 / infect)) * _TIME_STEP
            r_hat = r1 + (i_bar / infect
                          - r_bar * (1 / life_expectancy)) * _TIME_STEP

            pct_changes = (
                100 * (s_hat - s2) / s2,
                100 * (e_hat - e2_) / e2_,
                100 * (i_hat - i2) / i2,
                100 * (r_hat - r2) / r2,
            )

            s2 = (s2 + s_hat) / 2
            e2_ = (e2_ + e_hat) / 2
            i2 = (i2 + i_hat) / 2
            r2 = (r2 + r_hat) / 2

            if all(abs(pct) <= _CONVERGE_PCT for pct in pct_changes):
                break

        s1, e1, i1, r1 = s2, e2_, i2, r2
        s2, e2_, i2, r2 = 1.1 * s1, 1.1 * e1, 1.1 * i1, 1.1 * r1

    new_p = replace(p, S=s_bar, E=e_bar, I=i_bar, R=r_bar)
    return new_p, i_bar


class SeirModel:
    """Stateful wrapper around the SEIR polygon submodel. Port of ZCELLS."""

    def __init__(self, polypara_path: Path | str, seed: Optional[int] = None):
        self._initial_polygons = load_polygons(polypara_path)
        self.rng = random.Random(seed)

    def step(
        self, timestep: int, polygons: Optional[Sequence[Polygon]] = None,
    ) -> Tuple[List[float], List[Polygon]]:
        """Advance the submodel by one timestep.

        timestep == 0 (re-)initializes from polypara.dat, matching the
        original always re-reading that file fresh at timestep 0.
        timestep > 0 evolves the given polygon state by one step,
        clamping near-zero S/E/I and perturbing beta first.

        Returns (infected_fractions, updated_polygons). infected_fractions
        is 1-indexed by polygon id (length N_POLYGONS + 1, index 0 unused)
        to mirror INF(POLYID) in the original.
        """
        if timestep == 0:
            source = self._initial_polygons
        else:
            source = [
                replace(
                    p,
                    S=p.S if p.S > 0.0 else 0.01,
                    E=p.E if p.E > 0.0 else 0.01,
                    I=p.I if p.I > 0.0 else 0.01,
                    beta=self.rng.random() * 10.0,
                )
                for p in polygons
            ]

        inf = [0.0] * (N_POLYGONS + 1)
        updated: List[Polygon] = []
        for p in source:
            new_p, infected = spur_step(p)
            inf[new_p.id] = infected
            updated.append(new_p)
        return inf, updated
