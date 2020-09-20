import tkinter as tk
from tkinter import messagebox, filedialog
import os, random, pygame

try:
    from PIL import ImageTk, Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from companion import AbstractCompanion
from modules.matrix import RADIAL_DELTAS
from view import GridView, ObjectivesView
from game import DotGame, ObjectiveManager, CompanionGame
from dot import BasicDot, AbstractKindlessDot
from util import create_animation, ImageManager

__date__ = "24/10/2017"

def load_image_pil(image_id, size, prefix, suffix='.png'):
    """Returns a tkinter photo image

    Parameters:
        image_id (str): The filename identifier of the image
        size (tuple<int, int>): The size of the image to load
        prefix (str): The prefix to prepend to the filepath (i.e. root directory
        suffix (str): The suffix to append to the filepath (i.e. file extension)
    """
    width, height = size
    file_path = os.path.join(prefix, f"{width}x{height}", image_id + suffix)
    return ImageTk.PhotoImage(Image.open(file_path))


def load_image_tk(image_id, size, prefix, suffix='.gif'):
    """Returns a tkinter photo image

    Parameters:
        image_id (str): The filename identifier of the image
        size (tuple<int, int>): The size of the image to load
        prefix (str): The prefix to prepend to the filepath (i.e. root directory
        suffix (str): The suffix to append to the filepath (i.e. file extension)
    """
    width, height = size
    file_path = os.path.join(prefix, f"{width}x{height}", image_id + suffix)
    return tk.PhotoImage(file=file_path)


# This allows you to simply load png images with PIL if you have it,
# otherwise will default to gifs through tkinter directly
load_image = load_image_pil if HAS_PIL else load_image_tk  # pylint: disable=invalid-name

DEFAULT_ANIMATION_DELAY = 0  # (ms)
ANIMATION_DELAYS = {
    # step_name => delay (ms)
    'ACTIVATE_ALL': 50,
    'ACTIVATE': 100,
    'ANIMATION_BEGIN': 300,
    'ANIMATION_DONE': 0,
    'ANIMATION_STEP': 200
}
BAR_WIDTH = 60
BAR_HIGHT = 20


class InfoPanel(tk.Frame):
    """Displays information to the user."""

    def __init__(self, master):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget
        """
        super().__init__(master)
        self._moves = tk.Label(self, text='20', font="Verdana 25")
        self._moves.pack(side=tk.LEFT, anchor=tk.NW)

        frame = tk.Frame(self)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self._score = tk.Label(frame, text='0', font="Verdana 25", fg='grey')
        self._score.pack(side=tk.LEFT, anchor=tk.E, expand=1)

        self._img = tk.PhotoImage(file='images/companions/eskimo.png')
        self._companion = tk.Label(frame, image=self._img)
        self._companion.pack(anchor=tk.CENTER, expand=1)

        self._interval_bar = tk.Canvas(frame, height=25)
        self._interval_bar.pack(side=tk.BOTTOM)
        self.reset_bar()

        self._image_manager = ImageManager('images/dots/', loader=load_image)
        self._objectives = ObjectivesView(self, image_manager=self._image_manager)
        self._objectives.pack(side=tk.RIGHT, anchor=tk.E, expand=1)

    def set_moves(self, moves):
        """Sets the remaining moves

        Parameters:
            moves (int): the remaining moves
        """
        self._moves.config(text='{}'.format(moves))

    def set_score(self, score):
        """Sets the score

        Parameters:
            score (int): the score that the user gains
        """
        self._score.config(text='{}'.format(score))

    def set_objectives(self, objectives):
        """Updates the objectives

        Parameters:
           objectives (list<tuple<AbstractDot, int>>):
                    List of (objective, remaining) pairs
        """
        self._objectives.draw(objectives)

    def set_companion(self, img):
        """Sets the companion image

        Parameter:
           img (tk.PhotoImage): The companion image
        """
        self._img = img
        self._companion.config(image=self._img)

    def set_bar(self, step):
        """Sets the interval bar
           When the game is with a companion, the bar shows the times of charging the companion
           When the game is without a companion, the bar shows the user's moves

        Parameter:
           step (int): The progress that the bar reaches
        """
        self._interval_bar.create_rectangle(10+step*BAR_WIDTH, 5,
                                            10+(step+1)*BAR_WIDTH, 5+BAR_HIGHT, fill='SkyBlue')

    def reset_bar(self):
        """Resets the interval bar"""
        self._interval_bar.delete("all")
        for i in range(6):
            self._interval_bar.create_rectangle(10+i*BAR_WIDTH, 5,
                                                10+(i+1)*BAR_WIDTH, 5+BAR_HIGHT)


class CompanionDot(BasicDot):
    """A dot that can be activated to charge the companion"""
    DOT_NAME = "companion"

    def activate(self, position, game, activated, has_loop=False):
        game.companion.charge()


class SwirlDot(BasicDot):
    """A special dot that changes the kind of adjacent dots to its kind when activated"""
    DOT_NAME = "swirl"

    def activate(self, position, game, activated, has_loop=False):
        self._expired = True
        kind = self.get_kind()
        dots = list(game.grid.get_adjacent_cells(position, deltas=RADIAL_DELTAS))
        for i in dots:
            if game.grid[i].is_open():
                if game.grid[i].get_dot().get_name() == 'basic':
                    game.grid[i].set_dot(BasicDot(kind))
                elif game.grid[i].get_dot().get_name() == 'swirl':
                    game.grid[i].set_dot(SwirlDot(kind))
                elif game.grid[i].get_dot().get_name() == 'companion':
                    game.grid[i].set_dot(CompanionDot(kind))


class EskimoCompanion(AbstractCompanion):
    """A companion that randomly places a few swirl dots on the grid"""
    NAME = 'Eskimo'

    def activate(self, game):
        rows, columns = game.grid._dim
        number = random.randint(3, 7)
        for i in range(number):
            position = random.randrange(rows), random.randrange(columns)
            while not game.grid[position].is_open() or game.grid[position].get_dot().get_name() != 'basic':
                position = random.randrange(rows), random.randrange(columns)
            kind = game.grid[position].get_dot().get_kind()
            game.grid[position].set_dot(SwirlDot(kind))

            
class TurtleDot(AbstractKindlessDot):
    """A special dot that randomly swaps with an adjacent dot.
    When an adjacent dot is connected the turtle hides in its shell and does not move.
    If another adjacent dot is connected it be activated.
    """
    DOT_NAME = "Turtle"
    state = "turtle"
    times = 0

    def activate(self, position, game, activated, has_loop=False):
        self._expired = True

    def get_view_id(self):
        return "{0}/{1}".format(self.DOT_NAME, self.state)

    def after_resolved(self, position, game):
        if self.state == "turtle":
            dots = list(game.grid.get_adjacent_cells(position, deltas=RADIAL_DELTAS))
            destination = random.choice(dots)
            while not game.grid[destination].is_open():
                destination = random.choice(dots)
            game.grid[position].swap_with(game.grid[destination])

    def adjacent_activated(self, position, game, activated, activated_neighbours, has_loop=False):
        self.state = 'shell'
        self.times += 1
        if self.times == 2:
           return [position]


class DotsApp(object):
    """Top level GUI class for simple Dots & Co game"""

    def __init__(self, master):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget
        """
        pygame.init()
        self._master = master
        master.title('Dots')
        self._playing = True
        self._over = None
        self._player = 'None'
        self._scores = {}
        self._steps = 0
        self._image_manager = ImageManager('images/dots/', loader=load_image)

        # InfoPanel
        self._info = InfoPanel(master)
        self._info.pack(fill=tk.BOTH, expand=1)

        # Login
        top = tk.Toplevel()
        top.title('Login')
        tk.Label(top, text='Welcome to the Dots & Co game!').pack()
        frame = tk.Frame(top)
        frame.pack(side=tk.BOTTOM)
        tk.Label(frame, text="Name: ").pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=20)
        entry.pack(side=tk.LEFT)
        def record(*args):
            self._player = entry.get()
            if self.read_score()==None:
               self.save_score()
            top.destroy()
        tk.Button(frame, text="Start!", command=record).pack(side=tk.RIGHT)
        top.bind('<Return>', record)

        # Menu
        menubar = tk.Menu(master)
        master.config(menu=menubar)
        filemenu = tk.Menu(menubar)
        menubar.add_cascade(label='File', menu=filemenu)
        newgame = tk.Menu(menubar)
        filemenu.add_cascade(label='New Game', menu=newgame)
        newgame.add_command(label='With a Companion', command=self.with_companion)
        newgame.add_command(label='Without a Companion', command=self.without_companion)
        filemenu.add_command(label='Exit', command=self.exit)
        master.protocol("WM_DELETE_WINDOW", self.exit)

        # Game            
        counts = [10, 15, 25, 25]
        random.shuffle(counts)
        # randomly pair counts with each kind of dot
        objectives = zip([BasicDot(1), BasicDot(2), BasicDot(4), BasicDot(3)], counts)
        
        self._objectives = ObjectiveManager(list(objectives))
        self._info.set_objectives(list(objectives))

        self._dead_cells = {(2, 2), (2, 3), (2, 4),
                            (3, 2), (3, 3), (3, 4),
                            (4, 2), (4, 3), (4, 4),
                            (0, 7), (1, 7), (6, 7), (7, 7)}
        self._companion = EskimoCompanion()
        self._game = CompanionGame({TurtleDot: 1, CompanionDot: 4, BasicDot: 11},
                                   objectives=self._objectives,
                                   companion=self._companion,
                                   kinds=(1, 2, 3, 4), size=(8, 8),
                                   dead_cells=self._dead_cells)

        # Grid View
        self._grid_view = GridView(self._master, size=self._game.grid.size(),
                                   image_manager=self._image_manager)
        self._grid_view.pack()
        self._grid_view.draw(self._game.grid)
        self.draw_grid_borders()

        # Events
        self.bind_events()

        # Set initial score again to trigger view update automatically
        self._refresh_status()

        self.read_score()
        # mixer not working under Ubuntu
        # pygame.mixer.Sound('Sounds/start.wav').play()

    def draw_grid_borders(self):
        """Draws borders around the game grid"""

        borders = list(self._game.grid.get_borders())

        # this is a hack that won't work well for multiple separate clusters
        outside = max(borders, key=lambda border: len(set(border)))

        for border in borders:
            self._grid_view.draw_border(border, fill=border != outside)

    def bind_events(self):
        """Binds relevant events"""
        self._grid_view.on('start_connection', self._drag)
        self._grid_view.on('move_connection', self._drag)
        self._grid_view.on('end_connection', self._drop)

        self._game.on('reset', self._refresh_status)
        self._game.on('complete', self._drop_complete)

        self._game.on('connect', self._connect)
        self._game.on('undo', self._undo)

    def _animation_step(self, step_name):
        """Runs for each step of an animation

        Parameters:
            step_name (str): The name (type) of the step
        """
        self._refresh_status()
        self.draw_grid()

    def animate(self, steps, callback=lambda: None):
        """Animates some steps (i.e. from selecting some dots, activating companion, etc.
        
        Parameters:
            steps (generator): Generator which yields step_name (str) for each step in the animation
        """
        if steps is None:
            steps = (None for _ in range(1))

        animation = create_animation(self._master, steps,
                                     delays=ANIMATION_DELAYS, delay=DEFAULT_ANIMATION_DELAY,
                                     step=self._animation_step, callback=callback)
        animation()

    def _drop(self, position):  # pylint: disable=unused-argument
        """Handles the dropping of the dragged connection

        Parameters:
            position (tuple<int, int>): The position where the connection was
                                        dropped
        """
        if not self._playing:
            return

        if self._game.is_resolving():
            return

        self._grid_view.clear_dragged_connections()
        self._grid_view.clear_connections()

        self.animate(self._game.drop())

        # drop_sound = pygame.mixer.Sound('Sounds/drop.wav')
        # drop_sound.play()

    def _connect(self, start, end):
        """Draws a connection from the start point to the end point

        Parameters:
            start (tuple<int, int>): The position of the starting dot
            end (tuple<int, int>): The position of the ending dot
        """
        if self._game.is_resolving():
            return
        if not self._playing:
            return
        self._grid_view.draw_connection(start, end,
                                        self._game.grid[start].get_dot().get_kind())

    def _undo(self, positions):
        """Removes all the given dot connections from the grid view

        Parameters:
            positions (list<tuple<int, int>>): The dot connects to remove
        """
        for _ in positions:
            self._grid_view.undo_connection()

    def _drag(self, position):
        """Attempts to connect to the given position, otherwise draws a dragged
        line from the start

        Parameters:
            position (tuple<int, int>): The position to drag to
        """
        if self._game.is_resolving():
            return
        if not self._playing:
            return

        tile_position = self._grid_view.xy_to_rc(position)

        if tile_position is not None:
            cell = self._game.grid[tile_position]
            dot = cell.get_dot()

            if dot and self._game.connect(tile_position):
                self._grid_view.clear_dragged_connections()
                return

        kind = self._game.get_connection_kind()

        if not len(self._game.get_connection_path()):
            return

        start = self._game.get_connection_path()[-1]

        if start:
            self._grid_view.draw_dragged_connection(start, position, kind)

    def draw_grid(self):
        """Draws the grid"""
        self._grid_view.draw(self._game.grid)

    def with_companion(self):
        """Sets the companion for the new game with a companion and resets"""
        self._companion = EskimoCompanion()
        self.reset()

    def without_companion(self):
        """Cancels the companion for the new game witout a companion and resets"""
        self._companion = None
        self.reset()

    def reset(self):
        """Resets the game"""
        self._playing = True
        self._steps = 0
        self._game.reset()
        self._objectives.reset()
        self._refresh_status()
        self._info.reset_bar()
        # start_sound = pygame.mixer.Sound('Sounds/start.wav')
        # start_sound.play()
        if self._over is not None:
            self._info.after_cancel(self._animation)

        if self._companion:
            img = tk.PhotoImage(file='images/companions/eskimo.png')
            self._info.set_companion(img)
            self._game = CompanionGame({TurtleDot: 1, CompanionDot: 4, BasicDot: 11},
                                       objectives=self._objectives,
                                       companion=self._companion,
                                       kinds=(1, 2, 3, 4), size=(8, 8),
                                       dead_cells=self._dead_cells)
        if not self._companion:
            img = tk.PhotoImage(file='images/companions/useless.gif')
            self._info.set_companion(img)
            self._game = DotGame({BasicDot: 1}, objectives=self._objectives,
                                 kinds=(1, 2, 3, 4), size=(8, 8),
                                 dead_cells=self._dead_cells)
            self._info.set_bar(0)

        self._grid_view.draw(self._game.grid)
        self.bind_events()

    def exit(self):
        """Checks if the user wants to exit and closes the application if so"""
        reply = messagebox.askokcancel('Verify exit', 'Really quit?')
        if reply:
            self._master.destroy()

    def change_win(self):
        """Shows an animation when the user wins"""
        self._over = not self._over
        if self._over:
            img = tk.PhotoImage(file='images/win1.gif')
            self._info.set_companion(img)
        else:
            img = tk.PhotoImage(file='images/win2.gif')
            self._info.set_companion(img)
        self._animation = self._info.after(800, self.change_win)

    def change_lose(self):
        """Shows an animation when the user loses"""
        self._over = not self._over
        if self._over:
            img = tk.PhotoImage(file='images/gameover1.png')
            self._info.set_companion(img)
        else:
            img = tk.PhotoImage(file='images/gameover2.png')
            self._info.set_companion(img)
        self._animation = self._info.after(800, self.change_lose)

    def check_game_over(self):
        """Checks whether the game is over and shows an appropriate message box if so"""
        state = self._game.get_game_state()

        if state == self._game.GameState.WON:
            # Shows the animation and plays sound effects
            self._over = True
            self.change_win()
            # pygame.mixer.Sound('Sounds/success.wav').play()
            # Saves the best score
            if self._player == 'None':
                self.save_score()
            elif self._game.get_score() > self.read_score():
                self.save_score()
            # Shows the user's highest ranking and the top 3 players
            ranking = sorted(self._scores, key=self._scores.__getitem__, reverse=True)
            position = ranking.index(self._player) + 1
            top = ''
            for name in ranking[:3]:
                top += "{0}--{1}   ".format(name, self._scores.get(name))
            messagebox.showinfo("Game Over!",
                                "You won!!!\nYour best socre: {0}. Your highest ranking: {1}.\n Top 3: "
                                .format(self.read_score(), position) + top)
            self._playing = False

        elif state == self._game.GameState.LOST:
            self._over = True
            self.change_lose()
            # pygame.mixer.Sound('Sounds/lose.wav').play()
            messagebox.showinfo("Game Over!",
                                f"You didn't reach the objective(s) in time. You connected {self._game.get_score()} points")
            self._playing = False

    def read_score(self):
        """(int) Returns the user's former best score.
        Returns None if the user plays the game for the first time

        Precondition:
            The user's name does not consist ','
        """
        f = open('score.txt', 'r')
        lines = f.readlines()
        for l in lines:
            if l:
                s = l.split(',')
                self._scores[s[0]] = int(s[1])
        score = self._scores.get(self._player)
        f.close
        return score

    def save_score(self):
        """Saves the user's score"""
        self._scores[self._player] = self._game.get_score()
        result = ''
        for n in self._scores:
            line = str(n) + "," + str(self._scores[n]) + "\n"
            result += line
        f = open('score.txt', 'w')
        f.write(result)
        f.close

    def _drop_complete(self):
        """Handles the end of a drop animation"""
        if not self._companion:
            self._steps += 1
            step = self._steps % 6
            if step == 0:
                self._info.reset_bar()
            self._info.set_bar(step)

        if self._companion:
            charge = self._game.companion.get_charge()
            for i in range(charge):
                self._info.set_bar(i)
            if self._game.companion.is_fully_charged():
                # pygame.mixer.Sound('Sounds/companion.wav').play()
                steps = self._game.companion.activate(self._game)
                self._grid_view.draw(self._game.grid)
                self._game.companion.reset()
                self._info.reset_bar()
                self.check_game_over()
                return self.animate(steps)

        self._grid_view.draw(self._game.grid)
        self.check_game_over()

    def _refresh_status(self):
        """Handles change in objectives, remaining moves, and score."""
        status = self._objectives.get_status()
        self._info.set_objectives(status)

        moves = self._game.get_moves()
        self._info.set_moves(moves)

        score = self._game.get_score()
        self._info.set_score(score)


def main():
    """Sets-up the GUI for Dots & Co"""
    root = tk.Tk()
    app = DotsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
