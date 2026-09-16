from enum import Enum


class DeathCause(Enum):
    """
    What killed the player. It decides which corpse is left behind, so every
    entity that can damage the player declares one as `damage_type`.
    """

    TOWER = "tower"
    ZOMBIE = "zombie"
    NONE = "none"


def cause_from_source(source) -> DeathCause:
    """
    Raises rather than guessing: a damage source with a missing or malformed
    `damage_type` is a programming error, and silently defaulting it would
    hand the player the wrong corpse type.
    """
    if isinstance(source, DeathCause):
        return source
    if source is None:
        return DeathCause.NONE

    cause = getattr(source, "damage_type", None)
    if not isinstance(cause, DeathCause):
        raise TypeError(
            f"{type(source).__name__}.damage_type must be a DeathCause, got {cause!r}"
        )
    return cause
