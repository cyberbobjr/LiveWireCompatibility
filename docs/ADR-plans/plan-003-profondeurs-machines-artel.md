# Plan 003 — Profondeurs B42 des machines d'Artel Manufactory

ADR : [ADR-003](../ADR/003-profondeurs-machines-artel.md) (acceptée le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| P1 | Outil `tools/build_artel_depth.py` (bloc ajusté, projection et codage du moteur) et ses tests hors jeu | Terminée (2026-11-20) | — | D02, D03 | M | — |
| P2 | Carte `common/media/depthmaps/DEPTH_Artel.png` et `common/media/tileGeometry.txt` générées, contrôle : 0 pixel sans texel, cases d'Artel 200-223 laissées vides | Terminée (2026-11-20) | P1 | D01 | S | — |
| P3 | Documentation (architecture, spécifications, CHANGELOG) | Terminée (2026-11-20) | P2 | — | S | — |
| P5 | Généralisation (D04) : `tools/depthlib.py`, `tools/build_depth.py`, `tools/check_depth.py`, tests ; cartes de tous les profils | Terminée (2026-11-20) | P3 | D04 | M | — |
| P4 | Contrôle en jeu par l'utilisateur : lyophilisateur coloré de face dans « Afficher les consommateurs » | À valider (contrôle en jeu par l'utilisateur) | P2 | — | S | — |

## P1 — Outil

Fichiers : `tools/build_artel_depth.py`, `tests/test_artel_depth.py` (projection : coins du sol 1,0 / 0,75 / 0,5,
hauteur d'un niveau −0,5 ; bloc trouvé pour une silhouette synthétique ; aucun pixel sans texel).

## P2 — Carte

Commande : `python tools/build_artel_depth.py`. Critère : chaque tuile du profil Artel remplie, 0 pixel du sprite sans
texel, dimensions identiques à la carte d'Artel, aucune autre case remplie.

Modèle retenu après deux essais : le plus petit volume (premier essai) choisissait des plaques minces loin derrière la
machine, la silhouette d'un bloc étant ambiguë le long de l'axe de vue. Bloc carré centré sur la case (demi-largeur
jusqu'à 1 case pour les pièces qui débordent), seules demi-largeur et hauteur ajustées.

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 173 tests`, `OK` ; `python tools/build_artel_depth.py` →
40 sprites, `without depth 0` pour chacun, code 0 (lyophilisateur : bloc 0,15-0,85, hauteur 0,45 niveau, profondeurs
0,35 à 0,72) ; cases remplies : 40, aucune commune avec la carte d'Artel ; `pz_workshop_project.py validate .` → code 0.

## P5 — Généralisation (D04)

`tools/build_artel_depth.py` et `tests/test_artel_depth.py` renommés en `tools/depthlib.py` et `tests/test_depth.py` (P1 et P2
ci-dessus les citent sous l'ancien nom). Premier passage : les sprites servis par un renvoi incomplet étaient aussi
remplis ; abandonné après mesure (cartes du jeu elles-mêmes incomplètes, bloc plus grossier), voir D04.

Cartes livrées : `DEPTH_Artel.png` (40), `DEPTH_pa_arcades.png` (22, orientations nord et ouest et `pa_arcades_34` à `39`),
`DEPTH_pa_complex.png` (4), `DEPTH_pa_recreational.png` (8), `DEPTH_machinery_metal_bandsaw_01.png` (4),
`DEPTH_pws_tileset_01.png` (2) ; chacune `without depth 0`.

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 177 tests in 0.394s OK` ; `python tools/build_depth.py` → code 0 ;
`python tools/check_depth.py` → code 0, 7 profils, 229 sprites, `without depth 0` partout (notes : pixels opaques hors
profondeur de cartes existantes, 54 sprites, non corrigés).

## P4 — Contrôle en jeu

Fait par l'utilisateur (il lance lui-même les tests en jeu) : lyophilisateur Artel, une borne Project Arcade orientée
nord ou ouest, la scie à ruban de Machinery, la station météo, colorés de face dans « Afficher les consommateurs ».
