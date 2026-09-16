import os
from enum import Enum

import arcade
from entities.damage import DeathCause, cause_from_source
from entities.entities import Entity

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "entities", "player")

FRAME_SIZE = 64
RUN_FRAMES = 6
IDLE_FRAMES = 8

DEATH_SHEET = os.path.join(ASSETS_DIR, "Death", "Death.png")
DEATH_FRAMES = 6

# The skeleton only covers 16x20 px at the centre of each 64x64 frame; without
# this crop the surrounding emptiness lands in the hit box. Same box for every
# animation, otherwise the character jitters between them.
CHARACTER_BOX = (23, 23, 39, 43)
PLAYER_HEIGHT = 44

DYING_DURATION = 0.45
RESPAWN_DURATION = 0.9
BLINK_INTERVAL = 0.1
INVULNERABILITY_DURATION = 0.6

ATTACK_COOLDOWN = 0.4
ATTACK_RANGE_RATIO = 1.1   # of the player's own height, so it scales with it

# Open question from the spec, to settle after a playtest.
KEEP_RESISTANCE_ON_DEATH = True


class PlayerState(Enum):
    ALIVE = "alive"
    STAKED = "staked"
    DYING = "dying"
    DEAD = "dead"
    RESPAWNING = "respawning"


class Player(Entity):
    """The player, driven by the keyboard (ZQSD or arrow keys)."""

    def __init__(self, center_x=0, center_y=0):
        super().__init__(
            width=CHARACTER_BOX[2] - CHARACTER_BOX[0],
            height=CHARACTER_BOX[3] - CHARACTER_BOX[1],
            center_x=center_x,
            center_y=center_y,
        )
        self.acceleration = 900.0
        self.friction = 700.0
        self.max_speed = 300.0
        self.direction = "down"

        self.frame_duration = 0.08

        self._load_animations()

        # Arcade recomputes width/height on every frame change, so `scale` is
        # what must be set, not width/height.
        self.scale = PLAYER_HEIGHT / (CHARACTER_BOX[3] - CHARACTER_BOX[1])

        self.set_animation_direction("run_down")
        self.set_animation_playing(True)

        self.moving_up = False
        self.moving_down = False
        self.moving_left = False
        self.moving_right = False

        self.spawn_x = center_x
        self.spawn_y = center_y

        self.state = PlayerState.ALIVE
        self.death_cause = DeathCause.NONE
        self.death_count = 0
        self._state_timer = 0.0
        self._blink_timer = 0.0
        self._invulnerability_timer = 0.0
        self.attached_stake = None

        self.is_armed = False
        self.resistance_bonus = 0
        self._attack_cooldown = 0.0
        self.attack_active = False
        self.attack_id = 0   # read by Enemy.take_damage

        # Called at the moment of death, player still in place.
        self.on_death = None

    @property
    def is_controllable(self) -> bool:
        return self.state is PlayerState.ALIVE

    @property
    def is_vulnerable(self) -> bool:
        return self.state is PlayerState.ALIVE and self._invulnerability_timer <= 0.0

    def take_hit(self, source=None, fatal=False):
        """
        A hit absorbed by the resistance bonus does not kill. `fatal` skips
        that absorption: drowning or falling kills whatever the player carries.
        """
        if not self.is_vulnerable:
            return False

        if not fatal and self.resistance_bonus > 0:
            self.resistance_bonus -= 1
            self._invulnerability_timer = INVULNERABILITY_DURATION
            return False

        self.death_cause = cause_from_source(source)
        self.state = PlayerState.DYING
        self._state_timer = 0.0
        self.change_x = 0
        self.change_y = 0
        self.attack_active = False
        self._play_death_animation()
        return True

    def impale_with_stake(self, stake):
        """Attach a stake and let it drive the player into a wall."""
        if not self.is_vulnerable:
            return False

        self.attached_stake = stake
        stake.attached_player = self
        self.state = PlayerState.STAKED
        self.change_x = stake.change_x
        self.change_y = stake.change_y
        self.attack_active = False
        return True

    def crash_into_wall(self):
        """Finish a stake hit when the carried player reaches a wall."""
        if self.state is not PlayerState.STAKED:
            return False

        self.death_cause = DeathCause.DROWNING   # not really, but the corpse is a drowning corpse
        self.attached_stake = None
        self.change_x = 0
        self.change_y = 0
        self.state = PlayerState.DYING
        self._state_timer = 0.0
        self._play_death_animation()
        return True

    def die(self):
        """End of the dying phase: on_death lets the level drop the corpse."""
        self.death_count += 1
        self.is_armed = False
        if not KEEP_RESISTANCE_ON_DEATH:
            self.resistance_bonus = 0

        if self.on_death is not None:
            self.on_death(self)

        self.state = PlayerState.DEAD

    def respawn(self, entry_point=None):
        if entry_point is not None:
            self.spawn_x, self.spawn_y = entry_point

        self.center_x = self.spawn_x
        self.center_y = self.spawn_y
        self.change_x = 0
        self.change_y = 0
        self.alpha = 255
        self.death_cause = DeathCause.NONE
        self.state = PlayerState.ALIVE
        self._invulnerability_timer = INVULNERABILITY_DURATION
        self.set_animation_playing(True)

    def pick_up_bones(self, corpse):
        """Bones are both armour and weapon, as in the pitch."""
        self.resistance_bonus += 1
        self.is_armed = True

    def attack(self) -> bool:
        """The level applies the damage, via attack_active and attack_point()."""
        if not self.is_armed or not self.is_controllable or self._attack_cooldown > 0.0:
            return False

        self._attack_cooldown = ATTACK_COOLDOWN
        self.attack_active = True
        self.attack_id += 1
        return True

    def attack_point(self):
        """Centre of the struck area, in front of the player."""
        reach = self.height * ATTACK_RANGE_RATIO
        offsets = {
            "up": (0, reach),
            "down": (0, -reach),
            "left": (-reach, 0),
            "right": (reach, 0),
        }
        dx, dy = offsets[self.direction]
        return self.center_x + dx, self.center_y + dy

    def _load_animations(self):
        self.load_animation(
            "run_down", os.path.join(ASSETS_DIR, "Run/Run_F.png"),
            FRAME_SIZE, FRAME_SIZE, RUN_FRAMES, crop_box=CHARACTER_BOX,
        )
        self.load_animation(
            "run_up", os.path.join(ASSETS_DIR, "Run/Run_Back.png"),
            FRAME_SIZE, FRAME_SIZE, RUN_FRAMES, crop_box=CHARACTER_BOX,
        )
        self.load_animation(
            "run_right", os.path.join(ASSETS_DIR, "Run/Run_34F.png"),
            FRAME_SIZE, FRAME_SIZE, RUN_FRAMES, crop_box=CHARACTER_BOX,
        )
        # No dedicated left-facing sheet: the 3/4 view is mirrored.
        self.load_animation(
            "run_left", os.path.join(ASSETS_DIR, "Run/Run_34F.png"),
            FRAME_SIZE, FRAME_SIZE, RUN_FRAMES,
            mirror_horizontal=True, crop_box=CHARACTER_BOX,
        )

        self.load_animation(
            "idle_down", os.path.join(ASSETS_DIR, "Idle/Idle_F.png"),
            FRAME_SIZE, FRAME_SIZE, IDLE_FRAMES, crop_box=CHARACTER_BOX,
        )
        self.load_animation(
            "idle_up", os.path.join(ASSETS_DIR, "Idle/Idle_B.png"),
            FRAME_SIZE, FRAME_SIZE, IDLE_FRAMES, crop_box=CHARACTER_BOX,
        )
        self.load_animation(
            "idle_right", os.path.join(ASSETS_DIR, "Idle/Idle_34F.png"),
            FRAME_SIZE, FRAME_SIZE, IDLE_FRAMES, crop_box=CHARACTER_BOX,
        )
        self.load_animation(
            "idle_left", os.path.join(ASSETS_DIR, "Idle/Idle_34F.png"),
            FRAME_SIZE, FRAME_SIZE, IDLE_FRAMES,
            mirror_horizontal=True, crop_box=CHARACTER_BOX,
        )

        self.has_death_animation = os.path.exists(DEATH_SHEET)
        if self.has_death_animation:
            self.load_animation(
                "death", DEATH_SHEET,
                FRAME_SIZE, FRAME_SIZE, DEATH_FRAMES, crop_box=CHARACTER_BOX,
            )

    def _play_death_animation(self):
        if self.has_death_animation:
            self.set_animation_direction("death")
            self.set_animation_playing(True)
        else:
            self.set_animation_playing(False)

    def on_key_press(self, key):
        if key in (arcade.key.UP, arcade.key.Z):
            self.moving_up = True
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.moving_down = True
        elif key in (arcade.key.LEFT, arcade.key.Q):
            self.moving_left = True
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.moving_right = True
        elif key == arcade.key.SPACE:
            self.attack()

    def on_key_release(self, key):
        if key in (arcade.key.UP, arcade.key.Z):
            self.moving_up = False
        elif key in (arcade.key.DOWN, arcade.key.S):
            self.moving_down = False
        elif key in (arcade.key.LEFT, arcade.key.Q):
            self.moving_left = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.moving_right = False

    def update(self, delta_time: float = 1 / 60):
        self._invulnerability_timer = max(0.0, self._invulnerability_timer - delta_time)
        self._attack_cooldown = max(0.0, self._attack_cooldown - delta_time)
        if self._attack_cooldown <= 0.0:
            self.attack_active = False

        if self.state is PlayerState.DYING:
            self._update_dying(delta_time)
        elif self.state is PlayerState.STAKED:
            self._update_staked(delta_time)
        elif self.state is PlayerState.DEAD:
            self.state = PlayerState.RESPAWNING
            self._state_timer = 0.0
            self._blink_timer = 0.0
        elif self.state is PlayerState.RESPAWNING:
            self._update_respawning(delta_time)
        else:
            self._update_alive(delta_time)

    def _update_staked(self, delta_time: float):
        super().update(delta_time)

    def _update_alive(self, delta_time: float):
        dx, dy = 0, 0

        if self.moving_up:
            dy += 1
        if self.moving_down:
            dy -= 1
        if self.moving_left:
            dx -= 1
        if self.moving_right:
            dx += 1

        if dx != 0 or dy != 0:
            # Normalised so diagonals are not faster.
            if dx != 0 and dy != 0:
                norm = (dx ** 2 + dy ** 2) ** 0.5
                dx /= norm
                dy /= norm
            self.apply_acceleration(dx, dy, delta_time)
        else:
            self.apply_friction(delta_time)

        # Only four animations exist, so diagonals favour the horizontal axis,
        # which reads better with the 3/4 view we have.
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
        elif dy > 0:
            self.direction = "up"
        elif dy < 0:
            self.direction = "down"

        # Keeps the run animation from playing while only braking.
        speed = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if speed >= 5:
            self.set_animation_direction(f"run_{self.direction}")
        else:
            self.set_animation_direction(f"idle_{self.direction}")

        self.alpha = 255 if self._invulnerability_timer <= 0.0 else 140

        super().update(delta_time)

    def _update_dying(self, delta_time: float):
        self._state_timer += delta_time
        self.update_animation_frame(delta_time)

        if not self.has_death_animation:
            progress = min(1.0, self._state_timer / DYING_DURATION)
            self.alpha = int(255 * (1.0 - progress))

        if self._state_timer >= DYING_DURATION:
            self.die()

    def _update_respawning(self, delta_time: float):
        self._state_timer += delta_time
        self._blink_timer += delta_time

        if self._blink_timer >= BLINK_INTERVAL:
            self._blink_timer = 0.0
            self.alpha = 0 if self.alpha != 0 else 255

        if self._state_timer >= RESPAWN_DURATION:
            self.respawn()
