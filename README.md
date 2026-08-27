![Sunspot Umbra / Pore Evolution Model](assets/banner.png)

# Convert Rodney's FORTRAN code into python notebook

Hi David,

Do you think Claude can convert this old FORTRAN program to Python?   The sun.f file compiles OK with gfortran on this Mac, so I know it runs. 
It requires all these little data files, and asks for the umbra area around the sunspot counts.   
Then it outputs to a .csv file.   Really primitive, I wrote it years ago.   Maybe it could run in python Visual Studio? 


Rodney

---

## Python port (v1.0.0)

`sun.f` has been ported to a `sunmodel` Python package, with a CLI that reproduces
the original's interactive prompts and a JupyterLab notebook wrapper. See
`SUN_F_ANALYSIS.pdf` for a full write-up of the original FORTRAN code and the
decisions behind the port.

### Setup

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Run the command-line version

Reproduces the original's prompts (number of Umbra seen, total sunspots seen,
and three percentages) and its "Continue (1), Stop (0)" batch loop, writing
results to `SUN.CSV`:

```
.venv/bin/python main.py
```

Optional flags: `--rgo-data`, `--polypara`, `--output`, `--seed` (seeds the
SEIR submodel's random number generator for reproducible runs).

### Run the JupyterLab notebook

```
.venv/bin/jupyter lab
```

Open `Sun_Model.ipynb`. It wraps the same model in widgets: set the five
parameters, click **New run**, then **Run next batch** / **Run to completion**
to step through the sunspot data — the results table and an Umbra-vs-Pores
chart update live, and `SUN.CSV` is kept current on disk.

A kernel named "Python (sun.f port)" pointing at `.venv` is registered via:

```
.venv/bin/python -m ipykernel install --user --name=sun-fortran --display-name="Python (sun.f port)"
```

### Run the tests

Includes a regression test that validates the port's output against the real
gfortran-produced `SUN.CSV` checked into this repo, byte-for-byte:

```
.venv/bin/python -m pytest -q
```

### Project layout

```
sunmodel/                 the ported model (empirical curve-fit, SEIR submodel,
                           data readers, CSV report writer, simulation loop, CLI)
main.py                   CLI entry point
Sun_Model.ipynb           JupyterLab wrapper
build_notebook.py         regenerates Sun_Model.ipynb (edit this, not the .ipynb)
tests/                    pytest suite
SUN_F_ANALYSIS.pdf        analysis of the original sun.f
generate_analysis_pdf.py  regenerates the analysis PDF
```
