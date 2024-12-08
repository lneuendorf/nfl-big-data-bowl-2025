import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, Polygon, Ellipse
from matplotlib.font_manager import FontProperties
from matplotlib.offsetbox import OffsetImage
from matplotlib.patches import Wedge
from matplotlib.colors import to_rgba
import matplotlib.colors as mcolors
from IPython.display import HTML
import urllib
import PIL
import numpy as np
import pandas as pd

from utils.image_functions import contrast_ratio, plot_image
from visualization.scoreboard import Scoreboard

class NFLPlayAnimator:
    def __init__(
        self, 
        df_tracking: pd.DataFrame,
        df_play: pd.DataFrame,
        show_scoreboard: bool = True,
        clock_rolling: bool = True, 
        player_display_type: str = 'jerseys',
        show_player_legend: bool = True,
        plot_dir_arrows: bool = False,
        show_trenches_paths: bool = False
    ) -> None:
        """Used to plot 2d nfl tracking data.
        
        Args:
            df_tracking: DataFrame containing tracking data.
            df_play: DataFrame containing play data.
            show_scoreboard: Show the scoreboard. Defaults to True.
            clock_rolling: Clock is rolling. Defaults to True.
            player_display_type: How to display the player dots. Options:
                dots-team: Display players as dots.
                dots-positional: Display players as dots with different 
                        colors for each position.
                positions: Display players as circles with a flat side and 
                        a front "half-square".
                jerseys: Display players as circles with a flat side and a 
                        front "half-square" with jersey numbers.
            show_player_legend: Show the player legend. Defaults to True.
            plot_dir_arrows: Plot arrows showing player direction
            show_trenches_paths: Show paths of defensive and offensive linemen
                as well as linebackers and tight ends.
        """

        self.df_tracking = df_tracking
        self.df_play = df_play
        self.show_scoreboard = show_scoreboard
        self.clock_rolling = clock_rolling
        self.player_display_type = player_display_type
        self.show_player_legend = show_player_legend
        self.plot_dir_arrows = plot_dir_arrows
        self.show_trenches_paths = show_trenches_paths
        self.aspect_ratio = 1
        self.y_delta = 35
        self.x_limit_min = 0
        self.x_limit_max = 53.3
        self.numbers_font = FontProperties(fname='../../data/fonts/clarendon_bold.otf')
        self.legend_width = 12
        self.legend_txt_color = 'black'
        self.scoreboard_height = 3
        mpl.rcParams['animation.embed_limit'] = 100

        self.position_colors = {
            'QB': to_rgba('blue'), 
            'T': to_rgba('purple'), 
            'TE': to_rgba('green'),
            'WR': to_rgba('red'),  
            'DE': to_rgba('pink'), 
            'NT': to_rgba('darkred'), 
            'SS': to_rgba('darkseagreen'),  
            'FS': to_rgba('palegoldenrod'),
            'G': to_rgba('orange'),
            'OLB': to_rgba('darkcyan'),
            'DT': to_rgba('slategrey'),
            'CB': to_rgba('orchid'),
            'RB': to_rgba('dodgerblue'),
            'C': to_rgba('indigo'),
            'ILB': to_rgba('lime'),
            'MLB': to_rgba('gold'),
            'FB': to_rgba('darkviolet'),
            'DB': to_rgba('darkorange'),
            'LB': to_rgba('darkgreen'),
        }
        self.position_mapping = {
            'MLB': 'LB',
            'OLB': 'LB',
            'ILB': 'LB',
            'FS': 'S',
            'SS': 'S',
            'NT': 'DL',
            'DE': 'DL',
            'DT': 'DL',
            'CB': 'DB',
            'RB': 'RB',
            'FB': 'RB',
            'WR': 'WR',
            'TE': 'TE',
            'QB': 'QB',
            'C': 'OL',
            'G': 'OL',
            'T': 'OL',
        }

        self.zorder = {
            'field': 1,
            'field_markers': 2,
            'endzones': 3,
            'los_and_fd': 4,
            'defense': 5,
            'defense_numbers': 6,
            'offense': 7,
            'offense_numbers': 8,
            'football': 9,
            'scoreboard_background': 10,
            'scoreboard_foreground': 11,
            'player_legend': 12,
            'player_legend_text': 13,
        }

        if player_display_type not in ['dots-team', 'dots-positional', 'positions', 'jerseys']:
            raise ValueError("Invalid player_display_type. Must be one of 'dots-team', " + 
                             "'dots-potitional', 'positions', or 'jerseys'.")

    @property
    def touchdown_frame_id(self):
        if self._set_touchdown_frame_id is False:
            touchdown_frame_id = self.tracking_data.query('event=="touchdown"')['frame_id']
            if touchdown_frame_id.shape[0] > 0:
                self._touchdown_frame_id = touchdown_frame_id.values[0]
            else:
                self._touchdown_frame_id = None
            self._set_touchdown_frame_id = True
        return self._touchdown_frame_id
    
    @property
    def snap_frame_id(self):
        if self._set_snap_frame_id is False:
            snap_frame_id = self.tracking_data.query('event=="ball_snap"')['frame_id']
            if snap_frame_id.shape[0] > 0:
                self._snap_frame_id = snap_frame_id.values[0]
            else:
                self._snap_frame_id = None
            self._set_snap_frame_id = True
        return self._snap_frame_id
    
    # w 100 h 49
    @property
    def home_img(self):
        if self._home_img is None:
            img = PIL.Image.open(urllib.request.urlopen(self.play_data['home_team_logo']))
            img = img.convert('RGBA')

            # Resize the image to have a height of 100 pixels, keeping the aspect ratio
            width, height = img.size
            new_width = 98
            new_height = int((new_width / width) * height)
            img_resized = img.resize((new_width, new_height), PIL.Image.Resampling.LANCZOS)

            # crop height to be 49 pixels
            height_extra = new_height - 47
            if height_extra > 0:
                y = height_extra // 2
                height_delta = height_extra - y
                img_resized = img_resized.crop((10, y, new_width, new_height - height_delta))

            img_offset = OffsetImage(img_resized, zoom=1)

            self._home_img = img_offset

        return self._home_img
    
    @property
    def away_img(self):
        if self._away_img is None:
            img = PIL.Image.open(urllib.request.urlopen(self.play_data['away_team_logo']))
            img = img.convert('RGBA')

            # Resize the image to have a height of 100 pixels, keeping the aspect ratio
            width, height = img.size
            new_width = 98
            new_height = int((new_width / width) * height)
            img_resized = img.resize((new_width, new_height), PIL.Image.Resampling.LANCZOS)

            # crop height to be 49 pixels
            height_extra = new_height - 47
            if height_extra > 0:
                y = height_extra // 2
                height_delta = height_extra - y
                img_resized = img_resized.crop((10, y, new_width, new_height - height_delta))

            img_offset = OffsetImage(img_resized, zoom=1)

            self._away_img = img_offset

        return self._away_img
    
    @property
    def home_wordmark(self):
        if self._home_wordmark is None:
            self._home_wordmark = OffsetImage(
                PIL.Image.open(
                    urllib.request.urlopen(
                        self.play_data['home_team_wordmark']
                    )
                ).convert('RGBA'), zoom=1)
        return self._home_wordmark
    
    @property
    def home_wordmark_rotated(self):
        if self._home_wordmark_rotated is None:
            self._home_wordmark_rotated = OffsetImage(
                PIL.Image.open(
                    urllib.request.urlopen(
                        self.play_data['home_team_wordmark']
                    )
                ).convert('RGBA').rotate(180), zoom=1)
        return self._home_wordmark_rotated

    @property
    def def_tm_color(self):
        if self._def_tm_color is None:
            cr_1 = contrast_ratio(self.play_data['possession_team_color'], 
                                  self.play_data['defensive_team_color'])
            cr_2 = contrast_ratio(self.play_data['possession_team_color'], 
                                  self.play_data['defensive_team_color2'])
            self._def_tm_color = self.play_data['defensive_team_color'] if cr_1 > cr_2 \
                                 else self.play_data['defensive_team_color2']
        return self._def_tm_color

    @property
    def def_tm_edge_color(self):
        if self._def_tm_edge_color is None:
            cr_1 = contrast_ratio(self.play_data['possession_team_color'], 
                                  self.play_data['defensive_team_color'])
            cr_2 = contrast_ratio(self.play_data['possession_team_color'], 
                                  self.play_data['defensive_team_color2'])
            self._def_tm_edge_color =  self.play_data['defensive_team_color2'] if cr_1 > cr_2 \
                                       else self.play_data['defensive_team_color']
        return self._def_tm_edge_color
    
    def update_attributes(
        self,
        show_scoreboard: bool = None,
        clock_rolling: bool = None,
        player_display_type: str = None,
        show_player_legend: bool = None
    ) -> None:
        """Update the attributes of the class."""
        if show_scoreboard is not None:
            self.show_scoreboard = show_scoreboard
        if clock_rolling is not None:
            self.clock_rolling = clock_rolling
        if player_display_type is not None:
            self.player_display_type = player_display_type
        if show_player_legend is not None:
            self.show_player_legend = show_player_legend

    def plot_field(self):
        """Plot the NFL field layout with square aspect ratio."""
        # Hard limits for the x-axis (do not exceed the field width)
        if self.show_player_legend:
            self.ax.set_xlim(self.x_limit_min, self.x_limit_max + self.legend_width )
        else:
            self.ax.set_xlim(self.x_limit_min, self.x_limit_max)
        # Hard limits for the y-axis, updated dynamically later
        self.ax.set_ylim(self.y_limit_min, self.y_limit_min + self.y_delta)

        # Set y-axis ticks every 5 yards, excluding end zones
        yticks = [i for i in range(0, 121, 5) if i not in [5, 115]]
        self.ax.set_yticks(yticks)
        
        # Remove x-axis ticks
        self.ax.set_xticks([self.x_limit_min, self.x_limit_max])

        self.ax.grid(True, which='major', axis='y', color='white', linewidth=2)
        self.ax.grid(True, which='major', axis='x', color='white', linewidth=2)
        
        # Set background to light gray
        self.ax.set_facecolor('lightgray')
        
        # Remove plot spines (borders)
        for spine in self.ax.spines.values():
            spine.set_visible(False)

        # Set tick parameters and hide tick labels
        self.ax.tick_params(left=False, right=False, top=False, bottom=False, labelleft=False, labelbottom=False)

        # Draw line of scimmage
        self.ax.axhline(y=self.play_data['absolute_yardline_number'], color='blue', linewidth=2, zorder=self.zorder['los_and_fd'])

        # Draw first down line
        self.ax.axhline(y=self.play_data['absolute_yardline_number'] + self.play_data['yards_to_go'], color='yellow', linewidth=2, zorder=self.zorder['los_and_fd'])

        # Add yard markers
        for y in range(11, 110, 1):
            if y % 5 != 0:
                centerfield = self.x_limit_max / 2
                left_outer = Rectangle((1/2, y - 0.05), 2/3, 0.04, color='white')
                left_inner = Rectangle((centerfield - (37/12 + 1/3), y - 0.05), 2/3, 0.04, color='white')
                right_inner = Rectangle((centerfield + (37/12 - 1/3), y - 0.05), 2/3, 0.04, color='white')
                right_outer = Rectangle((self.x_limit_max - 7/6, y - 0.05), 2/3, 0.04, color='white')

            for hash_mark in [left_outer, left_inner, right_inner, right_outer]:
                self.ax.add_patch(hash_mark)

        # Add yardline numbers
        yardline_labels = {20: "1 0", 30: "2 0", 40: "3 0", 50: "4 0", 60: "5 0", 70: "4 0", 80: "3 0", 90: "2 0", 100: "1 0"}
        for y, label in yardline_labels.items():
            # Add yardline numbers on the left side
            self.ax.text(
                12, y, 
                label, 
                ha='center', va='center', 
                fontsize=30, 
                color='white', 
                rotation=-90, 
                fontproperties=self.numbers_font
            )
            # Add yardline numbers on the right side
            self.ax.text(
                self.x_limit_max - 12, y,
                label, 
                ha='center', va='center', 
                fontsize=30, 
                color='white', 
                rotation=90, 
                fontproperties=self.numbers_font
            )

            if y > 60:
                # plot arrows gonig up
                left_triangle = Polygon([[12, y + 1.8], [12.2, y + 2.55], [12.4, y + 1.8]], color='white')
                right_triangle = Polygon([[self.x_limit_max - 12, y + 1.8], [self.x_limit_max - 12.2, y + 2.55], [self.x_limit_max - 12.4, y + 1.8]], color='white')
                self.ax.add_patch(left_triangle)
                self.ax.add_patch(right_triangle)
            elif y < 60:
                # plot arrows going down
                left_triangle = Polygon([[12, y - 1.8], [12.2, y - 2.55], [12.4, y - 1.8]], color='white')
                right_triangle = Polygon([[self.x_limit_max - 12, y - 1.8], [self.x_limit_max - 12.2, y - 2.55], [self.x_limit_max - 12.4, y - 1.8]], color='white')
                self.ax.add_patch(left_triangle)
                self.ax.add_patch(right_triangle)

        # if y_limit_min + y_delta > 110, plot home_team_wordmark image from url in endzone
        if self.y_limit_min + self.y_delta > 110:
            # plot darker endzone
            endzone = Rectangle((0, 110), self.x_limit_max, 10, color='#b8b8b8')
            self.ax.add_patch(endzone)
            plot_image(self.ax, self.x_limit_max / 2, 115, self.home_wordmark, ord=self.zorder['endzones'])

        if self.y_limit_min < 10:
            # plot darker endzone
            endzone = Rectangle((0, 0), self.x_limit_max, 10, color='#b8b8b8')
            self.ax.add_patch(endzone)
            plot_image(self.ax, self.x_limit_max / 2, 5, self.home_wordmark_rotated, ord=self.zorder['endzones'])

    def plot_player_legend(self):
        y = self.y_limit_min + self.y_delta
        if self.show_scoreboard: y -= self.scoreboard_height
        rect_heading = Rectangle(
            (self.x_limit_max, y),
            self.legend_width ,
            .15,
            color=self.legend_txt_color,
            zorder=self.zorder['player_legend']
        )
        self.ax.add_patch(rect_heading)

        h = self.y_delta if self.show_scoreboard else self.y_delta + self.scoreboard_height
        rect_body = Rectangle(
            (self.x_limit_max, self.y_limit_min),
            self.legend_width ,
            h,
            color='#f0eee9',
            zorder=self.zorder['player_legend']
        )
        self.ax.add_patch(rect_body)

        self.ax.text(
            self.x_limit_max + (self.legend_width  / 2), y + 1.6,
            'Player Legend',
            ha='center', va='center',
            fontsize=20,
            fontweight='bold',
            color=self.legend_txt_color,
            zorder=self.zorder['player_legend_text'],
            fontdict={'family':'Arial'}
        )
        
        # loop through tracking data, plot {jersey_number}: {display_name} for each unique player
        if self.player_display_type == 'jerseys': 
            identifier = 'jersey_number'
        elif self.player_display_type == 'positions': 
            identifier = 'position'
        else:
            raise ValueError("Invalid player_display_type. Must be one of 'jerseys' or 'positions'" + 
                             " when show_player_legend is True.")
        players = self.tracking_data.query('club!="football"').groupby(['club', 'nfl_id', 'jersey_number', 'position', 'display_name']).size().reset_index()
        players = players.sort_values(['club', 'jersey_number']).reset_index(drop=True)
        current_team = None
        for i, player in players.iterrows():
            if player['club'] != current_team:
                current_team = player['club']
                self.ax.text(
                    self.x_limit_max + .5, y - 1 - 1.3 * i,
                    f'{current_team}',
                    ha='left', va='center',
                    fontsize=14,
                    fontweight='bold',
                    color=self.legend_txt_color,
                    zorder=self.zorder['player_legend_text'],
                    fontdict={'family':'Arial'}
                )
                y -= 1.3  # Add extra space between teams
            if identifier == 'jersey_number':
                msg = f'{int(player[identifier])}: {player.display_name} ({player.position})'
            else:
                msg = f'{player[identifier]}: {player.display_name}'
            self.ax.text(
                self.x_limit_max + 1.5, y - 1 - 1.3 * i,
                msg,
                ha='left', va='center',
                fontsize=12,
                fontweight='normal',
                color=self.legend_txt_color,
                zorder=self.zorder['player_legend_text'],
                fontdict={'family':'Arial'}
            )
    
    def update_frame(self, frame_id):
        """Update the plot for each frame."""
        self.ax.clear()

        # Plot the field
        self.plot_field()

        # Get data for the current frame
        frame_data = self.tracking_data[self.tracking_data['frame_id'] == frame_id]
        
        ball_y = None
        
        # Plot players and football
        if self.player_display_type in ['dots-positional', 'dots-team']:
            radius = 0.4
        else:
            radius = 0.7
        for club, group in frame_data.groupby('club'):
            if club == 'football':
                size = 140
                if self.player_display_type in ['dots-positional', 'dots-team']:
                    size = 80
                ball_y = group['y'].iloc[0]
                # Plot football as a regular circle
                ellipse = Ellipse((group['x'], group['y']), width=0.5, height=0.8, angle=0 , color='brown', ec='black', zorder=self.zorder['football'])
                self.ax.add_patch(ellipse)
                self.ax.scatter(group['x'], group['y'], color='white', marker='|', s=size / 3, zorder=self.zorder['football'])
            else:
                # Assign teams different colors
                if club == self.play_data['possession_team']:
                    color_hex = self.poss_tm_color
                    color = to_rgba(self.poss_tm_color)
                    path_color = 'grey'
                    ec = to_rgba(self.poss_tm_edge_color)
                    zord_players = self.zorder['offense']
                    zord_player_numbers = self.zorder['offense_numbers']
                else:
                    color_hex = self.def_tm_color
                    color = to_rgba(self.def_tm_color)
                    path_color = 'black'
                    ec = to_rgba(self.def_tm_edge_color)
                    zord_players = self.zorder['defense']
                    zord_player_numbers = self.zorder['defense_numbers']

                if frame_id >= self.snap_frame_id and self.show_trenches_paths:
                    positions = ['T','TE','G','C','ILB','MLB','LB','G','DE','DT','NT','OLB']
                    plays_before_current_frame = self.tracking_data.query('frame_id < @frame_id and position in @positions')
                    if plays_before_current_frame.query('club == @club').shape[0] != 0:
                        self.ax.scatter(
                            plays_before_current_frame.query('club == @club')['x'],
                            plays_before_current_frame.query('club == @club')['y'],
                            color=path_color,
                            s=5,
                            zorder=zord_players
                        )

                # Plot players as circles with a flat side and a front "half-square"
                for _, player in group.iterrows():
                    if self.player_display_type == 'dots-positional':
                        color = self.position_colors[player['position']]
                        if player['club'] == self.play_data['possession_team']:
                            ec = 'black'
                        else:
                            ec = 'blue'
                    
                    orientation = player['o']
                    x, y = player['x'], player['y']
                                            
                    # Create the Wedge for each player (flat side 180 degrees opposite orientation)
                    wedge = Wedge((x, y), radius, theta1=orientation+90, theta2=orientation-90, color=color, zorder=zord_players, ec=ec)

                    # Add the wedge to the axis
                    self.ax.add_patch(wedge)

                    # Calculate the half-square vertices
                    square_length = radius  # Length of the half-square extension in front of the flat side of the circle
                    angle_rad = np.radians(orientation)

                    # Calculate the direction vector for the front of the player (where the square will extend)
                    dx = square_length * np.cos(angle_rad)
                    dy = square_length * np.sin(angle_rad)

                    # Compute points along the flat edge of the circle (aligned with the player's orientation)
                    left_edge_x = x + radius * np.cos(angle_rad - np.pi/2)  # Left side of the flat edge
                    left_edge_y = y + radius * np.sin(angle_rad - np.pi/2)
                    right_edge_x = x + radius * np.cos(angle_rad + np.pi/2)  # Right side of the flat edge
                    right_edge_y = y + radius * np.sin(angle_rad + np.pi/2)

                    # Define the four corners of the square, extending from the flat side
                    # These corners are along the flat edge and then extend forward in the direction of the player's orientation
                    corners = [
                        (right_edge_x, right_edge_y),  # Right side of flat edge
                        (left_edge_x, left_edge_y),    # Left side of flat edge
                        (left_edge_x + dx, left_edge_y + dy),  # Front-left (extend forward)
                        (right_edge_x + dx, right_edge_y + dy)  # Front-right (extend forward)
                    ]

                    # Create the half-square polygon and add it to the axis
                    half_square = Polygon(corners, closed=True, color=color, zorder=zord_players, ec=ec)
                    self.ax.add_patch(half_square)

                    # add rectangular patch where circle and square meet
                    patch_radius = radius - 0.08
                    left_edge_x = x + patch_radius * np.cos(angle_rad - np.pi/2)  # Left side of the flat edge
                    left_edge_y = y + patch_radius * np.sin(angle_rad - np.pi/2)
                    right_edge_x = x + patch_radius * np.cos(angle_rad + np.pi/2)  # Right side of the flat edge
                    right_edge_y = y + patch_radius * np.sin(angle_rad + np.pi/2)
                    corners = [
                        (right_edge_x + .1 * dx, right_edge_y + .1 * dy),
                        (left_edge_x + .1 * dx, left_edge_y + .1 * dy),
                        (left_edge_x -.1 * dx, left_edge_y - .1 * dy),
                        (right_edge_x - .1 * dx, right_edge_y -.1 * dy)
                    ]
                    rect = Polygon(corners, closed=True, color=color, zorder=zord_players)
                    self.ax.add_patch(rect)

                    if self.plot_dir_arrows:
                        dir_radians = np.radians(player['dir'])
                        dx = 0.5 * np.cos(dir_radians)
                        dy = 0.5 * np.sin(dir_radians)
                        arrow = Polygon(
                            [[x + dx, y + dy], [x + 0.5 * dx - 0.25 * dy, y + 0.5 * dy + 0.25 * dx], [x + 0.5 * dx + 0.25 * dy, y + 0.5 * dy - 0.25 * dx]],
                            closed=True, color='black', zorder=zord_players
                        )
                        self.ax.add_patch(arrow)

                    # Plot the player's jersey number, centered at (x, y)
                    if self.player_display_type == 'jerseys':
                        jersey_number = int(player['jersey_number'])  # Convert float to int
                        self.ax.text(
                            x, y, 
                            str(jersey_number), 
                            color='white', 
                            ha='center', va='center', 
                            fontweight='bold', 
                            fontsize=12, 
                            zorder=zord_player_numbers
                        )
                    elif self.player_display_type in ['positions', 'dots-team']:
                        if self.player_display_type == 'positions':
                            fontsize = 9
                        else:
                            fontsize = 7
                        # calculate font color which maximizes contrast with player color
                        font_color = '#000000' if contrast_ratio(color_hex, '#000000') > contrast_ratio(color_hex, '#ffffff') else '#ffffff'
                        position = self.position_mapping.get(player['position'], player['position'])
                        self.ax.text(
                            x, y, 
                            position, 
                            color=font_color,
                            ha='center', 
                            va='center', 
                            fontweight='bold',
                            fontsize=fontsize,
                            zorder=zord_player_numbers
                        )
            
            # Dynamically adjust the y-axis limit based on the ball's y position
            if ball_y is not None:
                if ball_y < self.y_limit_min + 10:  # Ball near the bottom
                    self.y_limit_min = max(0, ball_y - 10)
                elif ball_y > self.y_limit_min + self.y_delta - 10:  # Ball near the top
                    self.y_limit_min = min(120 - self.y_delta, ball_y - self.y_delta + 10)
                self.ax.set_ylim(self.y_limit_min, self.y_limit_min + self.y_delta)

        if self.show_scoreboard: 
            self.scoreboard.plot_scoreboard(
                self.x_limit_max,
                self.y_limit_min,
                frame_id
            )

        if self.show_player_legend:
            self.plot_player_legend()

        return self.ax
    
    def init_animation(self) -> mpl.axes.Axes:
        """Initialize the animation to first frame of play."""
        
        self.plot_field()

        if self.show_scoreboard: 
            self.scoreboard = Scoreboard(
                self.ax, 
                self.play_data, 
                self.tracking_data['frame_id'].unique().tolist(),
                self.zorder,
                self.snap_frame_id, 
                self.touchdown_frame_id, 
                self.home_img, 
                self.away_img,
                self.clock_rolling,
                self.scoreboard_height
            )
            self.scoreboard.plot_scoreboard(
                self.x_limit_max,
                self.y_limit_min,
                frame_id=self.tracking_data.frame_id.min()
            )
        
        if self.show_player_legend: 
            self.plot_player_legend()

        return self.ax
    
    def _filter_data(self, game_id, play_id):
        # Filter tracking data for the specific game and play
        play = (self.df_tracking['game_id'] == game_id) & (self.df_tracking['play_id'] == play_id)
        self.tracking_data = self.df_tracking[play].copy()

        # Filter play data for the specific game and play
        play_cols = ['home_team_logo', 'away_team_logo', 'play_clock_at_snap', 'game_clock', 
             'absolute_yardline_number', 'yards_to_go', 'away_team_color', 
             'home_team_color', 'possession_team', 'defensive_team', 'down_and_dist', 
             'quarter_with_suffix', 'pre_snap_home_score', 'pre_snap_visitor_score',
             'possession_team_color', 'defensive_team_color', 'home_team_abbr', 'away_team_abbr',
             'home_team_wordmark', 'possession_team_color2', 'defensive_team_color2']
        cndtn = (self.df_play['game_id'] == game_id) & (self.df_play['play_id'] == play_id)
        self.play_data = self.df_play[cndtn][play_cols].to_dict(orient='records')[0]

    def _reset_flags_and_attributes(self):
        self._set_snap_frame_id = False
        self._set_touchdown_frame_id = False
        self._home_img = None
        self._away_img = None
        self._home_wordmark = None
        self._home_wordmark_rotated = None
        self._def_tm_color = None
        self._def_tm_edge_color = None
        self.poss_tm_color = self.play_data['possession_team_color']
        self.poss_tm_edge_color = self.play_data['possession_team_color2']

        # Set y min to be 10 yards behind the ball at snap
        ball_loc_at_snap = self.tracking_data[
            (self.tracking_data['club'] == 'football') & \
            (self.tracking_data['event'] == 'ball_snap')
        ]['y'].iloc[0]
        self.y_limit_min = round(ball_loc_at_snap - 10, 2)

        if self.show_scoreboard:
            self.y_limit_min -= self.scoreboard_height

    def animate_play(
        self, 
        game_id, 
        play_id, 
        output='console', 
        filepath=None,
        fps=10
    ) -> None:
        """Create the animation of the play.
        
        Args:
            game_id: The game id.
            play_id: The play id.
            output: The output of the animation. Options are 'console' or 'file'. Defaults to 'console'.
            filepath: The filepath to save the animation if output is 'file'. Defaults to None.
            fps: The frames per second of the animation. Defaults to 10.
        """

        if output == 'file' and filepath is None: 
            raise ValueError("If output is 'file', a filepath must be provided.")

        self._filter_data(game_id, play_id)

        self._reset_flags_and_attributes()

        # Create a new figure
        if self.show_player_legend:
            self.fig, self.ax = plt.subplots(figsize=(14, 8))
        else:
            self.fig, self.ax = plt.subplots(figsize=(12, 8))

        frame_ids = self.tracking_data['frame_id'].unique()

        ani = animation.FuncAnimation(
            self.fig, 
            self.update_frame,
            frames=frame_ids, 
            init_func=self.init_animation, 
            blit=False, 
            repeat=False
        )

        # Fit the plot to the figure
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        plt.close(self.fig)

        if output == 'console':
            return HTML(ani.to_jshtml(fps=fps))
        elif output == 'file':
            ani.save(filepath, writer='ffmpeg', fps=fps)
            return None