import os

import arcade
from entities.entities import Entity

# Dossier contenant les spritesheets du joueur (voir assets/player/)
DOSSIER_ASSETS = os.path.join(os.path.dirname(__file__), "assets", "player")

TAILLE_FRAME = 64       # chaque frame des spritesheets fait 64x64 px (résolution native)
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
        self.acceleration = 900.0
        self.friction = 700.0
        self.max_speed = 300.0
        self.direction = "bas"  # direction affichée par défaut (au repos)

        self.frame_duration = 0.08  # vitesse de l'animation (secondes par frame)

        self._charger_animations()

        # Chaque frame chargée fait TAILLE_FRAME px de large nativement ; Arcade
        # recalcule width/height = texture.width * scale à chaque changement de
        # frame, donc c'est `scale` qu'il faut fixer pour garder une taille
        # affichée constante, plutôt que width/height (qui seraient écrasés).
        self.scale = TAILLE_AFFICHAGE / TAILLE_FRAME * 8

        # Direction affichée par défaut, au repos
        self.set_animation_direction("run_bas")
        self.set_animation_playing(True)

        # État des touches actuellement enfoncées
        self.moving_up = False
        self.moving_down = False
        self.moving_left = False
        self.moving_right = False

        # --- Point de spawn (pour revenir ici après un coup) ---
        self.spawn_x = center_x
        self.spawn_y = center_y

        # --- État "touché / respawn" ---
        # "normal"  -> comportement habituel (contrôlable)
        # "respawn" -> clignote, ignore les inputs, revient au spawn après
        #              respawn_duration secondes
        self.etat = "normal"
        self.respawn_duration = 1.2   # durée totale du clignotement (secondes)
        self.respawn_timer = 0.0
        self.blink_interval = 0.1     # vitesse du clignotement (secondes par bascule)
        self.blink_timer = 0.0
        self.death_animation_finished = True

    def take_hit(self):
        """
        Appelée quand le joueur est touché par une balle (voir Level).
        Ignore le coup si le joueur est déjà en train de respawn (invulnérable).
        """
        if self.etat != "normal":
            return
        self.etat = "respawn"
        self.respawn_timer = 0.0
        self.blink_timer = 0.0
        self.change_x = 0
        self.change_y = 0
        self.set_animation_playing(False)
        self.death_animation_finished = False

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
        # Pas de spritesheet dédiée pour la gauche : on retourne la vue 3/4
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
        if self.etat == "respawn":
            self._update_respawn(delta_time)
            return

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
            self.direction="droite"
        elif dx < 0:
            self.direction="gauche"
        elif dy > 0:
            self.direction="haut"
        elif dy < 0:
            self.direction="bas"

        # L'animation ne tourne que si le personnage bouge réellement
        # (utile pendant la phase de freinage, où l'input a cessé mais la
        # vélocité n'est pas encore à zéro).
        vitesse = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if vitesse >=5:
            self.set_animation_direction("run_{}".format(self.direction))
        else:
            self.set_animation_direction("idle_{}".format(self.direction))

        # Intègre change_x/change_y dans center_x/center_y + fait avancer
        # l'animation (défini dans Entity)
        super().update(delta_time)

    def _update_respawn(self, delta_time: float):
        """Fait clignoter le joueur (immobile, invulnérable), puis le renvoie au spawn."""
        self.respawn_timer += delta_time
        self.blink_timer += delta_time

        if self.blink_timer >= self.blink_interval:
            self.blink_timer = 0.0
            # Bascule la visibilité : alpha=0 (invisible) <-> alpha=255 (visible)
            self.alpha = 0 if self.alpha != 0 else 255

        if self.respawn_timer >= self.respawn_duration:
            self.center_x = self.spawn_x
            self.center_y = self.spawn_y
            self.change_x = 0
            self.change_y = 0
            self.alpha = 255
            self.etat = "normal"
            self.death_animation_finished = True
            self.set_animation_playing(True)