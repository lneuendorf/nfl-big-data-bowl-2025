import matplotlib as mpl
from matplotlib.patches import Rectangle
from utils.image_functions import plot_image

class Scoreboard:
    def __init__(
            self, 
            ax: mpl.axes.Axes,
            play_data: dict,
            frame_ids: list,
            zorder: dict,
            snap_frame_id: int,
            touchdown_frameid: int | None,
            home_img: str,
            away_img: str,
            clock_rolling: bool = True,
            scoreboard_height: int = 3
        ) -> None:
        
        self.ax = ax
        self.play_data = play_data
        self.frame_ids = frame_ids
        self.zorder = zorder
        self.snap_frame_id = snap_frame_id
        self.touchdown_frameid = touchdown_frameid
        self.home_img = home_img
        self.away_img = away_img
        self.clock_rolling = clock_rolling
        self.scoreboard_height = scoreboard_height
        self._play_clocks = {}
        self._game_clocks = {}

    @property
    def play_clocks(self) -> dict:
        if self._play_clocks == {}:
            for fid in self.frame_ids:
                if fid <= self.snap_frame_id:
                    self._play_clocks[fid] = int(self.play_data['play_clock_at_snap'] + \
                                                 (self.snap_frame_id - fid) / 10 - .1)
                else:
                    self._play_clocks[fid] = 40
        return self._play_clocks

    @property
    def game_clocks(self) -> dict:
        if self._game_clocks == {}:
            game_clock_min = int(self.play_data['game_clock'].split(':')[0])
            game_clock_sec = int(self.play_data['game_clock'].split(':')[1])
            if self.clock_rolling:
                game_clock_sec = game_clock_sec + ((self.snap_frame_id % 10) / 10) + (self.snap_frame_id // 10)
                if game_clock_sec >= 60:
                    game_clock_min += game_clock_sec // 60
                    game_clock_sec = game_clock_sec % 60
            for fid in self.frame_ids:
                if fid < self.snap_frame_id:
                    if self.clock_rolling:
                        if game_clock_sec < 0:
                            if game_clock_min == 0:
                                game_clock_sec = 0
                                game_clock_min = 0
                            else:
                                game_clock_min -= 1
                                game_clock_sec = 59.9
                        else:
                            game_clock_sec -= 0.1
                        self._game_clocks[fid] = f'{int(game_clock_min):02}:{int(game_clock_sec):02}'
                    else:
                        self._game_clocks[fid] = self.play_data['game_clock']
                else:
                    if game_clock_sec < 0:
                        if game_clock_min == 0:
                            game_clock_sec = 0
                            game_clock_min = 0
                        else:
                            game_clock_min -= 1
                            game_clock_sec = 59.9
                    else:
                        game_clock_sec -= 0.1
                    self._game_clocks[fid] = f'{int(game_clock_min):02}:{int(game_clock_sec):02}'
        return self._game_clocks

    def update_scores(
            self, 
            frame_id: int,
            y_limit_min: int
        ) -> None:

        if self.touchdown_frameid and frame_id and frame_id > self.touchdown_frameid:
            if y_limit_min < 10:
                if self.play_data['possession_team'] == self.play_data['home_team_abbr']:
                    self.play_data['pre_snap_visitor_score'] += 6
                else:
                    self.play_data['pre_snap_home_score'] += 6
            else:
                if self.play_data['possession_team'] == self.play_data['home_team_abbr']:
                    self.play_data['pre_snap_home_score'] += 6
                else:
                    self.play_data['pre_snap_visitor_score'] += 6
            self.touchdown_frameid = None

    def draw_rectangle(
            self, 
            x_start: int,
            width: int,
            y_limit_min: int,
            facecolor: str,
        ) -> None:
        
        rect = Rectangle(
            (x_start, y_limit_min),
            width,
            self.scoreboard_height,
            facecolor=facecolor,
            edgecolor='black',
            linewidth=3,
            zorder=self.zorder['scoreboard_background']
        )
        self.ax.add_patch(rect)

    def add_text(
            self, 
            x_position: int,
            y_limit_min: int,
            text: str,
            fontsize: int = 20,
            color: str = 'white'
        ) -> None:
        
        txt_height = y_limit_min + self.scoreboard_height / 2
        self.ax.text(
            x_position,
            txt_height,
            text,
            ha='center', va='center',
            fontsize=fontsize,
            fontweight='bold',
            color=color,
            zorder=self.zorder['scoreboard_foreground']
        )

    def plot_scoreboard(
            self, 
            x_limit_max: int,
            y_limit_min: int,
            frame_id: int,
        ) -> None:
        
        x_interval = x_limit_max / 4

        self.update_scores(frame_id, y_limit_min)

        # Draw background rectangles for scoreboard sections
        self.draw_rectangle(0, x_interval, y_limit_min, self.play_data['away_team_color'])
        self.draw_rectangle(x_interval, x_interval * 2, y_limit_min, self.play_data['home_team_color'])
        self.draw_rectangle(x_interval * 2, x_interval, y_limit_min, '#1a1817')

        play_clock_color = 'red' if self.play_clocks[frame_id] <= 5 else 'grey'
        self.draw_rectangle(x_interval * 3 - 4, x_interval * 3, y_limit_min, play_clock_color)
        self.draw_rectangle(x_interval * 3, x_limit_max, y_limit_min, self.play_data['possession_team_color'])

        # Add text for away team score, home team score, time, play clock, and down and distance
        self.add_text(
            x_interval / 2 + 2.5, 
            y_limit_min, 
            f'{self.play_data["away_team_abbr"]} {self.play_data["pre_snap_visitor_score"]}'
        )
        self.add_text(
            x_interval * 1.5 + 2.5, 
            y_limit_min, 
            f'{self.play_data["home_team_abbr"]} {self.play_data["pre_snap_home_score"]}', 
        )
        self.add_text(
            x_interval * 2 + (x_interval / 2 - 2), 
            y_limit_min, 
            f'{self.play_data["quarter_with_suffix"]} {self.game_clocks[frame_id]}'
        )
        self.add_text(
            x_interval * 3 - 2, 
            y_limit_min, 
            f'{self.play_clocks[frame_id]:02}'
        )
        self.add_text(
            x_interval * 3.5, 
            y_limit_min, 
            self.play_data['down_and_dist']
        )

        # Add logos next to scores
        plot_image(
            ax = self.ax, 
            x = 5.5, 
            y = y_limit_min + self.scoreboard_height / 2,
            imagebox = self.away_img, 
            ord = self.zorder['scoreboard_foreground'],
            alignment = 'right-center',
        )

        plot_image(
            ax = self.ax, 
            x = x_interval + 5.5, 
            y = y_limit_min + self.scoreboard_height / 2, 
            imagebox = self.home_img, 
            ord = self.zorder['scoreboard_foreground'],
            alignment = 'right-center',
        )