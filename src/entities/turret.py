import math

import arcade
from entities.entities import Entity
from entities.bullet import Bullet


class Turret(Entity):
    """
    Tourelle statique : vise le joueur en continu et tire une Bullet vers
    lui à intervalle régulier. Ne se déplace jamais (pas de physique).
    """

    def __init__(self, center_x=0, center_y=0, level=None, player=None,
                 fire_interval=1.5, bullet_speed=400):
        super().__init__(
            width=48,
            height=48,
            color=arcade.color.DARK_RED,
            center_x=center_x,
            center_y=center_y,
        )
        # Une tourelle ne bouge pas : on neutralise la physique héritée d'Entity.
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = 0.0

        # Référence vers le niveau (pour y ajouter les balles tirées) et vers
        # le joueur (pour savoir où viser). Fournies à la création, voir
        # levels.py pour un exemple de câblage.
        self.level = level
        self.player = player

        self.fire_interval = fire_interval   # secondes entre deux tirs
        self.bullet_speed = bullet_speed
        self.time_since_last_shot = 0.0

    def update(self, delta_time: float = 1 / 60):
        if self.player is not None:
            self._viser_joueur()
            self._gerer_tir(delta_time)

        # Aucune vélocité à intégrer (immobile), mais on garde l'appel pour
        # rester cohérent avec les autres entités (et profiter d'une future
        # animation si tu en ajoutes une).
        super().update(delta_time)

    def _viser_joueur(self):
        """Oriente visuellement la tourelle vers le joueur (self.angle, en degrés)."""
        dx = self.player.center_x - self.center_x
        dy = self.player.center_y - self.center_y
        self.angle = -math.degrees(math.atan2(dy, dx))
        # Note : si tu ajoutes un vrai sprite de tourelle plus tard, il faudra
        # sans doute ajouter/soustraire un offset ici selon l'orientation
        # d'origine du dessin (ex: -90° si le canon pointe "vers le haut" par défaut).

    def _gerer_tir(self, delta_time):
        self.time_since_last_shot += delta_time
        if self.time_since_last_shot >= self.fire_interval:
            self.time_since_last_shot = 0.0
            self._tirer()

    def _tirer(self):
        if self.level is None:
            return

        dx = self.player.center_x - self.center_x
        dy = self.player.center_y - self.center_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance == 0:
            return

        direction_x = dx / distance
        direction_y = dy / distance

        balle = Bullet(
            center_x=self.center_x,
            center_y=self.center_y,
            direction_x=direction_x,
            direction_y=direction_y,
            speed=self.bullet_speed,
        )
        self.level.entities.append(balle)