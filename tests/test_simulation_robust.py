"""Tests for the "robust" dynamics mode (recommendations #1 and #4 from
analysis_report.qmd): SEIR state evolving every record with EXPO's result
actually applied, and a decay tied to elapsed calendar days instead of
raw record count.

Unlike test_simulation.py, there's no reference FORTRAN output to check
these against -- this mode doesn't exist in sun.f. These tests instead
check the properties the change was meant to deliver: real (non-frozen)
SEIR evolution, output that differs from the legacy path, and sane
behavior when a run is started mid-dataset.
"""
from pathlib import Path

from sunmodel.report import SunReport
from sunmodel.simulation import RunConfig, SunSimulation

REPO_ROOT = Path(__file__).resolve().parent.parent
RGO_DATA = REPO_ROOT / "rgo_data.prn"
POLYPARA = REPO_ROOT / "polypara.dat"

CONFIG = RunConfig(
    n_umbra_seen=4, n_sunspots_seen=27,
    penumbra_pct=0.40, umbra_sunspot_pct=0.60, umbra_group_area_pct=0.30,
)


def _run(tmp_path, dynamics, rgo_data_path=RGO_DATA, name="SUN.CSV"):
    out_path = tmp_path / name
    with SunReport(out_path) as report:
        sim = SunSimulation(CONFIG, rgo_data_path, POLYPARA, report,
                             seed=0, dynamics=dynamics)
        processed = sim.run_batch()
    return processed, out_path.read_text()


def test_rejects_unknown_dynamics_mode(tmp_path):
    out_path = tmp_path / "SUN.CSV"
    try:
        with SunReport(out_path) as report:
            SunSimulation(CONFIG, RGO_DATA, POLYPARA, report, dynamics="bogus")
    except ValueError as e:
        assert "dynamics" in str(e)
    else:
        raise AssertionError("expected ValueError for an invalid dynamics mode")


def test_robust_output_differs_from_legacy(tmp_path):
    _, legacy_csv = _run(tmp_path, "legacy", name="legacy.csv")
    _, robust_csv = _run(tmp_path, "robust", name="robust.csv")
    assert legacy_csv != robust_csv


def test_robust_output_is_finite_and_processes_all_records(tmp_path):
    from sunmodel.results import read_report_rows

    processed, _ = _run(tmp_path, "robust")
    assert processed == 82

    rows = read_report_rows(tmp_path / "SUN.CSV")
    assert len(rows) == 82
    for row in rows:
        assert math_isfinite(row["umbra"])
        assert math_isfinite(row["pores"])


def math_isfinite(x: float) -> bool:
    import math
    return math.isfinite(x)


def test_robust_seir_state_actually_evolves(tmp_path):
    """The whole point of recommendation #1: polygon state should not be
    frozen/reinitialized every record."""
    out_path = tmp_path / "SUN.CSV"
    with SunReport(out_path) as report:
        sim = SunSimulation(CONFIG, RGO_DATA, POLYPARA, report,
                             seed=0, dynamics="robust")
        initial_state = [(p.S, p.E, p.I, p.R) for p in sim._polygons]
        sim.run_batch()
        final_state = [(p.S, p.E, p.I, p.R) for p in sim._polygons]

    assert initial_state != final_state


def test_robust_mid_dataset_start_is_well_behaved(tmp_path):
    """Recommendation #4: a run starting partway through the dataset
    (rather than at record 1) should still produce finite, sane output --
    not a decay artifact from an inflated record count."""
    from sunmodel.results import read_report_rows
    from sunmodel.rgo_data import iter_records

    # Build a "mid-dataset" slice: everything from the 24-day gap onward
    # (rgo_data.prn's day column jumps from 2 to 26 partway through).
    all_records = list(iter_records(RGO_DATA))
    tail_records = [r for r in all_records if r.day >= 26]
    assert 0 < len(tail_records) < len(all_records)

    tail_path = tmp_path / "rgo_tail.prn"
    with open(RGO_DATA) as f:
        header = f.readline()
    with open(tail_path, "w") as f:
        f.write(header)
        for r in tail_records:
            f.write(f"{r.group_id} {r.day} {r.whole_spot_area} "
                     f"{r.field4} {r.field5} {r.umbra_area}\n")

    processed, _ = _run(tmp_path, "robust", rgo_data_path=tail_path, name="tail.csv")
    assert processed == len(tail_records)

    rows = read_report_rows(tmp_path / "tail.csv")
    for row in rows:
        assert math_isfinite(row["umbra"])
        assert math_isfinite(row["pores"])
        # Loose sanity bound: robust output shouldn't blow up just because
        # this run "starts" partway through the dataset.
        assert abs(row["umbra"]) < 1e6
        assert abs(row["pores"]) < 1e6
