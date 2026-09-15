import arcade


class Entity(arcade.SpriteSolidColor):
    """
    Classe de base pour toutes les entités du jeu (joueur, ennemis, objets...).

    Hérite de arcade.SpriteSolidColor pour avoir un rendu simple (rectangle
    coloré) sans avoir besoin d'images. Tu pourras plus tard créer une
    sous-classe qui charge une vraie texture si tu veux des sprites dessinés.
    """

    def __init__(self, width=40, height=40, color=arcade.color.WHITE, center_x=0, center_y=0):
        super().__init__(width, height, color)
        self.center_x = center_x
        self.center_y = center_y

        # Vitesse de déplacement en pixels/seconde, utilisée par les sous-classes
        self.speed = 200

    def update(self, delta_time: float = 1 / 60):
        """
        Logique de l'entité, appelée à chaque frame par Level.update().
        À surcharger dans les sous-classes (Player, Enemy, ...) pour définir
        un comportement : déplacement, IA, animation, etc.
        """
        pass