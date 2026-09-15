import arcade
from entities import Entity


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
        # Réglages physiques spécifiques au joueur (hérités d'Entity, ajustables ici)
        self.acceleration = 900.0
        self.friction = 700.0
        self.max_speed = 300.0

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

        if dx != 0 or dy != 0:
            # Normalisation pour ne pas accélérer plus vite en diagonale
            if dx != 0 and dy != 0:
                norme = (dx ** 2 + dy ** 2) ** 0.5
                dx /= norme
                dy /= norme

            # On accélère dans la direction voulue : la vélocité actuelle
            # (change_x/change_y) est conservée et réorientée petit à petit,
            # d'où l'effet d'inertie quand on change de direction.
            self.apply_acceleration(dx, dy, delta_time)
        else:
            # Aucune touche pressée : on freine progressivement jusqu'à l'arrêt.
            self.apply_friction(delta_time)

        # Intègre change_x/change_y dans center_x/center_y (défini dans Entity)
        super().update(delta_time)