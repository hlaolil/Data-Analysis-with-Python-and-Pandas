# %%
import pandas as pd

df = pd.read_csv("data/sample_lab_results.csv")
print(df.shape)

# %%
df.head()

# %%
df.info()