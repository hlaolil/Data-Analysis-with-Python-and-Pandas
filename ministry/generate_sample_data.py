"""
Generate a SYNTHETIC bivocational-ministry pastor survey.

This file only exists so the analysis can be run and tested before real survey
data is available. Every number it produces is made up. Replace the output with
your own survey export (same column names, or remap them in analysis.py CONFIG).

Run:  python ministry/generate_sample_data.py
Out:  data/sample_bivocational_survey.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N = 320
OUT = Path(__file__).resolve().parent.parent / "data" / "sample_bivocational_survey.csv"

rng = np.random.default_rng(SEED)


def likert(base, n_items, noise=0.8):
    """Turn a latent score (roughly 1-5) into n_items integer Likert answers."""
    items = base[:, None] + rng.normal(0, noise, size=(len(base), n_items))
    return np.clip(np.rint(items), 1, 5).astype(int)


# ---------------------------------------------------------------- who answered
status = rng.choice(["bivocational", "fully_funded"], size=N, p=[0.68, 0.32])
is_bivo = status == "bivocational"

bivo_reason = np.where(
    is_bivo,
    rng.choice(["financial_necessity", "missional_choice", "both"], size=N, p=[0.5, 0.25, 0.25]),
    "",
)

age = np.clip(rng.normal(52, 11, N), 25, 80).round().astype(int)
years_in_ministry = np.clip(age - 24 - rng.integers(0, 15, N), 1, 55)
gender = rng.choice(["male", "female"], size=N, p=[0.82, 0.18])
education = rng.choice(
    ["high_school", "bachelor", "mdiv", "doctorate"],
    size=N,
    p=[0.15, 0.35, 0.40, 0.10],
)
denomination = rng.choice(
    ["baptist", "methodist", "pentecostal", "nondenominational", "presbyterian", "other"],
    size=N,
    p=[0.30, 0.15, 0.15, 0.20, 0.08, 0.12],
)
# bivocational pastors skew rural / small town
region = np.where(
    is_bivo,
    rng.choice(["rural", "small_town", "suburban", "urban"], size=N, p=[0.40, 0.30, 0.15, 0.15]),
    rng.choice(["rural", "small_town", "suburban", "urban"], size=N, p=[0.12, 0.23, 0.35, 0.30]),
)

secular_job_sector = np.where(
    is_bivo,
    rng.choice(
        ["education", "trades_construction", "healthcare", "business_sales",
         "public_service", "agriculture", "self_employed", "other"],
        size=N,
    ),
    "none",
)

# ---------------------------------------------------------------- time & money
secular_hours = np.where(is_bivo, np.clip(rng.normal(36, 9, N), 8, 60), 0).round()
ministry_hours = np.where(
    is_bivo, np.clip(rng.normal(24, 7, N), 6, 50), np.clip(rng.normal(50, 7, N), 30, 70)
).round()
total_hours = secular_hours + ministry_hours

church_income_pct = np.where(
    is_bivo, np.clip(rng.normal(30, 15, N), 0, 80), np.clip(rng.normal(97, 4, N), 80, 100)
).round()

avg_attendance = np.where(
    is_bivo, rng.lognormal(np.log(55), 0.55, N), rng.lognormal(np.log(160), 0.6, N)
).round().astype(int)
avg_attendance = np.clip(avg_attendance, 8, 2500)
# 3-year change: small churches in rural areas tend to decline a bit
trend = rng.normal(0.0, 0.18, N) - 0.05 * (region == "rural") + 0.04 * (bivo_reason == "missional_choice")
attendance_3yr_ago = np.clip((avg_attendance / (1 + trend)).round(), 5, None).astype(int)
annual_budget_usd = (avg_attendance * rng.normal(1500, 350, N)).round(-2)

spouse_employed = rng.choice(["yes", "no", "no_spouse"], size=N, p=[0.60, 0.28, 0.12])
children_at_home = rng.poisson(1.0, N)

# ---------------------------------------------------------------- latent well-being
# burnout rises with total weekly hours; "missional choice" buffers it
burnout_latent = (
    1.6 + 0.035 * (total_hours - 40)
    - 0.35 * (bivo_reason == "missional_choice")
    + 0.20 * (bivo_reason == "financial_necessity")
    + rng.normal(0, 0.55, N)
)
burnout_latent = np.clip(burnout_latent + 0.9, 1, 5)
family_latent = np.clip(burnout_latent * 0.6 + 0.25 * children_at_home + rng.normal(0.4, 0.5, N), 1, 5)
calling_latent = np.clip(4.2 - 0.25 * (burnout_latent - 3) + rng.normal(0, 0.45, N), 1, 5)

burnout = likert(burnout_latent, 5)
# item 3 is worded positively ("I feel energized by my ministry") -> reverse of latent
burnout[:, 2] = 6 - burnout[:, 2]
family = likert(family_latent, 3)
calling = likert(calling_latent, 3)

satisfaction = np.clip(np.rint(10.5 - 1.4 * burnout_latent + rng.normal(0, 1.2, N)), 1, 10).astype(int)
p_leave = 1 / (1 + np.exp(-(-4.2 + 1.0 * burnout_latent - 0.4 * (calling_latent - 3))))
considering_leaving = np.where(rng.random(N) < p_leave, "yes", "no")

# ---------------------------------------------------------------- open-ended answers
challenges_bivo = [
    "Not enough time for sermon prep and visitation",
    "Finding time for my family while working two jobs",
    "Exhaustion, I am tired most weeks",
    "The congregation expects full-time availability",
    "Scheduling conflicts between my employer and funerals",
    "Financial stress even with two incomes",
    "Feeling isolated from other pastors",
    "Little time for rest or sabbath",
    "Training leaders so the church does not depend on me",
]
challenges_ff = [
    "Financial pressure on the church budget",
    "Burnout from constant demands",
    "Isolation and loneliness in leadership",
    "Balancing family time with evening meetings",
    "Volunteer recruitment",
    "Declining attendance after the pandemic",
]
benefits_bivo = [
    "My job connects me with people outside the church",
    "Relationships with coworkers open doors for the gospel",
    "Financial freedom so the church can fund mission",
    "The congregation has stepped up and members serve more",
    "Credibility in the community",
    "I understand the working life of my members",
    "Lay leaders have grown because they share the work",
]
benefits_ff = [
    "Time to focus on preaching and pastoral care",
    "Ability to invest in leaders",
    "Being available to the community",
    "Time for study and prayer",
]
greatest_challenge = np.where(is_bivo, rng.choice(challenges_bivo, N), rng.choice(challenges_ff, N))
greatest_benefit = np.where(is_bivo, rng.choice(benefits_bivo, N), rng.choice(benefits_ff, N))

# ---------------------------------------------------------------- assemble
survey_date = pd.Timestamp("2026-03-01") + pd.to_timedelta(rng.integers(0, 120, N), unit="D")

df = pd.DataFrame({
    "respondent_id": [f"R{i:04d}" for i in range(1, N + 1)],
    "survey_date": survey_date.strftime("%Y-%m-%d"),
    "ministry_status": status,
    "bivo_reason": bivo_reason,
    "age": age,
    "gender": gender,
    "education": education,
    "denomination": denomination,
    "years_in_ministry": years_in_ministry,
    "region": region,
    "secular_job_sector": secular_job_sector,
    "ministry_hours_week": ministry_hours.astype(int),
    "secular_hours_week": secular_hours.astype(int),
    "church_income_pct": church_income_pct.astype(int),
    "avg_attendance": avg_attendance,
    "attendance_3yr_ago": attendance_3yr_ago,
    "annual_budget_usd": annual_budget_usd,
    "spouse_employed": spouse_employed,
    "children_at_home": children_at_home,
    **{f"burnout_{i + 1}": burnout[:, i] for i in range(5)},
    **{f"family_strain_{i + 1}": family[:, i] for i in range(3)},
    **{f"calling_{i + 1}": calling[:, i] for i in range(3)},
    "ministry_satisfaction": satisfaction,
    "considering_leaving": considering_leaving,
    "greatest_challenge": greatest_challenge,
    "greatest_benefit": greatest_benefit,
})

# a little realistic messiness: some skipped answers
for col in ["age", "annual_budget_usd", "burnout_4", "ministry_satisfaction", "greatest_benefit"]:
    df.loc[rng.random(N) < 0.03, col] = np.nan

OUT.parent.mkdir(exist_ok=True)
df.to_csv(OUT, index=False)
print(f"wrote {len(df)} synthetic responses to {OUT}")
