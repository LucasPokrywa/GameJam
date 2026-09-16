import os
import tempfile

import arcade
from PIL import Image


class Entity(arcade.SpriteSolidColor):
    """
    Base class for every game entity. Renders as a coloured rectangle until
    load_animation() replaces that placeholder with real textures.
    """

    def __init__(self, width=40, height=40, color=arcade.color.WHITE, center_x=0, center_y=0):
        # `color` must be passed by keyword: the third positional argument of
        # SpriteSolidColor is center_x, so passing it positionally silently
        # dropped every colour.
        super().__init__(width, height, color=color)
        self.center_x = center_x
        self.center_y = center_y

        # Physics, in px/s and px/s². change_x / change_y are arcade's own
        # velocity attributes.
        self.acceleration = 900.0
        self.friction = 700.0
        self.max_speed = 300.0

        self.animations = {}
        self.current_animation = None
        self.current_frame_index = 0
        self.frame_duration = 0.1
        self.time_since_last_frame = 0.0
        self.animation_playing = True

        # True  -> the entity is kept inside the screen (the player)
        # False -> it is destroyed once fully off screen (a bullet)
        self.clamp_to_bounds = True

    def load_animation(self, name, spritesheet_path, frame_width, frame_height,
                       frame_count, row=0, mirror_horizontal=False, crop_box=None):
        """
        Slice one row of a spritesheet into `frame_count` frames stored under
        `name`.

        - row: which row to read, for sheets stacking several animations.
        - mirror_horizontal: flips each frame, so a 3/4 view can be reused for
          the opposite side without a second file.
        - crop_box: (x0, y0, x1, y1) inside each frame. Spritesheets often pad
          the character with transparency, which would otherwise end up in the
          hit box and make the sprite look tiny once scaled. Use the SAME box
          for every animation of an entity, or it will jitter between them.
        """
        sheet = Image.open(spritesheet_path).convert("RGBA")
        textures = []

        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(frame_count):
                box = (
                    i * frame_width,
                    row * frame_height,
                    (i + 1) * frame_width,
                    (row + 1) * frame_height,
                )
                frame = sheet.crop(box)
                if crop_box is not None:
                    frame = frame.crop(crop_box)
                if mirror_horizontal:
                    frame = frame.transpose(Image.FLIP_LEFT_RIGHT)

                temp_path = os.path.join(temp_dir, f"{name}_{i}.png")
                frame.save(temp_path)
                textures.append(arcade.load_texture(temp_path))

        self.animations[name] = textures

    def sync_hit_box_to_texture(self):
        """
        Rebuilds the hit box from the current texture.

        arcade only refreshes it when the sprite still carries its default
        texture (see Sprite.texture setter), so a SpriteSolidColor that gets a
        real texture keeps its placeholder rectangle and scales it a second
        time. Call this after load_animation() and after setting the final
        width / height.
        """
        if self.texture is None:
            return
        self.hit_box = arcade.hitbox.RotatableHitBox(
            self.texture.hit_box_points,
            position=self.position,
            angle=self.angle,
            scale=self.scale,
        )

    def set_animation_direction(self, name):
        if name not in self.animations or name == self.current_animation:
            return
        self.current_animation = name
        self.current_frame_index = 0
        self.time_since_last_frame = 0.0
        self.texture = self.animations[name][0]

    def set_animation_playing(self, playing: bool):
        """Stopping freezes the animation on its first frame."""
        if not playing and self.animation_playing:
            self.current_frame_index = 0
            self.time_since_last_frame = 0.0
            if self.current_animation:
                self.texture = self.animations[self.current_animation][0]
        self.animation_playing = playing

    def update_animation_frame(self, delta_time: float):
        if not self.current_animation or not self.animation_playing:
            return
        frames = self.animations[self.current_animation]
        self.time_since_last_frame += delta_time
        if self.time_since_last_frame >= self.frame_duration:
            self.time_since_last_frame -= self.frame_duration
            self.current_frame_index = (self.current_frame_index + 1) % len(frames)
            self.texture = frames[self.current_frame_index]

    def apply_friction(self, delta_time: float):
        """Brakes towards zero without changing direction on the way."""
        speed = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if speed == 0:
            return

        braking = self.friction * delta_time
        if braking >= speed:
            self.change_x = 0
            self.change_y = 0
        else:
            self.change_x -= braking * (self.change_x / speed)
            self.change_y -= braking * (self.change_y / speed)

    def apply_acceleration(self, direction_x: float, direction_y: float, delta_time: float):
        """
        Existing velocity is kept and steered progressively, which is what
        gives the drift when changing direction.
        """
        self.change_x += direction_x * self.acceleration * delta_time
        self.change_y += direction_y * self.acceleration * delta_time

        speed = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if speed > self.max_speed:
            ratio = self.max_speed / speed
            self.change_x *= ratio
            self.change_y *= ratio

    def update(self, delta_time: float = 1 / 60):
        """
        Subclasses set change_x / change_y (through apply_acceleration,
        apply_friction or their own AI) then call super().update().
        """
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time
        self.update_animation_frame(delta_time)
