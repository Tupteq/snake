import random

import pyglet
import pyglet.graphics
import pyglet.resource
from pyglet.window import key


# Used to order sprites
background = pyglet.graphics.OrderedGroup(0)
foreground = pyglet.graphics.OrderedGroup(1)

class Board:
    COLUMNS = 32
    ROWS = 18

    def __init__(self, game):
        self.back_image = pyglet.resource.image('background.png')
        self.back = pyglet.sprite.Sprite(
                self.back_image, batch=game.batch, group=background)

        self.brick_image = pyglet.resource.image('brick.png')
        self.board = [[None]*self.ROWS for row in range(self.COLUMNS)]
        for row in range(self.ROWS):
            for col in range(self.COLUMNS):
                if (row == 0 or col == 0
                        or row == self.ROWS-1 or col == self.COLUMNS-1):
                    self.board[col][row] = pyglet.sprite.Sprite(
                            self.brick_image, batch=game.batch,
                            group=foreground)

        game.push_handlers(self.on_resize)


    def on_resize(self, width, height):
        """Rescale sprites after window resize (also on app start).
        """
        self.back.scale = max(
                width / self.back_image.width, height / self.back_image.height)

        self.brick_px = min(width / self.COLUMNS, height / self.ROWS)
        self.brick_scale = self.brick_px / self.brick_image.width
        self.base_x = (width - self.brick_px * self.COLUMNS) / 2
        self.base_y = height - (height - self.brick_px * self.ROWS) / 2

        for row in range(self.ROWS):
            for col in range(self.COLUMNS):
                s = self.board[col][row]
                if s is not None:
                    self.position_brick(s, col, row)


    def position_brick(self, brick, col, row):
        brick.scale = self.brick_scale
        brick.x = self.base_x + col * self.brick_px
        brick.y = self.base_y - (row + 1) * self.brick_px  # +1 because of anchor point



class SnakeSegment(pyglet.sprite.Sprite):
    def __init__(self, image, board_x, board_y, batch):
        super().__init__(image, batch=batch, group=foreground)
        self.board_x = board_x
        self.board_y = board_y


class UP: dx = 0; dy = -1
class RIGHT: dx = 1; dy = 0
class DOWN: dx = 0; dy = 1
class LEFT: dx = -1; dy = 0

class Snake:
    def __init__(self, game):
        self.game = game
        self.body_image = pyglet.resource.image('snake.png')
        self.alive = False

        game.push_handlers(self.on_key_press)


    def reset(self):
        self.alive = True
        col = self.game.board.COLUMNS // 2
        row = self.game.board.ROWS // 2
        self.direction = RIGHT
        self.body = [
            SnakeSegment(self.body_image, col, row, self.game.batch),
            SnakeSegment(self.body_image, col+1, row, self.game.batch)
        ]
        self.position()


    def die(self):
        self.alive = False


    def position(self):
        for seg in self.body:
            self.game.board.position_brick(seg, seg.board_x, seg.board_y)


    def on_key_press(self, symbol, modifiers):
        if not self.alive:
            return
        if symbol == key.UP:
            self.direction = UP
        elif symbol == key.RIGHT:
            self.direction = RIGHT
        elif symbol == key.DOWN:
            self.direction = DOWN
        elif symbol == key.LEFT:
            self.direction = LEFT


    def get_next_step(self):
        if not self.alive:
            return
        head = self.body[0]
        return head.board_x + self.direction.dx, head.board_y + self.direction.dy


    def step(self, x, y, grow=False):
        if not self.alive:
            return

        if grow:
            tail = SnakeSegment(self.body_image, 0, 0, self.game.batch)
            self.body.append(tail)

        for i in range(len(self.body)-1, 0, -1):
            self.body[i].board_x = self.body[i-1].board_x
            self.body[i].board_y = self.body[i-1].board_y

        head = self.body[0]
        head.board_x = x
        head.board_y = y
        self.position()



class Food(pyglet.sprite.Sprite):
    def __init__(self, board, snake, batch):
        self.food_image = pyglet.resource.image('food.png')
        self.board = board
        super().__init__(self.food_image, batch=batch, group=foreground)

        while True:
            x = random.randint(1, board.COLUMNS-2)
            y = random.randint(1, board.ROWS-2)
            if board.board[x][y] is not None:
                continue
            for seg in snake.body:
                if x == seg.board_x and y == seg.board_y:
                    break
            else:
                break
        self.board_x = x
        self.board_y = y
        self.position()


    def position(self):
        self.board.position_brick(self, self.board_x, self.board_y)



class Game(pyglet.window.Window):
    STEP = 0.3  # Seconds

    def __init__(self):
        super().__init__(resizable=True)
        self.batch = pyglet.graphics.Batch()
        self.board = Board(self)
        self.snake = Snake(self)
        self.schedule = pyglet.clock.schedule_interval(func=self.update, interval=1/60)
        self.keys = key.KeyStateHandler()
        self.time = 0.0
        self.push_handlers(self.keys)

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)
        if symbol == key.R:
            self.snake.reset()
            self.food = Food(self.board, self.snake, self.batch)

    def update(self, dt):
        self.time += dt

        if self.time >= self.STEP:
            self.time -= self.STEP
            if not self.snake.alive:
                return

            x, y = self.snake.get_next_step()
            if self.board.board[x][y] is not None:
                self.snake.die()
                return

            if x == self.food.board_x and y == self.food.board_y:
                self.snake.step(x, y, True)
                self.food.delete()
                self.food = Food(self.board, self.snake, self.batch)
                return

            self.snake.step(x, y)



if __name__ == "__main__":
    pyglet.resource.path = ['res']
    pyglet.resource.reindex()
    window = Game()
    pyglet.app.run()
