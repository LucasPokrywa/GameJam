import math
import os

from entities.damage import DeathCause
from entities.entities import Entity

SPRITE = os.path.join(os.path.dirname(__file__), "..", "..",
                      "assets", "entities", "tower", "arrow.png")
FRAME_SIZE = 16
# arrow.png is a single complete projectile, unlike the previous horizontal
# bullet spritesheet.
FRAMES = 1
SCALE_FACTOR = 2


class Stake(Entity):
    """Stake fired by a turret: straight line, constant speed."""

    damage_type = DeathCause.TOWER

    def __init__(self, center_x, center_y, direction_x, direction_y, speed=400):
        super().__init__(
            width=FRAME_SIZE,
            height=FRAME_SIZE,
            center_x=center_x,
            center_y=center_y,
        )
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = speed

        self.load_animation("arrow", SPRITE, FRAME_SIZE, FRAME_SIZE, FRAMES)
        self.set_animation_direction("arrow")
        self.scale = SCALE_FACTOR
        self.frame_duration = 0.06

        # direction_x / direction_y must already be normalised; Turret does it.
        self.change_x = direction_x * speed
        self.change_y = direction_y * speed
        # The arrow artwork points west at angle 0, hence the half-turn.
        self.angle = 180 - math.degrees(math.atan2(direction_y, direction_x))

        # Unlike the player, a bullet must leave the screen instead of
        # sticking to its edge.
        self.clamp_to_bounds = False
        self.attached_player = None

    def update(self, delta_time: float = 1 / 60):
        if self.attached_player is not None:
            self.center_x = self.attached_player.center_x
            self.center_y = self.attached_player.center_y
            self.update_animation_frame(delta_time)
            return
        super().update(delta_time)
