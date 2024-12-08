import os
import sys
from os.path import join
from tqdm import tqdm
import pandas as pd
import numpy as np
import nfl_data_py as nfl
import logging  # Add this line for logging

# Initialize logging
logging.basicConfig(
    filename='play_animation.log',  # Log file path
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

ROOT_DIR = os.path.abspath(os.path.join(os.getcwd(), '..'))
sys.path.insert(0, os.path.join(ROOT_DIR,'..','py'))

import util
from plot.plotter import NFLPlayAnimator

pd.set_option('display.max_rows',None)
pd.set_option('display.max_columns',None)

# Define the path to the data folder
WEEK = 5
DATA_DIR = "../../data/"
WEEKS = range(WEEK, WEEK+3)

df_game = pd.read_csv(join(DATA_DIR, "games.csv"))
df_play = pd.read_csv(join(DATA_DIR, "plays.csv"))
df_player_play = pd.read_csv(join(DATA_DIR, "player_play.csv"))
df_player = pd.read_csv(join(DATA_DIR, "players.csv"))

tracking_dfs = []
for wk in tqdm(WEEKS, desc="Loading tracking files"):
    df = pd.read_csv(join(DATA_DIR, f'tracking_week_{wk}.csv'))
    if 'week' not in df.columns:
        df.insert(3,'week',wk)
    tracking_dfs.append(df)
    
df_tracking = pd.concat(tracking_dfs, axis=0)

del tracking_dfs

util.uncamelcase_columns(df_game)
util.uncamelcase_columns(df_player)
util.uncamelcase_columns(df_play)
util.uncamelcase_columns(df_player_play)
util.uncamelcase_columns(df_tracking)

# standardize direction to be offense moving right
df_tracking, df_play = util.standardize_direction(df_tracking, df_play)

df_game = df_game.query('week.isin(@WEEKS)').reset_index(drop=True)
game_ids = df_game['game_id'].unique().tolist()
df_player_play = df_player_play.query('game_id in @game_ids').reset_index(drop=True)

df_tracking = df_tracking.merge(df_player[['nfl_id','position']], on='nfl_id', how='left')

df_teams = nfl.import_team_desc()

team_cols = ['team_abbr', 'team_color','team_color2','team_logo_wikipedia', 'team_wordmark']

if 'possession_team_color' not in df_play.columns:
    df_play = df_play.merge(
        right=df_teams[team_cols].rename(columns={
            'team_abbr':'possession_team',
            'team_color':'possession_team_color',
            'team_color2':'possession_team_color2',
            'team_logo_wikipedia':'possession_team_logo',
            'team_wordmark':'possession_team_wordmark'
        }),
        how='left',
        on='possession_team'
    )

if 'defensive_team_color' not in df_play.columns:
    df_play = df_play.merge(
        right=df_teams[team_cols].rename(columns={
            'team_abbr':'defensive_team',
            'team_color':'defensive_team_color',
            'team_color2':'defensive_team_color2',
            'team_logo_wikipedia':'defensive_team_logo',
            'team_wordmark':'defensive_team_wordmark',
        }),
        how='left',
        on='defensive_team'
    )

if 'home_team_abbr' not in df_play.columns:
    df_play = df_play.merge(
        right=df_game[['game_id','home_team_abbr','visitor_team_abbr']],
        how='left',
        on='game_id'
    ).rename(columns={
        'visitor_team_abbr':'away_team_abbr'
    })
    

if 'home_team_wordmark' not in df_play.columns:
    df_play['home_team_wordmark'] = np.where(
        df_play.home_team_abbr == df_play.possession_team, 
        df_play.possession_team_wordmark, 
        df_play.defensive_team_wordmark
    )

if 'home_team_logo' not in df_play.columns:
    df_play['home_team_logo'] = np.where(
        df_play.home_team_abbr == df_play.possession_team, 
        df_play.possession_team_logo, 
        df_play.defensive_team_logo
    )
    df_play['away_team_logo'] = np.where(
        df_play.home_team_abbr == df_play.possession_team, 
        df_play.defensive_team_logo,
        df_play.possession_team_logo
    )

if 'home_team_color' not in df_play.columns:
    df_play['home_team_color'] = np.where(
        df_play.home_team_abbr == df_play.possession_team, 
        df_play.possession_team_color, 
        df_play.defensive_team_color
    )
    df_play['away_team_color'] = np.where(
        df_play.home_team_abbr == df_play.possession_team, 
        df_play.defensive_team_color,
        df_play.possession_team_color
    )

if 'down_and_dist' not in df_play.columns:
    down_map = {
        1:'1st',
        2:'2nd',
        3:'3rd',
        4:'4th'
    }
    df_play['down_and_dist'] = df_play['down'].map(down_map) + ' & ' + df_play['yards_to_go'].astype(str)

if 'quarter_with_suffix' not in df_play.columns:
    quarter_map = {
        1:'1st',
        2:'2nd',
        3:'3rd',
        4:'4th',
    }
    df_play['quarter_with_suffix'] = df_play['quarter'].map(quarter_map)

from matplotlib import pyplot as plt
from IPython.display import HTML

npa = NFLPlayAnimator(
    df_tracking,
    df_play,
    show_scoreboard=True,
    clock_rolling=True,
    player_display_type='dots-team',
    show_player_legend=False,
    plot_dir_arrows=False,
    show_trenches_paths=True
)

WRITE_PATH = r'/Users/lukeneuendorf/Library/Mobile Documents/com~apple~CloudDocs/bdb25'
MOTION_PATH = join(WRITE_PATH, 'motion')
SHIFT_PATH = join(WRITE_PATH, 'shift')
MOTION_AND_SHIFT_PATH = join(WRITE_PATH, 'motion_and_shift')
REGULAR_PATH = join(WRITE_PATH, 'regular')

key = ['game_id','play_id']

# Filter down to run plays only
run_plays = ['INSIDE_LEFT', 'OUTSIDE_RIGHT', 'OUTSIDE_LEFT', 'INSIDE_RIGHT']
df_run_plays = df_play.query('rush_location_type.isin(@run_plays)')[key + ['rush_location_type']]
df_tracking = df_tracking.merge(df_run_plays, on=key, how='inner').dropna(subset=['rush_location_type'])

# make folders in each directory for the different types of plays
for path in [MOTION_PATH, SHIFT_PATH, MOTION_AND_SHIFT_PATH, REGULAR_PATH]:
    for folder in run_plays:
        if not os.path.exists(join(path, folder)):
            os.makedirs(join(path, folder))
            
plays_grouped = df_tracking.groupby(key)['event'].agg(list).reset_index()
motion_only_plays = plays_grouped[
    plays_grouped['event'].apply(lambda events: 'man_in_motion' in events and 'shift' not in events)
]
motion_only_plays = motion_only_plays[key].reset_index(drop=True)

shift_only_plays = plays_grouped[
    plays_grouped['event'].apply(lambda events: 'shift' in events and 'man_in_motion' not in events)
]
shift_only_plays = shift_only_plays[key].reset_index(drop=True)

motion_and_shift_plays = plays_grouped[
    plays_grouped['event'].apply(lambda events: 'shift' in events and 'man_in_motion' in events)
]
motion_and_shift_plays = motion_and_shift_plays[key].reset_index(drop=True)

no_motion_no_shift_plays = plays_grouped[
    plays_grouped['event'].apply(lambda events: 'shift' not in events and 'man_in_motion' not in events)
]
no_motion_no_shift_plays = no_motion_no_shift_plays[key].reset_index(drop=True)

for i in tqdm(range(30), desc="Animating motion only plays"):
    try:
        row = np.random.choice(motion_only_plays.index)
        game_id, play_id = motion_only_plays.loc[row, key]
        run_type = df_tracking[(df_tracking['game_id'] == game_id) & (df_tracking['play_id'] == play_id)]['rush_location_type'].values[0]
        FOLDER = join(MOTION_PATH, run_type)
        npa.animate_play(game_id, play_id, output='file', filepath=join(FOLDER, f'{game_id}_{play_id}.mp4'))
    except Exception as e:
        logging.error(f'Failed to animate play a motion play: {e}')

for i in tqdm(range(30), desc="Animating shift only plays"):
    try:
        row = np.random.choice(shift_only_plays.index)
        game_id, play_id = shift_only_plays.loc[row, key]
        run_type = df_tracking[(df_tracking['game_id'] == game_id) & (df_tracking['play_id'] == play_id)]['rush_location_type'].values[0]
        FOLDER = join(SHIFT_PATH, run_type)
        npa.animate_play(game_id, play_id, output='file', filepath=join(FOLDER, f'{game_id}_{play_id}.mp4'))
    except Exception as e:
        logging.error(f'Failed to animate play a shift play: {e}')

for i in tqdm(range(30), desc="Animating motion and shift plays"):
    try:
        row = np.random.choice(motion_and_shift_plays.index)
        game_id, play_id = motion_and_shift_plays.loc[row, key]
        run_type = df_tracking[(df_tracking['game_id'] == game_id) & (df_tracking['play_id'] == play_id)]['rush_location_type'].values[0]
        FOLDER = join(MOTION_AND_SHIFT_PATH, run_type)
        npa.animate_play(game_id, play_id, output='file', filepath=join(FOLDER, f'{game_id}_{play_id}.mp4'))
    except Exception as e:
        logging.error(f'Failed to animate play a motion and shift play: {e}')
    
for i in tqdm(range(30), desc="Animating regular plays"):
    try:
        row = np.random.choice(no_motion_no_shift_plays.index)
        game_id, play_id = no_motion_no_shift_plays.loc[row, key]
        run_type = df_tracking[(df_tracking['game_id'] == game_id) & (df_tracking['play_id'] == play_id)]['rush_location_type'].values[0]
        FOLDER = join(REGULAR_PATH, run_type)
        npa.animate_play(game_id, play_id, output='file', filepath=join(FOLDER, f'{game_id}_{play_id}.mp4'))
    except Exception as e:
        logging.error(f'Failed to animate play a regular play: {e}')