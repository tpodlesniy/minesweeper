import sys

import pygame
from random import randint


class MCell:
    CLOSED = 0
    FLAGGED = 1
    QUESTIONED = 2
    MARK_STATES = ['X', '!', '?', ]

    def __init__(self, is_opened=False, is_mined=False, state=None):
        self.state = state if state else MCell.CLOSED
        self.is_mined = is_mined
        self.is_opened = is_opened

    def next_state(self):
        self.state = (self.state + 1) % len(MCell.MARK_STATES)
        return self.state

    def open(self):
        if self.state != MCell.FLAGGED:
            self.is_opened = True
            return int(self.is_mined)
        return -1

    def __show_value(self, show_mine=False):
        if show_mine and self.is_mined:
            return 'M'
        return MCell.MARK_STATES[self.state]

    def __repr__(self):
        return str(self)

    def __str__(self):
        return self.__show_value(True)


class MField:  # model

    def __init__(self, rows, cols, mines_count):
        self.rows = rows
        self.cols = cols
        self.mines_count = mines_count
        self.data = MField.create_field(cols, rows)
        self.set_mines(mines_count)

    @staticmethod
    def create_field(cols, rows):
        field = [None] * rows
        for i in range(len(field)):
            field[i] = [MCell() for j in range(cols)]
        return field

    def get_cell_or_none(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.data[row][col]
        else:
            return None

    def get_random_cell(self):
        row = randint(0, self.rows - 1)
        col = randint(0, self.cols - 1)
        return self.get_cell_or_none(row, col)

    def set_mines(self, count):
        for i in range(count):
            cell = self.get_random_cell()
            while cell.is_mined:
                cell = self.get_random_cell()
            cell.is_mined = True

    def get_neighbors_mine_count(self, row, col):
        result = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                cell = self.get_cell_or_none(row + i, col + j)
                if cell and cell.is_mined and not (i == 0 and j == 0):
                    result += 1
        return result

    def update_cell_state(self, row, col):
        return self.data[row][col].next_state()

    def open_cell(self, row, col):
        return self.data[row][col].open()

    def get_selected_mine_count(self):
        count = 0
        for row in self.data:
            for item in row:
                if item.state == MCell.FLAGGED:
                    count += 1
        return count

    def get_cells_elapsed(self):
        count = 0
        for row in self.data:
            for item in row:
                if item.state == MCell.CLOSED and item.is_opened == False:
                    count += 1
        return count

    def open_near_cells(self, row, col):
        for i_row in range(row - 1, row + 2):
            for i_col in range(col - 1, col + 2):
                if not (i_row == row and i_col == col) and 0 <= i_row < self.rows and 0 <= i_col < self.cols:
                    if not self.data[i_row][i_col].is_opened and not self.data[i_row][i_col].is_mined:
                        self.open_cell(i_row, i_col)
                        self.open_near_cells(i_row, i_col)


class MGame:  # controller
    def __init__(self, field):
        self.field = field
        self.rows = self.field.rows
        self.cols = self.field.cols
        self.mines = self.field.mines_count
        self.mines_initial = self.field.mines_count
        self.gameover = False
        self.gamewin = False

    def update_cell_state(self, row, col):
        result = self.field.update_cell_state(row, col)
        if result == MCell.FLAGGED and self.field.data[row][col].is_mined:
            self.mines -= 1
        elif result == MCell.QUESTIONED and self.field.data[row][col].is_mined:
            self.mines += 1
        self.check_gameover()

    def check_gameover(self):
        cells_elapsed = self.field.get_cells_elapsed()
        if cells_elapsed == 0 and self.mines == 0:
            self.gameover = True
            self.gamewin = True

    def open_cell(self, row, col):
        result = self.field.open_cell(row, col)
        if self.field.get_neighbors_mine_count(row, col) == 0:
            self.field.open_near_cells(row, col)
        if result == 1:
            self.gameover = True
            self.gamewin = False
        self.check_gameover()


class MPGViewCell:
    CELL_SIDE = 40
    COLOR_BORDER = (0, 0, 0)
    COLOR_CLOSED = (80, 80, 80)
    COLOR_MINED = (200, 0, 0)
    COLOR_OPENED = (255, 255, 255)
    COLOR_QUESTIONED = (0, 0, 255)
    COLOR_FLAGGED = (0, 255, 0)

    def __init__(self, screen):
        self.screen = screen
        self.cell_font = pygame.font.SysFont('Comic Sans MS', 20, True)

    def draw(self, cell, row, col, show_mines, m_count):
        base_x = MPGViewCell.CELL_SIDE * (row + 1)
        base_y = MPGViewCell.CELL_SIDE * (col + 1)

        color = self.get_bg_color(cell, show_mines)
        cell_rect = (base_x, base_y, MPGViewCell.CELL_SIDE, MPGViewCell.CELL_SIDE),
        pygame.draw.rect(self.screen, color, cell_rect, 0)
        pygame.draw.rect(self.screen, MPGViewCell.COLOR_BORDER, cell_rect, 2)

        if cell.is_opened:
            if m_count and not cell.is_mined:
                self.draw_mines_count(base_x, base_y, m_count)
        else:
            if cell.state == MCell.FLAGGED:
                self.draw_flag(base_x, base_y)
            if cell.state == MCell.QUESTIONED:
                self.draw_question(base_x, base_y)

    def get_bg_color(self, cell, show_mines):
        color = MPGViewCell.COLOR_OPENED if cell.is_opened else MPGViewCell.COLOR_CLOSED
        if show_mines and cell.is_mined:
            color = MPGViewCell.COLOR_MINED
        return color

    def draw_question(self, base_x, base_y):
        ts = self.cell_font.render(str('?'), False, (255, 0, 0))
        text_width = ts.get_rect().width
        text_height = ts.get_rect().height
        self.screen.blit(
            ts,
            (
                base_x + (MPGViewCell.CELL_SIDE - text_width) // 2,
                base_y + (MPGViewCell.CELL_SIDE - text_height) // 2
            )
        )

    def draw_flag(self, base_x, base_y):
        pygame.draw.line(
            self.screen,
            MPGViewCell.COLOR_FLAGGED,
            (base_x + MPGViewCell.CELL_SIDE // 2 + 5, base_y + 10),
            (base_x + MPGViewCell.CELL_SIDE // 2 + 5, base_y + MPGViewCell.CELL_SIDE - 10),
            2
        )
        pygame.draw.rect(
            self.screen,
            MPGViewCell.COLOR_FLAGGED,
            (base_x + MPGViewCell.CELL_SIDE // 2 - 5, base_y + 10, 10, 10),
            0
        )

    def draw_mines_count(self, base_x, base_y, m_count):
        ts = self.cell_font.render(str(m_count), False, (0, 0, 150))
        text_width = ts.get_rect().width
        text_height = ts.get_rect().height
        self.screen.blit(
            ts,
            (
                base_x + (MPGViewCell.CELL_SIDE - text_width) // 2,
                base_y + (MPGViewCell.CELL_SIDE - text_height) // 2
            )
        )


class MPGView:
    def __init__(self, game, field):
        self.game = game
        self.field = field
        pygame.init()
        pygame.font.init()  # Инициализация модуля font
        self.x, self.y = 0, 0
        self.interface_font = pygame.font.SysFont('Comic Sans MS', 20, True)
        self.screen = pygame.display.set_mode(
            (
                (self.game.cols + 2) * MPGViewCell.CELL_SIDE,
                (self.game.rows + 2) * MPGViewCell.CELL_SIDE
            )
        )
        self.pg_gameover = False
        self.cell_drawer = MPGViewCell(self.screen)

    def loop(self):
        while not self.pg_gameover:
            self.process_events()
            self.draw_scene()
            pygame.time.wait(10)

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.pg_gameover = True
            elif not self.game.gameover:
                if event.type == pygame.MOUSEMOTION:
                    self.x, self.y = event.pos
                    self.current_row = self.x // MPGViewCell.CELL_SIDE - 1
                    self.current_col = self.y // MPGViewCell.CELL_SIDE - 1
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if 0 <= self.current_row < self.game.rows and 0 <= self.current_col < self.game.cols:
                        if event.button == 1:
                            self.game.open_cell(self.current_row, self.current_col)
                        elif event.button == 3:
                            self.game.update_cell_state(self.current_row, self.current_col)

    def draw_cell(self, row, col, show_mines):
        neighbors_mine_count = self.field.get_neighbors_mine_count(row, col)
        self.cell_drawer.draw(self.field.data[row][col], row, col, show_mines, neighbors_mine_count)

    def draw_field(self, show_mines=False):
        for i in range(self.game.rows):
            for j in range(self.game.cols):
                self.draw_cell(i, j, show_mines)

    def draw_stats(self):
        m = 'Mines set: {}'.format(self.field.get_selected_mine_count())
        ts = self.interface_font.render(m, False, (0, 0, 0))
        self.screen.blit(ts, (40, 5))

    def draw_debug(self):
        m = '({}, {}) ... ({}, {})'.format(
            self.x,
            self.y,
            self.x // MPGViewCell.CELL_SIDE - 1,
            self.y // MPGViewCell.CELL_SIDE - 1
        )
        ts = self.interface_font.render(m, False, (0, 0, 0))
        self.screen.blit(ts, (0, 500))

    def draw_scene(self):
        self.screen.fill((255, 255, 255))
        self.draw_stats()
        self.draw_debug()
        self.draw_field(self.game.gameover and not self.game.gamewin)
        self.draw_game_result()
        pygame.display.flip()

    def draw_game_result(self):
        if not self.game.gameover:
            m = 'Game in process'
        else:
            m = 'You win' if self.game.gamewin else 'You lose'
        ts = self.interface_font.render(m, False, (0, 0, 0))
        self.screen.blit(ts, (280, 5))


class MTextView:  # view
    def __init__(self, game, field):
        self.game = game
        self.field = field

    def draw_cell(self, row, col, show_mines):
        cell = self.field.data[row][col]
        if show_mines and cell.is_mined:
            state = 'M'
        else:
            if cell.is_opened:
                state = str(self.field.get_neighbors_mine_count(row, col))
                if state == '0':
                    state = '.'
            else:
                state = MCell.MARK_STATES[cell.state]
        print(state, end='')

    def draw_field(self, show_mines=False):
        print('  |', end=' ')
        for i in range(self.game.cols):
            print(i, end=' ')
        print()
        for i in range(self.game.cols + 1):
            print('-', end='-')
        print('-')
        for i in range(self.game.rows):
            print(i, end=' | ')
            for j in range(self.game.cols):
                self.draw_cell(i, j, show_mines)
                print(end=' ')
            print(end='\n')

    def draw_stats(self):
        print('Mines set: {}'.format(self.field.get_selected_mine_count()))

    def get_prompt(self):
        return 'Please, type in 3 numbers (row[0, {}], col[0, {}], action[0, 1]): '.format(
            self.game.rows - 1,
            self.game.cols - 1,
        )

    def read_step_data(self):
        prompt = self.get_prompt()
        row, col, action = map(int, input(self.get_prompt()).split())
        while not 0 <= row < self.game.rows or \
                not 0 <= col < self.game.cols or \
                not action in [0, 1]:
            row, col, action = map(int, input(prompt).split())
        return row, col, action

    def step(self):
        self.draw_field()
        self.draw_stats()
        row, col, action = self.read_step_data()
        print()
        if action == 0:
            self.game.open_cell(row, col)
        else:
            self.game.update_cell_state(row, col)

    def loop(self):
        while not self.game.gameover:
            self.step()
        self.draw_field(True)
        if self.game.gamewin:
            print('You win')
        else:
            print('You loose')


if __name__ == '__main__':
    field = MField(rows=10, cols=10, mines_count=10)
    game = MGame(field)
    if len(sys.argv) != 2:
        print('Usage: \n'
              'python minesweeper.py --text\n'
              'python minesweeper.py --pg')
    else:
        if sys.argv[1] == '--text':
            view = MTextView(game, game.field)
        elif sys.argv[1] == '--pg':
            view = MPGView(game, game.field)
        view.loop()
