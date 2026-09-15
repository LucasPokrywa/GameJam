import arcade
from entities.player import Player


class Level:
    """
    Classe de base pour tous les niveaux du jeu.

    Chaque niveau définit son décor (murs, obstacles) et ses entités
    (joueur, ennemis, objets...). Pour créer un nouveau niveau, hérite de
    cette classe et surcharge la méthode setup().
    """

    def __init__(self, window_width, window_height, background_color=arcade.color.DARK_SLATE_GRAY):
        self.window_width = window_width
        self.window_height = window_height
        self.background_color = background_color

        # Sprites de décor / obstacles (pour les collisions plus tard)
        self.walls = arcade.SpriteList()

        # Toutes les entités présentes dans le niveau, y compris le joueur
        self.entities = arcade.SpriteList()

        self.player = None

        self.setup()

    def setup(self):
        """
        Construit le contenu du niveau : murs, ennemis, objets, position
        de départ du joueur, etc.

        Comportement par défaut : niveau vide avec le joueur au centre.
        Surcharge cette méthode dans une sous-classe pour un vrai niveau,
        par exemple :

            class Level1(Level):
                def setup(self):
                    self.player = Player(center_x=100, center_y=100)
                    self.entities.append(self.player)
                    # ajouter des murs, ennemis, etc.
        """
        self.player = Player(center_x=self.window_width // 2, center_y=self.window_height // 2)
        self.entities.append(self.player)

    def update(self, delta_time: float):
        for entity in self.entities:
            entity.update(delta_time)

        # Empêche les entités de sortir de l'écran
        # (à remplacer par de vraies collisions avec les murs plus tard)
        for entity in self.entities:
            if entity.left < 0:
                entity.left = 0
            if entity.right > self.window_width:
                entity.right = self.window_width
            if entity.bottom < 0:
                entity.bottom = 0
            if entity.top > self.window_height:
                entity.top = self.window_height

    def draw(self):
        self.walls.draw()
        self.entities.draw()


class EmptyLevel(Level):
    """Premier niveau : totalement vide, pour tester les déplacements du joueur."""
    pass