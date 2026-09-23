import pandas as pd
from pathlib import Path

for f in Path("data").glob("*.csv"):
    if f.name.startswith("sample_"):
        continue
    pd.read_csv(f, nrows=1000).to_csv(f"data/sample_{f.name}", index=False)