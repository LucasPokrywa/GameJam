import math
from enum import Enum

import arcade
from entities.damage import DeathCause
from entities.entities import Entity

ZOMBIE_COLOR = (95, 145, 75)
TOUGH_ZOMBIE_COLOR = (60, 105, 60)
ATTACKING_ZOMBIE_COLOR = (170, 200, 90)

ZOMBIE_SIZE = 32   # one map tile, like the corpse


class Enemy(Entity):
    """
    Shared enemy base. `damage_type` is read by Player.take_hit() to decide
    which corpse the player leaves behind.
    """

    damage_type = DeathCause.NONE

    def __init__(self, hp=1, requires_weapon=False, **kwargs):
        super().__init__(**kwargs)
        self.hp = hp
        self.requires_weapon = requires_weapon

        # Keeps a multi-frame attack from landing more than once.
        self.last_hit_attack_id = -1

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, player, amount=1) -> bool:
        if self.requires_weapon and not player.is_armed:
            return False
        if self.last_hit_attack_id == player.attack_id:
            return False

        self.last_hit_attack_id = player.attack_id
        self.hp -= amount
        if not self.is_alive:
            self.remove_from_sprite_lists()
        return True


class ZombieState(Enum):
    IDLE = "idle"
    CHASING = "chasing"
    ATTACKING = "attacking"


class Zombie(Enemy):
    """Charges the player and hits on contact; its victim leaves BONES."""

    damage_type = DeathCause.ZOMBIE

    def __init__(self, center_x=0, center_y=0, player=None,
                 speed=115.0, detection_range=240.0, attack_cooldown=0.9,
                 hp=1, requires_weapon=False):
        super().__init__(
            hp=hp,
            requires_weapon=requires_weapon,
            width=ZOMBIE_SIZE,
            height=ZOMBIE_SIZE,
            center_x=center_x,
            center_y=center_y,
        )
        self.player = player
        self.state = ZombieState.IDLE

        self.max_speed = speed
        self.acceleration = speed * 6      # sharp start, no drift
        self.friction = speed * 8

        self.detection_range = detection_range
        self.attack_cooldown = attack_cooldown
        self._time_since_attack = attack_cooldown   # can strike on first contact

        self.color = TOUGH_ZOMBIE_COLOR if requires_weapon else ZOMBIE_COLOR

    def detect_player(self, player) -> bool:
        """A dead or respawning player is not chased."""
        if player is None or not player.is_controllable:
            return False
        return self._distance_to(player) <= self.detection_range

    def _distance_to(self, target) -> float:
        return math.hypot(target.center_x - self.center_x,
                          target.center_y - self.center_y)

    def chase(self, player, delta_time):
        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        distance = math.hypot(dx, dy)
        if distance == 0:
            return

        self.apply_acceleration(dx / distance, dy / distance, delta_time)

    def attack(self, player) -> bool:
        if self._time_since_attack < self.attack_cooldown:
            return False

        self._time_since_attack = 0.0
        self.state = ZombieState.ATTACKING
        return player.take_hit(self)

    def update(self, delta_time: float = 1 / 60):
        self._time_since_attack += delta_time

        if self.player is not None and self.detect_player(self.player):
            if arcade.check_for_collision(self, self.player):
                self.attack(self.player)
                self.apply_friction(delta_time)
            else:
                self.state = ZombieState.CHASING
                self.chase(self.player, delta_time)
        else:
            self.state = ZombieState.IDLE
            self.apply_friction(delta_time)

        self._refresh_color()
        super().update(delta_time)

    def _refresh_color(self):
        """Placeholder until the zombie sprite lands."""
        if self.state is ZombieState.ATTACKING:
            self.color = ATTACKING_ZOMBIE_COLOR
        elif self.requires_weapon:
            self.color = TOUGH_ZOMBIE_COLOR
        else:
            self.color = ZOMBIE_COLOR
