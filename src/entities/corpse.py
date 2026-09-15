import arcade
import os
from entities.entities import Entity

# Dossier contenant les spritesheets du joueur (voir assets/player/)
DOSSIER_ASSETS = os.path.join(os.path.dirname(__file__), "assets", "corpse")

TAILLE_FRAME = 16       # chaque frame des spritesheets fait 16x16 px (résolution native)
TAILLE_AFFICHAGE = 16   # taille voulue à l'écran (px) -> ajuste cette valeur pour agrandir/réduire le perso


class Corpse(Entity):
    """
    Corps laissé au sol à l'endroit où le joueur a été touché.
    Immobile et solide : une fois ajoutée à Level.walls, elle bloque le
    passage comme n'importe quel obstacle du décor.
    """

    def __init__(self, center_x=0, center_y=0, color=arcade.color.DARK_BROWN):
        super().__init__(
            width=TAILLE_AFFICHAGE,
            height=TAILLE_AFFICHAGE,
            color=color,
            center_x=center_x,
            center_y=center_y,
        )
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = 0.0
        self.load_animation(
            "sprite", os.path.join(DOSSIER_ASSETS, "corpse.png"),
            TAILLE_FRAME, TAILLE_FRAME, 1,
        )
        self.set_animation_direction("sprite")
        self.scale = TAILLE_AFFICHAGE / TAILLE_FRAME * 2

    
    