# Overview

This is a patient data analysis software using python and pandas that demonstrates software development skill to filter, sort, aggregate (count / average), and do data conversion.

It analyses patient data obtained from kaggle.com at https://www.kaggle.com/datasets/prasad22/healthcare-dataset which features various attributes, such as patient demographics, medical conditions, and admission details

The purpose of writting this software is to demonstrates software development skill in data analysis with emphais on how pandas can be used to filter, sort, aggregate (count / average), and do data conversion.

Here is a link to a YouTube video demonstration of the program running and a walkthrough of the code.

[Software Demo Video](http://youtube.link.goes.here)

# Data Analysis Results

Question 1: top 10 primary diagnoses
primary_diagnosis
hypertension               232
obesity                    184
hyperlipidemia             175
chronic_kidney_disease      91
anxiety                     63
osteoarthritis              49
type2_diabetes              47
depression                  36
coronary_artery_disease     29
hypothyroidism              27

Question 2: average stay and number of stays by discharge place
                           mean  count
discharge_disposition                 
hospice                6.769231     26
skilled_nursing        5.727273    121
rehab                  5.647619    105
home                   5.356031    514
home_health            5.234234    222
expired                4.666667     12

Question 3: emergency visits by year
year
2018    19
2019    13
2020    17
2021    18
2022    19
2023    23
2024    20

# Development Environment

I developed this program on Windows using Visual Studio Code, with
the Python and Jupyter extensions installed. Python 3.13.15 was installed from
python.org. I used a virtual environment (venv) so that the project's
libraries are kept separate from the rest of the system.

The program is written in Python. It uses pandas 3.0.6 for loading, cleaning,
filtering, sorting and aggregating the data.

# Useful Websites

{Make a list of websites that you found helpful in this project}
* [Web Site Name](https://www.youtube.com/watch?v=ZyhVh-qRZPA&list=PL-osiE80TeTsWmV9i9c58mdDCSskIFdDS)
* [Web Site Name](https://pandas.pydata.org/)

# Future Work

Here is a list of things that I need to fix, improve, and add in the future.
* Install and use matplotlib 3.11.2 for the graphs

