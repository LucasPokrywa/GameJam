import os
import random
from enum import Enum

import arcade
import pyglet
from entities.damage import DeathCause, cause_from_source
from entities.entities import Entity

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "entities", "player")

FRAME_SIZE = 64
RUN_FRAMES = 6
IDLE_FRAMES = 8

DEATH_SHEET = os.path.join(ASSETS_DIR, "Death", "Death.png")
DEATH_FRAMES = 6
FOOTSTEP_INTERVAL = 0.18  # seconds between footstep sounds at normal walking speed (faster)

# (animation, spritesheet, mirrored). No dedicated left-facing sheet: the 3/4
# view is mirrored.
RUN_SHEETS = (
    ("run_down", "Run_F.png", False),
    ("run_up", "Run_Back.png", False),
    ("run_right", "Run_34F.png", False),
    ("run_left", "Run_34F.png", True),
)
IDLE_SHEETS = (
    ("idle_down", "Idle_F.png", False),
    ("idle_up", "Idle_B.png", False),
    ("idle_right", "Idle_34F.png", False),
    ("idle_left", "Idle_34F.png", True),
)

# Same poses, reinforced character: worn while the player carries bones.
ARMED_SUFFIX = "_armed"
ANIMATION_SETS = (
    ("", "Run", "Idle"),
    (ARMED_SUFFIX, "Run_Renforced", "Idle_Renforced"),
)

# The skeleton only covers 16x20 px at the centre of each 64x64 frame; without
# this crop the surrounding emptiness lands in the hit box. Same box for every
# animation, otherwise the character jitters between them.
# Keep the collision width slightly narrower than a 16 px map tile so the
# player can pass through one-tile corridors after the sprite is scaled.
CHARACTER_BOX = (25, 23, 37, 43)
PLAYER_HEIGHT = 32

DYING_DURATION = 0.45
RESPAWN_DURATION = 0.9
BLINK_INTERVAL = 0.1
BURN_DURATION = 3.0
BURN_BLINK_INTERVAL = 0.1
INVULNERABILITY_DURATION = 0.6

ATTACK_COOLDOWN = 0.4
ATTACK_RANGE_RATIO = 1.1   # of the player's own height, so it scales with it

# Open question from the spec, to settle after a playtest.
KEEP_RESISTANCE_ON_DEATH = True
BURNING_COLOR = (255, 120, 30)


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
        self.acceleration = 700.0
        self.friction = 1000.0
        self.max_speed = 220.0
        self.direction = "down"

        self.frame_duration = 0.08

        self._load_animations()

        # Arcade recomputes width/height on every frame change, so `scale` is
        # what must be set, not width/height. Keep a fixed reference scale for
        # all death/respawn transitions so the drowning shrink effect never
        # rewrites the player’s true normal size.
        self._reset_base_scale()

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
        self.was_impaled = False
        self.death_count = 0
        self._state_timer = 0.0
        self._blink_timer = 0.0
        self._invulnerability_timer = 0.0
        self._burn_timer = 0.0
        self._burn_blink_timer = 0.0
        self.is_burning = False
        self.attached_stake = None
        self.on_raft = None
        self.raft_jump_target = None
        self.raft_jump_timer = 0.0
        self.raft_jump_duration = 0.50
        self.raft_jump_base_scale = 1.0

        self.is_armed = False
        self.resistance_bonus = 0
        self._attack_cooldown = 0.0
        self.attack_active = False
        self.attack_id = 0   # read by Enemy.take_damage

        # Called at the moment of death, player still in place.
        self.on_death = None

        try:
            projet_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            death_sound_path = os.path.join(projet_root, "assets", "sounds", "player-dying.mp3")
            if os.path.exists(death_sound_path):
                self._death_sound = arcade.load_sound(death_sound_path)
            else:
                self._death_sound = None
        except Exception:
            self._death_sound = None

        # Load footstep sound (optional)
        try:
            projet_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            specific = os.path.join(projet_root, "assets", "sounds", "footstep-player.ogg")
            generic = os.path.join(projet_root, "assets", "sounds", "footstep.ogg")
            chosen = None
            if os.path.exists(specific):
                chosen = specific
            elif os.path.exists(generic):
                chosen = generic
            if chosen is not None:
                self._footstep_sound = arcade.load_sound(chosen)
            else:
                self._footstep_sound = None
        except Exception:
            self._footstep_sound = None

        self._footstep_timer = 0.0
        self.fire_particles = []
        self._fire_particle_timer = 0.0

    @property
    def is_controllable(self) -> bool:
        return self.state is PlayerState.ALIVE

    @property
    def is_vulnerable(self) -> bool:
        return self.state is PlayerState.ALIVE and self._invulnerability_timer <= 0.0

    def ignite(self):
        """Set the player on fire; the fire kills after a short delay."""
        if not self.is_vulnerable or self.is_burning:
            return False

        self.is_burning = True
        self._burn_timer = BURN_DURATION
        self._burn_blink_timer = 0.0
        self.color = BURNING_COLOR
        self.alpha = 255
        return True

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

        self.was_impaled = False
        self.death_cause = cause_from_source(source)
        self.state = PlayerState.DYING
        self._state_timer = 0.0
        self._death_start_scale = self.base_scale
        self.on_raft = None
        self.raft_jump_target = None
        self.raft_jump_start = None
        self.raft_jump_timer = 0.0
        self.scale = self.base_scale
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
        self.was_impaled = True
        self.state = PlayerState.STAKED
        self.change_x = stake.change_x
        self.change_y = stake.change_y
        self.attack_active = False
        return True

    def crash_into_wall(self):
        """Finish a stake hit when the carried player reaches a wall."""
        if self.state is not PlayerState.STAKED:
            return False

        self.death_cause = DeathCause.DROWNING #pour avoir un corps plateforme
        self.was_impaled = True
        self.attached_stake = None
        self.change_x = 0
        self.change_y = 0
        self.alpha = 255
        self.set_animation_playing(False)
        self.die()
        return True

    def die(self):
        """End of the dying phase: on_death lets the level drop the corpse."""
        self.death_count += 1
        self.is_armed = False
        self._reset_base_scale()
        self.alpha = 255
        self._death_start_scale = self.base_scale
        if not KEEP_RESISTANCE_ON_DEATH:
            self.resistance_bonus = 0

        if self.on_death is not None:
            self.on_death(self)

        try:
            if getattr(self, "_death_sound", None) is not None:
                arcade.play_sound(self._death_sound, volume=0.45)
        except Exception:
            pass
        self.state = PlayerState.DEAD

    def respawn(self, entry_point=None):
        if entry_point is not None:
            self.spawn_x, self.spawn_y = entry_point

        self.center_x = self.spawn_x
        self.center_y = self.spawn_y
        self.change_x = 0
        self.change_y = 0
        self.alpha = 255
        self.is_burning = False
        self.color = arcade.color.WHITE
        self.death_cause = DeathCause.NONE
        self.state = PlayerState.ALIVE
        self.was_impaled = False
        self._reset_base_scale()
        self._death_start_scale = self.base_scale
        self.fire_particles.clear()
        self._invulnerability_timer = INVULNERABILITY_DURATION
        self.set_animation_playing(True)

    def pick_up_bones(self, corpse):
        """Bones are both armour and weapon, as in the pitch."""
        self.resistance_bonus += 1
        self.is_armed = True

    def _reset_base_scale(self):
        # Keep the current window-scaled size as the true reference. The level
        # recalculates `base_scale` with `scale_to_window()`, so overwriting it
        # here with the raw sprite size breaks the respawn sizing.
        if not hasattr(self, "base_scale") or self.base_scale is None:
            self.base_scale = PLAYER_HEIGHT / (CHARACTER_BOX[3] - CHARACTER_BOX[1])
        self.scale = self.base_scale
        self._death_start_scale = self.base_scale

    def _force_base_scale(self):
        self.scale = self.base_scale

    def _scale_scalar(self) -> float:
        scale = self.scale
        if isinstance(scale, (tuple, list)):
            return float(scale[0]) if scale else 1.0
        return float(scale)

    def _start_raft_jump(self, target_x, target_y):
        """Small leap used when bridging across a floating corpse."""
        self.change_x = 0
        self.change_y = 0
        # Keep the current direction key pressed while the jump animation is
        # playing; otherwise the player must release and press it again to
        # continue moving bridge-to-bridge with the same input intent.
        self.raft_jump_start = (self.center_x, self.center_y)
        self.raft_jump_target = (target_x, target_y)
        self.raft_jump_timer = 0.0
        self.raft_jump_base_scale = self.base_scale

    def _raft_jump_target_for_move(self, dx: float, dy: float, step: float):
        """Let the player leave the bridge normally; wall impact is handled by collision push-out."""
        if self.on_raft is None:
            return self.center_x + dx * step, self.center_y + dy * step

        return self.center_x + dx * step, self.center_y + dy * step

    def _update_raft_jump(self, delta_time: float):
        if self.raft_jump_target is None:
            return False

        self.raft_jump_timer += delta_time
        t = min(1.0, self.raft_jump_timer / 0.50)
        base_scale = self.base_scale

        start_x, start_y = self.raft_jump_start
        target_x, target_y = self.raft_jump_target
        self.center_x = start_x + (target_x - start_x) * t
        self.center_y = start_y + (target_y - start_y) * t

        if t <= 0.5:
            scale_t = t / 0.5
            self.scale = base_scale * (1.0 + (1.5 - 1.0) * scale_t)
        else:
            scale_t = (t - 0.5) / 0.5
            self.scale = base_scale * (1.5 - (1.5 - 1.0) * scale_t)

        if self.raft_jump_timer >= 0.50:
            self.center_x, self.center_y = self.raft_jump_target
            self.scale = base_scale
            self.raft_jump_target = None
            self.raft_jump_start = None
            self.raft_jump_timer = 0.0
            self.raft_jump_base_scale = base_scale
            return True

        return False

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
        for suffix, run_dir, idle_dir in ANIMATION_SETS:
            for sheets, folder, frames in ((RUN_SHEETS, run_dir, RUN_FRAMES),
                                           (IDLE_SHEETS, idle_dir, IDLE_FRAMES)):
                for name, filename, mirrored in sheets:
                    self.load_animation(
                        name + suffix,
                        os.path.join(ASSETS_DIR, folder, filename),
                        FRAME_SIZE, FRAME_SIZE, frames,
                        mirror_horizontal=mirrored, crop_box=CHARACTER_BOX,
                    )

        self.has_death_animation = os.path.exists(DEATH_SHEET)
        if self.has_death_animation:
            self.load_animation(
                "death", DEATH_SHEET,
                FRAME_SIZE, FRAME_SIZE, DEATH_FRAMES, crop_box=CHARACTER_BOX,
            )

    def _set_pose(self, name):
        if self.is_armed and name + ARMED_SUFFIX in self.animations:
            name += ARMED_SUFFIX
        self.set_animation_direction(name)

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
            self._force_base_scale()
            self.alpha = 255
            self.on_raft = None
            self.raft_jump_target = None
            self.raft_jump_start = None
            self.raft_jump_timer = 0.0
            self.state = PlayerState.RESPAWNING
            self._state_timer = 0.0
            self._blink_timer = 0.0
        elif self.state is PlayerState.RESPAWNING:
            self._update_respawning(delta_time)
        else:
            self._update_alive(delta_time)

        if self.is_burning and self.state is PlayerState.ALIVE:
            self._update_burning(delta_time)

    def _update_staked(self, delta_time: float):
        super().update(delta_time)

    def _spawn_fire_particles(self):
        if not self.is_burning:
            return

        count = random.randint(2, 4)
        for _ in range(count):
            size = random.uniform(4.0, 8.0)
            life = random.uniform(0.25, 0.7)
            self.fire_particles.append({
                "x": self.center_x + random.uniform(-10.0, 10.0),
                "y": self.center_y + random.uniform(-4.0, 12.0),
                "vx": random.uniform(-30.0, 30.0),
                "vy": random.uniform(35.0, 95.0),
                "size": size,
                "life": life,
                "max_life": life,
                "color": (255, 120, 30),
            })

    def _update_fire_particles(self, delta_time: float):
        self._fire_particle_timer -= delta_time
        if self._fire_particle_timer <= 0.0:
            self._fire_particle_timer = random.uniform(0.02, 0.08)
            self._spawn_fire_particles()

        for particle in list(self.fire_particles):
            particle["x"] += particle["vx"] * delta_time
            particle["y"] += particle["vy"] * delta_time
            particle["vx"] *= 0.98
            particle["vy"] *= 0.94
            particle["vy"] -= 18.0 * delta_time
            particle["life"] -= delta_time

            if particle["life"] <= 0.0:
                self.fire_particles.remove(particle)

    def _draw_fire_particles(self):
        for particle in self.fire_particles:
            opacity = max(0, min(255, int(255 * (particle["life"] / particle["max_life"])) ))
            size = particle["size"]
            rect = pyglet.shapes.Rectangle(
                x=particle["x"] - size / 2,
                y=particle["y"] - size / 2,
                width=size,
                height=size,
                color=(255, 120, 30),
            )
            rect.opacity = opacity
            rect.draw()

    def draw(self):
        super().draw()
        self._draw_fire_particles()

    def _update_burning(self, delta_time: float):
        self._burn_timer -= delta_time
        self._burn_blink_timer += delta_time
        self._update_fire_particles(delta_time)
        if self._burn_blink_timer >= BURN_BLINK_INTERVAL:
            self._burn_blink_timer = 0.0
            self.alpha = 255 if self.alpha != 255 else 70

        if self._burn_timer <= 0.0:
            self.is_burning = False
            self.alpha = 255
            self.fire_particles.clear()
            self.take_hit(DeathCause.TOWER, fatal=True)

    def _update_alive(self, delta_time: float):
        if self.raft_jump_target is not None:
            self._update_raft_jump(delta_time)
            self.alpha = 255 if self._invulnerability_timer <= 0.0 else 140
            return

        if self.on_raft is not None:

            has_move_input = (self.moving_up or self.moving_down
                              or self.moving_left or self.moving_right)
            if self.center_x != self.on_raft.center_x or self.center_y != self.on_raft.center_y:
                if not has_move_input:
                    self._start_raft_jump(self.on_raft.center_x, self.on_raft.center_y)
                    self.alpha = 255 if self._invulnerability_timer <= 0.0 else 140
                    return

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
                if dx != 0 and dy != 0:
                    norm = (dx ** 2 + dy ** 2) ** 0.5
                    dx /= norm
                    dy /= norm
                step = max(self.width, self.height) * 1.25
                target_x, target_y = self._raft_jump_target_for_move(dx, dy, step)
                self._start_raft_jump(target_x, target_y)
                if dx > 0:
                    self.direction = "right"
                elif dx < 0:
                    self.direction = "left"
                elif dy > 0:
                    self.direction = "up"
                elif dy < 0:
                    self.direction = "down"
                self.alpha = 255 if self._invulnerability_timer <= 0.0 else 140
                return

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
            self._set_pose(f"run_{self.direction}")
            # Play footstep periodically while moving
            try:
                self._footstep_timer -= delta_time
                if self._footstep_timer <= 0.0 and getattr(self, "_footstep_sound", None) is not None:
                    arcade.play_sound(self._footstep_sound, volume=0.9)
                    self._footstep_timer = FOOTSTEP_INTERVAL
            except Exception:
                pass
        else:
            self._set_pose(f"idle_{self.direction}")
            self._footstep_timer = 0.0

        self.alpha = 255 if self._invulnerability_timer <= 0.0 else 140

        super().update(delta_time)

    def _update_dying(self, delta_time: float):
        if self.was_impaled:
            self.alpha = 255
            self.set_animation_playing(False)
            self.die()
            return

        self._state_timer += delta_time
        self.set_animation_playing(False)

        # Custom death effect: collapse to zero scale instead of playing the
        # death sprite sequence, for drowning and falling into the void.
        progress = min(1.0, self._state_timer / DYING_DURATION)
        start_scale = getattr(self, "_death_start_scale", self.base_scale)
        self.scale = max(0.0, start_scale * (1.0 - progress))
        self.alpha = int(255 * (1.0 - progress))

        if self._state_timer >= DYING_DURATION:
            self._force_base_scale()
            self.die()

    def _update_respawning(self, delta_time: float):
        self._state_timer += delta_time
        self._blink_timer += delta_time

        if self._blink_timer >= BLINK_INTERVAL:
            self._blink_timer = 0.0
            self.alpha = 0 if self.alpha != 0 else 255

        if self._state_timer >= RESPAWN_DURATION:
            self.respawn()
