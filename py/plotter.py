import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class TrackingDataPlotter:
    def __init__(self, df_game, df_play, df_player):
        self.df_game = df_game
        self.df_play = df_play
        self.df_player = df_player

    def plot_play(self, df_tracking, field_control_on=False, no_arrows=False,
              field_control_granularity=0.7, colorbar = False):
        
        z_ord = {
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
            'los': 0.8
        }

        color = {
            'off': 'lightgreen',
            'def': 'purple',
            'yardline': 'silver'
        }
        
        if df_tracking.play_id.nunique() != 1:
            raise ValueError('df_tracking must be a single play')
        if df_tracking.game_id.nunique() != 1:
            raise ValueError('df_tracking must be a single game')
        
        game_id = df_tracking.game_id.values[0]
        play_id = df_tracking.play_id.values[0]

        # Plot the sidelines
        plt.axhline(y=0, color=yardline_color, alpha=alpha_field, zorder=z_ord_field)
        plt.axhline(y=53.3, color=yardline_color, alpha=alpha_field, zorder=z_ord_field)

        # Plot the yardlines
        x_min_yardline, x_max_yardline = None, None
        if df_play is not None:
            est_catch_x = df_play_qry.guardrailed_estimated_catch_x.values[0]
            if est_catch_x < df_qry.x.min():
                x_min_yardline = int((est_catch_x // 10) * 10)
            else:
                x_min_yardline = int((df_qry.x.min() // 10) * 10)

            if est_catch_x > df_qry.x.max():
                x_max_yardline = int(math.ceil(est_catch_x / 10) * 10)
            else:
                x_max_yardline = int(math.ceil(df_qry.x.max() / 10) * 10)
        else: 
            x_min_yardline = int((df_qry.x.min() // 10) * 10)
            x_max_yardline = int(math.ceil(df_qry.x.max() / 10) * 10)

        for x in range(x_min_yardline, x_max_yardline+1, 10):
            if not (x < 10 or x > 110):
                plt.axvline(x=x, color=yardline_color, alpha=alpha_field, zorder=z_ord_field)
            if x >= 20 and x <= 60:
                plt.text(x=x-1.15, y=5, s=str(x-10), fontsize=12, color=yardline_color, 
                        alpha=alpha_field, zorder=z_ord_field)
                plt.text(x=x-1.45, y=48.3, s=str(x-10), fontsize=12, color=yardline_color, 
                        alpha=alpha_field, rotation=180, zorder=z_ord_field)
            elif x > 60 and x <= 100:
                yardline_mapper = {70:40, 80:30, 90:20, 100:10}
                plt.text(x=x-1.15, y=5, s=str(yardline_mapper[x]), fontsize=12, color=yardline_color, 
                        alpha=alpha_field, zorder=z_ord_field)
                plt.text(x=x-1.45, y=48.3, s=str(yardline_mapper[x]), fontsize=12, color=yardline_color, 
                        alpha=alpha_field, rotation=180, zorder=z_ord_field)

        # Shade the endzones
        if x_max_yardline >= 110:
            plt.axvline(x=120, color=yardline_color, alpha=alpha_field, zorder=z_ord_field)
            x_rect = [110, 120, 120, 110]
            y_rect = [0, 0, 53.3, 53.3] 
            plt.fill(x_rect, y_rect, color=yardline_color, alpha=0.3)
            plt.xlim(x_min_yardline-5, 120.1)
            plt.text(x=115, y=53.3/2, s="ENDZONE", fontsize=25, color=yardline_color, 
                    alpha=alpha_field, rotation=270, zorder=z_ord_field,
                    horizontalalignment='center', verticalalignment='center')
        elif x_min_yardline <= 10:
            plt.axvline(x=0, color=yardline_color, alpha=alpha_field, zorder=z_ord_field)
            x_rect = [0, 10, 10, 0]
            y_rect = [0, 0, 53.3, 53.3] 
            plt.fill(x_rect, y_rect, color=yardline_color, alpha=0.3)
            plt.xlim(-0.1, x_max_yardline+5)
            plt.text(x=5, y=53.3/2, s="ENDZONE", fontsize=25, color=yardline_color, 
                    alpha=alpha_field, rotation=90, zorder=z_ord_field,
                    horizontalalignment='center', verticalalignment='center')
        

        # Plot LOS and First Down Line
        plt.axvline(x=df_qry.absolute_yard_line.values[0], color='yellow', alpha=alpha_los, 
                    zorder=z_ord_los)
        plt.axvline(x=df_qry.absolute_yard_line.values[0] + df_qry.distance.values[0],
                    color='darkblue', alpha=alpha_first_down, zorder=z_ord_first_down)

        # Plot field control if asked
        if field_control_on and (df_play is not None):
            x_min = 0 if x_min_yardline <= 10 else x_min_yardline - 5
            x_max = 120 if x_max_yardline >= 110 else x_max_yardline + 5
            x_range = np.arange(x_min, x_max+field_control_granularity, field_control_granularity) 
            y_range = np.arange(0, 53.3+field_control_granularity, field_control_granularity)
            
            X, Y = np.meshgrid(x_range, y_range)
            
            coords = np.column_stack((X.flatten(), Y.flatten()))

            field_control_grid = field_control(df_player_qry=df_qry, 
                                            df_play_qry= df_play_qry, 
                                            coords=coords,
                                            grid_shape=X.shape)
            plt.imshow(field_control_grid, 
                    cmap=field_control_cmap,
                    interpolation='nearest', 
                    extent=[x_min, x_max+field_control_granularity, 0, 53.3+field_control_granularity], 
                    alpha=alpha_field_ctrl,
                    zorder=z_ord_field_ctrl)
            if colorbar:
                plt.colorbar()

        plt.ylim(-.1, 53.4)
        plt.axis('off')
        
        # Filter out duplicate labels and colors for the legend
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if colorbar and field_control_on and (df_play is not None):
            plt.legend(by_label.values(), by_label.keys(), loc='upper left', bbox_to_anchor=(1.25, 1))
        else:
            plt.legend(by_label.values(), by_label.keys(), loc='upper left', bbox_to_anchor=(1, 1))