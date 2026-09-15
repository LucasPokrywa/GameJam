import arcade
from entities.entities import Entity


class Bullet(Entity):
    """
    Projectile simple : part d'un point dans une direction donnée et
    avance en ligne droite à vitesse constante, jusqu'à sortir de l'écran
    (où Level la détruit automatiquement, voir clamp_to_bounds).
    """

    def __init__(self, center_x, center_y, direction_x, direction_y,
                 speed=400, width=12, height=12, color=arcade.color.YELLOW):
        super().__init__(
            width=width,
            height=height,
            color=color,
            center_x=center_x,
            center_y=center_y,
        )
        # Pas de friction ni d'accélération : la balle garde une vitesse
        # constante du début à la fin (contrairement au joueur qui a de
        # l'inertie).
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = speed

        # direction_x / direction_y doivent être un vecteur déjà normalisé
        # (longueur 1) : c'est Turret qui s'occupe de ce calcul.
        self.change_x = direction_x * speed
        self.change_y = direction_y * speed

        # Une balle ne doit pas rester coincée sur un bord de l'écran comme
        # le joueur : elle doit disparaître dès qu'elle en sort.
        self.clamp_to_bounds = False