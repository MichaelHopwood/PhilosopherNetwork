import pandas as pd

df1 = pd.read_csv('data//alexander_algoaddition_adddate.csv')
df2 = pd.read_csv('data//michael_algoaddition_adddate.csv')
df3 = pd.read_csv('data//randyll_algoaddition_adddate.csv')

df = pd.concat([df1, df2, df3], ignore_index=True)
del df['Unnamed: 0']
df.reset_index(drop=True, inplace=True)
df['id'] = df.index + 1
print(df.head())
df.to_csv('data//algoaddition_adddate.csv', index=False)

name_to_id_dict = dict(zip(df['name'].values.tolist(), df['id'].values.tolist()))

# Edge data
edge_data = []
for ind, row in df.iterrows():
    try:
        people = row['incoming_links'].split(':')
        for person in people:
            try:
                edge_data.append([name_to_id_dict[row['name']],
                            name_to_id_dict[person]])
            except KeyError:
                pass
    except AttributeError:
        pass

    try:
        people = row['outgoing_links'].split(':')
        for person in people:
            try:
                edge_data.append([name_to_id_dict[person],
                            name_to_id_dict[row['name']]])
            except KeyError:
                pass
    except AttributeError:
        pass

edge_df = pd.DataFrame(edge_data, columns=['source', 'target'])
edge_df.to_csv('data//algoaddition_adddate_edges.csv', index=False)