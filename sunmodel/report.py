"""SUN.CSV report writer.

Port of the WRITE(3,...) statements in PROGRAM SUN. Layout intentionally
mirrors the original's output (a short parameter header followed by one
comma-separated row per day), though exact column widths are not
guaranteed to be byte-identical to the FORTRAN FORMAT statements.
"""
from __future__ import annotations

from pathlib import Path
from typing import TextIO, Union


class SunReport:
    """Writes the SUN.CSV parameter header and per-day result rows."""

    def __init__(self, path: Union[Path, str]):
        self._fh: TextIO = open(path, "w", newline="")

    def write_header(self, n_umbra: int, n_sunspots: int, delta: float,
                      gamma: float, umbra_area_pct: float) -> None:
        w = self._fh
        w.write(f"\n Number of Umbra seen {n_umbra:3d}\n")
        w.write(f"\n Number of total sunspots {n_sunspots:4d}\n")
        w.write(f"\n Percentage of Umbra area with Penumbra {delta:5.2f}\n")
        w.write(f"\n Percentage of of sunspots in Umbra {gamma:5.2f}\n")
        w.write(f"\n Percent Umbra area to total group area {umbra_area_pct:5.2f}\n")
        w.write(" Days,      Umbra,       Pores,  CWSA, CUA\n")

    def write_row(self, day: int, susqi: float, susqs: float,
                  umbra_area: int, whole_spot_area: int) -> None:
        self._fh.write(
            f"{day:5d},{susqi:12.4f},{susqs:12.4f},"
            f"{umbra_area:4d},{whole_spot_area:4d}\n"
        )

    def flush(self) -> None:
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "SunReport":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
