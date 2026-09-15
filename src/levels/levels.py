import arcade
from entities.player import Player
from entities.turret import Turret
from entities.bullet import Bullet
from entities.corpse import Corpse


class Level:
    """
    Classe de base pour tous les niveaux du jeu.

    Chaque niveau définit son décor (murs, obstacles) et ses entités
    (joueur, ennemis, objets...). Pour créer un nouveau niveau, hérite de
    cette classe et surcharge la méthode setup().
    """

    def __init__(self, window_width, window_height, background_color=arcade.color.DARK_SLATE_GRAY):
        self.window_width = window_width
        self.window_height = window_height
        self.background_color = background_color

        # Sprites de décor / obstacles (pour les collisions plus tard)
        self.walls = arcade.SpriteList()

        # Toutes les entités présentes dans le niveau, y compris le joueur
        self.entities = arcade.SpriteList()

        self.player = None
        self._corpses_en_attente = []

        self.setup()

    def setup(self):
        """
        Construit le contenu du niveau : murs, ennemis, objets, position
        de départ du joueur, etc.

        Comportement par défaut : niveau vide avec le joueur au centre.
        Surcharge cette méthode dans une sous-classe pour un vrai niveau,
        par exemple :

            class Level1(Level):
                def setup(self):
                    self.player = Player(center_x=100, center_y=100)
                    self.entities.append(self.player)
                    # ajouter des murs, ennemis, etc.
        """
        self.player = Player(center_x=self.window_width // 2, center_y=self.window_height // 2)
        self.entities.append(self.player)

    def update(self, delta_time: float):
        # On itère sur une copie de la liste : certaines entités (ex: Turret)
        # peuvent en ajouter de nouvelles (ex: Bullet) pendant leur update(),
        # ce qui casserait une itération directe sur self.entities.
        for entity in list(self.entities):
            entity.update(delta_time)

        self._ajouter_corps_termines()
        self._gerer_collisions_balles()
        self._resoudre_collisions_solides()

        marge = 60  # tolérance en pixels avant de considérer une entité "hors écran"
        for entity in list(self.entities):
            if entity.clamp_to_bounds:
                # Bloque l'entité dans l'écran (comportement du joueur)
                if entity.left < 0:
                    entity.left = 0
                if entity.right > self.window_width:
                    entity.right = self.window_width
                if entity.bottom < 0:
                    entity.bottom = 0
                if entity.top > self.window_height:
                    entity.top = self.window_height
            else:
                # Détruit l'entité dès qu'elle est entièrement sortie de
                # l'écran (comportement d'une balle)
                hors_ecran = (
                    entity.right < -marge
                    or entity.left > self.window_width + marge
                    or entity.top < -marge
                    or entity.bottom > self.window_height + marge
                )
                if hors_ecran:
                    entity.remove_from_sprite_lists()

    def _gerer_collisions_balles(self):
        """Détruit les balles qui touchent un mur ou le joueur."""
        balles = [e for e in self.entities if isinstance(e, Bullet)]
        for balle in balles:
            if arcade.check_for_collision_with_list(balle, self.walls):
                balle.remove_from_sprite_lists()
                continue

            if self.player is None or self.player.etat != "normal":
                continue

            if arcade.check_for_collision(balle, self.player):
                self._toucher_joueur()
                balle.remove_from_sprite_lists()
                break  # une seule balle suffit à déclencher le coup

    def _toucher_joueur(self):
        """Mémorise le corps, qui apparaîtra à la fin de l'animation de mort."""
        self._corpses_en_attente.append((self.player.center_x, self.player.center_y))
        self.player.take_hit()

    def _ajouter_corps_termines(self):
        """Ajoute les corps dont l'animation de mort est terminée."""
        if self.player is None or not self.player.death_animation_finished:
            return

        for center_x, center_y in self._corpses_en_attente:
            self.walls.append(Corpse(center_x=center_x, center_y=center_y))
        self._corpses_en_attente.clear()

    def _resoudre_collisions_solides(self):
        """
        Empêche le joueur de traverser les murs/obstacles (dont les Corpse).
        Résolution simple par axe : on repousse le joueur hors de l'obstacle
        le long de l'axe où le chevauchement est le plus faible.
        """
        if self.player is None or self.player.etat != "normal":
            # Pendant le respawn, le joueur est figé/invulnérable : on ignore
            # les collisions (évite un "coup de pied" au moment où le corps
            # apparaît pile à sa position).
            return

        obstacles_touches = arcade.check_for_collision_with_list(self.player, self.walls)
        for obstacle in obstacles_touches:
            chevauchement_x = min(self.player.right, obstacle.right) - max(self.player.left, obstacle.left)
            chevauchement_y = min(self.player.top, obstacle.top) - max(self.player.bottom, obstacle.bottom)

            if chevauchement_x < chevauchement_y:
                if self.player.center_x < obstacle.center_x:
                    self.player.center_x -= chevauchement_x
                else:
                    self.player.center_x += chevauchement_x
                self.player.change_x = 0
            else:
                if self.player.center_y < obstacle.center_y:
                    self.player.center_y -= chevauchement_y
                else:
                    self.player.center_y += chevauchement_y
                self.player.change_y = 0

    def draw(self):
        self.walls.draw()
        self.entities.draw()


class EmptyLevel(Level):
    """Premier niveau : totalement vide, pour tester les déplacements du joueur."""
    pass


class TurretDemoLevel(Level):
    """
    Niveau de démonstration : le joueur en bas, une tourelle en haut qui
    vise et tire dessus. Sert d'exemple pour câbler une Turret dans un
    niveau (référence au niveau + au joueur).
    """

    def setup(self):
        self.player = Player(center_x=self.window_width // 2, center_y=100)
        self.entities.append(self.player)

        tourelle = Turret(
            center_x=self.window_width // 2,
            center_y=self.window_height - 100,
            level=self,
            player=self.player,
            fire_interval=1.2,
            bullet_speed=350,
        )
        self.entities.append(tourelle)