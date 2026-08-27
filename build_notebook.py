"""
Generates Sun_Model.ipynb -- a JupyterLab wrapper around the sunmodel
package (the Python port of Rodney's sun.f).

Run with the project's venv:
    .venv/bin/python build_notebook.py
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# ---------------------------------------------------------------- intro
md(r"""# Sunspot Umbra / Pore Evolution Model

A JupyterLab wrapper around **`sunmodel`**, the Python port of Rodney's original
`sun.f` FORTRAN program. It models how sunspot **umbra** (dark core) and
**penumbra** (surrounding region) evolve day to day, using an empirical
saturating growth curve plus a small SEIR-style submodel of 8 solar-disk regions.

See `SUN_F_ANALYSIS.pdf` in this repo for a full write-up of the original code.

**How to use this notebook:**
1. Run every cell from top to bottom once (*Run → Run All Cells*), so the
   widgets and helper functions are all defined.
2. Adjust the parameter widgets to the values you'd normally be prompted for
   (umbra seen, total sunspots seen, and three percentages), then click
   **New run**.
3. Click **Run next batch** to process one batch of days at a time (mirrors the
   original's "Continue (1), Stop (0)" loop), or **Run to completion** to process
   all remaining data in one go.
4. The results table and chart update after every batch. The same CSV file the
   original program wrote (`SUN.CSV` by default) is written to disk as you go.
""")

# ---------------------------------------------------------------- setup
md("## 1. Setup")

code(r"""import matplotlib.pyplot as plt
import pandas as pd
from ipywidgets import (
    BoundedFloatText, Button, HBox, IntText, Label, Layout, Output, Text, VBox,
)
from IPython.display import display

from sunmodel import RunConfig, SunReport, SunSimulation, read_report_rows

%matplotlib inline
""")

# ---------------------------------------------------------------- parameters
md(r"""## 2. Parameters

These are the same five values `sun.f` prompted for interactively, plus the
file paths and an optional random seed for the SEIR submodel (leave blank for a
different draw each run).""")

code(r"""label_layout = Layout(width="260px")
field_layout = Layout(width="160px")

w_umbra_seen = IntText(value=4, description="", layout=field_layout)
w_total_sunspots = IntText(value=27, description="", layout=field_layout)
w_delta = BoundedFloatText(value=0.40, min=0, max=1, step=0.01, description="", layout=field_layout)
w_gamma = BoundedFloatText(value=0.60, min=0, max=1, step=0.01, description="", layout=field_layout)
w_P = BoundedFloatText(value=0.30, min=0, max=1, step=0.01, description="", layout=field_layout)

w_rgo_data = Text(value="rgo_data.prn", layout=Layout(width="300px"))
w_polypara = Text(value="polypara.dat", layout=Layout(width="300px"))
w_output = Text(value="SUN.CSV", layout=Layout(width="300px"))
w_seed = IntText(value=42, description="", layout=field_layout)

def row(label_text, widget):
    return HBox([Label(label_text, layout=label_layout), widget])

params_box = VBox([
    row("Number of Umbra seen", w_umbra_seen),
    row("Number of total sunspots seen", w_total_sunspots),
    row("Penumbra % of Umbra area (delta)", w_delta),
    row("% of sunspots in Umbra (gamma)", w_gamma),
    row("% of Umbra area to total group area (P)", w_P),
    row("rgo_data.prn path", w_rgo_data),
    row("polypara.dat path", w_polypara),
    row("Output CSV path", w_output),
    row("Random seed (SEIR submodel)", w_seed),
])
display(params_box)
""")

# ---------------------------------------------------------------- run controls
md(r"""## 3. Run the simulation

**New run** (re)starts a simulation from the current parameters, overwriting the
output CSV. **Run next batch** processes one batch of days, same as answering
"Continue (1)" in the original program. **Run to completion** repeats that until
the data file is exhausted.""")

code(r"""results = pd.DataFrame(columns=["day", "umbra", "pores", "cwsa", "cua"])
sim = None
report = None
status_out = Output()
table_out = Output()
chart_out = Output()


def _refresh_views():
    table_out.clear_output(wait=True)
    with table_out:
        display(results.tail(10))
    chart_out.clear_output(wait=True)
    with chart_out:
        plot_results(results)


def _new_run(_button=None):
    global sim, report, results
    status_out.clear_output()
    if report is not None:
        report.close()
    config = RunConfig(
        n_umbra_seen=w_umbra_seen.value,
        n_sunspots_seen=w_total_sunspots.value,
        penumbra_pct=w_delta.value,
        umbra_sunspot_pct=w_gamma.value,
        umbra_group_area_pct=w_P.value,
    )
    seed = w_seed.value if w_seed.value != 0 else None
    report = SunReport(w_output.value)
    sim = SunSimulation(config, w_rgo_data.value, w_polypara.value, report, seed=seed)
    results = pd.DataFrame(columns=["day", "umbra", "pores", "cwsa", "cua"])
    with status_out:
        print("New run started.")
        print(f" Sunspots = {sim.total_sunspots}  Pores = 0  Actual Sunspots = {sim.total_sunspots}")
    _refresh_views()


def _run_batch(_button=None):
    global results
    if sim is None:
        with status_out:
            print("Click 'New run' first.")
        return
    processed = sim.run_batch()
    report.flush()
    npores, nspots = sim.pore_summary()
    with status_out:
        if processed == 0:
            print("End of data file reached -- no more batches to run.")
        else:
            print(f"Processed {processed} records. "
                  f"Sunspots = {sim.total_sunspots}  Pores = {npores}  Actual Sunspots = {nspots}")
    results = pd.DataFrame(read_report_rows(w_output.value))
    _refresh_views()


def _run_to_completion(_button=None):
    if sim is None:
        with status_out:
            print("Click 'New run' first.")
        return
    while True:
        processed = sim.run_batch()
        if processed == 0:
            break
    report.flush()
    global results
    results = pd.DataFrame(read_report_rows(w_output.value))
    npores, nspots = sim.pore_summary()
    with status_out:
        print(f"Done. Sunspots = {sim.total_sunspots}  Pores = {npores}  Actual Sunspots = {nspots}")
    _refresh_views()


btn_new = Button(description="New run", button_style="primary")
btn_batch = Button(description="Run next batch")
btn_all = Button(description="Run to completion")
btn_new.on_click(_new_run)
btn_batch.on_click(_run_batch)
btn_all.on_click(_run_to_completion)

display(HBox([btn_new, btn_batch, btn_all]))
display(status_out)
""")

# ---------------------------------------------------------------- chart
md(r"""## 4. Results

`Umbra` and `Pores` are on the same scale (both derived percentages of umbra
area), so they share one axis rather than a dual-axis plot.""")

code(r"""# Two-series line chart: Umbra vs. Pores over the cumulative record index.
# Colors are slots 1 (blue) and 2 (orange) of the project's validated
# categorical palette -- fixed hue order, not cycled.
UMBRA_COLOR = "#2a78d6"
PORES_COLOR = "#eb6834"


def plot_results(df: pd.DataFrame) -> None:
    if df.empty:
        print("No results yet -- click 'New run' then a run button above.")
        return
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = range(1, len(df) + 1)
    ax.plot(x, df["umbra"], color=UMBRA_COLOR, linewidth=2, label="Umbra")
    ax.plot(x, df["pores"], color=PORES_COLOR, linewidth=2, label="Pores")
    ax.set_xlabel("Record #")
    ax.set_ylabel("Estimated value")
    ax.set_title("Umbra vs. Pores evolution")
    ax.grid(True, color="#dddddd", linewidth=0.7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    plt.show()


display(chart_out)
display(table_out)
""")

# ---------------------------------------------------------------- export
md(r"""## 5. Export

`SUN.CSV` (or whatever path you set above) is kept up to date on disk after
every batch. This cell just re-displays the full results table if you want to
inspect or further analyze it (e.g. `results.to_excel(...)`, `results.plot(...)`).""")

code(r"""results
""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3 (sun.f port)",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "pygments_lexer": "ipython3"},
}

with open("Sun_Model.ipynb", "w") as f:
    nbf.write(nb, f)

print("Wrote Sun_Model.ipynb")
