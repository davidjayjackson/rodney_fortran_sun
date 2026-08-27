"""Helpers for reading a SunReport CSV back out as tabular data.

Kept dependency-free (no pandas) so sunmodel itself stays lightweight;
callers (e.g. the notebook) wrap the returned rows in a DataFrame if
they want one.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Union

ROW_KEYS = ("day", "umbra", "pores", "cwsa", "cua")


def read_report_rows(path: Union[Path, str]) -> List[Dict[str, float]]:
    """Parse the per-day data rows out of a SunReport-format CSV file."""
    rows: List[Dict[str, float]] = []
    in_data = False
    with open(path) as f:
        for line in f:
            if line.startswith(" Days,"):
                in_data = True
                continue
            if not in_data:
                continue
            line = line.strip()
            if not line:
                continue
            day, umbra, pores, cwsa, cua = (x.strip() for x in line.split(","))
            rows.append({
                "day": int(day), "umbra": float(umbra), "pores": float(pores),
                "cwsa": int(cwsa), "cua": int(cua),
            })
    return rows
