import math
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from field_control import field_control

def send_cols_to_end_of_dataframe(df, cols):
    for col in cols:
        df.insert(len(df.columns)-1, col, df.pop(col))

def send_col_to_index_in_dataframe(df, col, idx):
    df.insert(idx, col, df.pop(col))

def plot_play(df_player, game_id, play_id, df_play=None, field_control_on=False, no_arrows=False,
              field_control_granularity=0.7, colorbar = False):
    """
    Plots a single frame of a play

    Parameters
    ----------
    df_player: tracking data at a player level
    game_id: component of composite key
    play_id: component of composite key
    df_play: tracking data at a play level, including estimated catch point
    field_control_on: plots field control of the offense if True and df_play was passed
    no_arrows: dont plot the arrows
    field_control_granularity: the pixel width of field control
    colorbar: display the colorbar if feild control is plotted
    """
    
    qb_color = 'black'
    tgt_color = 'darkgreen'
    off_color = 'lightgreen'
    def_color = 'purple'
    est_catch_color = 'black'
    yardline_color = 'silver' 
    field_control_cmap = 'PRGn'
    
    alpha_player = 0.8
    alpha_field = 1
    alpha_field_ctrl = 0.6
    alpha_first_down = 0.4
    alpha_los = 0.8

    z_ord_player = 4
    z_ord_field_ctrl = 2
    z_ord_los = 3
    z_ord_first_down = 3
    z_ord_field = 1
    
    df_qry = df_player.query('game_id==@game_id & play_id==@play_id')
    
    label_colors = {}
    
    for i, row in df_qry.iterrows():
        row_dict = row.to_dict()
        player_id = row_dict['player_id']
        qb_id = row_dict['qb_id']
        tgt_id = row_dict['tgt_id']
        off_def = row_dict['off_def']
        
        if player_id == qb_id:
            label = 'qb'
            color = qb_color
        elif player_id == tgt_id:
            label = 'tgt'
            color = tgt_color
        elif off_def == 'off':
            label = 'off'
            color = off_color
        elif off_def == 'def':
            label = 'def'
            color = def_color
        
        plt.scatter(row_dict['x'], row_dict['y'], c=color, label=label, alpha=alpha_player, 
                    zorder=z_ord_player)

        # Plot the vector arrows
        if not no_arrows:
            dx = np.cos(row_dict['dir_radians']) * row_dict['s'] * .5 
            dy = np.sin(row_dict['dir_radians']) * row_dict['s'] * .5 
            plt.arrow(row_dict['x'], row_dict['y'], dx, dy, head_width=0.5, head_length=0.5, 
                      fc=color, ec=color, alpha=alpha_player, zorder=z_ord_player)

        label_colors[label] = color

    # Plot the estimated catch point if included
    df_play_qry = None
    if df_play is not None:
        df_play_qry = df_play.query('game_id==@game_id & play_id==@play_id')
        x,y = df_play_qry.guardrailed_estimated_catch_x.values[0], df_play_qry.guardrailed_estimated_catch_y.values[0]
        plt.scatter(x, y, c=est_catch_color, label='est catch', alpha=alpha_player,
                    zorder=z_ord_player, marker='x')

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