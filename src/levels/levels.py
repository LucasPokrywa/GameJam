import math
import os

import arcade
from PIL import Image

from entities.xbow import Xbow
from entities.altar import SacrificeAltar
from entities.corpse import Corpse, CorpseType
from entities.bullet import Bullet
from entities.damage import DeathCause
from entities.enemy import Zombie
from entities.entities import Entity
from entities.player import Player
from entities.stake import Stake
from entities.turret import Turret

PUZZLE1_MAP_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "images", "puzzle1"
)

LEVEL1_MAP_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "images", "map1"
)
LEVEL1_FLOOR = os.path.join(LEVEL1_MAP_DIR, "map_niveau1.png")
LEVEL1_WALL_MASK = os.path.join(LEVEL1_MAP_DIR, "mur_map_niveau1.png")
LEVEL1_WATER = os.path.join(LEVEL1_MAP_DIR, "eau_map_niveau1.png")
LEVEL1_VOID = os.path.join(LEVEL1_MAP_DIR, "vide_map_niveau1.png")
LEVEL1_PROPS = os.path.join(LEVEL1_MAP_DIR, "decors_map_niveau1.png")
LEVEL1_DOOR = os.path.join(LEVEL1_MAP_DIR, "porte_map_niveau1.png")

ListbackgroundLevel1 = [LEVEL1_FLOOR, LEVEL1_WATER, LEVEL1_VOID, LEVEL1_PROPS]
ListMasksLevel1 = [LEVEL1_WALL_MASK, LEVEL1_WATER, LEVEL1_VOID]

PUZZLE0_MAP_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "images", "puzzle0"
)

PUZZLE0_FLOOR = os.path.join(PUZZLE0_MAP_DIR, "Puzzle0.png")
PUZZLE0_WALL_MASK = os.path.join(PUZZLE0_MAP_DIR, "Walls.png")
PUZZLE0_WATER = os.path.join(PUZZLE0_MAP_DIR, "Water.png")
PUZZLE0_VOID = os.path.join(PUZZLE0_MAP_DIR, "Void.png")

ListbackgroundPuzzle0 = [PUZZLE0_FLOOR, PUZZLE0_WATER, None, None]
ListMasksPuzzle0 = [PUZZLE0_WALL_MASK, PUZZLE0_WATER, None]

PUZZLE1_FLOOR = os.path.join(PUZZLE1_MAP_DIR, "Puzzle1.png")
PUZZLE1_WALL_MASK = os.path.join(PUZZLE1_MAP_DIR, "Walls.png")
PUZZLE1_WATER = os.path.join(PUZZLE1_MAP_DIR, "Water.png")
PUZZLE1_VOID = os.path.join(PUZZLE1_MAP_DIR, "Void.png")

ListbackgroundPuzzle1 = [PUZZLE1_FLOOR, PUZZLE1_WATER, PUZZLE1_VOID, None]
ListMasksPuzzle1 = [PUZZLE1_WALL_MASK, PUZZLE1_WATER, PUZZLE1_VOID]

MAP_SIZE = 256   # the map1 PNGs are 256x256
TILE_SIZE = 16   # the artwork is drawn on a 16 px grid, 16x16 tiles

# Everything below is expressed in that 256x256 artwork space and converted
# with world_point(), so the level follows the window instead of assuming the
# 800x600 it was designed in.
#
# The map is square and drawn with a single uniform scale, letterboxed in the
# window: stretching it to the window ratio turned 16 px tiles into rectangles
# (1.78x on a 16:9 screen) and the round holes into ovals.
REFERENCE_SCALE = 600 / MAP_SIZE

# Both boxes are measured on the artwork above, in image coordinates.
DOOR_GAP = (112, 0, 144, 48)      # punched out of the wall mask
DOOR_PANEL = (112, 32, 144, 47)   # stone panel of the door layer

BACKGROUND_COLOR = (0x19, 0x14, 0x26)   # same dark as the maps' border

BURNABLE_GREEN = (70, 190, 80)
BURNABLE_ORANGE = (255, 135, 35)
BURNABLE_BLACK = (10, 10, 10)

# Holes painted into the map1 floor, measured on the artwork: each is a
# 14x14 image-space square. Walking into one drops the player next to
# another, picked at random.
LEVEL1_HOLES = [
    (87, 183),
    (103, 87),
    (119, 119),
    (183, 167),
]
LEVEL1_PAIRED_HOLE = {
            0: 1,  # Trou 1 emmène au Trou 2
            1: 0,  # Trou 2 emmène au Trou 1
            2: 3,  # Trou 3 emmène au Trou 4
            3: 2,  # Trou 4 emmène au Trou 3
}
HOLE_HALF = 7          # image px
HOLE_EXIT_GAP = 3      # image px below the hole, clear of its trigger box


class Level:
    """
    Base class for every level: scenery, entities, and the per-frame rules
    binding them together.
    """

    def __init__(self, window_width, window_height,
                 background_color=BACKGROUND_COLOR):
        self.window_width = window_width
        self.window_height = window_height
        self.background_color = background_color
        self.background = arcade.SpriteList()

        # Uniform scale, and the offset that centres the square map.
        self.map_scale = min(window_width, window_height) / MAP_SIZE
        self.map_size = MAP_SIZE * self.map_scale
        self.map_left = (window_width - self.map_size) / 2
        self.map_bottom = (window_height - self.map_size) / 2

        self.walls = arcade.SpriteList()

        # Lethal ground, read off the map masks: the water drowns the player
        # and leaves a floating body, the void swallows the body with it.
        self.water = arcade.SpriteList()
        self.void = arcade.SpriteList()

        # Kept apart from walls: depending on their type corpses either block
        # the way or get picked up.
        self.corpses = arcade.SpriteList()
        self.burnable_obstacles = arcade.SpriteList()

        # Also held in self.entities; see add_enemy().
        self.enemies = arcade.SpriteList()

        self.entities = arcade.SpriteList()

        self.player = None
        self.altar = None
        self.holes = []      # world coordinates, filled from image space
        self.on_death = None   # wired by main.py to RoundManager.register_death

        self._solid_obstacles_cache = []
        self._shot_obstacles_cache = []
        self._rafts_cache = []

        self.setup()

        # The player notifies the level while still standing where it died,
        # so the corpse drops in the right place.
        if self.player is not None:
            self.player.on_death = self._on_player_death

    def _layer(self, path):
        """Loads one map1 PNG, square and centred in the window."""
        layer = arcade.Sprite(path)
        layer.center_x = self.map_left + self.map_size / 2
        layer.center_y = self.map_bottom + self.map_size / 2
        layer.width = self.map_size
        layer.height = self.map_size
        return layer

    @property
    def sprite_scale(self) -> float:
        """Entities grow with the map they stand on."""
        return self.map_scale / REFERENCE_SCALE

    # Attributes expressed in pixels, or pixels per second, which must grow
    # with the window alongside the sprite itself.
    SCALED_ATTRIBUTES = ("max_speed", "acceleration", "friction",
                         "detection_range", "bullet_speed")

    def scale_to_window(self, sprite, speeds=True):
        factor = self.sprite_scale
        if factor == 1.0:
            return sprite

        current = sprite.scale
        base = current[0] if hasattr(current, "__getitem__") else current
        sprite.scale = base * factor

        if not speeds:
            return sprite

        for name in self.SCALED_ATTRIBUTES:
            value = getattr(sprite, name, None)
            if value:
                setattr(sprite, name, value * factor)
        return sprite

    def world_point(self, image_x, image_y):
        """Turns a point of the 256x256 artwork into world coordinates."""
        return (
            self.map_left + image_x * self.map_scale,
            self.map_bottom + (MAP_SIZE - image_y) * self.map_scale,
        )

    def world_length(self, image_length) -> float:
        return image_length * self.map_scale

    def snap_to_tile(self, sprite):
        """
        Centres the sprite on the map tile it stands on, and sizes it to fill
        that tile exactly.

        The size matters as much as the position: _standing_on() tests a
        single point, so a body smaller than its tile would leave a seam of
        unbridged water between two neighbours.
        """
        tile = self.world_length(TILE_SIZE)
        column = int((sprite.center_x - self.map_left) // tile)
        row = int((sprite.center_y - self.map_bottom) // tile)

        sprite.width = tile
        sprite.height = tile
        sprite.center_x = self.map_left + (column + 0.5) * tile
        sprite.center_y = self.map_bottom + (row + 0.5) * tile

        # The default hit box hugs the opaque pixels, and the corpse art is
        # drawn inside its frame, so left/right/bottom/top would cover half a
        # tile. Built last: a fresh HitBox does not inherit position or scale.
        texture = sprite.texture
        if texture is not None:
            half_w, half_h = texture.width / 2, texture.height / 2
            sprite.hit_box = arcade.hitbox.HitBox(
                ((-half_w, -half_h), (half_w, -half_h),
                 (half_w, half_h), (-half_w, half_h)),
                position=(sprite.center_x, sprite.center_y),
                scale=(sprite.scale_x, sprite.scale_y),
            )
        return sprite

    def world_rect(self, image_box):
        """Turns a box of the 256x256 artwork into (center_x, center_y, w, h)."""
        x0, y0, x1, y1 = image_box
        center_x, center_y = self.world_point((x0 + x1) / 2, (y0 + y1) / 2)
        return center_x, center_y, self.world_length(x1 - x0), self.world_length(y1 - y0)

    def _load_level_scenery(self, Listbackground, ListMasks, gap=None):
        """
        Map1 layers, then the opaque pixels of its masks turned into walls and
        into lethal ground. `gap` (image coordinates) is ignored from the wall
        mask, which is how the doorway gets punched through the top wall.

        The water and void PNGs are both the artwork and the collision mask,
        so repainting them is enough to move a hazard.
        """
        self.background.append(self._layer(Listbackground[0]))
        # Props before the hazards: a rock drawn over the pit made a lethal
        # tile look like solid ground.
        if Listbackground[3]:
            self.background.append(self._layer(Listbackground[3]))
        if Listbackground[1]:
            self.background.append(self._layer(Listbackground[1]))
        if Listbackground[2]:
            self.background.append(self._layer(Listbackground[2]))

        self._mask_to_sprites(ListMasks[0], self.walls, skip=gap)
        if ListMasks[1]:
            self._mask_to_sprites(ListMasks[1], self.water)
        if ListMasks[2]:
            self._mask_to_sprites(ListMasks[2], self.void)

    def _mask_runs(self, path, skip=None):
        """
        Opaque pixels of a mask, as few image-space boxes as possible:
        horizontal runs, stacked vertically while they keep the same span.
        `skip` is a box ignored from the mask.
        """
        mask = Image.open(path).convert("RGBA")
        mask_width, mask_height = mask.size
        open_runs = {}

        def is_set(x, y):
            if skip is not None:
                x0, y0, x1, y1 = skip
                if x0 <= x < x1 and y0 <= y < y1:
                    return False
            return mask.getpixel((x, y))[3] != 0

        for y in range(mask_height):
            x = 0
            while x < mask_width:
                while x < mask_width and not is_set(x, y):
                    x += 1
                start = x
                while x < mask_width and is_set(x, y):
                    x += 1
                if start == x:
                    continue

                end = x
                key = (start, end)
                run = open_runs.get(key)
                if run is not None and run[3] == y:
                    run[3] = y + 1
                else:
                    if run is not None:
                        yield tuple(run)
                    open_runs[key] = [start, end, y, y + 1]

        for run in open_runs.values():
            yield tuple(run)

    def _mask_to_sprites(self, path, sprites, skip=None):
        """Fills `sprites` with invisible rectangles covering a mask."""
        for start_x, end_x, start_y, end_y in self._mask_runs(path, skip):
            if end_y <= start_y:
                continue

            # Rounded up: rounding down leaves a sub-pixel seam between two
            # stacked runs, and _standing_on() tests a single point, so the
            # player could stand in the seam and survive the pit.
            rect = arcade.SpriteSolidColor(
                max(1, math.ceil(self.world_length(end_x - start_x))),
                max(1, math.ceil(self.world_length(end_y - start_y))),
                color=arcade.color.WHITE,
            )
            rect.center_x, rect.center_y = self.world_point(
                (start_x + end_x) / 2, (start_y + end_y) / 2
            )
            rect.alpha = 0
            sprites.append(rect)
        return sprites

    def is_complete(self) -> bool:
        """
        Whether the round objective is met. Never, by default: such a round
        can only end on the clock. Concrete levels override this.
        """
        return False

    def setup(self):
        """Empty room with the player at its centre; override in subclasses."""
        self.player = Player(center_x=self.window_width // 2,
                             center_y=self.window_height // 2)
        self.scale_to_window(self.player)
        self.entities.append(self.player)

    def update(self, delta_time: float):
        self._refresh_obstacles()

        # Copy of the list: a Turret may append a Bullet during its update,
        # which would break iterating directly.
        for entity in list(self.entities):
            entity.update(delta_time)

        self._handle_bullet_collisions()
        self._handle_burnable_obstacle_collisions()
        self._handle_player_attack()
        self._handle_bone_pickup()
        self._resolve_solid_collisions()
        self._handle_hazard_collisions()
        self._keep_enemies_off_hazards()
        self._handle_hole_collisions()

        margin = 60
        for entity in list(self.entities):
            if entity.clamp_to_bounds:
                if entity.left < 0:
                    entity.left = 0
                if entity.right > self.window_width:
                    entity.right = self.window_width
                if entity.bottom < 0:
                    entity.bottom = 0
                if entity.top > self.window_height:
                    entity.top = self.window_height
            else:
                off_screen = (
                    entity.right < -margin
                    or entity.left > self.window_width + margin
                    or entity.top < -margin
                    or entity.bottom > self.window_height + margin
                )
                if off_screen:
                    entity.remove_from_sprite_lists()

    def _refresh_obstacles(self):
        walls = list(self.walls)
        burnable = [o for o in self.burnable_obstacles if o.blocks_movement()]
        self._solid_obstacles_cache = walls + burnable + [c for c in self.corpses if c.blocks_movement()]
        self._shot_obstacles_cache = walls + burnable + [c for c in self.corpses if c.blocks_projectile()]
        self._rafts_cache = [c for c in self.corpses if c.bridges_hazard()]

    def solid_obstacles(self):
        return self._solid_obstacles_cache

    def rafts(self):
        """Bodies floating on the water, walkable for as long as they last."""
        return self._rafts_cache

    def shot_obstacles(self):
        """Read by the turrets every frame for their line of sight."""
        return self._shot_obstacles_cache

    def add_enemy(self, enemy):
        """entities updates and draws it, enemies makes it collide."""
        self.scale_to_window(enemy)
        # Last position clear of lethal ground; see _keep_enemies_off_hazards().
        enemy.safe_point = (enemy.center_x, enemy.center_y)
        self.entities.append(enemy)
        self.enemies.append(enemy)
        return enemy

    def _handle_bullet_collisions(self):
        obstacles = self.shot_obstacles()
        bullets = [e for e in self.entities if isinstance(e, Bullet)]

        for bullet in bullets:
            if any(arcade.check_for_collision(bullet, o) for o in obstacles):
                bullet.remove_from_sprite_lists()
                continue

            if self.player is None or not self.player.is_vulnerable:
                continue

            if arcade.check_for_collision(bullet, self.player):
                self.player.ignite()
                bullet.remove_from_sprite_lists()
                break   # one bullet is enough to land the hit

        stakes = [e for e in self.entities if isinstance(e, Stake)]
        for stake in stakes:
            if stake.attached_player is not None:
                continue

            if any(arcade.check_for_collision(stake, o) for o in obstacles):
                stake.remove_from_sprite_lists()
                continue

            if self.player is not None and self.player.is_vulnerable \
                    and arcade.check_for_collision(stake, self.player):
                self.player.impale_with_stake(stake)

    def _handle_burnable_obstacle_collisions(self):
        if self.player is None or not self.player.is_burning:
            return

        for obstacle in self.burnable_obstacles:
            if (obstacle.blocks_movement()
                    and arcade.check_for_collision(self.player, obstacle)):
                obstacle.start_burning()

    def _handle_player_attack(self):
        if self.player is None or not self.player.attack_active:
            return

        hit_x, hit_y = self.player.attack_point()
        radius = self.player.height
        for enemy in list(self.enemies):
            if math.hypot(enemy.center_x - hit_x, enemy.center_y - hit_y) <= radius:
                enemy.take_damage(self.player)

    def _handle_bone_pickup(self):
        if self.player is None or not self.player.is_controllable:
            return

        for corpse in list(self.corpses):
            if corpse.is_pickable() and arcade.check_for_collision(self.player, corpse):
                corpse.on_player_contact(self.player)

    @staticmethod
    def _standing_on(sprite, grounds):
        """
        The first of `grounds` the sprite's centre stands on.

        Testing a single point, rather than asking the sprite to fit inside a
        rectangle, is what makes this independent of how the mask got sliced:
        a pool is cut into horizontal runs, and a 44 px body never fits inside
        an 8 px run. Same convention as _handle_hole_collisions().

        Half-open on the top and right edges, to match the floor division in
        snap_to_tile(): otherwise a body drowned on the top edge of a pool is
        snapped onto the shore tile above and bridges nothing.
        """
        x, y = sprite.center_x, sprite.center_y
        for ground in grounds:
            if ground.left <= x < ground.right and ground.bottom <= y < ground.top:
                return ground
        return None

    def _handle_hazard_collisions(self):
        """
        Water and void kill on contact, whatever resistance the player has
        picked up. A body floating on the water cancels it, which is how a
        pool gets bridged; the void keeps the body, so it can never be.
        """
        if self.player is None or not self.player.is_controllable:
            return

        if self._standing_on(self.player, self.water) is not None:
            if self._standing_on(self.player, self.rafts()) is None:
                self.player.take_hit(DeathCause.DROWNING, fatal=True)
            return

        if self._standing_on(self.player, self.void) is not None:
            if self._standing_on(self.player, self.rafts()) is None:
                self.player.take_hit(DeathCause.VOID, fatal=True)
            return

    def _keep_enemies_off_hazards(self):
        """
        Enemies neither drown nor fall: they are sent back to where they last
        stood on solid ground.

        A point test and a rewind, not the _push_out() used for walls: lethal
        ground is sliced into thin horizontal runs, and pushing along the
        smallest overlap would slide an enemy sideways down a run instead of
        stopping it at the shore.
        """
        for enemy in list(self.enemies):
            if (self._standing_on(enemy, self.water) is not None
                    or self._standing_on(enemy, self.void) is not None):
                enemy.center_x, enemy.center_y = enemy.safe_point
                enemy.change_x = 0
                enemy.change_y = 0
            else:
                enemy.safe_point = (enemy.center_x, enemy.center_y)

    def _handle_hole_collisions(self):
        if self.player is None or not self.player.is_controllable:
            return

        half = self.world_length(HOLE_HALF)
        px, py = self.player.center_x, self.player.center_y
        for index, (x, y) in enumerate(self.holes):
            if abs(px - x) <= half and abs(py - y) <= half:
                self.teleport_out_of_hole(index)
                return
    
    def hole_exit(self, index):
        """Just below a hole, clear of its trigger box."""
        x, y = self.holes[index]
        half = self.world_length(HOLE_HALF)
        gap = self.world_length(HOLE_EXIT_GAP)
        return x, y - (half + self.player.height / 2 + gap)

    def teleport_out_of_hole(self, entered_index):
        """Drops the player below another hole, never the one just entered."""
        if entered_index in LEVEL1_PAIRED_HOLE:
            target = LEVEL1_PAIRED_HOLE[entered_index]
            self.player.center_x, self.player.center_y = self.hole_exit(target)

    def _on_player_death(self, player):
        """
        The cause of death decides the corpse type, and whether there is a
        body at all: the void keeps it.
        """
        corpse = Corpse.from_death_cause(player.death_cause,
                                         player.center_x, player.center_y)

        if self.on_death is not None:
            self.on_death()

        if corpse is None:
            return

        self.scale_to_window(corpse)

        # A floating body is a walkable tile of the pool, so it has to line up
        # with the water it bridges rather than with where the player fell.
        if corpse.bridges_hazard():
            self.snap_to_tile(corpse)

        self.corpses.append(corpse)
        self._refresh_obstacles()

        # Dying right on an altar slot lays the body there.
        if self.altar is not None:
            self.altar.try_register(corpse)

    def _resolve_solid_collisions(self):
        """A zombie bumps into a wall corpse, exactly like the player does."""
        obstacles = self.solid_obstacles()

        if self.player is not None:
            if self.player.attached_stake is not None:
                if any(arcade.check_for_collision(self.player, wall)
                       for wall in self.walls):
                    stake = self.player.attached_stake
                    self.player.crash_into_wall()
                    if stake is not None:
                        stake.remove_from_sprite_lists()
            elif self.player.is_controllable:
                self._push_out(self.player, obstacles)

        for enemy in list(self.enemies):
            self._push_out(enemy, obstacles)

    def _push_out(self, sprite, obstacles) -> bool:
        """Pushes the sprite out along the axis of smallest overlap."""
        touched = False

        for obstacle in obstacles:
            if obstacle is sprite or not arcade.check_for_collision(sprite, obstacle):
                continue
            touched = True

            overlap_x = min(sprite.right, obstacle.right) - max(sprite.left, obstacle.left)
            overlap_y = min(sprite.top, obstacle.top) - max(sprite.bottom, obstacle.bottom)

            if overlap_x < overlap_y:
                if sprite.center_x < obstacle.center_x:
                    sprite.center_x -= overlap_x
                else:
                    sprite.center_x += overlap_x
                sprite.change_x = 0
            else:
                if sprite.center_y < obstacle.center_y:
                    sprite.center_y -= overlap_y
                else:
                    sprite.center_y += overlap_y
                sprite.change_y = 0

        return touched

    def draw(self):
        self.background.draw(pixelated=True)
        if self.altar is not None:
            self.altar.draw()
        self.walls.draw(pixelated=True)
        self.corpses.draw(pixelated=True)
        self.entities.draw(pixelated=True)


class Door(Entity):
    """
    Round exit, solid until the altar is filled. Invisible like the other
    walls: `closed_layer` is what shows it, and drops with it. Levels with no
    door artwork pass none.
    """

    def __init__(self, center_x, center_y, width, height, closed_layer=None):
        super().__init__(width=int(width), height=int(height),
                         center_x=center_x, center_y=center_y)
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = 0.0
        self.alpha = 0
        self.closed_layer = closed_layer
        self.is_open = False

    def open(self):
        if self.is_open:
            return
        self.is_open = True
        self.remove_from_sprite_lists()
        if self.closed_layer is not None:
            self.closed_layer.remove_from_sprite_lists()


class BurnableObstacle(Entity):
    """A solid green block that burns away when touched by a burning player."""

    GREEN_DURATION = 0.35
    ORANGE_DURATION = 0.35
    FADE_DURATION = 0.8

    def __init__(self, center_x, center_y, width, height):
        super().__init__(width=int(width), height=int(height),
                         color=BURNABLE_GREEN, center_x=center_x,
                         center_y=center_y)
        self.phase = "green"
        self.phase_timer = 0.0
        self.is_destroyed = False
        self.alpha = 255

    def blocks_movement(self) -> bool:
        return not self.is_destroyed

    def start_burning(self):
        if self.phase != "green":
            return
        self.phase = "orange"
        self.phase_timer = 0.0

    @staticmethod
    def _lerp_color(start, end, progress):
        return tuple(round(a + (b - a) * progress)
                     for a, b in zip(start, end))

    def update(self, delta_time: float):
        if self.is_destroyed:
            return

        self.phase_timer += delta_time
        if self.phase == "green":
            self.color = BURNABLE_GREEN
        elif self.phase == "orange":
            progress = min(1.0, self.phase_timer / self.ORANGE_DURATION)
            self.color = self._lerp_color(BURNABLE_GREEN, BURNABLE_ORANGE,
                                          progress)
            if self.phase_timer >= self.ORANGE_DURATION:
                self.phase = "black"
                self.phase_timer = 0.0
        elif self.phase == "black":
            progress = min(1.0, self.phase_timer / self.FADE_DURATION)
            self.color = self._lerp_color(BURNABLE_ORANGE, BURNABLE_BLACK,
                                          progress)
            self.alpha = round(255 * (1.0 - progress))
            if self.phase_timer >= self.FADE_DURATION:
                self.is_destroyed = True
                self.remove_from_sprite_lists()

        self.update_animation_frame(delta_time)


# Image-space placements, checked against the walls, the holes and the
# water; see tests/test_level1.py.
LEVEL1_SPAWN = (128, 200)
LEVEL1_ALTAR = (64, 128)
LEVEL1_TURRETS = ((64, 68), (198, 68))
LEVEL1_ZOMBIE = (147, 128)
LEVEL1_TOUGH_ZOMBIE = (198, 192)


class Level1(Level):
    """
    First round on map1: two turrets, two zombies, the altar on the left and
    the top door as the exit. Filling the altar opens it; walking through it
    ends the round.
    """

    def setup(self):
        self._load_level_scenery(ListbackgroundLevel1, ListMasksLevel1, gap=DOOR_GAP)

        # Closed state: the door layer covers the corridor the floor paints.
        closed_layer = self._layer(LEVEL1_DOOR)
        self.background.append(closed_layer)

        self.door = Door(*self.world_rect(DOOR_PANEL), closed_layer)
        self.walls.append(self.door)

        self.holes = [self.world_point(x, y) for x, y in LEVEL1_HOLES]

        self.player = Player(*self.world_point(*LEVEL1_SPAWN))
        self.scale_to_window(self.player)
        self.entities.append(self.player)

        altar_x, altar_y = self.world_point(*LEVEL1_ALTAR)
        self.altar = SacrificeAltar(
            center_x=altar_x,
            center_y=altar_y,
            required_sacrifices={CorpseType.WALL: 1, CorpseType.BONES: 1},
            on_unlock=self._open_door,
            scale=self.sprite_scale,
        )

        for point in LEVEL1_TURRETS:
            x, y = self.world_point(*point)
            self.entities.append(self.scale_to_window(Turret(
                center_x=x, center_y=y,
                level=self, player=self.player,
                fire_interval=1.4, bullet_speed=330,
            )))

        self.add_enemy(Zombie(*self.world_point(*LEVEL1_ZOMBIE),
                              player=self.player))
        self.add_enemy(Zombie(
            *self.world_point(*LEVEL1_TOUGH_ZOMBIE), player=self.player,
            hp=2, requires_weapon=True, detection_range=140.0,
        ))

        self.round_complete = False

        self._player_text = arcade.Text("", 12, 12, arcade.color.LIGHT_GRAY, 12)

    def is_complete(self) -> bool:
        return self.round_complete

    def _open_door(self, altar):
        self.door.open()

    def update(self, delta_time: float):
        super().update(delta_time)

        if self.round_complete or not self.door.is_open:
            return

        if (self.player.center_y >= self.door.bottom
                and self.door.left <= self.player.center_x <= self.door.right):
            self.round_complete = True

    def draw(self):
        super().draw()

        # L'objectif (sacrifices) est affiché par le HUD (ui.draw_hud) en haut à
        # droite. Ici on ne garde que le récap joueur en bas à gauche.
        self._player_text.text = (
            f"Morts : {self.player.death_count}    Os : {self.player.resistance_bonus}"
        )
        self._player_text.draw()

PUZZLE1_SPAWN = (128, 200)
PUZZLE1_DOOR = (240, 136, 16, 16)
PUZZLE1_BURNABLE = (128, 48, 16, 96)
PUZZLE1_TURRETS = ((92, 86),)

class Puzzle1(Level):
    """
    First round on map1: two turrets, two zombies, the altar on the left and
    the top door as the exit. Filling the altar opens it; walking through it
    ends the round.
    """

    def setup(self):
        self._load_level_scenery(ListbackgroundPuzzle1, ListMasksPuzzle1, gap=DOOR_GAP)

        self.player = Player(*self.world_point(*PUZZLE1_SPAWN))
        self.scale_to_window(self.player)
        self.entities.append(self.player)

        self.round_complete = False

        self._objective_text = arcade.Text("", 12, self.window_height - 22,
                                           arcade.color.WHITE, 12)
        self._player_text = arcade.Text("", 12, 12, arcade.color.LIGHT_GRAY, 12)

        obstacle_x, obstacle_y, obstacle_width, obstacle_height = PUZZLE1_BURNABLE
        obstacle = BurnableObstacle(
            *self.world_point(obstacle_x, obstacle_y),
            self.world_length(obstacle_width),
            self.world_length(obstacle_height),
        )
        self.burnable_obstacles.append(obstacle)
        self.entities.append(obstacle)

        door_x, door_y, door_width, door_height = PUZZLE1_DOOR
        center_x, center_y = self.world_point(door_x, door_y)
        self.door = Door(
            center_x,
            center_y,
            self.world_length(door_width),
            self.world_length(door_height),
        )

    
        x, y = self.world_point(14.5*16, 10.5*16)
        self.entities.append(self.scale_to_window(Xbow(
        center_x=x, center_y=y,
        level=self, player=self.player,
        fire_interval=1.4, bullet_speed=330, orientation="west"
        )))

        for point in PUZZLE1_TURRETS:
            x, y = self.world_point(*point)
            self.entities.append(self.scale_to_window(Turret(
                center_x=x, center_y=y,
                level=self, player=self.player,
                fire_interval=1.4, bullet_speed=330,
            )))

    def is_complete(self) -> bool:
        return self.round_complete

    def update(self, delta_time: float):
        super().update(delta_time)
        if (self.player.center_y >= self.door.bottom
                and self.door.left <= self.player.center_x <= self.door.right):
            self.round_complete = True
                

    def draw(self):
        super().draw()

        self._player_text.text = (
            f"Morts : {self.player.death_count}    Os : {self.player.resistance_bonus}"
        )
        self._player_text.draw()

PUZZLE0_SPAWN = (120, 200)

class Puzzle0(Level):
    """
    First round on map1: two turrets, two zombies, the altar on the left and
    the top door as the exit. Filling the altar opens it; walking through it
    ends the round.
    """

    def setup(self):
        self._load_level_scenery(ListbackgroundPuzzle0, ListMasksPuzzle0, gap=DOOR_GAP)

        self.player = Player(*self.world_point(*PUZZLE0_SPAWN))
        self.scale_to_window(self.player)
        self.entities.append(self.player)

        self.round_complete = False

        self._objective_text = arcade.Text("", 12, self.window_height - 22,
                                           arcade.color.WHITE, 12)
        self._player_text = arcade.Text("", 12, 12, arcade.color.LIGHT_GRAY, 12)

        center_x, center_y, width, height = self.world_rect((120, 24, 16, 16))
        self.door = Door(center_x, center_y, width, height)

    def is_complete(self) -> bool:
        return self.round_complete

    def update(self, delta_time: float):
        super().update(delta_time)
        if (self.player.center_y >= self.door.bottom
                and self.door.left <= self.player.center_x <= self.door.right):
            self.round_complete = True
        

    def draw(self):
        super().draw()

        self._player_text.text = (
            f"Morts : {self.player.death_count}    Os : {self.player.resistance_bonus}"
        )
        self._player_text.draw()


class TurretDemoLevel(Level):
    """Minimal example of wiring a turret into a level."""

    def setup(self):
        self._load_level_scenery(ListbackgroundLevel1, ListMasksLevel1, gap=DOOR_GAP)
        self.player = Player(center_x=self.window_width // 2, center_y=150)
        self.entities.append(self.player)

        self.entities.append(Turret(
            center_x=self.window_width // 2,
            center_y=self.window_height - 200,
            level=self,
            player=self.player,
            fire_interval=1.2,
            bullet_speed=350,
        ))
