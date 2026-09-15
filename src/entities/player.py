import os

import arcade
from entities.entities import Entity

# Dossier contenant les spritesheets du joueur (voir assets/player/)
DOSSIER_ASSETS = os.path.join(os.path.dirname(__file__), "assets", "player")

TAILLE_FRAME = 64    # chaque frame des spritesheets fait 64x64 px (résolution native)
TAILLE_AFFICHAGE = 16   # taille voulue à l'écran (px) -> ajuste cette valeur pour agrandir/réduire le perso
NB_FRAMES_COURSE = 6    # nombre de frames dans l'animation de course


class Player(Entity):
    """Le joueur, contrôlé par le clavier (ZQSD ou flèches)."""

    def __init__(self, center_x=0, center_y=0):
        super().__init__(
            width=TAILLE_AFFICHAGE,
            height=TAILLE_AFFICHAGE,
            color=arcade.color.GREEN,
            center_x=center_x,
            center_y=center_y,
        )
        # Réglages physiques spécifiques au joueur (hérités d'Entity, ajustables ici)
        self.acceleration = 1800.0
        self.friction = 1400.0
        self.max_speed = 500.0
        self.direction = "bas"  # direction affichée par défaut

        self.frame_duration = 0.08  # vitesse de l'animation (secondes par frame)

        self._charger_animations()

        # Chaque frame chargée fait TAILLE_FRAME px de large nativement ; Arcade
        # recalcule width/height = texture.width * scale à chaque changement de
        # frame, donc c'est `scale` qu'il faut fixer pour garder une taille
        # affichée constante, plutôt que width/height (qui seraient écrasés).
        self.scale = TAILLE_AFFICHAGE / TAILLE_FRAME *8

        # Direction affichée par défaut, au repos
        self.set_animation_direction("idle_{}".format(self.direction))
        self.set_animation_playing(True)

        # État des touches actuellement enfoncées
        self.moving_up = False
        self.moving_down = False
        self.moving_left = False
        self.moving_right = False

    def _charger_animations(self):
        """Découpe les spritesheets et enregistre une animation par direction."""
        self.load_animation(
            "run_bas", os.path.join(DOSSIER_ASSETS, "Run/Run_F.png"),
            TAILLE_FRAME, TAILLE_FRAME, NB_FRAMES_COURSE,
        )
        self.load_animation(
            "run_haut", os.path.join(DOSSIER_ASSETS, "Run/Run_Back.png"),
            TAILLE_FRAME, TAILLE_FRAME, NB_FRAMES_COURSE,
        )
        self.load_animation(
            "run_droite", os.path.join(DOSSIER_ASSETS, "Run/Run_34F.png"),
            TAILLE_FRAME, TAILLE_FRAME, NB_FRAMES_COURSE,
        )
        # Pas de spritesheet dédiée pour la gauche : on retourne la vue 3/4
        self.load_animation(
            "run_gauche", os.path.join(DOSSIER_ASSETS, "Run/Run_34F.png"),
            TAILLE_FRAME, TAILLE_FRAME, NB_FRAMES_COURSE,
            miroir_horizontal=True,
        )

        self.load_animation(
            "idle_bas", os.path.join(DOSSIER_ASSETS, "Idle/Idle_F.png"),
            TAILLE_FRAME, TAILLE_FRAME, 8,
        )

        self.load_animation(
            "idle_haut", os.path.join(DOSSIER_ASSETS, "Idle/Idle_B.png"),
            TAILLE_FRAME, TAILLE_FRAME, 8,
        )

        self.load_animation(
            "idle_droite", os.path.join(DOSSIER_ASSETS, "Idle/Idle_34F.png"),
            TAILLE_FRAME, TAILLE_FRAME, 8,
        )

        self.load_animation(
            "idle_gauche", os.path.join(DOSSIER_ASSETS, "Idle/Idle_34F.png"),
            TAILLE_FRAME, TAILLE_FRAME, 8,
            miroir_horizontal=True,
        )

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

        # --- Choix de la direction affichée ---
        # On n'a que 4 animations (haut/bas/gauche/droite) : en diagonale, on
        # privilégie l'axe horizontal, qui est visuellement plus lisible avec
        # la vue 3/4 dont on dispose.
        if dx > 0:
            self.direction = "droite"
        elif dx < 0:
            self.direction = "gauche"
        elif dy > 0:
            self.direction = "haut"
        elif dy < 0:
            self.direction = "bas"

        # L'animation ne tourne que si le personnage bouge réellement
        # (utile pendant la phase de freinage, où l'input a cessé mais la
        # vélocité n'est pas encore à zéro).
        vitesse = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if vitesse <= 5:
            self.set_animation_direction("idle_{}".format(self.direction))
        else:
            self.set_animation_direction("run_{}".format(self.direction))

        # Intègre change_x/change_y dans center_x/center_y + fait avancer
        # l'animation (défini dans Entity)
        super().update(delta_time)