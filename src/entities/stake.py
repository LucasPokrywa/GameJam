import math
import os

from entities.damage import DeathCause
from entities.entities import Entity

SPRITE = os.path.join(os.path.dirname(__file__), "..", "..",
                      "assets", "entities", "tower", "bullet.png")
FRAME_SIZE = 16
FRAMES = 8
ARROW_BOX = (0, 5, 15, 12)
SCALE_FACTOR = 2


class Stake(Entity):
    """Stake fired by a turret: straight line, constant speed."""

    damage_type = DeathCause.TOWER

    def __init__(self, center_x, center_y, direction_x, direction_y, speed=400):
        super().__init__(
            width=ARROW_BOX[2] - ARROW_BOX[0],
            height=ARROW_BOX[3] - ARROW_BOX[1],
            center_x=center_x,
            center_y=center_y,
        )
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = speed

        self.load_animation("arrow", SPRITE, FRAME_SIZE, FRAME_SIZE, FRAMES,
                            crop_box=ARROW_BOX)
        self.set_animation_direction("arrow")
        self.scale = SCALE_FACTOR
        self.frame_duration = 0.06

        # direction_x / direction_y must already be normalised; Turret does it.
        self.change_x = direction_x * speed
        self.change_y = direction_y * speed
        self.angle = -math.degrees(math.atan2(direction_y, direction_x))

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
