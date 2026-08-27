"""
Generates SUN_F_ANALYSIS.pdf - a written analysis of sun.f (Rodney's FORTRAN
sunspot umbra/penumbra evolution model), for review ahead of a Python port.

Run with the project's venv:
    .venv/bin/python generate_analysis_pdf.py
"""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem, PageBreak
)
from reportlab.lib.enums import TA_LEFT
import datetime

OUT_FILE = "SUN_F_ANALYSIS.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="Title2", parent=styles["Title"], fontSize=20, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="SubTitle", parent=styles["Normal"], fontSize=11,
    textColor=colors.grey, spaceAfter=20,
))
styles.add(ParagraphStyle(
    name="H1", parent=styles["Heading1"], fontSize=15, spaceBefore=18, spaceAfter=8,
    textColor=colors.HexColor("#1a3a5c"),
))
styles.add(ParagraphStyle(
    name="H2", parent=styles["Heading2"], fontSize=12.5, spaceBefore=12, spaceAfter=6,
    textColor=colors.HexColor("#2c5580"),
))
styles.add(ParagraphStyle(
    name="Body", parent=styles["BodyText"], fontSize=10, leading=14,
    spaceAfter=8, alignment=TA_LEFT,
))
styles.add(ParagraphStyle(
    name="Mono", parent=styles["BodyText"], fontName="Courier", fontSize=8.5,
    leading=11, backColor=colors.HexColor("#f4f4f4"), borderPadding=6,
    spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="BulletBody", parent=styles["BodyText"], fontSize=10, leading=14,
))

def P(text):
    return Paragraph(text, styles["Body"])

def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(t, styles["BulletBody"]), leftIndent=6) for t in items],
        bulletType="bullet", start="•", leftIndent=14, spaceAfter=10,
    )

story = []

# ---------------------------------------------------------------- Title page
story.append(Paragraph("Analysis of sun.f", styles["Title2"]))
story.append(Paragraph(
    "A FORTRAN 77 model of sunspot umbra/penumbra evolution &mdash; "
    "prepared ahead of a Python port", styles["SubTitle"]
))
story.append(P(
    f"<b>Source file:</b> sun.f &nbsp;&nbsp; "
    f"<b>Prepared:</b> {datetime.date.today():%B %d, %Y}"
))
story.append(Spacer(1, 12))

story.append(Paragraph("Big picture", styles["H1"]))
story.append(P(
    "This is a 1990s/2000s-era FORTRAN 77 program that models how sunspot "
    "<b>umbra</b> (dark core) and <b>penumbra</b> (surrounding lighter region) "
    "evolve over time, based on a paper by Bogdan et al. (Science, 6 Feb 2004) "
    "on sunspot pore structure. It:"
))
story.append(bullets([
    "Reads pre-processed sunspot observation data (<font face='Courier'>rgo_data.prn</font>, "
    "from the Royal Greenwich Observatory) &mdash; daily counts of sunspot area "
    "(CWSA = corrected whole spot area, CUA = corrected umbra area) per group.",
    "Asks the user interactively for calibration parameters (Umbra count, total "
    "sunspot count, and three percentages).",
    "Runs a batch loop over &ldquo;Carrington rotations&rdquo; (27-day solar rotation "
    "periods), computing a predicted umbra/pore evolution value for each day using "
    "an empirical exponential-decay model (<font face='Courier'>EXPO</font> and its helpers).",
    "Separately, an epidemic-style differential-equation model "
    "(<font face='Courier'>SPUR</font>, borrowed from disease-spread modeling &mdash; "
    "S-E-I-R: Susceptible/Exposed/Infected/Removed) simulates how &ldquo;infection&rdquo; "
    "(spot state) spreads between 8 polygon cells on the solar disk, using a simple "
    "numerical relaxation method.",
    "Writes results to <font face='Courier'>SUN.CSV</font>.",
]))
story.append(P(
    "It is really two loosely-coupled models glued together: an empirical curve-fit "
    "(<font face='Courier'>EXPO</font>/<font face='Courier'>ENERGY</font>/"
    "<font face='Courier'>MASS</font>/<font face='Courier'>JTEMP</font>/"
    "<font face='Courier'>E2</font>) driving the main per-day output, and an SIR-style "
    "compartmental model (<font face='Courier'>SPUR</font>/<font face='Courier'>ZCELLS</font>/"
    "<font face='Courier'>MOVES</font>) meant to represent spatial spreading between regions, "
    "whose output barely feeds back into the main calculation (it's summed into "
    "<font face='Courier'>POSQ</font> only for the first record of each batch, then unused)."
))

# ---------------------------------------------------------------- Main program
story.append(Paragraph("PROGRAM SUN &mdash; main program (lines 1&ndash;206)", styles["H1"]))

story.append(Paragraph("Setup", styles["H2"]))
story.append(P(
    "<font face='Courier'>IMPLICIT DOUBLE PRECISION</font> means any variable starting "
    "with A&ndash;H or O&ndash;Z defaults to double precision &mdash; classic FORTRAN "
    "convention, and the reason the code has almost no explicit type declarations. "
    "The program opens <font face='Courier'>rgo_data.prn</font> for input and "
    "<font face='Courier'>SUN.CSV</font> for output."
))

story.append(Paragraph("User prompts", styles["H2"]))
story.append(P("Five values are read interactively and echoed into the CSV header:"))
tbl_data = [
    ["Variable", "Prompt", "Notes"],
    ["beta", "Number of Umbra seen", "used as a scale constant C = beta * ICUA"],
    ["rr", "Number of total sunspots seen", "converted to a fraction: rr = (rr+1)/100"],
    ["delta", "% of Umbra area with Penumbra", "used as a filter/scale multiplier"],
    ["g", "% of sunspots in Umbra", "used with alpha to scale SUSQI"],
    ["P", "% of Umbra area to total group area", "Pr = (1-P)/10, x = 1/Pr"],
]
t = Table(tbl_data, colWidths=[0.8*inch, 2.5*inch, 3.0*inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f4")]),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t)
story.append(Spacer(1, 8))
story.append(P(
    "<font face='Courier'>K=1</font> and <font face='Courier'>alpha=.95</font> are "
    "hardcoded &mdash; these were originally user prompts too, now commented out, "
    "suggesting someone simplified the interface at some point."
))

story.append(Paragraph("Main DO WHILE loop", styles["H2"]))
story.append(P(
    "Each pass through the outer loop asks the user &ldquo;Continue (1), Stop (0)&rdquo; "
    "&mdash; this is a manual, semi-interactive batch process rather than a single "
    "run-to-completion program. While continuing, it loops "
    "<font face='Courier'>DO 100 IREC = NREC, NBATCH</font>, reading one record per day "
    "from <font face='Courier'>rgo_data.prn</font>: group id (ICSG), day, whole-spot area "
    "(ICWSA), and umbra area (ICUA), among others."
))
story.append(bullets([
    "For each record, derives model parameters (RINF, freq, C, PG) as simple multiples "
    "of ICUA, scaled by the user's calibration percentages.",
    "<b>First K days of a batch</b> (K=1, so effectively just the first record): calls "
    "ZCELLS (the SPUR/epidemic submodel) to get an INF array, sums it into F, then calls "
    "EXPO to compute an evolution estimate from the empirical formulas.",
    "<b>Remaining days</b>: uses a simple decay POSQ = 1/IREC instead of the empirical model.",
    "Also computes a REMQ &ldquo;removal&rdquo; term, but only on odd IREC values.",
    "Combines everything into SUSQS (sunspot-count estimate) and SUSQI (umbra/pore "
    "estimate) via formulas resembling discrete diffusion/logistic terms, each rescaled "
    "again by delta / g / alpha.",
    "Writes one CSV row per record: day, SUSQI, SUSQS, ICUA, ICWSA.",
    "Accumulates avepores (running sum of SUSQS) &mdash; reported back to the user as "
    "npores / nspots at the top of the next outer-loop pass.",
    "After a batch, advances NREC/NBATCH to the next chunk; if reading from the RGO "
    "data file, N is re-derived from the last day seen as roughly 3 Carrington "
    "rotations (3&times;days &minus; 3).",
]))

story.append(Paragraph("Error handling", styles["H2"]))
story.append(P(
    "Labels 350 / 400 / 60 are classic GOTO-based error handlers for file read/write "
    "failures, reporting where execution broke via LOC (a manually maintained "
    "&ldquo;line marker&rdquo; variable) and IREC."
))

# ---------------------------------------------------------------- EXPO family
story.append(Paragraph(
    "SUBROUTINE EXPO and helpers &mdash; the empirical curve-fit model", styles["H1"]
))
story.append(P(
    "Given time, PG, RINF, freq, and C, EXPO computes an output F. This is explicitly "
    "an ad-hoc curve fit (&ldquo;SICE&rdquo;, roughly a saturation/inflection curve "
    "estimate) built from four sub-formulas &mdash; ENERGY (H), MASS (M), JTEMP (J), "
    "and E2 (ESQR) &mdash; that all follow the same pattern: take ln(time), turn it "
    "into an angle via arctan, then exponentiate back out. The header comment block "
    "documents the intended formulas, though variable names in code don't always match "
    "the comments one-to-one (e.g. <font face='Courier'>v</font> in the comments "
    "corresponds to <font face='Courier'>time</font>)."
))
tbl2 = [
    ["Subroutine", "Output", "Shape"],
    ["ENERGY", "H", "exp(-atan(tan(acos(1/(ln(time)*&pi;)))))-style sigmoid of ln(time)"],
    ["MASS", "M", "same transform shape, scaled by .4 instead of &pi;"],
    ["JTEMP", "J", "nested log/exp/atan transform, guarded for ln(time) &le; 0"],
    ["E2", "ESQR", "similar transform combined with &pi;"],
]
t2 = Table(tbl2, colWidths=[1.1*inch, 0.7*inch, 4.5*inch])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f4")]),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t2)
story.append(Spacer(1, 8))
story.append(P("These feed into the final combination:"))
story.append(Paragraph(
    "K = J&sup3; &nbsp;&nbsp; KT = log10(K&middot;PG) (floored at 2.5 if &le; 0)<br/>"
    "SICE = [1 / (3&pi;&middot;H&sup3;&middot;freq&sup3;)] &middot; "
    "[3&middot;&radic;ESQR / (4&pi;&middot;M&middot;freq)]<sup>KT</sup><br/>"
    "F = SICE &middot; freq &middot; M &middot; C",
    styles["Mono"]
))
story.append(P(
    "This is essentially a hand-fit empirical function with no obvious physical "
    "derivation &mdash; it approximates an S-shaped (saturating) growth curve. "
    "<font face='Courier'>CPI</font> (computing c = exp(exp(10/&pi;)), a very large "
    "constant) is dead code &mdash; it's never called from anywhere in the program."
))

# ---------------------------------------------------------------- SPUR family
story.append(Paragraph(
    "ZCELLS / SPUR / MOVES / ran2 &mdash; the epidemic (SEIR) submodel", styles["H1"]
))
story.append(P(
    "This is a separate epidemiological SIR/SEIR model &mdash; literally borrowed "
    "(the header comment says &ldquo;simulate Olsen and Schaffer's SPUR equations&rdquo;, "
    "and variable names S/E/I/R map to Susceptible/Exposed/Infected/Removed) and "
    "repurposed to model 8 polygon &ldquo;cells&rdquo; on the solar disk, presumably "
    "one per active region or quadrant."
))
story.append(Paragraph("ZCELLS(timestep, inf)", styles["H2"]))
story.append(bullets([
    "If timestep == 0: reads initial conditions from polypara.dat (8 rows: polygon ID, "
    "S/E/I/R fractions, a/g/m rate constants, B = beta/contact-rate seed), calls SPUR "
    "for each polygon, and writes results to TIMENEW.DAT.",
    "Otherwise: reads previous state from TIMEOLD.DAT, applies MOVES to jitter the "
    "contact rate B via a random-number draw, re-runs SPUR, and rotates "
    "TIMENEW.DAT &rarr; TIMEOLD.DAT for the next call.",
    "Returns inf(8) &mdash; the &ldquo;Infected&rdquo; fraction per polygon after "
    "settling &mdash; interpreted by the main program as pore-visibility percentages.",
]))
story.append(Paragraph("SPUR", styles["H2"]))
story.append(P(
    "A classic explicit numerical relaxation of the SEIR ODEs (dS/dt, dE/dt, dI/dt, "
    "dR/dt), using a birth/death rate 1/LIFEXPT and a fixed-point &ldquo;average-and-"
    "relax&rdquo; inner loop, run up to 50 outer iterations, each inner-looping until "
    "percent changes converge under CRIT = .00001. The final IAV(10) (infected fraction "
    "at the 10th of 11 sampled points) becomes the polygon's output."
))
story.append(Paragraph("MOVES / ran2", styles["H2"]))
story.append(P(
    "ran2 is the classic <i>Numerical Recipes</i> linear-congruential random-number "
    "generator with a shuffle table. MOVES draws one such value to perturb B (the "
    "transmission/contact-rate parameter) between timesteps, simulating some randomness "
    "in sunspot region movement."
))
story.append(P(
    "<b>Important wiring note:</b> in the main program, K=1 means the ZCELLS/EXPO "
    "combined branch only executes for the very first IREC of each batch "
    "(IREC.LE.K), and ZCELLS is always called with timestep = IREC&minus;1, i.e. "
    "typically timestep = 0 &mdash; so it mostly just re-reads polypara.dat fresh every "
    "time rather than evolving TIMENEW.DAT/TIMEOLD.DAT across calls. This SEIR submodel "
    "is largely vestigial/underused as currently wired into the main loop."
))

story.append(PageBreak())

# ---------------------------------------------------------------- Data files
story.append(Paragraph("Data files", styles["H1"]))
tbl3 = [
    ["File", "Role"],
    ["rgo_data.prn", "Input: daily sunspot group observations (group id, day, CWSA, "
                      "LAT, LONG, CUA)"],
    ["polypara.dat", "Input: initial S/E/I/R + rate parameters per polygon (8 rows) "
                      "for the SPUR submodel"],
    ["TIMENEW.DAT / TIMEOLD.DAT", "Scratch/state files ping-ponged between SPUR "
                                   "timesteps"],
    ["SUN.CSV", "Output: header of user-entered parameters, then per-day "
                 "Days, Umbra (SUSQI), Pores (SUSQS), CWSA, CUA"],
]
t3 = Table(tbl3, colWidths=[1.8*inch, 4.5*inch])
t3.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f4f4")]),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(t3)

# ---------------------------------------------------------------- Assessment
story.append(Paragraph("Assessment for the Python port", styles["H1"]))
story.append(bullets([
    "The interactive READ(*,*) prompts (umbra count, total spots, three percentages, "
    "and the Continue/Stop loop) map naturally to Python input() calls &mdash; or, "
    "better, function/CLI arguments so the model can run non-interactively or from "
    "a notebook cell.",
    "All of the EXPO/ENERGY/MASS/JTEMP/E2 math is straightforward scalar math "
    "(math.log, math.atan, math.exp, math.sqrt) &mdash; trivial to port one-to-one.",
    "SPUR's fixed-point relaxation loop and ran2's hand-rolled RNG are the fiddliest "
    "pieces to port faithfully. ran2 should probably become random.random() (or "
    "NumPy's Generator) unless bit-for-bit reproducibility of the original FORTRAN "
    "random sequence is required.",
    "The GOTO-based error handling and the LOC &ldquo;line marker&rdquo; pattern have "
    "no direct Python equivalent &mdash; ordinary try/except around file I/O replaces "
    "it more cleanly.",
    "Recommend replacing the file-based state ping-pong (TIMENEW.DAT/TIMEOLD.DAT) with "
    "an in-memory list of dicts/dataclasses per polygon, writing only SUN.CSV as the "
    "actual persistent output.",
]))
story.append(Spacer(1, 10))
story.append(P(
    "<b>Open questions before porting:</b> confirm the intended behavior of the "
    "underused K / ZCELLS branch (should the SEIR submodel actually evolve across "
    "calls, or is the current re-read-every-time behavior acceptable?), and whether "
    "SUN.CSV's exact column format needs to match the legacy output byte-for-byte."
))

doc = SimpleDocTemplate(
    OUT_FILE, pagesize=LETTER,
    leftMargin=0.85*inch, rightMargin=0.85*inch,
    topMargin=0.85*inch, bottomMargin=0.85*inch,
    title="Analysis of sun.f", author="Claude Code",
)
doc.build(story)
print(f"Wrote {OUT_FILE}")
