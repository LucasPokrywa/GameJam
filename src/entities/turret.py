import math
import os
from enum import Enum

from entities.bullet import Bullet
from entities.damage import DeathCause
from entities.entities import Entity

SPRITE = os.path.join(os.path.dirname(__file__), "..", "..",
                      "assets", "entities", "tower", "tower.png")
FRAME_SIZE = 16
FRAMES = 8
# The flame sits in the middle of its frame; cropping keeps the hit box on it.
FLAME_BOX = (2, 0, 14, 16)
SCALE_FACTOR = 2

IDLE_TINT = (150, 150, 170)
AIMING_TINT = (255, 255, 255)
COOLDOWN_TINT = (200, 180, 180)


class TurretState(Enum):
    IDLE = "idle"
    AIMING = "aiming"
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


class Turret(Entity):
    """
    Static turret that only fires when it actually sees the player: a WALL
    corpse dropped on its axis makes it harmless.
    """

    damage_type = DeathCause.TOWER

    def __init__(self, center_x=0, center_y=0, level=None, player=None,
                 fire_interval=1.5, bullet_speed=400,
                 detection_range=420.0, aim_duration=0.45):
        super().__init__(
            width=FLAME_BOX[2] - FLAME_BOX[0],
            height=FLAME_BOX[3] - FLAME_BOX[1],
            center_x=center_x,
            center_y=center_y,
        )
        self.load_animation("flame", SPRITE, FRAME_SIZE, FRAME_SIZE, FRAMES,
                            crop_box=FLAME_BOX)
        self.set_animation_direction("flame")
        self.scale = SCALE_FACTOR
        self.frame_duration = 0.09
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = 0.0

        self.level = level
        self.player = player

        self.fire_interval = fire_interval   # reload after a shot
        self.bullet_speed = bullet_speed
        self.detection_range = detection_range
        self.aim_duration = aim_duration     # telegraph before firing

        self.state = TurretState.IDLE
        self.line_of_sight = False
        self._timer = 0.0

    def detect_player(self, player) -> bool:
        if player is None or not player.is_controllable:
            return False
        if self._distance_to(player) > self.detection_range:
            return False
        return self.line_of_sight

    def check_line_of_sight(self, player, obstacles):
        """A single obstacle on the axis is enough to blind the turret."""
        if player is None:
            self.line_of_sight = False
            return False

        for obstacle in obstacles:
            if segment_crosses_rect(
                self.center_x, self.center_y,
                player.center_x, player.center_y,
                obstacle.left, obstacle.right, obstacle.bottom, obstacle.top,
            ):
                self.line_of_sight = False
                return False

        self.line_of_sight = True
        return True

    def _distance_to(self, target) -> float:
        return math.hypot(target.center_x - self.center_x,
                          target.center_y - self.center_y)

    def _obstacles(self):
        if self.level is None:
            return []
        return self.level.shot_obstacles()

    def aim(self):
        self.state = TurretState.AIMING
        self._timer = 0.0

    def fire(self):
        self.state = TurretState.FIRING
        self._spawn_bullet()
        self.state = TurretState.COOLDOWN
        self._timer = 0.0

    def update(self, delta_time: float = 1 / 60):
        self._timer += delta_time
        self.check_line_of_sight(self.player, self._obstacles())

        if self.state is TurretState.COOLDOWN:
            if self._timer >= self.fire_interval:
                self.state = TurretState.IDLE
        elif self.state is TurretState.AIMING:
            if not self.detect_player(self.player):
                # Player took cover mid-aim: shot cancelled.
                self.state = TurretState.IDLE
            elif self._timer >= self.aim_duration:
                self.fire()
        elif self.detect_player(self.player):
            self.aim()

        self._refresh_color()
        super().update(delta_time)

    def _refresh_color(self):
        """The flame flares white while aiming: that is the telegraph."""
        if self.state is TurretState.AIMING:
            self.color = AIMING_TINT
        elif self.state is TurretState.COOLDOWN:
            self.color = COOLDOWN_TINT
        else:
            self.color = IDLE_TINT

    def _spawn_bullet(self):
        if self.level is None:
            return

        dx = self.player.center_x - self.center_x
        dy = self.player.center_y - self.center_y
        distance = math.hypot(dx, dy)
        if distance == 0:
            return

        bullet = Bullet(
            center_x=self.center_x,
            center_y=self.center_y,
            direction_x=dx / distance,
            direction_y=dy / distance,
            speed=self.bullet_speed,
        )
        # The speed is already scaled, it comes from self.bullet_speed.
        self.level.scale_to_window(bullet, speeds=False)
        self.level.entities.append(bullet)
