
import pandas as pd

# -------------------------------------------------
# Question 1
# Which primary diagnoses are most common?
# -------------------------------------------------
dx = pd.read_csv("data/sample_diagnoses.csv")

# count each diagnosis
#value_counts already sorts most common first
counts = dx["primary_diagnosis"].value_counts()

# keep the top 10
top10 = counts.head(10)

print("Question 1: top 10 primary diagnoses")
print(top10)
print()

# -------------------------------------------------
# Question 2
# What is the average stay, and how many stays, for each discharge place?
# -------------------------------------------------
out = pd.read_csv("data/sample_outcomes.csv")

# split by discharge place
# then average stay 
# and count stays
summary = out.groupby("discharge_disposition")["length_of_stay_days"].agg(["mean", "count"])

# longest average stay first
summary = summary.sort_values("mean", ascending=False)

print("Question 2: average stay and number of stays by discharge place")
print(summary)
print()

# -------------------------------------------------
# Question 3
# Among emergency visits only, how many visits are there each year?
# -------------------------------------------------
dx = pd.read_csv("data/sample_diagnoses.csv")

# convert text dates into real dates
dx["visit_date"] = pd.to_datetime(dx["visit_date"])

# convert date into a year
dx["year"] = dx["visit_date"].dt.year

# filter: keep emergency visits only
er = dx[dx["visit_type"] == "emergency"]

# count emergency visits in each year
er_by_year = er.groupby("year")["patient_id"].count()

print("Question 3: emergency visits by year")
print(er_by_year)