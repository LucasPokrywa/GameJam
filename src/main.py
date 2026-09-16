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

from enum import Enum, auto

import arcade

import ui
from round_manager import RoundManager, RoundState, creer_rounds_par_defaut
from levels.levels import Level1, TurretDemoLevel

LARGEUR_ECRAN = 800
HAUTEUR_ECRAN = 600
TITRE = "MANY MEN"

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
        1: Level1,
        # 2: Level2, ...  <- à compléter avec le level-design final
    }
    classe_level = niveaux.get(numero, TurretDemoLevel)
    return classe_level(largeur, hauteur)


class MonJeu(arcade.Window):
    def __init__(self):
        super().__init__(LARGEUR_ECRAN, HAUTEUR_ECRAN, TITRE, resizable=True)
        self.etat = EtatJeu.MENU
        self.rm = RoundManager(creer_rounds_par_defaut())
        self.level = None

        self.round_reussi = False   # mémorise l'issue du round pour l'écran de fin
        self.tuto_timer = 0.0
        self.pause_confirm_quit = False  # True quand la confirmation de quit est affichée

    def setup(self):
        """Initialisation unique (police, plein écran, état de départ)."""
        ui.charger_police()
        self.set_fullscreen(True)   # arcade gère le viewport HiDPI correctement
        self._aller_menu()

    def _basculer_fenetre(self):
        """F11 : plein écran <-> fenêtré."""
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

    def _terminer_round(self, reussi):
        """Bascule vers l'écran de fin de round (réussi ou échoué)."""
        self.round_reussi = reussi
        self.etat = EtatJeu.FIN_ROUND

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
            ui.draw_hud(self.rm, self.width, self.height)

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
                self._demarrer_partie()
            elif key == arcade.key.ESCAPE:
                self.close()

        elif self.etat == EtatJeu.TUTO:
            if key == arcade.key.ENTER:
                self._charger_round_courant()   # passer le tutoriel

        elif self.etat == EtatJeu.JEU:
            if key == arcade.key.ESCAPE:
                self.pause_confirm_quit = False
                self.etat = EtatJeu.PAUSE
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
                    self._aller_menu()
                elif key in (arcade.key.N, arcade.key.ESCAPE):
                    self.pause_confirm_quit = False   # annule -> retour menu pause
            else:
                # Menu pause
                if key == arcade.key.ESCAPE:
                    self.etat = EtatJeu.JEU            # reprendre
                elif key == arcade.key.Q:
                    self.pause_confirm_quit = True     # demander confirmation

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


def main():
    jeu = MonJeu()
    jeu.setup()
    arcade.run()


if __name__ == "__main__":
    main()
