from enum import Enum

import arcade
from entities.corpse import CorpseType
from entities.entities import Entity

EMPTY_SLOT_COLORS = {
    CorpseType.WALL: (120, 125, 140),
    CorpseType.BONES: (170, 160, 130),
    CorpseType.RAFT: (80, 110, 145),
}
FILLED_SLOT_COLOR = (200, 170, 80)

SLOT_SIZE = 40   # a 32 px corpse laid on it still overlaps generously
SLOT_SPACING = 64

SLOT_LABELS = {CorpseType.WALL: "mur", CorpseType.BONES: "os",
               CorpseType.RAFT: "radeau"}


class AltarState(Enum):
    LOCKED = "locked"
    PARTIALLY_FILLED = "partially_filled"
    UNLOCKED = "unlocked"


class Slot(Entity):
    """One altar socket, accepting a single corpse type."""

    def __init__(self, center_x, center_y, required_type, size=SLOT_SIZE):
        super().__init__(
            width=size,
            height=size,
            color=EMPTY_SLOT_COLORS[required_type],
            center_x=center_x,
            center_y=center_y,
        )
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = 0.0

        self.required_type = required_type
        self.corpse = None

    @property
    def is_filled(self) -> bool:
        return self.corpse is not None

    def accepts(self, corpse) -> bool:
        return not self.is_filled and corpse.corpse_type is self.required_type

    def fill(self, corpse):
        self.corpse = corpse
        corpse.slot = self
        corpse.center_x = self.center_x
        corpse.center_y = self.center_y
        self.color = FILLED_SLOT_COLOR

    def clear(self):
        if self.corpse is not None:
            self.corpse.slot = None
        self.corpse = None
        self.color = EMPTY_SLOT_COLORS[self.required_type]


class SacrificeAltar:
    """
    The player must lay a specific combination of corpses here to open the
    round's exit.

    Chosen deposit rule: the player dies DIRECTLY on a slot. Switching to
    carrying or pushing corpses only means replacing try_register().
    """

    def __init__(self, center_x, center_y, required_sacrifices,
                 on_unlock=None, scale=1.0):
        self.center_x = center_x
        self.center_y = center_y
        self.scale = scale

        # e.g. {CorpseType.WALL: 1, CorpseType.BONES: 1}
        self.required_sacrifices = dict(required_sacrifices)
        self.current_sacrifices = {type_: 0 for type_ in self.required_sacrifices}

        self.state = AltarState.LOCKED
        self.on_unlock = on_unlock   # typically RoundManager.complete_round

        self.slots = arcade.SpriteList()
        self._build_slots()

    def _build_slots(self):
        expected = []
        for type_, count in self.required_sacrifices.items():
            expected.extend([type_] * count)

        if not expected:
            return

        spacing = SLOT_SPACING * self.scale
        total_width = (len(expected) - 1) * spacing
        start_x = self.center_x - total_width / 2

        for index, type_ in enumerate(expected):
            self.slots.append(Slot(
                center_x=start_x + index * spacing,
                center_y=self.center_y,
                required_type=type_,
                size=round(SLOT_SIZE * self.scale),
            ))

    def try_register(self, corpse) -> bool:
        """Called by the level for every corpse that appears."""
        if not corpse.is_sacrificable():
            return False
        if self._matching_slot(corpse) is None:
            return False
        return corpse.move_to_altar(self)

    def register(self, corpse) -> bool:
        """Called by Corpse.move_to_altar()."""
        slot = self._matching_slot(corpse)
        if slot is None:
            return False

        slot.fill(corpse)
        self.current_sacrifices[corpse.corpse_type] += 1
        self.update_state()
        return True

    def _matching_slot(self, corpse):
        for slot in self.slots:
            if slot.accepts(corpse) and arcade.check_for_collision(slot, corpse):
                return slot
        return None

    def check_condition(self) -> bool:
        return all(
            self.current_sacrifices.get(type_, 0) >= count
            for type_, count in self.required_sacrifices.items()
        )

    def update_state(self):
        previous = self.state

        if self.check_condition():
            self.state = AltarState.UNLOCKED
        elif any(count > 0 for count in self.current_sacrifices.values()):
            self.state = AltarState.PARTIALLY_FILLED
        else:
            self.state = AltarState.LOCKED

        # Only once, when crossing the threshold.
        if self.state is AltarState.UNLOCKED and previous is not AltarState.UNLOCKED:
            self.unlock()

    def unlock(self):
        if self.on_unlock is not None:
            self.on_unlock(self)

    def render_slots(self):
        self.slots.draw()

    def draw(self):
        self.render_slots()

    def progress_text(self) -> str:
        """HUD label, e.g. 'mur 1/1  os 0/1'."""
        return "  ".join(
            f"{SLOT_LABELS[type_]} {self.current_sacrifices.get(type_, 0)}/{count}"
            for type_, count in self.required_sacrifices.items()
        )
