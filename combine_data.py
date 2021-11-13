import pandas as pd

df1 = pd.read_csv('data//alexander_algoaddition_adddate.csv')
df2 = pd.read_csv('data//michael_algoaddition_adddate.csv')
df3 = pd.read_csv('data//randyll_algoaddition_adddate.csv')

df = pd.concat([df1, df2, df3])
print(df.head())
df.to_csv('data//algoaddition_adddate.csv')