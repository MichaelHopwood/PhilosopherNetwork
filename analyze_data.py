import pandas as pd

df = pd.read_csv('data//algoaddition_adddate.csv', index_col='Unnamed: 0', na_values=['FILL'])
print(df.isna().sum())
print(df.shape)