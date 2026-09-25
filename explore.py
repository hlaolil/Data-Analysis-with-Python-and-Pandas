# %%
import pandas as pd

df = pd.read_csv("data/sample_lab_results.csv")
print(df)
print(df.shape)

# %%
df.info()

# %%
df.head(3)

# %%
df.tail(3)
# %%
