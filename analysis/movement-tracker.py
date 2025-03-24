from pathlib import Path
import pandas as pd 

csv_path = Path("output/counts_by_place_5.csv")

df = pd.read_csv(csv_path)
print(df.head())

