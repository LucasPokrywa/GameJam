# MANY MEN

Jeu réalisé dans le cadre d'une game jam, avec [Python](https://www.python.org/) et la
bibliothèque [arcade](https://api.arcade.academy/).

## Description du jeu

**MANY MEN** est un jeu d'action/puzzle en 2D vu de dessus, découpé en **6 rounds**
chronométrés (60 secondes chacun par défaut). Dans chaque round, il faut remplir une
consigne précise (atteindre la sortie, bloquer des tirs, récupérer des os, activer un
bouton, survivre...) avant la fin du temps imparti.

Le twist du jeu : **ta mort n'est pas une fin, c'est une ressource.** Selon la façon dont
le joueur meurt, son cadavre devient un élément utilisable dans le niveau :

- Mort transpercé par une flèche → le corps devient un **mur**, qui peut bloquer une
  tourelle ou une trajectoire.
- Mort face à un zombie → le corps laisse des **os** ramassables, qui renforcent le
  joueur suivant.
- Mort noyé → le corps devient un **radeau**, utilisable comme pont sur l'eau.

Le joueur peut aussi **sacrifier** des corps sur un autel pour progresser dans certaines
salles. L'objectif est donc de mourir intelligemment pour ouvrir la voie, plutôt que
d'éviter la mort à tout prix.

### Contrôles

| Touche | Action |
|---|---|
| `Z` `Q` `S` `D` (ou flèches directionnelles) | Se déplacer |
| `Espace` | Attaquer |
| `Échap` | Pause / retour au menu |
| `F11` | Basculer plein écran / fenêtré |
| `Entrée` | Valider (menu, tutoriel, fin de round) |

## Bibliothèques utilisées

- [`arcade`](https://api.arcade.academy/) (>=3.0,<4.0) — moteur de jeu 2D (fenêtre,
  sprites, collisions, sons)
- [`numpy`](https://numpy.org/) — calculs sur les sprites et les assets
- [`pillow`](https://python-pillow.org/) — traitement d'images
- [`pyyaml`](https://pyyaml.org/) — chargement de configuration
- [`pytest`](https://pytest.org/) — tests unitaires (notamment la logique de rounds)
- [`pyglet`](https://pyglet.org/) (optionnel) — lecture audio en boucle plus fiable pour
  la musique de fond

Le dossier `trailer/` contient un projet [Remotion](https://remotion.dev) (React /
TypeScript) séparé, utilisé pour générer la bande-annonce du jeu à partir des assets
existants ; il n'est pas nécessaire pour jouer.

## Architecture

```
GameJam/
├── src/
│   ├── main.py             # Point d'entrée : fenêtre arcade et machine à états
│   │                       #  globale (MENU -> TUTO -> JEU -> FIN_ROUND -> VICTOIRE)
│   ├── round_manager.py    # Logique pure des rounds (chrono, morts, score),
│   │                       #  testable indépendamment d'arcade
│   ├── ui.py               # Écrans (menu, HUD, pause, fin de round, victoire)
│   ├── entities/           # Entités du jeu
│   │   ├── player.py       # Joueur : déplacement, attaque, gestion des morts
│   │   ├── enemy.py        # Ennemis (zombies, ...)
│   │   ├── turret.py       # Tourelles
│   │   ├── xbow.py         # Arbalètes / tirs
│   │   ├── bullet.py       # Projectiles
│   │   ├── corpse.py       # Transformation du cadavre (mur / os / radeau)
│   │   ├── altar.py        # Autel de sacrifice
│   │   ├── stake.py        # Pieux / pièges
│   │   ├── button.py       # Boutons / mécanismes à activer
│   │   ├── damage.py       # Gestion des dégâts
│   │   └── entities.py     # Classes de base communes
│   └── levels/
│       └── levels.py       # Définition des niveaux (Tutorial, Puzzle0/1,
│                            #  Level3/4/5, TurretDemoLevel, ButtonMapLevel...)
├── assets/
│   ├── entities/            # Spritesheets des personnages/ennemis
│   ├── images/               # Décors et tuiles des salles
│   ├── fonts/                 # Police du jeu
│   └── sounds/                 # Musiques et effets sonores
├── trailer/                 # Bande-annonce (projet Remotion séparé, React/TS)
├── requirements.txt         # Dépendances Python
├── install.sh / install.bat # Scripts d'installation (Linux/macOS / Windows)
└── Dungeon Gathering Free Version.rar  # Pack d'assets tiers utilisé pour le décor
```

Le code sépare volontairement :
- la **logique de round** (`round_manager.py`), pure et testable sans dépendance à
  `arcade` ;
- le **contenu d'un niveau** (`levels/levels.py`), qui définit la carte et la consigne
  de chaque round ;
- l'**orchestration** (`main.py`), qui fait le lien entre les deux et gère les écrans.

## Installation et lancement

### Linux / macOS

```bash
./install.sh
source .venv/bin/activate
python src/main.py
```

### Windows

```bat
install.bat
```

(`install.bat` installe les dépendances puis lance directement le jeu.)

## Tests

Les tests couvrent notamment la logique de `round_manager.py` :

```bash
pytest
```
