import arcade
from entities.entities import Entity


class Player(Entity):
    """Le joueur, contrôlé par le clavier (ZQSD ou flèches)."""

    def __init__(self, center_x=0, center_y=0):
        super().__init__(
            width=40,
            height=40,
            color=arcade.color.GREEN,
            center_x=center_x,
            center_y=center_y,
        )
        self.speed = 250

        # État des touches actuellement enfoncées
        self.moving_up = False
        self.moving_down = False
        self.moving_left = False
        self.moving_right = False

    def on_key_press(self, key):
        """Appelé par la fenêtre principale quand une touche est pressée."""
        if key in (arcade.key.UP, arcade.key.Z):
            self.moving_up = True
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.moving_down = True
        elif key in (arcade.key.LEFT, arcade.key.Q):
            self.moving_left = True
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.moving_right = True

    def on_key_release(self, key):
        """Appelé par la fenêtre principale quand une touche est relâchée."""
        if key in (arcade.key.UP, arcade.key.Z):
            self.moving_up = False
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.moving_down = False
        elif key in (arcade.key.LEFT, arcade.key.Q):
            self.moving_left = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.moving_right = False

    def update(self, delta_time: float = 1 / 60):
        dx, dy = 0, 0

        if self.moving_up:
            dy += 1
        if self.moving_down:
            dy -= 1
        if self.moving_left:
            dx -= 1
        if self.moving_right:
            dx += 1

        # Normalisation pour ne pas aller plus vite en diagonale
        if dx != 0 and dy != 0:
            norme = (dx ** 2 + dy ** 2) ** 0.5
            dx /= norme
            dy /= norme

        self.center_x += dx * self.speed * delta_time
        self.center_y += dy * self.speed * delta_time