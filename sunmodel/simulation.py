"""Main simulation loop.

Port of PROGRAM SUN in sun.f, minus the Y/T/ETA/... polynomial-fit
arrays and COMMON block: in the original those are only ever read on
the ADAT.NE.'Y' branch, and ADAT is hardcoded to 'Y' and never
reassigned, so that branch -- and everything it depends on -- is dead
code. Dropping it changes no computed output.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Tuple, Union

from .empirical import expo
from .rgo_data import SunspotRecord, iter_records
from .report import SunReport
from .seir import SeirModel

# Hardcoded in the original (these were interactive prompts too, until
# someone commented them out in favor of fixed values).
DURATION_K = 1
ALPHA = 0.95
NEIGHBOR_Z = 8.0
INITIAL_BATCH_DAYS = 85


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
                 seed: Optional[int] = None):
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

        umbra_area = float(record.umbra_area)
        rinf = self.rr * umbra_area
        freq = self.g * umbra_area
        c = self.beta * umbra_area
        pg = self.P * umbra_area
        freq = (c / freq) ** 2

        time = (self.irec / self.n) + 0.01

        if self.irec <= DURATION_K:
            inf, _ = self.seir.step(self.irec - 1)
            f_sum = sum(inf[1:int(NEIGHBOR_Z) + 1])
            posq = f_sum / NEIGHBOR_Z
            # NOTE: the original calls EXPO here and discards the result --
            # the line that would apply it to POSQ ("POSQ=F*POSQ") is
            # commented out in sun.f. Called here purely for fidelity;
            # since expo() is a pure function this has no effect on output.
            expo(self.n, time, pg, rinf, freq, c)
        else:
            posq = 1.0 / self.irec

        if (self.irec + 1) % 2 == 1:  # i.e. irec is even
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
