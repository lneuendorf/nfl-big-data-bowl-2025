import re
from typing import Tuple

import pandas as pd
import numpy as np

def standardize_direction(
    df_tracking: pd.DataFrame,
    df_play: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Standardize the direction of the play and the players to be vertical.

    The direction of the play is set to be bottom to top, with the offensive
    moving from the bottom to the top.

    Args:
        df_tracking: The tracking data.
        df_play: The play data.

    Returns:
        The tracking data and the play data with the direction standardized.
    """
    
    left_play = df_tracking['play_direction'] == 'left'
    
    original_x = df_tracking['x'].copy()
    original_y = df_tracking['y'].copy()
    
    df_tracking['y'] = np.where(
        left_play, 
        120 - original_x,
        original_x
    )
    df_tracking['x'] = np.where(
        left_play, 
        original_y,
        53.3 - original_y
    )

    #TODO: figure out if you need to flip the direction of the players 
    # df_tracking['dir'] = np.where(
    #     left_play, 
    #     (df_tracking['dir'] - 90) % 360, 
    #     (df_tracking['dir'] + 90) % 360
    # )
    # df_tracking['o'] = np.where(
    #     left_play, 
    #     (df_tracking['o'] - 90) % 360, 
    #     (df_tracking['o'] + 90) % 360
    # )

    df_tracking['dir'] = (180 - df_tracking['dir']) % 360
    df_tracking['o'] = (180 - df_tracking['o']) % 360

    key = ['game_id', 'play_id']
    df_play = df_play.merge(
        right = df_tracking.drop_duplicates(key)[key + ['play_direction']], 
        how = 'left', 
        on = key
    )

    # Drop plays that arent in the tracking data
    df_play = df_play.dropna(subset=['play_direction']).reset_index(drop=True)

    df_play['absolute_yardline_number'] = np.where(
        df_play.play_direction == "left", 
        120 - df_play.absolute_yardline_number, 
        df_play.absolute_yardline_number
    )
    
    df_play.drop('play_direction', axis=1)

    return df_tracking, df_play

def uncamelcase_columns(df: pd.DataFrame) -> None:
    df.columns = [re.sub(r'(?<!^)(?=[A-Z])', '_', word).lower() for word in df.columns]