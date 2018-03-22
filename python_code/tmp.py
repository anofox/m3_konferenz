def get_max(df):
    return df.index.get_level_values(1).max()

def get_min(df):
    return df.index.get_level_values(1).max()

df_dates = df.groupby(level = 0).apply(trans_function2)
df['hour'] = df.index.get_level_values(1).hour
df['weekday'] = df.index.get_level_values(1).weekday

df['date'] = df.index.get_level_values(1).date
df_count = df.groupby([df.index.get_level_values(0), 'date'])['hour'].agg(['count']).reset_index()

merge = pd.merge(df, df_count, how='left', sort=False)
merge.index(['id', 'date'])