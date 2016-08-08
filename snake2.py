import random
import pyglet
import pyglet.graphics
import pyglet.resource
from pyglet.window import key


# Used to order sprites
background = pyglet.graphics.OrderedGroup(0)
foreground = pyglet.graphics.OrderedGroup(1)
hud = pyglet.graphics.OrderedGroup(2)


class Brick(pyglet.sprite.Sprite):
    bricks = set()
    dirty = set()
    game = None

    def __init__(self, image, col=0, row=0, group=foreground):
        super().__init__(image, batch=self.game.batch, group=group)
        self.bricks.add(self)
        self.col, self.row = col, row

    @property
    def col(self):
        return self._col

    @col.setter
    def col(self, v):
        self._col = v
        self.dirty.add(self)

    @property
    def row(self):
        return self._row

    @row.setter
    def row(self, v):
        self._row = v
        self.dirty.add(self)

    def place(self):
        self.scale = self.game.brick_scale
        self.x = self.game.base_x + self.col * self.game.brick_px
        self.y = self.game.base_y - (self.row + 1) * self.game.brick_px  # +1 because of anchor point

    def delete(self):
        self.dirty.discard(self)
        self.bricks.remove(self)
        super().delete()


class UP: dcol = 0; drow = -1
class RIGHT: dcol = 1; drow = 0
class DOWN: dcol = 0; drow = 1
class LEFT: dcol = -1; drow = 0

class Snake:
    def __init__(self, game):
        col = game.COLUMNS // 2
        row = game.ROWS // 2
        self.direction = RIGHT
        self.body_image = pyglet.resource.image('snake.png')
        self.body = [
            Brick(self.body_image, col, row),
            Brick(self.body_image, col-1, row)
        ]
        self.alive = True
        game.push_handlers(self.on_key_press)
        self.game = game


    def die(self):
        self.game.pop_handlers()
        self.alive = False

    def delete(self):
        for seg in self.body:
            seg.delete()

    def on_key_press(self, symbol, modifiers):
        if not self.alive:
            return
        direction = None
        if symbol == key.UP:
            direction = UP
        elif symbol == key.RIGHT:
            direction = RIGHT
        elif symbol == key.DOWN:
            direction = DOWN
        elif symbol == key.LEFT:
            direction = LEFT
        if direction is not None:
            col, row = self.get_next_step(direction)
            if col == self.body[1].col and row == self.body[1].row:
                return
            else:
                self.direction = direction
        
        
    def get_next_step(self, direction=None):
        if direction is None:
            direction = self.direction
        if not self.alive:
            return
        head = self.body[0]
        return head.col + direction.dcol, head.row + direction.drow


    def step(self, col, row, grow=False):
        if not self.alive:
            return

        if grow:
            tail = Brick(self.body_image)
            self.body.append(tail)

        for i in range(len(self.body)-1, 0, -1):
            self.body[i].col = self.body[i-1].col
            self.body[i].row = self.body[i-1].row

        head = self.body[0]
        head.col = col
        head.row = row



class Food(Brick):
    def __init__(self):
        self.food_image = pyglet.resource.image('food.png')
        super().__init__(self.food_image)

        while True:
            col = random.randint(1, self.game.COLUMNS-2)
            row = random.randint(1, self.game.ROWS-2)
            for brick in self.bricks:
                if col == brick.col and row == brick.row:
                    break
            else:
                break  # No collision
        self.col = col
        self.row = row



class Game(pyglet.window.Window):
    STEP = 0.2  # Seconds
    COLUMNS = 32
    ROWS = 18
    HUD_HEIGHT = 30
    
    def __init__(self):
        super().__init__(resizable=True)
        pyglet.clock.set_fps_limit(60)
        self.batch = pyglet.graphics.Batch()
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.score = 0
        self.label = pyglet.text.Label(
                'Press R to Start', 'Times New Roman', 36,
                color=(255, 0, 0, 255),
                anchor_x='center', anchor_y='center',
                batch=self.batch, group=hud)
        self.score_label = pyglet.text.Label(
                '', 'Times New Roman', 24,
                color=(255, 255, 0, 255),
                anchor_x='center', anchor_y='top',
                batch=self.batch, group=hud)

        self.back_image = pyglet.resource.image('background.png')
        self.back = pyglet.sprite.Sprite(
                self.back_image, batch=self.batch, group=background)

        self.brick_image = pyglet.resource.image('brick.png')
        Brick.game = self  # Set up globally used game object
        for row in range(self.ROWS):
            for col in range(self.COLUMNS):
                if (row == 0 or col == 0
                        or row == self.ROWS-1 or col == self.COLUMNS-1):
                    Brick(self.brick_image, col, row)

        self.snake = self.food = None


    def start(self):
        if self.snake:
            self.snake.delete()
        self.snake = Snake(self)
        if self.food:
            self.food.delete()
        self.food = Food()
        pyglet.clock.unschedule(self.update)
        pyglet.clock.tick()  # Reset dt
        pyglet.clock.schedule_interval(self.update, self.STEP)
        self.label.text = ""
        self.set_score(0)
        
    def set_score(self, v):
        self.score = v
        self.score_label.text = str(self.score)


    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.back.scale = max(
                width / self.back_image.width, height / self.back_image.height)

        self.brick_px = min(width / self.COLUMNS, (height - self.HUD_HEIGHT) / self.ROWS)
        self.brick_scale = self.brick_px / self.brick_image.width
        self.base_x = (width - self.brick_px * self.COLUMNS) / 2
        self.base_y = height - (height - self.brick_px * self.ROWS + self.HUD_HEIGHT) / 2
        
        self.label.x = self.width // 2
        self.label.y = self.height // 2
        
        self.score_label.x = self.width // 2
        self.score_label.y = self.base_y + self.HUD_HEIGHT

        Brick.dirty |= Brick.bricks

    def on_draw(self):
        while Brick.dirty:
            brick = Brick.dirty.pop()
            brick.place()
        self.clear()
        self.batch.draw()


    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)
        if symbol == key.R:
            self.start()
    

    def update(self, dt):
        if not self.snake.alive:
            return

        col, row = self.snake.get_next_step()
        for brick in Brick.bricks:
            if col == brick.col and row == brick.row:
                if brick is self.food:
                    self.snake.step(col, row, True)
                    self.food.delete()
                    self.food = Food()
                    self.set_score(self.score + 1)
                        
                else:
                    self.snake.die()
                    self.label.text = "Game Over"
                return

        self.snake.step(col, row)



if __name__ == "__main__":
    pyglet.resource.path = ['res']
    pyglet.resource.reindex()
    window = Game()
pyglet.app.run()