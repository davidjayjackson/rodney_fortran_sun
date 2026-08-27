"""Empirical evolution-rate model.

Port of the EXPO, ENERGY, MASS, JTEMP and E2 subroutines in sun.f. These
are pure functions with no documented physical derivation -- the
original's header comment gives the intended formulas as ASCII art; the
implementations below follow the FORTRAN source exactly, including one
notable operator-precedence quirk (see the comment in expo() below).
"""
from __future__ import annotations

import math

PI = 3.141592654  # matches the constant literal used throughout sun.f


def energy(time: float) -> float:
    """H: a sigmoid-shaped transform of ln(time). Port of SUBROUTINE ENERGY."""
    ln_h = math.log(time)
    cosrad = 1.0 / (ln_h * PI)
    sinrad = abs(cosrad ** 2 - 1.0)
    tanrad = math.sqrt(sinrad) / cosrad
    angle = -math.atan(tanrad)
    degtan = -angle
    return 1.0 / math.exp(degtan)


def mass(time: float) -> float:
    """M: same transform shape as energy(), scaled by 0.4 instead of pi.
    Port of SUBROUTINE MASS."""
    ln_m = math.log(time)
    cosdeg = 1.0 / (ln_m / 0.4)
    tan_ = math.sqrt(abs(1.0 - cosdeg ** 2)) / cosdeg
    arctan = math.atan(tan_)
    return math.exp(arctan)


def jtemp(time: float) -> float:
    """J: exp(atan(exp(pi*ln(ln(time))))), guarded for ln(time) <= 0.
    Port of SUBROUTINE JTEMP."""
    ln_j = math.log(time)
    if ln_j <= 0:
        return 0.0
    tanrad = math.exp(PI * math.log(ln_j))
    angle = math.atan(tanrad)
    return math.exp(angle)


def e2(time: float) -> float:
    """ESQR: inv(exp(atan(inv(ln(pi*gm))))). Port of SUBROUTINE E2."""
    cosrad = (1.0 / (math.log(time) / 0.4)) ** 2
    sinrad = abs(cosrad ** 2 - 1.0)
    temp = math.sqrt(sinrad)
    tanrad = temp / cosrad
    gm = 1.0 / math.atan(tanrad)
    ln_e2 = math.log(PI * gm)
    tanrad2 = 1.0 / ln_e2
    angle = math.atan(tanrad2)
    return 1.0 / math.exp(angle)


def cpi() -> float:
    """c = exp(exp(10/pi)). Port of SUBROUTINE CPI.

    Dead code in the original -- CPI is never called anywhere in sun.f.
    Kept here for reference only.
    """
    return math.exp(math.exp((1.0 / PI) * 10.0))


def expo(n: float, time: float, pg: float, rinf: float, freq: float, c: float) -> float:
    """Return F, the saturating evolution estimate. Port of SUBROUTINE EXPO."""
    pg = 1.0 - ((pg - rinf) / (pg + rinf))
    h = energy(time)
    m = mass(time)
    esqr = e2(time)
    j = jtemp(time + 1)
    k = j ** 3
    kt = math.log10(k * pg)
    if kt <= 0.0:
        kt = 5.0 / 2.0
    s1 = 1.0 / (3 * PI * (h ** 3 * freq ** 3))
    # NOTE: sun.f writes this as "3*DSQRT(ESQR)/4*PI*M*freq" -- FORTRAN's
    # left-to-right */ precedence makes that ((3*sqrt(esqr))/4)*PI*M*freq,
    # NOT sqrt(esqr) divided by (4*PI*M*freq) as the header comment implies.
    # Reproduced literally here for numerical fidelity with the original.
    s2 = (((3 * math.sqrt(esqr)) / 4) * PI * m * freq) ** kt
    sice = s1 * s2
    return (sice * freq) * (m * c)
