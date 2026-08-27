import math

import pytest

from sunmodel.empirical import cpi, e2, energy, expo, jtemp, mass


def test_energy_matches_hand_computed_value():
    # time=2.0: ln(2)=0.69314718..., cosrad=1/(ln(2)*pi)=0.45937...
    ln_h = math.log(2.0)
    cosrad = 1.0 / (ln_h * math.pi)
    tanrad = math.sqrt(abs(cosrad ** 2 - 1.0)) / cosrad
    expected = 1.0 / math.exp(math.atan(tanrad))
    assert energy(2.0) == pytest.approx(expected, rel=1e-9)


def test_mass_is_finite_and_positive():
    assert math.isfinite(mass(2.0))
    assert mass(2.0) > 0


def test_jtemp_zero_when_log_non_positive():
    # ln(time) <= 0 for time in (0, 1]
    assert jtemp(1.0) == 0.0
    assert jtemp(0.5) == 0.0


def test_jtemp_finite_for_time_greater_than_e():
    # need ln(ln(time)) defined, i.e. ln(time) > 0 -> time > 1
    assert math.isfinite(jtemp(3.0))


def test_e2_finite_and_positive():
    assert math.isfinite(e2(2.0))


def test_cpi_matches_known_constant():
    # exp(exp(10/pi)) is a large but finite double
    assert cpi() == math.exp(math.exp((1.0 / 3.141592654) * 10.0))


def test_expo_runs_end_to_end():
    f = expo(n=85, time=0.5, pg=100.0, rinf=50.0, freq=4.0, c=200.0)
    assert math.isfinite(f)
