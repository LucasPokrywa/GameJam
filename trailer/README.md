# Trailer MANY MEN

Trailer de 30 s (1920x1080, 30 fps) monte avec [Remotion](https://remotion.dev).
Tout est dessine a partir des assets du jeu : les salles de `assets/images/` sont
aplaties dans `public/rooms/`, les spritesheets de `assets/entities/` sont rejouees
telles quelles, et la musique est `assets/sounds/main-theme.mp3`.

## Lancer

```bash
npm install
npm run dev                                   # Remotion Studio
npx remotion render Trailer out/many-men-trailer.mp4
```

Chaque scene est aussi une composition a part (dossier `Scenes` du Studio), pour
regler une seule sequence sans rejouer les 30 s.

## Decoupage

| Scene | Duree | Contenu |
|---|---|---|
| `Ouverture` | 4,3 s | Round 3, une fleche tue le joueur — « TU VAS MOURIR. » |
| `Regle` | 5,2 s | La regle du jeu : ta mort decide de ce que devient ton corps |
| `Mur` | 3,8 s | Mort par fleche → cadavre-MUR, la tourelle est aveuglee |
| `Os` | 3,8 s | Mort par zombie → OS ramassables, le joueur passe renforce |
| `Radeau` | 3,8 s | Noyade → RADEAU, le corps sert de pont |
| `Autel` | 5,4 s | Les socles se remplissent, puis les cinq salles |
| `Titre` | 6,0 s | Carte de titre |

## Regenerer les salles

`public/rooms/*.png` empile les couches dans le meme ordre que
`Level._load_level_scenery` (sol, decors, eau, vide, porte). A refaire si une map
bouge dans `assets/images/`.

## A verifier

Les noms de l'equipe sont en dur dans `src/scenes/Titre.tsx` (releves depuis
l'historique Git) — a corriger si la liste est fausse ou incomplete.
