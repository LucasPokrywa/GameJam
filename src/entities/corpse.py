import os
from enum import Enum

from entities.damage import DeathCause
from entities.entities import Entity

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "entities", "corpse")

FRAME_SIZE = 16
DISPLAY_SIZE = 8
SCALE_FACTOR = DISPLAY_SIZE / FRAME_SIZE * 8


class CorpseType(Enum):
    WALL = "wall"
    BONES = "bones"
    RAFT = "raft"


class CorpseState(Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    SACRIFICED = "sacrificed"


# Exhaustive on purpose: a new DeathCause must be mapped here explicitly
# rather than silently falling back to some default corpse. None means the
# body is lost and nothing is left behind.
CAUSE_TO_TYPE = {
    DeathCause.TOWER: CorpseType.BONES,
    DeathCause.ZOMBIE: CorpseType.BONES,
    DeathCause.DROWNING: CorpseType.RAFT,
    DeathCause.VOID: None,
    DeathCause.NONE: CorpseType.WALL,
}

SPRITES = {
    CorpseType.WALL: "corpse.png",
    CorpseType.BONES: "bones.png",
    CorpseType.RAFT: "water.png",
}
FALLBACK_SPRITE = "corpse.png"
FALLBACK_TINTS = {
    CorpseType.WALL: (150, 155, 165),
    CorpseType.BONES: (255, 240, 200),
    CorpseType.RAFT: (90, 130, 170),
}


class Corpse(Entity):
    """
    Body left where the player died. Its type follows the cause of death:
    WALL blocks movement and arrows, BONES can be picked up, RAFT floats and
    is walked on.
    """

    def __init__(self, center_x=0, center_y=0, corpse_type=CorpseType.WALL):
        super().__init__(
            width=DISPLAY_SIZE,
            height=DISPLAY_SIZE,
            center_x=center_x,
            center_y=center_y,
        )
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = 0.0

        self.corpse_type = corpse_type
        self.state = CorpseState.ACTIVE
        self.slot = None

        self._load_sprite()

    @classmethod
    def from_death_cause(cls, death_cause, center_x, center_y):
        """None when the cause leaves no body, e.g. falling into the void."""
        corpse_type = CAUSE_TO_TYPE[death_cause]
        if corpse_type is None:
            return None
        return cls(center_x, center_y, corpse_type)

    def _load_sprite(self):
        path = os.path.join(ASSETS_DIR, SPRITES[self.corpse_type])
        tint = None
        if not os.path.exists(path):
            path = os.path.join(ASSETS_DIR, FALLBACK_SPRITE)
            tint = FALLBACK_TINTS[self.corpse_type]

        name = self.corpse_type.value
        self.load_animation(name, path, FRAME_SIZE, FRAME_SIZE, 1)
        self.set_animation_direction(name)
        self.scale = DISPLAY_SIZE / FRAME_SIZE * SCALE_FACTOR

        if tint is not None:
            self.color = tint   # after load_animation, which replaces the texture

    def blocks_movement(self) -> bool:
        return self.corpse_type is CorpseType.WALL and self.state is CorpseState.ACTIVE

    def blocks_projectile(self) -> bool:
        return self.blocks_movement()

    def is_pickable(self) -> bool:
        return self.corpse_type is CorpseType.BONES and self.state is CorpseState.ACTIVE

    def bridges_hazard(self) -> bool:
        """A floating body makes the water under it walkable."""
        return self.corpse_type is CorpseType.RAFT and self.state is CorpseState.ACTIVE

    def is_sacrificable(self) -> bool:
        return self.state is CorpseState.ACTIVE

    def on_player_contact(self, player) -> bool:
        if not self.is_pickable():
            return False

        player.pick_up_bones(self)
        self.state = CorpseState.CONSUMED
        self.remove_from_sprite_lists()
        return True

    def move_to_altar(self, altar) -> bool:
        if not self.is_sacrificable():
            return False

        self.state = CorpseState.SACRIFICED
        if not altar.register(self):
            self.state = CorpseState.ACTIVE
            return False
        return True
