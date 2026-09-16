"""
Affichage de l'interface (HUD et écrans plein écran).

Ce module ne contient QUE des fonctions de dessin, sans état : c'est
`main.py`, via sa machine à états, qui décide quel écran afficher et appelle
la fonction correspondante depuis `on_draw()`. Les fonctions lisent les infos
dont elles ont besoin dans le RoundManager (temps restant, morts, consigne...)
mais ne le modifient jamais.

API arcade 3.x : le dessin de texte passe par `arcade.draw_text` et les
rectangles pleins par `arcade.draw_lrbt_rectangle_filled(left, right, bottom,
top, color)` (les anciennes fonctions `draw_rectangle_*` de la 2.x n'existent
plus).
"""

import os
import random

import arcade
import numpy as np
from PIL import Image, ImageDraw


# --- Police -----------------------------------------------------------------
# Police optionnelle : si le chargement échoue (ou avant chargement), arcade
# retombe sur sa police par défaut, donc le HUD reste toujours dessiné.
CHEMIN_POLICE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "fonts", "ARIAL.TTF"
)
NOM_POLICE = ("Arial", "calibri")  # tuple de fallback passé à draw_text


def charger_police():
    """
    Charge la police du jeu. À appeler une fois depuis MonJeu.setup()
    (le contexte graphique arcade doit exister). Sans effet en cas d'échec.
    """
    try:
        arcade.load_font(CHEMIN_POLICE)
    except Exception:
        # Police introuvable / format non supporté : on garde la police par
        # défaut d'arcade, ce n'est pas bloquant.
        pass


# --- Couleurs & tailles -----------------------------------------------------
COULEUR_TEXTE = arcade.color.WHITE
COULEUR_ACCENT = arcade.color.GOLD
COULEUR_ALERTE = arcade.color.RED_ORANGE       # timer quand le temps est court
COULEUR_SUCCES = arcade.color.LIGHT_GREEN
COULEUR_ECHEC = arcade.color.RED
COULEUR_VOILE = (0, 0, 0, 190)                 # overlay semi-transparent (RGBA)

SEUIL_TEMPS_CRITIQUE = 10.0  # secondes en dessous desquelles le timer vire au rouge

# Règle centrale du jeu, expliquée au joueur pendant le tutoriel (cf. pitch).
REGLE_TUTO = "La facon dont tu meurs decide de ce que devient ton corps."


# --------------------------------------------------------------------------- #
# Direction artistique du menu (reprend la DA de l'affiche : cachot sombre en
# briques, crâne pixel-art os/gris, titre crème, éclaboussures rouge sombre)
# --------------------------------------------------------------------------- #

CHEMIN_BRIQUE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "assets", "images", "map1", "mur_map_niveau1.png",
)

# Palette tirée de l'affiche
_OS = (237, 230, 214, 255)         # blanc "os"
_OS_GRIS = (150, 148, 150, 255)    # ombre grise du crâne
_OS_SOMBRE = (26, 20, 18, 255)     # cavités (yeux, nez, dents)
_SANG_SOMBRE = (110, 12, 12)
_SANG = (156, 22, 20)
_CREME = (235, 228, 212)
_ROUGE_HALO = (120, 10, 10)

# Crâne pixel-art (comme sur l'affiche) : '.' vide, 'W' os, 'G' gris, 'K' sombre.
_SKULL_GRID = [
    ".WWWWWWWWW.",
    "WWWWWWWWWWW",
    "WWWWWWWWWWW",
    "WWWWWWWWWWW",
    "WKKKWWWKKKW",
    "WKGKWWWKGKW",
    "WKKKWWWKKKW",
    "WWWWWWWWWWW",
    "WWWWWKWWWWW",
    "WWWWKKKWWWW",
    "WWWWWWWWWWW",
    "WKWKWKWKWKW",
    ".WWWWWWWWW.",
]

# Cache des textures du menu, construites une seule fois (clé = taille écran).
_MENU_CACHE = {}


def _texture_crane():
    """Construit la texture du crâne pixel-art à partir de _SKULL_GRID."""
    couleurs = {"W": _OS, "G": _OS_GRIS, "K": _OS_SOMBRE}
    h = len(_SKULL_GRID)
    w = len(_SKULL_GRID[0])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y, ligne in enumerate(_SKULL_GRID):
        for x, ch in enumerate(ligne):
            if ch in couleurs:
                px[x, y] = couleurs[ch]
    return arcade.Texture(img)


def _texture_ambiance(largeur, hauteur):
    """Voile sombre + vignette (coins assombris) pour l'atmosphère cachot."""
    yy, xx = np.mgrid[0:hauteur, 0:largeur]
    dx = (xx - largeur / 2) / (largeur / 2)
    dy = (yy - hauteur / 2) / (hauteur / 2)
    dist = np.clip(np.sqrt(dx * dx + dy * dy) / 1.4, 0, 1)
    # Base plus opaque + vignette forte : noie l'effet "grille" de la tuile et
    # réchauffe la pierre bleutée vers un brun cachot.
    alpha = np.clip(150 + (dist ** 2) * 205, 0, 252).astype(np.uint8)

    rgba = np.zeros((hauteur, largeur, 4), np.uint8)
    rgba[..., 0] = 42   # ton brun chaud dans l'ombre
    rgba[..., 1] = 26
    rgba[..., 2] = 16
    rgba[..., 3] = alpha
    return arcade.Texture(Image.fromarray(rgba, "RGBA"))


def _texture_sang(largeur, hauteur):
    """Génère un calque d'éclaboussures de sang (déterministe via seed)."""
    img = Image.new("RGBA", (largeur, hauteur), (0, 0, 0, 0))
    dessin = ImageDraw.Draw(img)
    rnd = random.Random(7)

    def eclaboussure(cx, cy, echelle):
        for _ in range(rnd.randint(5, 9)):
            r = rnd.randint(int(4 * echelle), int(15 * echelle))
            ox = rnd.randint(-int(20 * echelle), int(20 * echelle))
            oy = rnd.randint(-int(15 * echelle), int(15 * echelle))
            couleur = rnd.choice([_SANG_SOMBRE, _SANG])
            a = rnd.randint(150, 215)
            dessin.ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r],
                           fill=couleur + (a,))
        for _ in range(rnd.randint(3, 6)):  # gouttelettes
            r = rnd.randint(1, 3)
            ox = rnd.randint(-int(32 * echelle), int(32 * echelle))
            oy = rnd.randint(-int(26 * echelle), int(34 * echelle))
            dessin.ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r],
                           fill=_SANG + (190,))

    for fx, fy, ech in [
        (0.30, 0.84, 1.1), (0.70, 0.86, 1.2), (0.50, 0.92, 1.0),
        (0.16, 0.70, 0.8), (0.86, 0.68, 0.9),
        (0.20, 0.30, 0.7), (0.82, 0.34, 0.75), (0.50, 0.40, 0.9),
    ]:
        eclaboussure(largeur * fx, hauteur * fy, ech)
    return arcade.Texture(img)


def _menu_assets(largeur, hauteur):
    """Charge/construit (une seule fois) les textures du menu."""
    cle = (largeur, hauteur)
    if cle not in _MENU_CACHE:
        _MENU_CACHE[cle] = {
            "brique": arcade.load_texture(CHEMIN_BRIQUE),
            "ambiance": _texture_ambiance(largeur, hauteur),
            "sang": _texture_sang(largeur, hauteur),
            "crane": _texture_crane(),
        }
    return _MENU_CACHE[cle]


def _titre_sanglant(texte, largeur, y, taille):
    """Titre crème entouré d'un halo rouge sombre (effet lueur de l'affiche)."""
    for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3),
                   (-2, -2), (2, 2), (-2, 2), (2, -2)]:
        arcade.draw_text(texte, largeur / 2 + dx, y + dy, _ROUGE_HALO,
                         font_size=taille, anchor_x="center", anchor_y="center",
                         font_name=NOM_POLICE, bold=True)
    arcade.draw_text(texte, largeur / 2, y, _CREME,
                     font_size=taille, anchor_x="center", anchor_y="center",
                     font_name=NOM_POLICE, bold=True)


# --------------------------------------------------------------------------- #
# Briques réutilisables
# --------------------------------------------------------------------------- #

def _voile(largeur, hauteur, couleur=COULEUR_VOILE):
    """Assombrit tout l'écran pour faire ressortir un écran de menu/transition."""
    arcade.draw_lrbt_rectangle_filled(0, largeur, 0, hauteur, couleur)


def _texte_centre(texte, largeur, y, taille=20, couleur=COULEUR_TEXTE,
                  gras=False):
    """Texte centré horizontalement, avec une ombre portée pour la lisibilité."""
    arcade.draw_text(
        texte, largeur / 2 + 2, y - 2, (0, 0, 0),
        font_size=taille, anchor_x="center", anchor_y="center",
        font_name=NOM_POLICE, bold=gras,
    )
    arcade.draw_text(
        texte, largeur / 2, y, couleur,
        font_size=taille, anchor_x="center", anchor_y="center",
        font_name=NOM_POLICE, bold=gras,
    )


def draw_fond_ambiance(largeur, hauteur, sang_alpha=100):
    """
    Fond commun à tous les écrans plein écran (DA de l'affiche) :
    briques tuilées + voile sombre/vignette + éclaboussures de sang.
    Réutilise les textures mises en cache par le menu.
    """
    a = _menu_assets(largeur, hauteur)
    tuile = 256
    for x in range(0, largeur, tuile):
        for y in range(0, hauteur, tuile):
            arcade.draw_texture_rect(a["brique"], arcade.LBWH(x, y, tuile, tuile),
                                     pixelated=True)
    arcade.draw_texture_rect(a["ambiance"], arcade.LBWH(0, 0, largeur, hauteur))
    if sang_alpha > 0:
        arcade.draw_texture_rect(a["sang"], arcade.LBWH(0, 0, largeur, hauteur),
                                 alpha=sang_alpha)


# --------------------------------------------------------------------------- #
# HUD en jeu
# --------------------------------------------------------------------------- #

def draw_hud(rm, largeur, hauteur, objectif=None):
    """
    HUD affiché pendant qu'un round est EN_COURS :
      - le timer, seul, en haut à gauche (rouge quand le temps devient court) ;
      - en haut à droite : le numéro de round + la condition de victoire.

    `objectif` : lignes de la condition de victoire (ex. les sacrifices restants
    fournis par le niveau). Si None, on retombe sur la consigne du round.
    Le compteur de morts / os est affiché en bas à gauche par le niveau.
    """
    # --- Timer (coin haut-gauche) ---
    restant = rm.temps_restant
    couleur_timer = COULEUR_ALERTE if restant <= SEUIL_TEMPS_CRITIQUE else COULEUR_TEXTE
    arcade.draw_text(
        "{:04.1f}".format(restant),  # ex: 42.3 / 07.5
        12, hauteur - 28,
        couleur_timer,
        font_size=26,
        anchor_x="left", anchor_y="center",
        font_name=NOM_POLICE, bold=True,
    )

    # --- Round + condition de victoire (coin haut-droit) ---
    arcade.draw_text(
        "Round {}/{}".format(rm.numero_courant, len(rm.rounds)),
        largeur - 12, hauteur - 20,
        COULEUR_ACCENT,
        font_size=16,
        anchor_x="right", anchor_y="center",
        font_name=NOM_POLICE, bold=True,
    )
    arcade.draw_text(
        objectif if objectif else rm.config_courante.consigne,
        largeur - 12, hauteur - 40,
        COULEUR_TEXTE,
        font_size=12,
        anchor_x="right", anchor_y="center",
        font_name=NOM_POLICE,
    )


# --------------------------------------------------------------------------- #
# Écrans plein écran (menu, tutoriel, transitions, fin de partie)
# --------------------------------------------------------------------------- #

def draw_menu(largeur, hauteur):
    """Menu principal illustré, reprenant la DA de l'affiche."""
    a = _menu_assets(largeur, hauteur)

    # 1+2) Fond briques + vignette (le sang est ajouté plus bas, par-dessus le crâne)
    draw_fond_ambiance(largeur, hauteur, sang_alpha=0)

    # 3) Crâne pixel-art centré, avec un contour sombre pour l'asseoir
    cote = min(largeur, hauteur) * 0.36
    ratio = len(_SKULL_GRID) / len(_SKULL_GRID[0])  # hauteur / largeur du bitmap
    cx, cy = largeur / 2, hauteur * 0.45
    contour = cote * 0.05
    arcade.draw_texture_rect(  # silhouette agrandie = contour sombre
        a["crane"],
        arcade.XYWH(cx, cy, cote + 2 * contour, (cote + 2 * contour) * ratio),
        color=arcade.types.Color(18, 13, 11, 255), pixelated=True,
    )
    arcade.draw_texture_rect(
        a["crane"], arcade.XYWH(cx, cy, cote, cote * ratio), pixelated=True,
    )

    # 4) Éclaboussures de sang par-dessus le crâne (comme sur l'affiche)
    arcade.draw_texture_rect(a["sang"], arcade.LBWH(0, 0, largeur, hauteur))

    # 5) Titre crème à halo rouge + accroche
    _titre_sanglant("MANY MEN", largeur, hauteur * 0.86, taille=54)
    _texte_centre("Mourir pour mieux avancer", largeur, hauteur * 0.76,
                  taille=15, couleur=(190, 60, 55))

    # 6) Options
    _texte_centre("[ Entree ]  Jouer", largeur, hauteur * 0.15,
                  taille=22, couleur=COULEUR_SUCCES, gras=True)
    _texte_centre("[ Echap ]  Quitter", largeur, hauteur * 0.08,
                  taille=17, couleur=(210, 200, 185))


def draw_tutoriel(largeur, hauteur, temps_restant):
    """
    Écran de tutoriel (~10 s) qui explique la règle centrale de la boucle.
    `temps_restant` : secondes avant de basculer automatiquement dans le jeu.
    """
    draw_fond_ambiance(largeur, hauteur)
    _texte_centre("COMMENT CA MARCHE", largeur, hauteur * 0.72,
                  taille=26, couleur=COULEUR_ACCENT, gras=True)
    _texte_centre(REGLE_TUTO, largeur, hauteur * 0.56,
                  taille=18, couleur=COULEUR_TEXTE)
    _texte_centre("Tue par une fleche  ->  ton corps devient un MUR",
                  largeur, hauteur * 0.44, taille=15, couleur=COULEUR_TEXTE)
    _texte_centre("Tue par un zombie  ->  tes os deviennent une ARMURE",
                  largeur, hauteur * 0.37, taille=15, couleur=COULEUR_TEXTE)
    _texte_centre("Debut dans {}s   ( Entree pour passer )".format(int(temps_restant) + 1),
                  largeur, hauteur * 0.18, taille=16, couleur=COULEUR_ACCENT)


def draw_fin_round(rm, largeur, hauteur, reussi):
    """
    Écran de transition entre deux rounds.
    - reussi=True  : round validé, score = nombre de morts.
    - reussi=False : round échoué (temps dépassé / consigne ratée).
    """
    draw_fond_ambiance(largeur, hauteur)
    if reussi:
        _texte_centre("ROUND {} REUSSI".format(rm.numero_courant),
                      largeur, hauteur * 0.64, taille=34,
                      couleur=COULEUR_SUCCES, gras=True)
        _texte_centre("Morts ce round : {}".format(rm.compute_score()),
                      largeur, hauteur * 0.50, taille=20)
        suite = "Round final" if rm.is_last_round else "Round suivant"
        _texte_centre("[ Entree ]  {}".format(suite),
                      largeur, hauteur * 0.32, taille=20, couleur=COULEUR_ACCENT)
    else:
        _texte_centre("ROUND {} ECHOUE".format(rm.numero_courant),
                      largeur, hauteur * 0.64, taille=34,
                      couleur=COULEUR_ECHEC, gras=True)
        _texte_centre("Temps depasse ou consigne ratee",
                      largeur, hauteur * 0.50, taille=18)
        _texte_centre("[ Entree ]  Reessayer",
                      largeur, hauteur * 0.32, taille=20, couleur=COULEUR_ACCENT)


def draw_pause(largeur, hauteur):
    """Menu Pause (habillé à la DA du jeu)."""
    draw_fond_ambiance(largeur, hauteur)
    _texte_centre("PAUSE", largeur, hauteur * 0.62,
                  taille=44, couleur=COULEUR_ACCENT, gras=True)
    _texte_centre("[ Echap ]  Reprendre", largeur, hauteur * 0.42,
                  taille=22, couleur=COULEUR_SUCCES)
    _texte_centre("[ Q ]  Quitter la partie", largeur, hauteur * 0.34,
                  taille=22, couleur=COULEUR_TEXTE)


def draw_confirm_quit(largeur, hauteur):
    """Confirmation avant d'abandonner la partie et de revenir au menu."""
    draw_fond_ambiance(largeur, hauteur)
    _voile(largeur, hauteur, (0, 0, 0, 150))  # assombri : moment de décision
    _texte_centre("Quitter la partie ?", largeur, hauteur * 0.58,
                  taille=30, couleur=COULEUR_ECHEC, gras=True)
    _texte_centre("La progression sera perdue.", largeur, hauteur * 0.46,
                  taille=16, couleur=COULEUR_TEXTE)
    _texte_centre("[ O ]  Oui, quitter        [ N ]  Non, reprendre",
                  largeur, hauteur * 0.30, taille=18, couleur=COULEUR_ACCENT)


def draw_victoire(rm, largeur, hauteur):
    """Écran de victoire finale : les 5 rounds sont validés."""
    draw_fond_ambiance(largeur, hauteur)
    _texte_centre("VICTOIRE", largeur, hauteur * 0.62,
                  taille=48, couleur=COULEUR_SUCCES, gras=True)
    _texte_centre("Morts au total : {}".format(rm.morts_totales),
                  largeur, hauteur * 0.46, taille=22)
    _texte_centre("[ Entree ]  Menu principal",
                  largeur, hauteur * 0.28, taille=20, couleur=COULEUR_ACCENT)


def draw_game_over(rm, largeur, hauteur):
    """Écran de Game Over (si on décide qu'un échec de round termine la partie)."""
    draw_fond_ambiance(largeur, hauteur)
    _texte_centre("GAME OVER", largeur, hauteur * 0.60,
                  taille=48, couleur=COULEUR_ECHEC, gras=True)
    _texte_centre("Round {} non valide".format(rm.numero_courant),
                  largeur, hauteur * 0.46, taille=20)
    _texte_centre("[ Entree ]  Menu principal",
                  largeur, hauteur * 0.28, taille=20, couleur=COULEUR_ACCENT)
