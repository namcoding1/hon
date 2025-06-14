import curses
import random
import time

# Tetromino shapes
TETROMINOES = [
    [[1, 1, 1, 1]],                         # I
    [[1, 1], [1, 1]],                        # O
    [[0, 1, 0], [1, 1, 1]],                  # T
    [[1, 0, 0], [1, 1, 1]],                  # J
    [[0, 0, 1], [1, 1, 1]],                  # L
    [[1, 1, 0], [0, 1, 1]],                  # S
    [[0, 1, 1], [1, 1, 0]]                   # Z
]

WIDTH = 10
HEIGHT = 20

class Tetris:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.board = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.score = 0
        self.level = 1
        self.tetromino = None
        self.next_tetromino = self.new_tetromino()
        self.spawn_new()

    def new_tetromino(self):
        shape = random.choice(TETROMINOES)
        tetro = [row[:] for row in shape]
        return tetro

    def spawn_new(self):
        self.tetromino = self.next_tetromino
        self.next_tetromino = self.new_tetromino()
        self.tetro_x = WIDTH // 2 - len(self.tetromino[0]) // 2
        self.tetro_y = 0
        if self.check_collision(self.tetro_x, self.tetro_y, self.tetromino):
            self.game_over()

    def rotate(self, tetro):
        return [list(row)[::-1] for row in zip(*tetro)]

    def check_collision(self, x, y, tetro):
        for i, row in enumerate(tetro):
            for j, cell in enumerate(row):
                if cell:
                    if (j + x < 0 or j + x >= WIDTH or i + y >= HEIGHT or self.board[i + y][j + x]):
                        return True
        return False

    def merge(self):
        for i, row in enumerate(self.tetromino):
            for j, cell in enumerate(row):
                if cell:
                    self.board[self.tetro_y + i][self.tetro_x + j] = cell
        self.clear_lines()
        self.spawn_new()

    def clear_lines(self):
        cleared = 0
        new_board = [row for row in self.board if any(cell == 0 for cell in row)]
        cleared = HEIGHT - len(new_board)
        while len(new_board) < HEIGHT:
            new_board.insert(0, [0] * WIDTH)
        self.board = new_board
        self.score += cleared ** 2

    def game_over(self):
        self.stdscr.addstr(HEIGHT // 2, WIDTH // 2 - 4, 'Game Over')
        self.stdscr.refresh()
        time.sleep(2)
        curses.endwin()
        quit()

    def draw_board(self):
        self.stdscr.clear()
        for y, row in enumerate(self.board):
            for x, cell in enumerate(row):
                if cell:
                    self.stdscr.addstr(y, x*2, '[]')
                else:
                    self.stdscr.addstr(y, x*2, '  ')
        for i, row in enumerate(self.tetromino):
            for j, cell in enumerate(row):
                if cell and self.tetro_y + i >= 0:
                    self.stdscr.addstr(self.tetro_y + i, (self.tetro_x + j)*2, '[]')
        self.stdscr.addstr(0, WIDTH*2 + 2, f'Score: {self.score}')
        self.stdscr.refresh()

    def move(self, dx, dy):
        if not self.check_collision(self.tetro_x + dx, self.tetro_y + dy, self.tetromino):
            self.tetro_x += dx
            self.tetro_y += dy
            return True
        return False

    def drop(self):
        if not self.move(0, 1):
            self.merge()

    def rotate_tetromino(self):
        rotated = self.rotate(self.tetromino)
        if not self.check_collision(self.tetro_x, self.tetro_y, rotated):
            self.tetromino = rotated

    def run(self):
        self.stdscr.nodelay(True)
        last_move = time.time()
        while True:
            self.draw_board()
            c = self.stdscr.getch()
            if c == curses.KEY_LEFT:
                self.move(-1, 0)
            elif c == curses.KEY_RIGHT:
                self.move(1, 0)
            elif c == curses.KEY_DOWN:
                self.drop()
            elif c == curses.KEY_UP:
                self.rotate_tetromino()
            elif c == ord('q'):
                break
            if time.time() - last_move > max(0.1, 1 - self.level*0.1):
                self.drop()
                last_move = time.time()
        curses.endwin()


def main(stdscr):
    curses.curs_set(0)
    tetris = Tetris(stdscr)
    tetris.run()

if __name__ == '__main__':
    curses.wrapper(main)
