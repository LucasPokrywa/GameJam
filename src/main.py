"""
Point d'entrée du jeu et machine à états globale.

MonJeu (la fenêtre arcade) orchestre les grands états du jeu :

    MENU  ->  TUTO  ->  JEU  ->  FIN_ROUND  --(réussi)-->  round suivant / VICTOIRE
                          ^            |
                          |            +--(échoué)--> réessayer le même round
                          +-------------------------------------+

Le contenu d'un round (le Level) et la logique de round (le RoundManager) sont
volontairement séparés : ce fichier est la "colle" qui, à chaque round, crée le
bon Level, lance le chrono, compte les morts et enchaîne sur l'écran suivant.
"""

import sys
from enum import Enum, auto

import arcade
import os
try:
    import pyglet
except Exception:
    pyglet = None

import ui
from round_manager import RoundManager, RoundState, creer_rounds_par_defaut
from levels.levels import Level1, Level3, Puzzle1, TurretDemoLevel, Puzzle0

# arcade echantillonne ses textures en LINEAR par defaut, ce qui rend le pixel
# art flou des que l'echelle n'est pas 1:1.
arcade.SpriteList.DEFAULT_TEXTURE_FILTER = arcade.gl.NEAREST, arcade.gl.NEAREST

LARGEUR_ECRAN = 800
HAUTEUR_ECRAN = 600
TITRE = "MANY MEN"

# set_fullscreen() de pyglet ne fait pas le plein écran macOS : il recrée une
# fenêtre sans bordure qui capture l'écran. On passe par toggleFullScreen: de
# Cocoa, ce que déclenche le bouton vert.
MACOS = sys.platform == "darwin"
NS_FULLSCREEN_PRIMARY = 1 << 7   # NSWindowCollectionBehaviorFullScreenPrimary

DUREE_TUTO = 10.0  # secondes d'affichage du tutoriel avant de lancer le jeu

class EtatJeu(Enum):
    """Les grands écrans du jeu."""
    MENU = auto()
    TUTO = auto()
    JEU = auto()
    PAUSE = auto()
    FIN_ROUND = auto()
    VICTOIRE = auto()


def creer_niveau(numero, largeur, hauteur):
    """
    Fabrique le Level correspondant à un numéro de round.

    Les rounds sans niveau dédié retombent sur TurretDemoLevel : il suffit
    d'ajouter les suivants ici au fur et à mesure du level-design.
    """
    niveaux = {
        1:Puzzle0,
        2:Puzzle1,
        3:Level3
    }
    classe_level = niveaux.get(numero, TurretDemoLevel)
    return classe_level(largeur, hauteur)


class MonJeu(arcade.Window):
    def __init__(self):
        super().__init__(LARGEUR_ECRAN, HAUTEUR_ECRAN, TITRE, resizable=True)
        self.etat = EtatJeu.MENU
        self.rm = RoundManager(creer_rounds_par_defaut())
        self.level = None

        # Music player / background theme
        self._music_player = None
        self._music_sound = None
        self._music_playing = False
        self._menu_click_sound = None
        self._current_music = None
        # Round & UI state
        self.round_reussi = False
        self.tuto_timer = 0.0
        self.pause_confirm_quit = False

    def setup(self):
        """Initialisation unique (police, plein écran, état de départ)."""
        ui.charger_police()
        if MACOS:
            # Avant arcade.run(), toggleFullScreen: laisse la fenêtre dans une
            # taille bâtarde : on attend le premier tick.
            arcade.schedule_once(lambda _dt: self._basculer_fenetre(), 0)
        else:
            self.set_fullscreen(True)   # arcade gère le viewport HiDPI correctement
        self._aller_menu()

    def _start_music(self, filename: str = "main-theme.mp3", volume: float = 0.35):
        """Start background music from `assets/sounds/{filename}`.

        Uses pyglet where available for reliable looping; falls back to arcade.
        """
        if self._music_playing:
            # If the requested file is already playing, do nothing.
            if getattr(self, "_current_music", None) == filename:
                return
            # Otherwise stop current music and continue to start the requested one.
            try:
                self._stop_music()
            except Exception:
                pass
        try:
            projet_root = os.path.dirname(os.path.dirname(__file__))
            chosen = os.path.join(projet_root, "assets", "sounds", filename)
            if not os.path.exists(chosen):
                return
            # remember current music
            self._current_music = filename

            # Try pyglet player for reliable looping
            if pyglet is not None:
                try:
                    source = pyglet.media.load(chosen)
                    player = pyglet.media.Player()
                    player.queue(source)
                    # Set volume and loop behaviour
                    try:
                        player.volume = volume
                    except Exception:
                        pass
                    try:
                        player.loop = True
                    except Exception:
                        try:
                            player.eos_action = 'loop'
                        except Exception:
                            pass
                    player.play()
                    self._music_player = player
                    self._music_playing = True
                    return
                except Exception:
                    self._music_player = None

            # Fallback to arcade sound (may not loop depending on arcade version)
            try:
                self._music_sound = arcade.load_sound(chosen)
                try:
                    arcade.play_sound(self._music_sound, volume=volume, loop=True)
                except TypeError:
                    arcade.play_sound(self._music_sound, volume=volume)
                self._music_playing = True
            except Exception:
                pass
        except Exception:
            pass



    def _basculer_fenetre(self):
        """F11 : plein écran <-> fenêtré."""
        if MACOS:
            self._nswindow.setCollectionBehavior_(NS_FULLSCREEN_PRIMARY)
            self._nswindow.toggleFullScreen_(None)
        else:
            self.set_fullscreen(not self.fullscreen)

    def on_resize(self, width, height):
        """
        Suit les changements de taille (dont le passage plein écran) : arcade met
        à jour la projection, et on resynchronise les bornes du niveau courant
        pour que le joueur reste bloqué dans les limites du nouvel écran.
        """
        super().on_resize(width, height)
        if self.level is not None:
            self.level.window_width = width
            self.level.window_height = height

    # ------------------------------------------------------------------ #
    # Transitions d'état
    # ------------------------------------------------------------------ #

    def _aller_menu(self):
        self.etat = EtatJeu.MENU
        self.level = None
        arcade.set_background_color(arcade.color.BLACK)
        # Start menu music
        self._start_music(filename="menu-theme.mp3", volume=0.35)

    def _demarrer_partie(self):
        """Repart d'une partie neuve : round 1, écran de tutoriel."""
        self.rm = RoundManager(creer_rounds_par_defaut())
        self.etat = EtatJeu.TUTO
        self.tuto_timer = 0.0
        arcade.set_background_color(arcade.color.BLACK)

    def _charger_round_courant(self):
        """Crée le Level du round courant et démarre le chrono."""
        self.level = creer_niveau(self.rm.numero_courant, self.width, self.height)
        # Chaque mort du joueur incrémente le compteur du RoundManager.
        self.level.on_death = self.rm.register_death
        arcade.set_background_color(self.level.background_color)
        self.rm.start_round()
        self.etat = EtatJeu.JEU
        self._start_music(filename="main-theme.mp3", volume=0.35)

    def _terminer_round(self, reussi):
        """Bascule vers l'écran de fin de round (réussi ou échoué)."""
        self.round_reussi = reussi
        self.etat = EtatJeu.FIN_ROUND
        self._stop_music()

    def _apres_fin_round(self):
        """Action déclenchée par [Entree] sur l'écran de fin de round."""
        if not self.round_reussi:
            # Échec : on rejoue le même round.
            self.rm.restart_round()
            self._charger_round_courant()
            return

        # Réussi : round suivant, ou victoire si c'était le dernier.
        if self.rm.load_next_round():
            self._charger_round_courant()
        else:
            self.etat = EtatJeu.VICTOIRE

    # ------------------------------------------------------------------ #
    # Boucle de jeu
    # ------------------------------------------------------------------ #

    def on_update(self, delta_time):
        if self.etat == EtatJeu.TUTO:
            self.tuto_timer += delta_time
            if self.tuto_timer >= DUREE_TUTO:
                self._charger_round_courant()
            return

        if self.etat == EtatJeu.JEU:
            self.level.update(delta_time)

            # Le chrono tourne et peut échouer le round tout seul au dépassement.
            if self.rm.update_timer(delta_time) == RoundState.ECHOUE:
                self._terminer_round(reussi=False)
                return

            # Consigne du niveau remplie -> round réussi.
            if self.level.is_complete():
                self.rm.complete_round()
                self._terminer_round(reussi=True)

    def on_draw(self):
        self.clear()

        if self.etat == EtatJeu.MENU:
            ui.draw_menu(self.width, self.height)

        elif self.etat == EtatJeu.TUTO:
            ui.draw_tutoriel(self.width, self.height, DUREE_TUTO - self.tuto_timer)

        elif self.etat == EtatJeu.JEU:
            self.level.draw()
            # Condition de victoire (haut-droite) : les sacrifices restants si le
            # niveau a un autel, sinon la consigne générique du round.
            objectif = None
            altar = getattr(self.level, "altar", None)
            if altar is not None:
                objectif = "Sacrifices : {}".format(altar.progress_text())
            ui.draw_hud(self.rm, self.width, self.height, objectif)

        elif self.etat == EtatJeu.PAUSE:
            if self.pause_confirm_quit:
                ui.draw_confirm_quit(self.width, self.height)
            else:
                ui.draw_pause(self.width, self.height)

        elif self.etat == EtatJeu.FIN_ROUND:
            ui.draw_fin_round(self.rm, self.width, self.height, self.round_reussi)

        elif self.etat == EtatJeu.VICTOIRE:
            ui.draw_victoire(self.rm, self.width, self.height)

    # ------------------------------------------------------------------ #
    # Entrées clavier (dispatch selon l'état)
    # ------------------------------------------------------------------ #

    def on_key_press(self, key, modifiers):
        # Bascule plein écran / fenêtré, disponible depuis n'importe quel écran.
        if key == arcade.key.F11:
            self._basculer_fenetre()
            return

        if self.etat == EtatJeu.MENU:
            if key == arcade.key.ENTER:
                self._play_menu_click()
                self._demarrer_partie()
            elif key == arcade.key.ESCAPE:
                self._play_menu_click()
                self.close()

        elif self.etat == EtatJeu.TUTO:
            if key == arcade.key.ENTER:
                self._play_menu_click()
                self._charger_round_courant()   # passer le tutoriel

        elif self.etat == EtatJeu.JEU:
            if key == arcade.key.ESCAPE:
                self.pause_confirm_quit = False
                self._play_menu_click()
                self.etat = EtatJeu.PAUSE
                self._stop_music()
            elif key == arcade.key.N:
                # DEBUG (temporaire) : valide le round à la main tant que les
                # vraies conditions is_complete() des niveaux n'existent pas.
                self.rm.complete_round()
                self._terminer_round(reussi=True)
            else:
                self.level.player.on_key_press(key)

        elif self.etat == EtatJeu.PAUSE:
            if self.pause_confirm_quit:
                # Écran de confirmation "Quitter la partie ?"
                if key in (arcade.key.O, arcade.key.Y):
                    self._play_menu_click()
                    self._aller_menu()
                elif key in (arcade.key.N, arcade.key.ESCAPE):
                    self._play_menu_click()
                    self.pause_confirm_quit = False   # annule -> retour menu pause
            else:
                # Menu pause
                if key == arcade.key.ESCAPE:
                    self._play_menu_click()
                    self.etat = EtatJeu.JEU
                    self._start_music()
                elif key == arcade.key.Q:
                    self._play_menu_click()
                    self.pause_confirm_quit = True

        elif self.etat == EtatJeu.FIN_ROUND:
            if key == arcade.key.ENTER:
                self._apres_fin_round()
            elif key == arcade.key.ESCAPE:
                self._aller_menu()

        elif self.etat == EtatJeu.VICTOIRE:
            if key in (arcade.key.ENTER, arcade.key.ESCAPE):
                self._aller_menu()

    def on_key_release(self, key, modifiers):
        if self.etat == EtatJeu.JEU:
            self.level.player.on_key_release(key)

    # ------------------------------------------------------------------ #
    # Music helpers
    # ------------------------------------------------------------------ #
    

    def _stop_music(self):
        try:
            if getattr(self, "_music_player", None) is not None:
                try:
                    self._music_player.pause()
                except Exception:
                    pass
                try:
                    self._music_player.delete()
                except Exception:
                    pass
                self._music_player = None
            # No reliable stop for arcade.play_sound fallback; just clear flag.
            self._music_playing = False
        except Exception:
            pass

    def _play_menu_click(self):
        """Play the menu click sound once (lazy-loads the asset)."""
        try:
            if getattr(self, "_menu_click_sound", None) is None:
                projet_root = os.path.dirname(os.path.dirname(__file__))
                candidates = [
                    os.path.join(projet_root, "assets", "sounds", "menu-click.mp3"),
                    os.path.join(projet_root, "assets", "sounds", "menu-click.ogg"),
                ]
                chosen = None
                for c in candidates:
                    if os.path.exists(c):
                        chosen = c
                        break
                if chosen is not None:
                    self._menu_click_sound = arcade.load_sound(chosen)
                else:
                    self._menu_click_sound = None

            if getattr(self, "_menu_click_sound", None) is not None:
                arcade.play_sound(self._menu_click_sound, volume=0.7)
        except Exception:
            pass
 

def main():
    jeu = MonJeu()
    jeu.setup()
    arcade.run()


if __name__ == "__main__":
    main()
