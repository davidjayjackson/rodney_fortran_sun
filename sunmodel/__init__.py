"""sunmodel: Python port of Rodney's sun.f sunspot umbra/pore evolution model.

Ported from the FORTRAN 77 program in sun.f, which combines:

  * an empirical, saturating evolution-rate curve (see empirical.py,
    ported from EXPO/ENERGY/MASS/JTEMP/E2), and
  * a small SEIR (Susceptible/Exposed/Infected/Removed) submodel over
    8 solar-disk "polygon" regions (see seir.py, ported from
    SPUR/ZCELLS/MOVES/ran2),

driven record-by-record over daily sunspot observations (rgo_data.py)
and written to a CSV report (report.py). simulation.py orchestrates the
whole run; cli.py reproduces the original's interactive prompts.

See SUN_F_ANALYSIS.pdf for a full write-up of the original code and the
decisions behind this port.
"""
from .simulation import RunConfig, SunSimulation
from .report import SunReport
from .results import read_report_rows
from .seir import Polygon, SeirModel

__all__ = [
    "RunConfig", "SunSimulation", "SunReport", "Polygon", "SeirModel",
    "read_report_rows",
]
