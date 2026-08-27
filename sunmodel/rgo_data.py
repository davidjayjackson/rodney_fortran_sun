"""Reader for rgo_data.prn -- daily sunspot group observations from the
Royal Greenwich Observatory (via the VB Makemap program).

Port of the READ(25,9) loop in PROGRAM SUN (FORMAT 6(I14)).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class SunspotRecord:
    """One daily observation row from rgo_data.prn.

    group_id, day and umbra_area (CUA) are used by the model; the two
    middle fields are read but their exact meaning isn't documented in
    sun.f beyond the file header's column names (CWSA/LAT/LONG).
    """
    group_id: int
    day: int
    whole_spot_area: int  # CWSA
    field4: int
    field5: int
    umbra_area: int  # CUA


def iter_records(path: Path | str) -> Iterator[SunspotRecord]:
    """Yield SunspotRecord rows from rgo_data.prn, skipping its title row."""
    with open(path) as f:
        next(f)  # "NREC LABEL" title row
        for line in f:
            line = line.strip()
            if not line:
                continue
            fields = line.split()
            if len(fields) != 6:
                raise ValueError(f"expected 6 fields in rgo_data.prn row, got: {line!r}")
            group_id, day, cwsa, f4, f5, cua = (int(x) for x in fields)
            yield SunspotRecord(group_id, day, cwsa, f4, f5, cua)
