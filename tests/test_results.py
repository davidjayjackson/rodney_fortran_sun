from pathlib import Path

from sunmodel.results import read_report_rows

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_read_report_rows_parses_reference_csv():
    rows = read_report_rows(REPO_ROOT / "SUN.CSV")
    assert len(rows) == 82
    assert rows[0] == {"day": 1, "umbra": 0.6731, "pores": 8.1978, "cwsa": 10, "cua": 50}
    assert rows[-1]["day"] == 30
