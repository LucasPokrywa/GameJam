import math
import os
from enum import Enum

from entities.stake import Stake
from entities.damage import DeathCause
from entities.entities import Entity

SPRITE = os.path.join(os.path.dirname(__file__), "..", "..",
                      "assets", "entities", "tower", "arrow_tower.png")
FRAME_SIZE = 16
# arrow_tower.png stores its firing and cooldown poses vertically.
FRAMES = 1
SCALE_FACTOR = 2

COOLDOWN_TINT = (200, 180, 180)
FIRING_DURATION = 0.18


class TurretState(Enum):
    FIRING = "firing"
    COOLDOWN = "cooldown"


def segment_crosses_rect(x1, y1, x2, y2, left, right, bottom, top) -> bool:
    """
    Liang-Barsky clipping: each of the four edges narrows the range [t0, t1]
    of valid positions along the segment. If it empties, the segment misses.
    """
    dx = x2 - x1
    dy = y2 - y1
    t0, t1 = 0.0, 1.0

    for p, q in ((-dx, x1 - left), (dx, right - x1),
                 (-dy, y1 - bottom), (dy, top - y1)):
        if p == 0:   # segment parallel to this edge
            if q < 0:
                return False
            continue

        r = q / p
        if p < 0:
            if r > t1:
                return False
            t0 = max(t0, r)
        else:
            if r < t0:
                return False
            t1 = min(t1, r)

    return t0 <= t1


class Xbow(Entity):
    """
    Static turret that only fires when it actually sees the player: a WALL
    corpse dropped on its axis makes it harmless.
    """

    damage_type = DeathCause.TOWER

    def __init__(self, center_x=0, center_y=0, level=None, player=None,
                 fire_interval=1.5, bullet_speed=400,
                 detection_range=420.0, aim_duration=0.45, orientation="east"):
        super().__init__(
            width=FRAME_SIZE,
            height=FRAME_SIZE,
            center_x=center_x,
            center_y=center_y,
        )
        self.load_animation("cooldown", SPRITE, FRAME_SIZE, FRAME_SIZE, FRAMES,
                            row=0)
        self.load_animation("firing", SPRITE, FRAME_SIZE, FRAME_SIZE, FRAMES,
                            row=1)
        self.set_animation_direction("cooldown")
        self.scale = SCALE_FACTOR
        self.frame_duration = 0.09
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = 0.0

        self.level = level
        self.player = player
        angles = {"east": 180, "north": 90, "west": 0, "south": -90}
        if orientation not in angles:
            raise ValueError(f"Unsupported Xbow orientation: {orientation!r}")
        self.orientation = orientation
        # The artwork faces west by default; rotate it with its projectile.
        self.angle = angles[orientation]
        self.fire_interval = fire_interval   # reload after a shot
        self.bullet_speed = bullet_speed
        self.detection_range = detection_range
        self.aim_duration = aim_duration     # telegraph before firing

        self.state = TurretState.COOLDOWN
        self._timer = 0.0

    def _distance_to(self, target) -> float:
        return math.hypot(target.center_x - self.center_x,
                          target.center_y - self.center_y)

    def fire(self):
        self.state = TurretState.FIRING
        self.set_animation_direction("firing")
        self._spawn_stake()
        self._timer = 0.0

    def update(self, delta_time: float = 1 / 60):
        self._timer += delta_time

        if self.state is TurretState.COOLDOWN:
            if self._timer >= self.fire_interval:
                self.fire()
        elif self.state is TurretState.FIRING:
            if self._timer >= FIRING_DURATION:
                self.state = TurretState.COOLDOWN
                self.set_animation_direction("cooldown")
                self._timer = 0.0

        super().update(delta_time)

    def _spawn_stake(self):

        if self.orientation == "east":
            dx = 1
            dy = 0
        elif self.orientation == "west":
            dx = -1
            dy = 0
        elif self.orientation == "north":
            dx = 0
            dy = 1
        elif self.orientation == "south":
            dx = 0
            dy = -1

        stake = Stake(
            center_x=self.center_x,
            center_y=self.center_y,
            direction_x=dx,
            direction_y=dy,
            speed=self.bullet_speed,
        )
        # The speed is already scaled, it comes from self.bullet_speed.
        self.level.scale_to_window(stake, speeds=False)
        self.level.entities.append(stake)
