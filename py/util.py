import re
import pandas as pd
import numpy as np

def standardize_direction(df_tracking, df_play):
    
    left_play = df_tracking['play_direction'] == 'left'
    
    df_tracking['x'] = np.where(left_play, 120 - df_tracking['x'], df_tracking['x'])
    df_tracking['y'] = np.where(left_play, 53.3 - df_tracking['y'], df_tracking['y'])
    df_tracking['dir'] = np.where(left_play, (df_tracking['dir'] - 180) % 360, df_tracking['dir'])
    df_tracking['o'] = np.where(left_play, (df_tracking['o'] - 180) % 360, df_tracking['o'])

    # flip the degree axis system to be in alignment with the radian circle
    df_tracking['dir'] = (90 - df_tracking['dir']) % 360
    df_tracking['o'] = (90 - df_tracking['o']) % 360

    key = ['game_id','play_id']
    df_play = df_play.merge(df_tracking[key + ['play_direction']], how='left', on=key)
    df_play['absolute_yardline_number'] = np.where(df_play.play_direction == "left", 
                                                   120 - df_play.absolute_yardline_number, 
                                                   df_play.absolute_yardline_number)
    df_play.drop('play_direction', axis=1)

    return df_tracking, df_play

def uncamelcase_columns(df):
    df.columns = [re.sub(r'(?<!^)(?=[A-Z])', '_', word).lower() for word in df.columns]