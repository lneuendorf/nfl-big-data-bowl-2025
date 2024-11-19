import math
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

from field_control import field_control

class TrackingDataPlotter:
    def __init__(self, df_game, df_play, df_player):
        self.df_game = df_game
        self.df_play = df_play
        self.df_player = df_player

    def plot_play(self, df_tracking, frame_id=None, save_path=None, plot_arrows=True, 
                  plot_field_control=False, field_control_granularity=0.7, colorbar=True):
        z_ord = {
            'football': 5,
            'player': 4,
            'los': 3,
            'first_down': 3,
            'field_ctrl': 2,
            'field': 1
        }

        alpha = {
            'player': 0.8,
            'field': 1,
            'field_ctrl': 0.6,
            'first_down': 0.4,
            'los': 0.9
        }

        color = {
            'off': 'green',
            'def': 'purple',
            'yardline': 'silver',
            'first_down': 'darkblue',
            'los': 'yellow',
            'football': 'brown',
            'field_ctrl': 'PRGn',
            'field': 'whitesmoke'
        }

        df = df_tracking.copy()
        if df.play_id.nunique() != 1:
            raise ValueError('df_tracking must be a single play')
        if df.game_id.nunique() != 1:
            raise ValueError('df_tracking must be a single game')

        gid = df.game_id.values[0]
        pid = df.play_id.values[0]
        play = self.df_play[(self.df_play.game_id == gid) & (self.df_play.play_id == pid)].to_dict(orient='records')[0]
        week = df.week.values[0]
        game = self.df_game[self.df_game.game_id == gid].to_dict(orient='records')[0]
        home_tm = game['home_team_abbr']
        away_tm = game['visitor_team_abbr']
        home_tm_score = play['pre_snap_home_score']
        away_tm_score = play['pre_snap_visitor_score']
        down_mapper = {1: '1st', 2: '2nd', 3: '3rd', 4: '4th'}
        down = down_mapper[play['down']]
        play_desc = f"Q{play['quarter']} - {down} & {play['yards_to_go']} - {play['play_description']}"

        fig, ax = plt.subplots(figsize=(12, 6.33))

        x_min_yardline = int((df.x.min() // 10) * 10)
        x_max_yardline = int(math.ceil(df.x.max() / 10) * 10)

        df['dir_radians'] = np.radians(df['dir'])
        not_football = df['club'] != "football"
        df['dx'] = np.where(not_football, np.cos(df['dir_radians']) * df['s'] * 0.5, None)
        df['dy'] = np.where(not_football, np.sin(df['dir_radians']) * df['s'] * 0.5, None)
        df['offense'] = df['club'] == play['possession_team']

        def plot_field():
            # Shade field
            x_rect = [x_min_yardline, x_max_yardline, x_max_yardline, x_min_yardline]
            y_rect = [0, 0, 53.3, 53.3]
            ax.fill(x_rect, y_rect, color=color['yardline'], alpha=0.3)

            ax.axhline(y=0, color=color['yardline'], alpha=alpha['field'], zorder=z_ord['field'], xmin=0, xmax=120)
            ax.axhline(y=53.3, color=color['yardline'], alpha=alpha['field'], zorder=z_ord['field'], xmin=0, xmax=120)

            for x in range(x_min_yardline, x_max_yardline + 1, 10):
                if not (x < 10 or x > 110):
                    ax.axvline(x=x, color=color['yardline'], alpha=alpha['field'], zorder=z_ord['field'])
                if x >= 20 and x <= 60:
                    ax.text(x=x - 1.15, y=5, s=str(x - 10), fontsize=12,
                            color=color['yardline'], alpha=alpha['field'], zorder=z_ord['field'])
                    ax.text(x=x - 1.45, y=48.3, s=str(x - 10), fontsize=12,
                            color=color['yardline'], alpha=alpha['field'], rotation=180, zorder=z_ord['field'])
                elif x > 60 and x <= 100:
                    yardline_mapper = {70: 40, 80: 30, 90: 20, 100: 10}
                    ax.text(x=x - 1.15, y=5, s=str(yardline_mapper[x]), fontsize=12,
                            color=color['yardline'], alpha=alpha['field'], zorder=z_ord['field'])
                    ax.text(x=x - 1.45, y=48.3, s=str(yardline_mapper[x]), fontsize=12,
                            color=color['yardline'], alpha=alpha['field'], rotation=180, zorder=z_ord['field'])

            if x_max_yardline >= 110:
                ax.axvline(x=120, color=color['yardline'], alpha=alpha['field'], zorder=z_ord['field'])
                x_rect = [110, 120, 120, 110]
                y_rect = [0, 0, 53.3, 53.3]
                ax.fill(x_rect, y_rect, color=color['yardline'], alpha=0.3)
                ax.text(x=115, y=53.3 / 2, s="ENDZONE", fontsize=25, color=color['yardline'],
                        alpha=alpha['field'], rotation=270, zorder=z_ord['field'],
                        verticalalignment='center', horizontalalignment='center')
            elif x_min_yardline <= 10:
                ax.axvline(x=0, color=color['yardline'], alpha=alpha['field'], zorder=z_ord['field'])
                x_rect = [0, 10, 10, 0]
                y_rect = [0, 0, 53.3, 53.3]
                ax.fill(x_rect, y_rect, color=color['yardline'], alpha=0.3)
                ax.text(x=5, y=53.3 / 2, s="ENDZONE", fontsize=25, color=color['yardline'],
                        alpha=alpha['field'], rotation=90, zorder=z_ord['field'],
                        verticalalignment='center', horizontalalignment='center')

            ax.axvline(x=play['absolute_yardline_number'], color=color['los'], alpha=alpha['los'], zorder=z_ord['los'])
            ax.axvline(x=play['absolute_yardline_number'] + play['yards_to_go'],
                       color=color['first_down'], alpha=alpha['first_down'], zorder=z_ord['first_down'])

        df_offense = df[df['club'] == play['possession_team']]
        df_defense = df[df['club'] == play['defensive_team']]
        df_football = df[df['club'] == 'football']

        if frame_id is not None:
            # Plot a single frame
            ax.clear()
            ax.set_ylim(-.1, 53.4)
            xmin, xmax = x_min_yardline, x_max_yardline
            if x_min_yardline == 10:
                xmin = -0.08
            if x_max_yardline == 110:
                xmax = 120.08
            ax.set_xlim(xmin, xmax)
            ax.axis('off')

            plot_field()

            df_frame_offense = df_offense[df_offense['frame_id'] == frame_id]
            df_frame_defense = df_defense[df_defense['frame_id'] == frame_id]
            df_frame_football = df_football[df_football['frame_id'] == frame_id]

            ax.scatter(df_frame_offense['x'], df_frame_offense['y'],
                       color=color['off'], s=100, alpha=alpha['player'], zorder=z_ord['player'])
            ax.scatter(df_frame_defense['x'], df_frame_defense['y'],
                       color=color['def'], s=100, alpha=alpha['player'], zorder=z_ord['player'])
            ax.scatter(df_frame_football['x'], df_frame_football['y'],
                       color=color['football'], s=50, alpha=alpha['player'], zorder=z_ord['football'], marker="D")

            if plot_arrows:
                # Plot direction arrows for offense
                for _, player in df_frame_offense.iterrows():
                    ax.arrow(player['x'], player['y'], player['dx'], player['dy'],
                             head_width=0.5, head_length=0.5, fc=color['off'], ec=color['off'],
                             alpha=alpha['player'], zorder=z_ord['player'])

                # Plot direction arrows for defense
                for _, player in df_frame_defense.iterrows():
                    ax.arrow(player['x'], player['y'], player['dx'], player['dy'],
                             head_width=0.5, head_length=0.5, fc=color['def'], ec=color['def'],
                             alpha=alpha['player'], zorder=z_ord['player'])

            # Show play description and score
            ax.text(5, 58, f"{home_tm} {home_tm_score} - {away_tm} {away_tm_score}",
                    fontsize=15, color='black', alpha=0.7, zorder=5,
                    verticalalignment='center', horizontalalignment='left')
            ax.text(5, 55.5, play_desc, fontsize=15, color='black', alpha=0.7, zorder=5,
                    verticalalignment='center', horizontalalignment='left')

            plt.show()

            # Save as static image if a save path is provided
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
                plt.close(fig)  # Close the figure to free memory
                return

        # Plot the animation
        else:
            def update(frame_id):
                ax.clear()
                ax.set_ylim(-.1, 53.4)
                xmin, xmax = x_min_yardline, x_max_yardline
                if x_min_yardline == 10:
                    xmin = -0.08
                if x_max_yardline == 110:
                    xmax = 120.08
                ax.set_xlim(xmin, xmax)
                ax.axis('off')
    
                plot_field()
    
                df_frame_offense = df_offense[df_offense['frame_id'] == frame_id]
                df_frame_defense = df_defense[df_defense['frame_id'] == frame_id]
                df_frame_football = df_football[df_football['frame_id'] == frame_id]
    
                ax.scatter(df_frame_offense['x'], df_frame_offense['y'],
                           color=color['off'], s=100, alpha=alpha['player'], zorder=z_ord['player'])
                ax.scatter(df_frame_defense['x'], df_frame_defense['y'], 
                           color=color['def'], s=100, alpha=alpha['player'], zorder=z_ord['player'])
                ax.scatter(df_frame_football['x'], df_frame_football['y'], 
                           color=color['football'], s=50, alpha=alpha['player'], zorder=z_ord['football'], marker="D")
    
                if plot_arrows:
                    # Plot direction arrows for offense
                    for _, player in df_frame_offense.iterrows():
                        ax.arrow(player['x'], player['y'], player['dx'], player['dy'], 
                                 head_width=0.5, head_length=0.5, fc=color['off'], ec=color['off'], 
                                 alpha=alpha['player'], zorder=z_ord['player'])
        
                    # Plot direction arrows for defense
                    for _, player in df_frame_defense.iterrows():
                        ax.arrow(player['x'], player['y'], player['dx'], player['dy'], 
                                 head_width=0.5, head_length=0.5, fc=color['def'], ec=color['def'], 
                                 alpha=alpha['player'], zorder=z_ord['player'])
    
                if plot_field_control:
                    x_min = 0 if x_min_yardline <= 10 else x_min_yardline - 5
                    x_max = 120 if x_max_yardline >= 110 else x_max_yardline + 5
                    x_range = np.arange(x_min, x_max+field_control_granularity, field_control_granularity) 
                    y_range = np.arange(0, 53.3+field_control_granularity, field_control_granularity)
                    
                    X, Y = np.meshgrid(x_range, y_range)
                    
                    coords = np.column_stack((X.flatten(), Y.flatten()))
            
                    field_control_grid = field_control(df_tracking=df, 
                                                       coords=coords,
                                                       grid_shape=X.shape)
                    plt.imshow(field_control_grid, 
                               cmap=color['field_ctrl'],
                               interpolation='nearest', 
                               extent=[x_min, x_max+field_control_granularity, 0, 53.3+field_control_granularity], 
                               alpha=alpha['field_ctrl'],
                               zorder=z_ord['field_ctrl'])
    
                ax.set_title(f"2022 Week {week}: {away_tm}:{away_tm_score} @ {home_tm}:{home_tm_score}", 
                             fontsize=20, loc='left', y=1.08)
                ax.text(x=x_min_yardline, y=55.5, s=play_desc, fontsize=12, color='black', 
                        alpha=alpha['field'], zorder=z_ord['field'], 
                        verticalalignment='center', horizontalalignment='left')
                ax.text(x=x_min_yardline, y=-2, s=f'Time elapsed: {frame_id/10} s', fontsize=12, color='black', 
                        alpha=alpha['field'], zorder=z_ord['field'], 
                        verticalalignment='center', horizontalalignment='left')
    
            frames = sorted(df['frame_id'].unique())
            
            anim = FuncAnimation(fig, update, frames=frames, interval=100)
    
            if save_path:
                anim.save(save_path, writer='ffmpeg' if save_path.endswith('.mp4') else 'imagemagick')
            else:
                plt.show()
