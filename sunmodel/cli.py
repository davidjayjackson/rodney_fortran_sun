"""Interactive command-line entry point.

Port of PROGRAM SUN's user prompts and "Continue (1) / Stop (0)" batch
loop.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from .report import SunReport
from .simulation import RunConfig, SunSimulation

DEFAULT_RGO_DATA = "rgo_data.prn"
DEFAULT_POLYPARA = "polypara.dat"
DEFAULT_OUTPUT = "SUN.CSV"


def prompt_config() -> RunConfig:
    print(" Program simulates sunspot pore evolution")
    print(" from Umbra, Penumbra structure using")
    print(" State transition NLDE")
    return RunConfig(
        n_umbra_seen=int(input(" Enter number of Umbra seen\n > ")),
        n_sunspots_seen=int(input(" Enter number of total sunspots seen\n > ")),
        penumbra_pct=float(input(" Percentage of Umbra area with Penumbra - delta\n > ")),
        umbra_sunspot_pct=float(input(" Percentage of sunspots in Umbra - gamma\n > ")),
        umbra_group_area_pct=float(input(" Percent of Umbra area to total group area\n > ")),
    )


def run_interactive(config: RunConfig, rgo_data_path: Path, polypara_path: Path,
                     output_path: Path, seed: Optional[int], dynamics: str = "legacy") -> None:
    with SunReport(output_path) as report:
        sim = SunSimulation(config, rgo_data_path, polypara_path, report,
                             seed=seed, dynamics=dynamics)
        while True:
            npores, nspots = sim.pore_summary()
            print(f" Sunspots = {sim.total_sunspots:3d} Pores = {npores:3d}"
                  f" Actual Sunspots = {nspots:3d}")
            answer = input(" Continue (1), Stop (0)\n > ").strip()
            if answer != "1":
                break
            processed = sim.run_batch()
            if processed == 0:
                print(" End of rgo_data.prn reached.")
                break


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Sunspot umbra/pore evolution model")
    parser.add_argument("--rgo-data", type=Path, default=Path(DEFAULT_RGO_DATA),
                         help="path to rgo_data.prn")
    parser.add_argument("--polypara", type=Path, default=Path(DEFAULT_POLYPARA),
                         help="path to polypara.dat")
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_OUTPUT),
                         help="path to write the CSV report")
    parser.add_argument("--seed", type=int, default=None,
                         help="seed the SEIR submodel's random number generator")
    parser.add_argument("--dynamics", choices=["legacy", "robust"], default="legacy",
                         help="'legacy' (default) reproduces sun.f's arithmetic exactly, "
                              "including its SEIR/EXPO-discarding bug; 'robust' lets SEIR "
                              "state evolve every record, applies EXPO's result to POSQ, "
                              "and replaces the 1/IREC decay with an elapsed-day decay")
    args = parser.parse_args(argv)

    config = prompt_config()
    run_interactive(config, args.rgo_data, args.polypara, args.output, args.seed, args.dynamics)


if __name__ == "__main__":
    main()
