import re
import pandas as pd

def standardize_direction(df):
    df_normalized = df.copy()
    
    df_normalized.loc[df['play_direction'] == 'left', 'x'] = 120 - df_normalized['x']
    df_normalized.loc[df['play_direction'] == 'left', 'y'] = 53.3 - df_normalized['y']
    df_normalized.loc[df['play_direction'] == 'left', 'dir'] = (90 - df_normalized['dir']) %360
    df_normalized.loc[df['play_direction'] == 'left', 'o'] = (90 - df_normalized['o']) %360
    
    return df_normalized

def uncamelcase_columns(df):
    df.columns = [re.sub(r'(?<!^)(?=[A-Z])', '_', word).lower() for word in df.columns]