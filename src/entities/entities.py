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

        # --- Paramètres physiques (px/s et px/s²) ---
        # self.change_x / self.change_y sont des attributs natifs d'arcade.Sprite :
        # ils représentent la vélocité actuelle de l'entité.
        self.acceleration = 900.0   # accélération appliquée quand l'entité "pousse" dans une direction
        self.friction = 700.0       # décélération appliquée quand rien ne pousse (freinage naturel)
        self.max_speed = 300.0      # vitesse maximale atteignable

    def apply_friction(self, delta_time: float):
        """
        Réduit progressivement la vélocité vers 0 (freinage), sans changer sa
        direction avant qu'elle n'atteigne 0. À appeler quand l'entité ne
        reçoit plus d'impulsion (plus d'input, plus de force).
        """
        vitesse = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if vitesse == 0:
            return

        freinage = self.friction * delta_time
        if freinage >= vitesse:
            self.change_x = 0
            self.change_y = 0
        else:
            self.change_x -= freinage * (self.change_x / vitesse)
            self.change_y -= freinage * (self.change_y / vitesse)

    def apply_acceleration(self, direction_x: float, direction_y: float, delta_time: float):
        """
        Accélère l'entité dans une direction donnée (vecteur normalisé),
        puis limite le résultat à max_speed. La vélocité existante est
        conservée et progressivement réorientée : c'est ce qui donne
        l'effet "inertie" quand on change de direction.
        """
        self.change_x += direction_x * self.acceleration * delta_time
        self.change_y += direction_y * self.acceleration * delta_time

        vitesse = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if vitesse > self.max_speed:
            echelle = self.max_speed / vitesse
            self.change_x *= echelle
            self.change_y *= echelle

    def update(self, delta_time: float = 1 / 60):
        """
        Intègre la vélocité (change_x / change_y) dans la position.
        Commun à toutes les entités. Les sous-classes (Player, Enemy, ...)
        doivent définir change_x/change_y (via apply_acceleration/apply_friction
        ou une IA) PUIS appeler super().update(delta_time) pour déplacer
        réellement l'entité.
        """
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time