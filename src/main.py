import arcade
from levels.levels import EmptyLevel

LARGEUR_ECRAN = 800
HAUTEUR_ECRAN = 600
TITRE = "Mon jeu - vue du dessus"


class MonJeu(arcade.Window):
    def __init__(self):
        super().__init__(LARGEUR_ECRAN, HAUTEUR_ECRAN, TITRE)
        self.level = None

    def setup(self):
        """Initialise le niveau de départ."""
        self.level = EmptyLevel(LARGEUR_ECRAN, HAUTEUR_ECRAN)
        arcade.set_background_color(self.level.background_color)

    def on_draw(self):
        self.clear()
        self.level.draw()

    def on_update(self, delta_time):
        self.level.update(delta_time)

    def on_key_press(self, key, modifiers):
        self.level.player.on_key_press(key)

    def on_key_release(self, key, modifiers):
        self.level.player.on_key_release(key)


def main():
    jeu = MonJeu()
    jeu.setup()
    arcade.run()


if __name__ == "__main__":
    main()