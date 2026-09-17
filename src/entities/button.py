import os

import arcade

from entities.entities import Entity

BUTTON_ASSET = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "entities", "button", "Button.png"
)


class Button(Entity):
    """Pressure switch that opens a door when a monster stands on it."""

    def __init__(self, center_x=0, center_y=0, width=32, height=32,
                 on_press=None, on_release=None, allow_player=True,
                 activators=None):
        super().__init__(width=width, height=height,
                         color=arcade.color.DARK_GRAY,
                         center_x=center_x, center_y=center_y)
        self.acceleration = 0.0
        self.friction = 0.0
        self.max_speed = 0.0
        self.pressed = False
        self.allow_player = allow_player
        self.on_press = on_press
        self.on_release = on_release
        self.activators = activators or []

        self._load_texture()

    def _load_texture(self):
        if not os.path.exists(BUTTON_ASSET):
            return

        sheet = arcade.load_texture(BUTTON_ASSET)
        if sheet is None or sheet.width == 0 or sheet.height == 0:
            return

        # The asset is a 3-frame strip. We use the first and last frame to show
        # the off/on state, while keeping the raw file as the button art.
        self.load_animation("button", BUTTON_ASSET, 16, 16, 3)
        self.set_animation_direction("button")
        self.frame_duration = 0.25
        self.scale = max(1, round((self.width / 16) * 2))
        self.texture = self.animations["button"][0]
        self.sync_hit_box_to_texture()

    def _is_activator(self, sprite):
        if sprite is None or sprite is self:
            return False
        if not self.allow_player and getattr(sprite, "is_controllable", False):
            return False
        if hasattr(sprite, "is_alive") and not sprite.is_alive:
            return False
        return arcade.check_for_collision(self, sprite)

    def _update_visual_state(self):
        if not self.animations:
            return
        index = 2 if self.pressed else 0
        self.texture = self.animations["button"][min(index, len(self.animations["button"]) - 1)]

    def update(self, delta_time: float = 1 / 60, activators=None):
        if activators is None:
            activators = self.activators
        if activators is None:
            activators = []

        active_activators = [sprite for sprite in activators if self._is_activator(sprite)]
        is_pressed = bool(active_activators)
        if is_pressed and not self.pressed:
            self.pressed = True
            self._update_visual_state()
            if self.on_press is not None:
                self.on_press(self)
        elif (not is_pressed) and self.pressed:
            self.pressed = False
            self._update_visual_state()
            if self.on_release is not None:
                self.on_release(self)

    def draw(self):
        self._update_visual_state()
        super().draw()
