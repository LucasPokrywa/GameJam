import os
import tempfile

import arcade
from PIL import Image


class Entity(arcade.SpriteSolidColor):
    """
    Classe de base pour toutes les entités du jeu (joueur, ennemis, objets...).

    Hérite de arcade.SpriteSolidColor pour avoir un rendu simple (rectangle
    coloré) par défaut, tant qu'aucune animation n'est chargée. Dès qu'une
    animation est chargée via load_animation(), elle remplace ce placeholder.
    """

    def __init__(self, width=40, height=40, color=arcade.color.WHITE, center_x=0, center_y=0):
        super().__init__(width, height, color)
        self.center_x = center_x
        self.center_y = center_y

        # --- Paramètres physiques (px/s et px/s²) ---
        # self.change_x / self.change_y sont des attributs natifs d'arcade.Sprite :
        # ils représentent la vélocité actuelle de l'entité.
        self.acceleration = 900.0   # accélération appliquée quand l'entité "pousse" dans une direction
        self.friction = 700.0       # décélération appliquée quand rien ne pousse (freinage naturel)
        self.max_speed = 300.0      # vitesse maximale atteignable

        # --- Animation ---
        self.animations = {}            # nom -> liste de arcade.Texture
        self.current_animation = None   # nom de l'animation actuellement affichée
        self.current_frame_index = 0
        self.frame_duration = 0.1       # secondes passées sur chaque frame
        self.time_since_last_frame = 0.0
        self.animation_playing = True   # si False, l'animation reste figée sur sa frame courante

    def load_animation(self, name, spritesheet_path, frame_width, frame_height,
                        frame_count, row=0, miroir_horizontal=False):
        """
        Découpe une ligne d'une spritesheet en frame_count frames de taille
        frame_width x frame_height, et les enregistre sous le nom `name`.

        - row : index de la ligne à utiliser (0 = première ligne), utile si
          ta feuille contient plusieurs animations empilées verticalement.
        - miroir_horizontal : retourne chaque frame horizontalement. Pratique
          pour réutiliser un sprite "3/4 face" comme animation du côté opposé
          sans avoir besoin d'un fichier séparé.
        """
        feuille = Image.open(spritesheet_path).convert("RGBA")
        textures = []

        with tempfile.TemporaryDirectory() as dossier_temp:
            for i in range(frame_count):
                boite = (
                    i * frame_width,
                    row * frame_height,
                    (i + 1) * frame_width,
                    (row + 1) * frame_height,
                )
                frame = feuille.crop(boite)
                if miroir_horizontal:
                    frame = frame.transpose(Image.FLIP_LEFT_RIGHT)

                chemin_temp = os.path.join(dossier_temp, f"{name}_{i}.png")
                frame.save(chemin_temp)
                textures.append(arcade.load_texture(chemin_temp))

        self.animations[name] = textures

    def set_animation_direction(self, name):
        """
        Change l'animation affichée (ex : le joueur change de direction).
        Ne fait rien si `name` est déjà l'animation en cours ou n'existe pas.
        """
        if name not in self.animations or name == self.current_animation:
            return
        self.current_animation = name
        self.current_frame_index = 0
        self.time_since_last_frame = 0.0
        self.texture = self.animations[name][0]

    def set_animation_playing(self, playing: bool):
        """
        Démarre/arrête l'avancement des frames. Quand on arrête (playing=False),
        l'animation se fige sur sa première frame (effet "idle" simple, en
        attendant d'avoir de vraies animations d'idle dédiées).
        """
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
        """
        Réduit progressivement la vélocité vers 0 (freinage), sans changer sa
        direction avant qu'elle n'atteigne 0. À appeler quand l'entité ne
        reçoit plus d'impulsion (plus d'input, plus de force).
        """
        vitesse = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if vitesse == 0:
            return

        freinage = self.friction * delta_time
        if freinage >= vitesse:
            self.change_x = 0
            self.change_y = 0
        else:
            self.change_x -= freinage * (self.change_x / vitesse)
            self.change_y -= freinage * (self.change_y / vitesse)

    def apply_acceleration(self, direction_x: float, direction_y: float, delta_time: float):
        """
        Accélère l'entité dans une direction donnée (vecteur normalisé),
        puis limite le résultat à max_speed. La vélocité existante est
        conservée et progressivement réorientée : c'est ce qui donne
        l'effet "inertie" quand on change de direction.
        """
        self.change_x += direction_x * self.acceleration * delta_time
        self.change_y += direction_y * self.acceleration * delta_time

        vitesse = (self.change_x ** 2 + self.change_y ** 2) ** 0.5
        if vitesse > self.max_speed:
            echelle = self.max_speed / vitesse
            self.change_x *= echelle
            self.change_y *= echelle

    def update(self, delta_time: float = 1 / 60):
        """
        Intègre la vélocité (change_x / change_y) dans la position, puis fait
        avancer l'animation en cours. Commun à toutes les entités. Les
        sous-classes (Player, Enemy, ...) doivent définir change_x/change_y
        (via apply_acceleration/apply_friction ou une IA) PUIS appeler
        super().update(delta_time).
        """
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time
        self.update_animation_frame(delta_time)