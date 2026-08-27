"""Integration test: validates the Python port against SUN.CSV, the
actual output of a real gfortran run of sun.f checked into this repo
(inputs were 4 umbra seen, 27 total sunspots, delta=0.40, g=0.60,
P=0.30 -- see the file's own header).
"""
from pathlib import Path

from sunmodel.report import SunReport
from sunmodel.simulation import RunConfig, SunSimulation

REPO_ROOT = Path(__file__).resolve().parent.parent
RGO_DATA = REPO_ROOT / "rgo_data.prn"
POLYPARA = REPO_ROOT / "polypara.dat"
REFERENCE_CSV = REPO_ROOT / "SUN.CSV"


def _reference_data_rows() -> list[str]:
    lines = REFERENCE_CSV.read_text().splitlines()
    header_end = next(i for i, line in enumerate(lines) if line.startswith(" Days,"))
    return [line for line in lines[header_end + 1:] if line.strip()]


def test_matches_reference_fortran_output(tmp_path):
    config = RunConfig(
        n_umbra_seen=4, n_sunspots_seen=27,
        penumbra_pct=0.40, umbra_sunspot_pct=0.60, umbra_group_area_pct=0.30,
    )
    out_path = tmp_path / "SUN.CSV"

    with SunReport(out_path) as report:
        sim = SunSimulation(config, RGO_DATA, POLYPARA, report, seed=0)
        processed = sim.run_batch()

    assert processed == 82  # rgo_data.prn has 82 data rows, all in one batch (N=85)

    out_lines = out_path.read_text().splitlines()
    header_end = next(i for i, line in enumerate(out_lines) if line.startswith(" Days,"))
    actual_rows = [line for line in out_lines[header_end + 1:] if line.strip()]

    assert actual_rows == _reference_data_rows()
