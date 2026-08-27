"""Main simulation loop.

Port of PROGRAM SUN in sun.f, minus the Y/T/ETA/... polynomial-fit
arrays and COMMON block: in the original those are only ever read on
the ADAT.NE.'Y' branch, and ADAT is hardcoded to 'Y' and never
reassigned, so that branch -- and everything it depends on -- is dead
code. Dropping it changes no computed output.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

from .empirical import expo
from .rgo_data import SunspotRecord, iter_records
from .report import SunReport
from .seir import Polygon, SeirModel

# Hardcoded in the original (these were interactive prompts too, until
# someone commented them out in favor of fixed values).
DURATION_K = 1
ALPHA = 0.95
NEIGHBOR_Z = 8.0
INITIAL_BATCH_DAYS = 85

DYNAMICS_MODES = ("legacy", "robust")

# Arbitrary, tunable -- there's no physical derivation for this any more
# than there was for the 1/IREC decay it replaces (see empirical.py's
# module docstring re: EXPO/ENERGY/MASS having no documented derivation
# either). Chosen to decay noticeably but not vanish across the ~30-day
# span typical of one rgo_data.prn run; override via the constructor.
DEFAULT_REMQ_HALF_LIFE_DAYS = 14.0


@dataclass
class RunConfig:
    """The five values PROGRAM SUN prompts the user for."""
    n_umbra_seen: int             # 'beta' in the original
    n_sunspots_seen: int          # raw 'rr' before its (rr+1)/100 transform
    penumbra_pct: float           # 'delta': % of umbra area with penumbra
    umbra_sunspot_pct: float      # 'g': % of sunspots in umbra
    umbra_group_area_pct: float   # 'P': % of umbra area to total group area


class SunSimulation:
    """Batch-driven sunspot umbra/pore evolution simulation.

    Mirrors the original's "Continue (1) / Stop (0)" batching: call
    run_batch() repeatedly (e.g. driven by a CLI prompt, see cli.py)
    until the sunspot data file is exhausted or the caller stops.
    """

    def __init__(self, config: RunConfig, rgo_data_path: Union[Path, str],
                 polypara_path: Union[Path, str], report: SunReport,
                 seed: Optional[int] = None, dynamics: str = "legacy",
                 remq_half_life_days: float = DEFAULT_REMQ_HALF_LIFE_DAYS):
        if dynamics not in DYNAMICS_MODES:
            raise ValueError(f"dynamics must be one of {DYNAMICS_MODES}, got {dynamics!r}")
        self.dynamics = dynamics
        self.remq_half_life_days = remq_half_life_days

        self.cfg = config
        self.beta = float(config.n_umbra_seen)
        self.rr = (config.n_sunspots_seen + 1) / 100.0
        self.delta = config.penumbra_pct
        self.g = config.umbra_sunspot_pct
        self.P = config.umbra_group_area_pct
        self.Pr = (1.0 - self.P) / 10.0
        self.x = 1.0 / self.Pr

        self.report = report
        self.seir = SeirModel(polypara_path, seed=seed)
        self._records: Iterator[SunspotRecord] = iter_records(rgo_data_path)

        # In robust mode the SEIR polygon state is carried forward record
        # to record (see _robust_posq) instead of being re-read from
        # polypara.dat on every call, so it needs an explicit initial step.
        self._polygons: Optional[List[Polygon]] = None
        if self.dynamics == "robust":
            _, self._polygons = self.seir.step(0)

        # Day of the first record seen by *this run* (not necessarily day 1
        # of rgo_data.prn -- a run can be handed a mid-dataset slice). The
        # robust remq decay is measured from here, so its trajectory only
        # depends on elapsed calendar time within this run, never on how
        # many records happened to precede it.
        self._run_start_day: Optional[int] = None

        self.n = INITIAL_BATCH_DAYS  # 'N' in the original; mutates as batches progress
        self.irec = 1                # running record counter, never resets across batches
        self.last_day = 1
        self.remq = 0.0              # persists across records; only updated on even irec
        self.avepores = 0.0
        self.total_sunspots = config.n_sunspots_seen

        self.report.write_header(
            config.n_umbra_seen, config.n_sunspots_seen,
            self.delta, self.g, self.P,
        )

    def pore_summary(self) -> Tuple[int, int]:
        """(pores seen so far, sunspots minus pores) -- the values printed
        at the top of each "Continue?" prompt in the original."""
        npores = int(self.avepores) // self.irec if self.irec else 0
        nspots = self.total_sunspots - npores
        return npores, nspots

    def run_batch(self) -> int:
        """Process one batch of records and advance to the next batch
        boundary. Returns the number of records processed (0 once the
        data file is exhausted)."""
        nbatch = self.irec + self.n - 1
        processed = 0
        while self.irec <= nbatch:
            try:
                record = next(self._records)
            except StopIteration:
                break
            self._process_record(record)
            processed += 1

        if self.last_day > 85:
            self.last_day = 27
        self.n = self.last_day * 3 - 3
        return processed

    def _process_record(self, record: SunspotRecord) -> None:
        if record.day > self.last_day:
            self.last_day = record.day
        if self._run_start_day is None:
            self._run_start_day = record.day

        umbra_area = float(record.umbra_area)
        rinf = self.rr * umbra_area
        freq = self.g * umbra_area
        c = self.beta * umbra_area
        pg = self.P * umbra_area
        freq = (c / freq) ** 2

        time = (self.irec / self.n) + 0.01

        if self.dynamics == "robust":
            posq = self._robust_posq(time, pg, rinf, freq, c)
        else:
            posq = self._legacy_posq(time, pg, rinf, freq, c)

        if (self.irec + 1) % 2 == 1:  # i.e. irec is even
            if self.dynamics == "robust":
                self.remq = self._robust_remq(record.day)
            else:
                self.remq = -(1.0 / self.irec) * (self.g * (1 - ALPHA)) * self.delta

        susqs = ((1 - self.Pr) * self.rr * (self.n * umbra_area + self.n * self.remq)) / (
            NEIGHBOR_Z + self.Pr * self.rr * (self.x * umbra_area + self.x * self.remq)
        )
        susqi = ((1 - self.Pr) * self.beta * self.n * posq) / (
            NEIGHBOR_Z + self.Pr * self.beta * self.x * posq
        )
        susqs *= self.delta
        susqi *= (self.delta + self.g * ALPHA)

        self.report.write_row(record.day, susqi, susqs,
                               record.umbra_area, record.whole_spot_area)
        self.avepores += susqs
        self.irec += 1

    def _legacy_posq(self, time: float, pg: float, rinf: float,
                      freq: float, c: float) -> float:
        """Original behavior: SEIR/EXPO only ever run on the very first
        record (DURATION_K=1), and EXPO's result is computed then
        discarded -- reproduced here purely for numerical fidelity with
        sun.f. See the module-level [An important caveat...] note in
        analysis_report.qmd."""
        if self.irec <= DURATION_K:
            inf, _ = self.seir.step(self.irec - 1)
            f_sum = sum(inf[1:int(NEIGHBOR_Z) + 1])
            posq = f_sum / NEIGHBOR_Z
            expo(self.n, time, pg, rinf, freq, c)
        else:
            posq = 1.0 / self.irec
        return posq

    def _robust_posq(self, time: float, pg: float, rinf: float,
                      freq: float, c: float) -> float:
        """Recommendation #1: SEIR state evolves every record (instead of
        being re-read from polypara.dat and discarded after record 1),
        and EXPO's result actually scales POSQ (the original's commented-
        out 'POSQ=F*POSQ')."""
        inf, self._polygons = self.seir.step(self.irec, polygons=self._polygons)
        f_sum = sum(inf[1:int(NEIGHBOR_Z) + 1])
        posq = f_sum / NEIGHBOR_Z
        f = expo(self.n, time, pg, rinf, freq, c)
        return f * posq

    def _robust_remq(self, day: int) -> float:
        """Recommendation #4: replace the 1/IREC decay (tied to how many
        records this process happened to have handled) with a decay tied
        to elapsed calendar days since this run's first record. A run
        started mid-dataset (or resumed) reproduces the same trajectory a
        continuous run would have from that point on, instead of one
        distorted by an arbitrary record count."""
        elapsed_days = max(day - self._run_start_day, 0)
        decay = math.exp(-elapsed_days / self.remq_half_life_days)
        return -decay * (self.g * (1 - ALPHA)) * self.delta
