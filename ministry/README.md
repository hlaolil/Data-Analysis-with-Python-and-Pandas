# Bivocational Ministry Research: Survey Analysis

This folder applies the pandas techniques from the main project (filtering, sorting, grouping and aggregating, and data conversion) to a survey of **bivocational pastors**, meaning pastors who also hold a secular job. **Fully funded** pastors are the comparison group.

> ⚠️ `data/sample_bivocational_survey.csv` is **synthetic** (made up by `generate_sample_data.py`). It is only here to test the pipeline. Rerun the analysis on your real survey before citing any number.

## Quick start

```bash
pip install -r ministry/requirements.txt
python ministry/generate_sample_data.py        # (re)create synthetic sample
python ministry/analysis.py                     # analyse the sample
python ministry/analysis.py --data my_survey.csv   # analyse YOUR data (.csv or .xlsx)
```

Outputs go to `ministry/output/`: `report.md` (all tables and charts), one CSV per table (`q<question>_<table>.csv`) and the PNG charts.

## Research questions

| # | Question | pandas techniques |
|---|----------|-------------------|
| Q1 | Who responded? (group sizes, demographics, region, reason for bivocational ministry, job sector) | `value_counts`, `groupby().agg`, `crosstab(normalize=)` |
| Q2 | How heavy is the weekly work load? | derived columns, `groupby` means, % over 60 h |
| Q3 | Do bivocational and fully funded pastors differ in burnout, family strain, sense of calling and satisfaction? | Likert composites, reverse coding, Cronbach's α, Cohen's d |
| Q4 | Does burnout rise with total work hours? | `pd.cut` hour bands, Spearman correlation matrix |
| Q5 | Are bivocationally led churches growing or declining? | 3-year attendance change, `pivot_table` by size and region |
| Q6 | Who is considering leaving ministry? | `pd.qcut` burnout tertiles, rates by group |
| Q7 | What themes appear in the open-ended challenges and benefits? | keyword theme coding with `str` methods; uncoded answers listed for review |
| Q8 | What predicts burnout among bivocational pastors? | standardized OLS regression (numpy) |

## Using your own data

1. Export your survey (Qualtrics, Google Forms, SurveyMonkey, etc.) to CSV or Excel, with **one row per respondent**.
2. Open `analysis.py` and edit the **CONFIG** block:
   * `COLUMN_MAP` maps your column names to the names below.
   * `GROUP_LABELS` sets the values that mark bivocational and fully funded pastors.
   * `SCALES` and `REVERSE_ITEMS` set the Likert items behind each composite. Leave out any scale your survey lacks.
   * `THEMES` holds the keywords for coding open-ended answers. Refine it using the "answers no theme caught" table.
3. Run `python ministry/analysis.py --data path/to/export.csv`.

Real survey files in `data/` stay out of git automatically: `.gitignore` excludes everything except `sample_*.csv`. Keep respondent data out of the repository.

### Expected columns

| Column | Meaning |
|---|---|
| `respondent_id` | anonymous ID |
| `ministry_status` | `bivocational` / `fully_funded` |
| `bivo_reason` | `financial_necessity` / `missional_choice` / `both` (blank for fully funded) |
| `age`, `gender`, `education`, `denomination`, `years_in_ministry`, `region` | demographics |
| `secular_job_sector` | type of secular job |
| `ministry_hours_week`, `secular_hours_week` | weekly hours |
| `church_income_pct` | % of household income paid by the church |
| `avg_attendance`, `attendance_3yr_ago`, `annual_budget_usd` | church vitality |
| `spouse_employed`, `children_at_home` | family context |
| `burnout_1..5` (item 3 positively worded), `family_strain_1..3`, `calling_1..3` | 1–5 Likert items |
| `ministry_satisfaction` | 1–10 |
| `considering_leaving` | yes / no |
| `greatest_challenge`, `greatest_benefit` | open-ended text |

## Notes on method

* A composite score is the mean of its items. It is left blank when fewer than half the items were answered.
* Cronbach's α ≥ 0.70 is the usual threshold for acceptable reliability.
* Cohen's d is read as about 0.2 small, 0.5 medium and 0.8 large.
* Q8 reports t-values without p-values, so no `scipy` is needed. Treat |t| > 2 as a rough sign of a reliable association. For publication, confirm these results in a dedicated package such as `statsmodels`.
* Charts omit subgroups with fewer than `MIN_CELL_N` (10) respondents.
