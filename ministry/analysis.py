"""
Bivocational Ministry Research - survey analysis with pandas.

Answers eight research questions about bivocational vs. fully funded pastors:
time load, well-being (burnout, family strain, sense of calling), church
vitality, intent to leave, and themes in open-ended answers.

Run on the bundled synthetic sample:
    python ministry/analysis.py

Run on your own survey export (CSV or Excel):
    python ministry/analysis.py --data path/to/my_survey.csv

If your column names differ, edit COLUMN_MAP below (your name -> name used here)
instead of changing the analysis code. Outputs (tables, charts, a Markdown
report) go to ministry/output/.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "sample_bivocational_survey.csv"
OUT_DIR = Path(__file__).resolve().parent / "output"

# =====================================================================
# CONFIG - adapt these to your own survey instrument
# =====================================================================

# Rename your survey's columns to the names this script expects.
# e.g. {"Q3_status": "ministry_status", "Q12_hours_church": "ministry_hours_week"}
COLUMN_MAP: dict[str, str] = {}

# Values in ministry_status that count as each group (case-insensitive).
GROUP_LABELS = {
    "bivocational": "Bivocational",
    "fully_funded": "Fully funded",
}

# Likert scales: composite name -> item columns. Items listed in REVERSE_ITEMS
# are positively worded and get flipped (6 - x on a 1-5 scale).
SCALES = {
    "burnout": ["burnout_1", "burnout_2", "burnout_3", "burnout_4", "burnout_5"],
    "family_strain": ["family_strain_1", "family_strain_2", "family_strain_3"],
    "calling": ["calling_1", "calling_2", "calling_3"],
}
REVERSE_ITEMS = ["burnout_3"]
LIKERT_MAX = 5

# Subgroups smaller than this are left off charts (too few to be meaningful).
MIN_CELL_N = 10

# Keyword dictionary for coding open-ended answers into themes.
# A response can match several themes. Extend this as you read your data.
THEMES = {
    "Time (pressure / availability)": ["time", "schedul", "busy", "two jobs", "availability", "sermon prep"],
    "Fatigue / burnout": ["tired", "exhaust", "burnout", "rest", "sabbath", "demands"],
    "Family": ["family", "spouse", "wife", "husband", "children", "kids"],
    "Finances": ["financ", "money", "budget", "income", "salary"],
    "Isolation": ["isolat", "lonel", "alone", "other pastors"],
    "Congregational expectations": ["expect", "congregation", "depend on me"],
    "Lay leadership / shared ministry": ["leader", "lay", "members serve", "share the work", "stepped up", "volunteer"],
    "Community connection / witness": ["community", "coworker", "outside the church", "gospel", "credibility", "working life"],
    "Church decline": ["declin", "pandemic", "attendance"],
    "Study & spiritual focus": ["study", "prayer", "preaching", "pastoral care"],
}

# Chart palette (validated categorical order: blue, orange, aqua)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]


# =====================================================================
# Loading & cleaning
# =====================================================================
def load(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)  # needs openpyxl
    else:
        df = pd.read_csv(path)
    df = df.rename(columns=COLUMN_MAP)

    # tidy text categories
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].str.strip()
    df["ministry_status"] = df["ministry_status"].str.lower()
    df["group"] = df["ministry_status"].map(GROUP_LABELS).fillna("Other")

    # data conversion
    if "survey_date" in df:
        df["survey_date"] = pd.to_datetime(df["survey_date"], errors="coerce")
    for item in REVERSE_ITEMS:
        if item in df:
            df[item] = (LIKERT_MAX + 1) - df[item]

    # derived variables
    df["total_work_hours"] = df["ministry_hours_week"] + df["secular_hours_week"].fillna(0)
    df["attendance_change_pct"] = (
        (df["avg_attendance"] - df["attendance_3yr_ago"]) / df["attendance_3yr_ago"] * 100
    )
    df["church_size"] = pd.cut(
        df["avg_attendance"],
        bins=[0, 50, 100, 250, np.inf],
        labels=["<50", "50-99", "100-249", "250+"],
        right=False,
    )
    df["hours_band"] = pd.cut(
        df["total_work_hours"],
        bins=[0, 50, 60, 70, np.inf],
        labels=["<50 h", "50-59 h", "60-69 h", "70+ h"],
        right=False,
    )
    df["leaving"] = df["considering_leaving"].str.lower().eq("yes").astype(int)
    return df


def cronbach_alpha(items: pd.DataFrame) -> float:
    items = items.dropna()
    k = items.shape[1]
    if k < 2 or len(items) < 2:
        return float("nan")
    item_var = items.var(ddof=1).sum()
    total_var = items.sum(axis=1).var(ddof=1)
    return k / (k - 1) * (1 - item_var / total_var)


def cohens_d(a: pd.Series, b: pd.Series) -> float:
    a, b = a.dropna(), b.dropna()
    pooled = np.sqrt(((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / pooled


def add_scales(df: pd.DataFrame) -> pd.DataFrame:
    """Composite = mean of available items (needs at least half the items answered)."""
    rows = []
    for name, cols in SCALES.items():
        cols = [c for c in cols if c in df]
        answered = df[cols].notna().sum(axis=1)
        df[name] = df[cols].mean(axis=1).where(answered >= len(cols) / 2)
        rows.append({"scale": name, "items": len(cols), "cronbach_alpha": round(cronbach_alpha(df[cols]), 3)})
    return pd.DataFrame(rows).set_index("scale")


# =====================================================================
# Research questions
# =====================================================================
def q1_profile(df):
    """Who responded? Sample profile by group."""
    counts = df["group"].value_counts().rename("n").to_frame()
    counts["percent"] = (counts["n"] / counts["n"].sum() * 100).round(1)
    demo = df.groupby("group").agg(
        mean_age=("age", "mean"),
        mean_years_in_ministry=("years_in_ministry", "mean"),
        median_attendance=("avg_attendance", "median"),
        pct_female=("gender", lambda s: (s.str.lower() == "female").mean() * 100),
    ).round(1)
    region = pd.crosstab(df["region"], df["group"], normalize="columns").mul(100).round(1)
    reasons = (
        df.loc[df["ministry_status"] == "bivocational", "bivo_reason"]
        .value_counts(normalize=True).mul(100).round(1).rename("percent of bivocational")
    )
    sectors = (
        df.loc[df["ministry_status"] == "bivocational", "secular_job_sector"]
        .value_counts().rename("n")
    )
    return {"Group sizes": counts.join(demo), "Region (% of group)": region,
            "Reason for bivocational ministry": reasons.to_frame(),
            "Secular job sector (bivocational)": sectors.to_frame()}


def q2_time(df):
    """How heavy is the weekly work load?"""
    t = df.groupby("group").agg(
        ministry_hours=("ministry_hours_week", "mean"),
        secular_hours=("secular_hours_week", "mean"),
        total_hours=("total_work_hours", "mean"),
        pct_over_60h=("total_work_hours", lambda s: (s >= 60).mean() * 100),
        church_income_pct=("church_income_pct", "mean"),
    ).round(1)
    return {"Weekly hours by group": t}


def q3_wellbeing(df):
    """Do bivocational pastors differ in burnout, family strain, calling, satisfaction?"""
    outcomes = list(SCALES) + ["ministry_satisfaction"]
    desc = df.groupby("group")[outcomes].agg(["mean", "std", "count"]).round(2)
    bivo = df[df["ministry_status"] == "bivocational"]
    ff = df[df["ministry_status"] == "fully_funded"]
    effects = pd.DataFrame({
        "bivocational_mean": [bivo[o].mean() for o in outcomes],
        "fully_funded_mean": [ff[o].mean() for o in outcomes],
        "cohens_d": [cohens_d(bivo[o], ff[o]) for o in outcomes],
    }, index=outcomes).round(2)
    effects["effect_size"] = pd.cut(
        effects["cohens_d"].abs(), [0, 0.2, 0.5, 0.8, np.inf],
        labels=["negligible", "small", "medium", "large"], right=False,
    )
    by_reason = (
        bivo.groupby("bivo_reason")[outcomes].mean().round(2)
        .sort_values("burnout", ascending=False)
    )
    return {"Well-being by group": desc, "Effect sizes (bivocational vs fully funded)": effects,
            "Bivocational pastors by reason": by_reason}


def q4_hours_burnout(df):
    """Does burnout climb with total weekly work hours?"""
    band = df.groupby("hours_band", observed=True).agg(
        n=("burnout", "count"), mean_burnout=("burnout", "mean"),
        mean_family_strain=("family_strain", "mean"), pct_considering_leaving=("leaving", "mean"),
    )
    band["pct_considering_leaving"] *= 100
    corr_cols = ["total_work_hours", "ministry_hours_week", "secular_hours_week",
                 "children_at_home", "burnout", "family_strain", "calling", "ministry_satisfaction"]
    corr = df[corr_cols].corr(method="spearman").round(2)
    return {"Burnout by total weekly hours": band.round(2),
            "Spearman correlations": corr}


def q5_church_vitality(df):
    """Are bivocationally led churches growing or declining (3-year change)?"""
    g = df.groupby(["church_size", "group"], observed=True)["attendance_change_pct"].agg(["median", "mean", "count"]).round(1)
    r = df.pivot_table(index="region", columns="group", values="attendance_change_pct",
                       aggfunc="median", observed=True).round(1)
    share_growing = df.assign(growing=df["attendance_change_pct"] > 0).groupby("group")["growing"].mean().mul(100).round(1)
    return {"Attendance change % by church size": g,
            "Median attendance change % by region": r,
            "% of churches growing": share_growing.to_frame("% growing")}


def q6_leaving(df):
    """Who is considering leaving pastoral ministry?"""
    df = df.copy()
    df["burnout_level"] = pd.qcut(df["burnout"], 3, labels=["low", "moderate", "high"])
    by_group = df.groupby("group")["leaving"].agg(["mean", "sum", "count"])
    by_group["mean"] = (by_group["mean"] * 100).round(1)
    by_group = by_group.rename(columns={"mean": "% considering leaving", "sum": "n yes", "count": "n"})
    by_burn = pd.crosstab(df["burnout_level"], df["group"], values=df["leaving"], aggfunc="mean").mul(100).round(1)
    return {"Considering leaving by group": by_group, "% considering leaving by burnout level": by_burn}


def code_themes(text: pd.Series) -> pd.DataFrame:
    lower = text.fillna("").str.lower()
    return pd.DataFrame({theme: lower.apply(lambda t, kw=kws: any(k in t for k in kw))
                         for theme, kws in THEMES.items()})


def q7_themes(df):
    """What themes appear in open-ended challenges and benefits?"""
    out = {}
    for col, label in [("greatest_challenge", "Challenges"), ("greatest_benefit", "Benefits")]:
        if col not in df:
            continue
        coded = code_themes(df[col]).join(df["group"])
        answered = df[col].notna()
        pct = coded[answered].groupby("group").mean().T.mul(100).round(1)
        pct = pct[(pct > 0).any(axis=1)].sort_values(pct.columns[0], ascending=False)
        out[f"{label}: % of respondents mentioning theme"] = pct
        uncoded = df.loc[answered & ~coded[list(THEMES)].any(axis=1), col]
        if len(uncoded):
            out[f"{label}: answers no theme caught (review & extend THEMES)"] = uncoded.value_counts().head(10).to_frame("n")
    return out


def q8_predictors(df):
    """Which factors relate most to burnout among bivocational pastors? (simple OLS)"""
    b = df[df["ministry_status"] == "bivocational"].copy()
    b["necessity"] = (b["bivo_reason"] == "financial_necessity").astype(int)
    b["spouse_works"] = (b["spouse_employed"] == "yes").astype(int)
    predictors = ["secular_hours_week", "ministry_hours_week", "children_at_home",
                  "necessity", "spouse_works", "years_in_ministry"]
    data = b[predictors + ["burnout"]].dropna()
    X = (data[predictors] - data[predictors].mean()) / data[predictors].std()  # standardized betas
    X.insert(0, "intercept", 1.0)
    y = data["burnout"].to_numpy()
    beta, *_ = np.linalg.lstsq(X.to_numpy(), y, rcond=None)
    resid = y - X.to_numpy() @ beta
    n, k = X.shape
    se = np.sqrt(np.diag(resid @ resid / (n - k) * np.linalg.inv(X.T.to_numpy() @ X.to_numpy())))
    r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    table = pd.DataFrame({"beta (per 1 SD)": beta, "std_error": se, "t": beta / se}, index=X.columns).round(3)
    table = table.drop("intercept").sort_values("t", key=abs, ascending=False)
    table.attrs["note"] = f"n = {n}, R² = {r2:.3f}. |t| > ~2 suggests a reliable association."
    return {"Burnout predictors (bivocational only)": table}


# =====================================================================
# Charts
# =====================================================================
def make_charts(df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
        "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    })
    paths = []

    def save(fig, name):
        p = OUT_DIR / name
        fig.tight_layout()
        fig.savefig(p, dpi=160)
        plt.close(fig)
        paths.append(p)

    groups = [g for g in GROUP_LABELS.values() if g in set(df["group"])]

    # 1. Weekly hours split (stacked horizontal bars)
    hrs = df.groupby("group")[["ministry_hours_week", "secular_hours_week"]].mean().reindex(groups)
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.barh(hrs.index, hrs["ministry_hours_week"], color=SERIES[0], label="Ministry", height=0.5,
            edgecolor=SURFACE, linewidth=2)
    ax.barh(hrs.index, hrs["secular_hours_week"], left=hrs["ministry_hours_week"], color=SERIES[1],
            label="Secular job", height=0.5, edgecolor=SURFACE, linewidth=2)
    for i, (m, s) in enumerate(hrs.to_numpy()):
        ax.text(m + s + 1, i, f"{m + s:.0f} h total", va="center", color=INK_2)
    ax.set_xlim(0, hrs.sum(axis=1).max() * 1.25)
    ax.set_xlabel("Average hours per week")
    ax.set_title("Weekly work load")
    ax.grid(axis="y", visible=False)
    ax.invert_yaxis()
    ax.legend(frameon=False, ncols=2, loc="lower right", bbox_to_anchor=(1, 1.0))
    save(fig, "01_weekly_hours.png")

    # 2. Burnout by total hours band
    band = df.groupby("hours_band", observed=True)["burnout"].agg(["mean", "count"])
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.bar(band.index.astype(str), band["mean"], color=SERIES[0], width=0.6)
    for i, (m, n) in enumerate(band.to_numpy()):
        ax.text(i, m + 0.05, f"{m:.2f}\n(n={int(n)})", ha="center", va="bottom", color=INK_2, fontsize=9)
    ax.set_ylim(1, LIKERT_MAX)
    ax.set_ylabel(f"Mean burnout (1-{LIKERT_MAX})")
    ax.set_xlabel("Total weekly work hours (ministry + secular)")
    ax.set_title("Burnout rises with total work hours")
    ax.grid(axis="x", visible=False)
    save(fig, "02_burnout_by_hours.png")

    # 3. Well-being comparison (grouped bars)
    scales = list(SCALES)
    means = df.groupby("group")[scales].mean().reindex(groups)
    x = np.arange(len(scales))
    w = 0.36
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for i, g in enumerate(groups):
        bars = ax.bar(x + (i - (len(groups) - 1) / 2) * w, means.loc[g], w - 0.03, color=SERIES[i], label=g)
        ax.bar_label(bars, fmt="%.2f", padding=2, color=INK_2, fontsize=9)
    ax.set_xticks(x, [s.replace("_", " ").title() for s in scales])
    ax.set_ylim(1, LIKERT_MAX)
    ax.set_ylabel(f"Mean score (1-{LIKERT_MAX})")
    ax.set_title("Well-being scales by group")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, ncols=len(groups), loc="upper right")
    save(fig, "03_wellbeing_by_group.png")

    # 4. Attendance change by church size (grouped bars, median)
    ch = df.pivot_table(index="church_size", columns="group", values="attendance_change_pct",
                        aggfunc="median", observed=True).reindex(columns=groups)
    n = df.pivot_table(index="church_size", columns="group", values="attendance_change_pct",
                       aggfunc="count", observed=True).reindex(index=ch.index, columns=groups)
    ch = ch.where(n >= MIN_CELL_N)  # hide medians resting on a handful of churches
    x = np.arange(len(ch))
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for i, g in enumerate(groups):
        bars = ax.bar(x + (i - (len(groups) - 1) / 2) * w, ch[g], w - 0.03, color=SERIES[i], label=g)
        ax.bar_label(bars, labels=["" if np.isnan(v) else f"{v:+.1f}%" for v in ch[g]],
                     padding=2, color=INK_2, fontsize=8)
    ax.axhline(0, color=INK_2, linewidth=1)
    ax.set_xticks(x, [f"{c} attenders" for c in ch.index.astype(str)])
    ax.set_ylabel("Median 3-year change (%)")
    ax.set_title("Attendance change by church size")
    fig.text(0.01, 0.01, f"Cells with fewer than {MIN_CELL_N} churches are omitted.", color=INK_2, fontsize=8)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False)
    save(fig, "04_attendance_change.png")

    # 5. Challenge themes (bivocational only)
    if "greatest_challenge" in df:
        bivo = df[df["ministry_status"] == "bivocational"]
        pct = code_themes(bivo["greatest_challenge"].dropna()).mean().mul(100)
        pct = pct[pct > 0].sort_values()
        fig, ax = plt.subplots(figsize=(7, 0.45 * len(pct) + 1.2))
        ax.barh(pct.index, pct.to_numpy(), color=SERIES[0], height=0.6)
        for i, v in enumerate(pct.to_numpy()):
            ax.text(v + 0.5, i, f"{v:.0f}%", va="center", color=INK_2, fontsize=9)
        ax.set_xlim(0, pct.max() * 1.15)
        ax.set_xlabel("% of bivocational respondents mentioning")
        ax.set_title("Greatest challenges named by bivocational pastors")
        ax.grid(axis="y", visible=False)
        save(fig, "05_challenge_themes.png")
    return paths


# =====================================================================
# Report
# =====================================================================
QUESTIONS = [
    ("Q1. Who responded?", q1_profile),
    ("Q2. How heavy is the weekly work load?", q2_time),
    ("Q3. Do bivocational and fully funded pastors differ in well-being?", q3_wellbeing),
    ("Q4. Does burnout rise with total work hours?", q4_hours_burnout),
    ("Q5. Are bivocationally led churches growing or declining?", q5_church_vitality),
    ("Q6. Who is considering leaving pastoral ministry?", q6_leaving),
    ("Q7. What themes appear in open-ended answers?", q7_themes),
    ("Q8. What predicts burnout among bivocational pastors?", q8_predictors),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA, help="survey CSV/XLSX file")
    ap.add_argument("--no-charts", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    pd.set_option("display.width", 140)
    pd.set_option("display.max_columns", 20)

    df = load(args.data)
    reliability = add_scales(df)

    md = [f"# Bivocational Ministry Survey - Results\n",
          f"Data: `{args.data.name}` - {len(df)} respondents.\n"]
    if args.data.resolve() == DEFAULT_DATA.resolve():
        md.append("> **Synthetic sample data.** These numbers are made up for testing; "
                  "rerun with `--data` on your real survey.\n")
    md += ["## Scale reliability\n", "Cronbach's alpha ≥ 0.70 is usually considered acceptable.\n",
           reliability.to_markdown(), ""]
    print("Scale reliability (Cronbach's alpha)\n", reliability, "\n", sep="")

    for i, (title, fn) in enumerate(QUESTIONS, start=1):
        print("=" * 70, f"\n{title}\n", "=" * 70, sep="")
        md.append(f"## {title}\n")
        for j, (name, table) in enumerate(fn(df).items(), start=1):
            print(f"\n{name}\n{table}")
            md += [f"**{name}**\n", table.to_markdown(), ""]
            if table.attrs.get("note"):
                print(table.attrs["note"])
                md.append(f"_{table.attrs['note']}_\n")
            table.to_csv(OUT_DIR / f"q{i}_{j}.csv")
        print()

    if not args.no_charts:
        md.append("## Charts\n")
        for p in make_charts(df):
            md.append(f"![{p.stem}]({p.name})\n")
            print("chart:", p.relative_to(ROOT))

    (OUT_DIR / "report.md").write_text("\n".join(md), encoding="utf-8")
    print("report:", (OUT_DIR / "report.md").relative_to(ROOT))


if __name__ == "__main__":
    main()
