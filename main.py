#!/usr/bin/env python
"""Run the sunspot umbra/pore evolution model (Python port of sun.f).

Usage:
    .venv/bin/python main.py
    .venv/bin/python main.py --rgo-data rgo_data.prn --output SUN.CSV --seed 42

You'll be prompted for the same five values the original FORTRAN program
asked for (number of umbra seen, total sunspots seen, and three
percentages), then asked "Continue (1), Stop (0)" to process the sunspot
data in batches, same as the original.
"""
from sunmodel.cli import main

if __name__ == "__main__":
    main()
