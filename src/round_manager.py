"""
Gestion des rounds du jeu.

Le RoundManager ne connaît RIEN du contenu d'un niveau (murs, ennemis,
condition de victoire...) ni d'arcade : c'est de la logique pure, donc
testable en isolation avec pytest. Il s'occupe uniquement de :

    - suivre le round courant (index dans une liste de RoundConfig) ;
    - décompter le temps imparti (60 s par défaut) et échouer le round au
      dépassement ;
    - compter les morts du round et calculer le score ;
    - passer au round suivant / détecter la victoire finale.

C'est `main.py` qui pilote ce manager : il instancie le Level correspondant
au round courant, appelle `update_timer()` chaque frame, `register_death()`
à chaque mort du joueur, et `complete_round()` quand le niveau signale que
sa consigne est remplie.
"""

from dataclasses import dataclass, field
from enum import Enum, auto


DUREE_ROUND_PAR_DEFAUT = 60.0  # secondes max par round (voir pitch : 5 rounds de 60 s)
NB_ROUNDS = 5


class RoundState(Enum):
    """État du round courant."""
    PRET = auto()       # round chargé mais pas encore démarré
    EN_COURS = auto()   # le chrono tourne, le joueur joue
    REUSSI = auto()     # consigne remplie dans le temps imparti
    ECHOUE = auto()     # temps dépassé (ou consigne ratée)


@dataclass
class RoundConfig:
    """
    Description d'un round, indépendante de son implémentation dans le niveau.

    - numero   : numéro affiché (1..5).
    - consigne : texte expliquant l'objectif du round (utilisé par l'UI et le
                 tutoriel). Le détail de la *vérification* de cette consigne
                 vit dans le Level, pas ici.
    - duree    : temps maximum en secondes.
    """
    numero: int
    consigne: str = ""
    duree: float = DUREE_ROUND_PAR_DEFAUT


class RoundManager:
    """
    Machine à états d'un round + suivi du temps, des morts et du score.

    Cycle de vie typique piloté depuis main.py :

        rm = RoundManager(creer_rounds_par_defaut())
        rm.start_round()                     # -> EN_COURS
        # chaque frame :
        etat = rm.update_timer(delta_time)   # échoue tout seul si le temps est dépassé
        # à chaque mort du joueur :
        rm.register_death()
        # quand le niveau signale sa consigne remplie :
        rm.complete_round()                  # -> REUSSI
        # puis :
        if rm.load_next_round():             # démarre le round suivant
            ...                              # (recréer le Level correspondant)
        else:
            ...                              # plus de round -> Victoire finale
    """

    def __init__(self, rounds):
        self.rounds = list(rounds)
        if not self.rounds:
            raise ValueError("RoundManager a besoin d'au moins un round.")

        self.index_courant = 0
        self.state = RoundState.PRET

        self.temps_ecoule = 0.0
        self.morts_round = 0

        # Historique des morts par numéro de round (rempli quand un round se
        # termine, réussi ou échoué). Sert au score total / à l'écran de fin.
        self._morts_par_round = {}

    # ------------------------------------------------------------------ #
    # Accès pratiques
    # ------------------------------------------------------------------ #

    @property
    def config_courante(self) -> RoundConfig:
        """Le RoundConfig du round en cours."""
        return self.rounds[self.index_courant]

    @property
    def numero_courant(self) -> int:
        """Numéro (1..N) du round en cours."""
        return self.config_courante.numero

    @property
    def temps_restant(self) -> float:
        """Secondes restantes avant échec (jamais négatif)."""
        return max(0.0, self.config_courante.duree - self.temps_ecoule)

    @property
    def is_last_round(self) -> bool:
        """True si le round courant est le dernier de la liste."""
        return self.index_courant >= len(self.rounds) - 1

    # ------------------------------------------------------------------ #
    # Transitions
    # ------------------------------------------------------------------ #

    def start_round(self):
        """
        (Re)démarre le round courant : remet le chrono et les morts à zéro et
        passe en EN_COURS. Utilisable aussi bien pour un nouveau round que pour
        rejouer un round échoué (voir restart_round()).
        """
        self.temps_ecoule = 0.0
        self.morts_round = 0
        self.state = RoundState.EN_COURS
        # En cas de rejeu d'un round échoué, on efface son ancienne entrée
        # d'historique pour que morts_round/morts_totales repartent propres.
        self._morts_par_round.pop(self.numero_courant, None)

    def update_timer(self, delta_time: float) -> RoundState:
        """
        Fait avancer le chrono. À appeler chaque frame depuis on_update().

        Ne fait rien si le round n'est pas EN_COURS (utile pendant un écran de
        fin de round où on continue d'appeler update). Déclenche fail_round()
        automatiquement si le temps imparti est dépassé.

        Retourne l'état résultant, pour que l'appelant sache tout de suite si
        le round vient d'échouer au temps.
        """
        if self.state != RoundState.EN_COURS:
            return self.state

        self.temps_ecoule += delta_time
        if self.temps_ecoule >= self.config_courante.duree:
            self.temps_ecoule = self.config_courante.duree
            self.fail_round()
        return self.state

    def register_death(self):
        """
        Signale une mort du joueur. À brancher sur le moment de mort
        (Level._toucher_joueur / Player.take_hit). Ignorée hors EN_COURS pour
        ne pas compter de morts pendant un écran de transition.
        """
        if self.state == RoundState.EN_COURS:
            self.morts_round += 1

    def complete_round(self):
        """
        Marque le round comme REUSSI (la consigne du niveau est remplie).
        Sans effet si le round n'est pas EN_COURS.
        """
        if self.state != RoundState.EN_COURS:
            return
        self.state = RoundState.REUSSI
        self._enregistrer_historique()

    def fail_round(self):
        """
        Marque le round comme ECHOUE (temps dépassé, ou consigne définitivement
        ratée). Sans effet si le round n'est pas EN_COURS.
        """
        if self.state != RoundState.EN_COURS:
            return
        self.state = RoundState.ECHOUE
        self._enregistrer_historique()

    def restart_round(self):
        """Rejoue le round courant depuis le début (après un échec)."""
        self.start_round()

    def load_next_round(self) -> bool:
        """
        Passe au round suivant et le démarre.

        Retourne True si un round suivant a bien été chargé, False s'il n'y a
        plus de round (= victoire finale, tous les rounds sont derrière nous).
        Le contenu du niveau (le Level) est recréé par l'appelant, pas ici.
        """
        if self.is_last_round:
            return False
        self.index_courant += 1
        self.start_round()
        return True

    # ------------------------------------------------------------------ #
    # Score
    # ------------------------------------------------------------------ #

    def compute_score(self) -> int:
        """
        Score du round courant = nombre de morts (plus c'est bas, mieux c'est,
        cf. pitch « Mourir pour mieux avancer »).
        """
        return self.morts_round

    @property
    def morts_totales(self) -> int:
        """Somme des morts sur tous les rounds terminés + le round en cours."""
        total = sum(self._morts_par_round.values())
        # Le round en cours n'est pas encore dans l'historique (il n'y entre
        # qu'à complete_round/fail_round) : on ajoute ses morts à la volée,
        # sans double comptage une fois le round terminé.
        if self.numero_courant not in self._morts_par_round:
            total += self.morts_round
        return total

    def historique_morts(self) -> dict:
        """Copie de l'historique {numero_round: morts} des rounds terminés."""
        return dict(self._morts_par_round)

    # ------------------------------------------------------------------ #
    # Interne
    # ------------------------------------------------------------------ #

    def _enregistrer_historique(self):
        """Fige le nombre de morts du round qui vient de se terminer."""
        self._morts_par_round[self.numero_courant] = self.morts_round


def creer_rounds_par_defaut() -> list:
    """
    Construit 5 rounds placeholder pour pouvoir intégrer le RoundManager dès
    maintenant, avant que le design final des niveaux ne soit prêt.

    Les consignes sont provisoires : à remplacer par les vraies conditions
    de chaque round une fois le level-design arrêté (coordination avec le dev
    des niveaux).
    """
    consignes = [
        "Atteins la sortie.",
        "Bloque les tirs pour ouvrir un passage.",
        "Récupère les os d'un squelette tombé.",
        "Traverse la salle sans te faire toucher.",
        "Survis et atteins la sortie finale.",
    ]
    return [
        RoundConfig(numero=i + 1, consigne=consignes[i])
        for i in range(NB_ROUNDS)
    ]
