import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML

def plot_play_with_speed(
    df_tracking, 
    game_play_id, 
    NON_STATIONARY_THRESHOLD=1.0, 
    MOVING_WINDOW=3, 
    every_other_frame=True, 
    event_col='event',
    plot_motion=True,
    highlight_offensive_positions=True,
    show_motion_frames=False,
    highlight_oline=False,
    highlight_primary_rb=False,
    highlight_pullers=False
) -> HTML:
    qry = 'game_play_id==@game_play_id'
    tracking_play = df_tracking.query(qry).copy().reset_index(drop=True)

    # Keep every other frame, the first and last frames, and frames with events
    first_frame = tracking_play['frame_id'].min()
    last_frame = tracking_play['frame_id'].max()
    frames_with_events = tracking_play.groupby('frame_id')[event_col].transform('any')

    if every_other_frame:
        tracking_play = tracking_play[
            (tracking_play['frame_id'] == first_frame) | 
            (tracking_play['frame_id'] == last_frame) | 
            (frames_with_events) |
            (tracking_play['frame_id'] % 2 == 0)  # Keep even frames only
        ].copy().reset_index(drop=True)

    frames = tracking_play['frame_id'].unique()
    current_event = [None]  

    field_width = 53.3

    # Prepare speed data for the motion player
    if plot_motion:
        cols = ['frame_id','s','nfl_id']
        if show_motion_frames:
            cols = ['frame_id','s','motion_frame','nfl_id']
        motion_query = df_tracking.query(
            'game_play_id==@game_play_id and ' +
            'offense and ' +
            'motion_player'
        )[cols]
        motion_query['s_smoothed'] = motion_query['s'].rolling(window=MOVING_WINDOW, min_periods=1, center=True).mean()
        min_speed = motion_query['s_smoothed'].min()
        max_speed = motion_query['s_smoothed'].max()
        ball_snap_frame_id = tracking_play.query('event_new == "ball_snap"').frame_id.iloc[0]
        line_set_frame_ids = tracking_play.query('event_new == "line_set"').frame_id.values.tolist()
        motion_player_id = motion_query['nfl_id'].iloc[0]

        # Extract speed and frames
        speed_frames = motion_query['frame_id'].values
        speeds_smoothed = motion_query['s_smoothed'].values

    if plot_motion:
        fig, (ax, ax_speed) = plt.subplots(2, 1, figsize=(10, 10), gridspec_kw={'height_ratios': [5, 2]})
    else:
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    
    padding = 2
    min_y = tracking_play.y.min() - padding
    max_y = tracking_play.y.max() + padding

    los = tracking_play['absolute_yardline_number'].iloc[0]
    to_go_line = los + tracking_play['yards_to_go'].iloc[0]

    def update(frame_id):
        """Update function for each animation frame."""
        ax.clear()
        if plot_motion:
            ax_speed.clear()

        # Field plot
        ax.set_facecolor('lightgrey')
        ax.set_yticks(np.arange(10, 110+1, 5))
        ax.grid(which='major', axis='y', linestyle='-', linewidth='0.5', color='black', zorder=1)

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        ax.set_xlim(0, field_width)
        ax.set_ylim(min_y, max_y)

        current_frame = tracking_play.query('frame_id == @frame_id')

        if highlight_offensive_positions:
            lineman = current_frame.query('offense and position_by_loc in ["LT","LG","C","RG","RT","T","G"]')
            qb = current_frame.query('offense and position_by_loc == "QB"')
            rb = current_frame.query('offense and position_by_loc == "RB"')
            fb = current_frame.query('offense and position_by_loc == "FB"')
            te = current_frame.query('offense and position_by_loc == "TE"')
            wr = current_frame.query('offense and position_by_loc == "WR"')
        else:
            offense = current_frame.query('offense')

        if highlight_offensive_positions:
            ax.scatter(lineman.x, lineman.y, c='lightblue', edgecolor='black', label='Lineman', zorder=2)
            ax.scatter(qb.x, qb.y, c='purple', edgecolor='black', label='QB', zorder=2)
            ax.scatter(rb.x, rb.y, c='orange', edgecolor='black', label='RB', zorder=2)
            ax.scatter(fb.x, fb.y, c='pink', edgecolor='black', label='FB', zorder=2)
            ax.scatter(te.x, te.y, c='green', edgecolor='black', label='TE', zorder=2)
            ax.scatter(wr.x, wr.y, c='red', edgecolor='black', label='WR', zorder=2)

        if not highlight_offensive_positions:
            ax.scatter(offense.x, offense.y, c='#fc8077', edgecolor='black', label='Offense', zorder=2)

        if highlight_oline:
            oline = current_frame.query('offense and on_oline')
            ax.scatter(oline.x, oline.y, c='red', marker='x', label='Offensive Line', zorder=2, s=20, lw=1)

        if highlight_primary_rb:
            primary_rb = current_frame.query('offense and primary_rb')
            ax.scatter(primary_rb.x, primary_rb.y, c='green', marker='x', label='Primary RB', zorder=2, s=20, lw=1)

        if highlight_pullers:
            pullers = current_frame.query('offense and (puller_left_of_rt or puller_left_of_center)')
            ax.scatter(pullers.x, pullers.y, facecolors="none", edgecolor='pink', label='Puller', zorder=2)

        if plot_motion:
            motion_player = current_frame.query('motion_player')
            ax.scatter(motion_player.x, motion_player.y, c='red', edgecolor='black', label='Motion Player', zorder=2)

        # Plot defense and football
        defense = current_frame.query('~offense and club != "football"')
        football = current_frame.query('club == "football"')
        ax.scatter(defense.x, defense.y, c='blue', edgecolor='black', label='Defense', zorder=2)
        ax.scatter(football.x, football.y, c='brown', edgecolor='black', label='Football', s=20, zorder=3)

        # Plot the line of scrimmage and to-go line
        ax.axhline(los, color='blue', linewidth=1.2, linestyle='-', zorder=1)
        ax.axhline(to_go_line, color='yellow', linewidth=1.2, linestyle='-', zorder=1)

        # Event annotation
        event = current_frame[event_col].iloc[0]
        box_color = 'white'  # Default color
        alpha_value = 0.8    # Transparency value
        
        # Set box color based on event type
        if event == 'line_set':
            box_color = 'green'
            alpha_value = 0.5  # More transparency for the green box
        elif event == 'ball_snap':
            box_color = 'red'
            alpha_value = 0.5  # More transparency for the red box
        
        ax.text(
            1, max_y + 1.5, f"{event}",
            fontsize=12, ha='left', color='black',
            bbox=dict(facecolor=box_color, alpha=alpha_value),
            zorder=4
        )

        ax.text(52.3, max_y + 1.5, f"{frame_id / 10:.01f} s", fontsize=12, ha='right', color='black', 
                bbox=dict(facecolor='white', alpha=0.8), zorder=4)

        # Speed plot
        if plot_motion:
            up_to_frame = motion_query[motion_query['frame_id'] <= frame_id]
            ax_speed.plot(
                up_to_frame['frame_id'], 
                up_to_frame['s_smoothed'], 
                zorder=2, 
                color='red'
            )
            ax_speed.hlines(
                NON_STATIONARY_THRESHOLD, 
                xmin=motion_query['frame_id'].min(), 
                xmax=motion_query['frame_id'].max(), 
                color='darkgrey',
                zorder=1
            )
            ax_speed.fill_between(
                up_to_frame['frame_id'],  # x values
                up_to_frame['s_smoothed'],  # y values
                NON_STATIONARY_THRESHOLD,  # baseline
                where=up_to_frame['s_smoothed'] > NON_STATIONARY_THRESHOLD,  # condition for shading
                interpolate=True,         # interpolates between points
                color='lightgrey',       # shading color
                alpha=0.5,               # transparency
                zorder=0
            )

            ax_speed.axvline(ball_snap_frame_id, color='black', linestyle='--', zorder=1)

            for line_set_frame_id in line_set_frame_ids:
                ax_speed.axvline(line_set_frame_id, color='green', linestyle='--', zorder=1, lw=1)

            if show_motion_frames:
                motion_frames = up_to_frame.query('motion_frame').frame_id.values.tolist()
                if motion_frames:
                    ax_speed.fill_between(
                        x=motion_frames,  # x values
                        y1=min_speed-2,  # y values
                        y2=max_speed+2,
                        color='red',       # shading color
                        alpha=0.5,               # transparency
                        zorder=0
                    )

            ax_speed.set_xlabel('Frame ID')
            ax_speed.set_ylabel('Speed (yd/s)')
            ax_speed.set_xlim(motion_query['frame_id'].min(), motion_query['frame_id'].max())
            ax_speed.set_ylim(min_speed-2, max_speed+2)
            ax_speed.title.set_text(f"Motion Player: {motion_player_id}")

        # show legend
        ax.legend(loc='upper right', bbox_to_anchor=(1, 1))

    ani = FuncAnimation(fig, update, frames=frames, interval=100, repeat=False)

    plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.95)

    plt.close(fig)

    return HTML(ani.to_jshtml(fps=5))