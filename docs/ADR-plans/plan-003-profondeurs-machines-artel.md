# Plan 003 — Profondeurs B42 des machines d'Artel Manufactory

ADR : [ADR-003](../ADR/003-profondeurs-machines-artel.md) (acceptée le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| P1 | Outil `tools/build_artel_depth.py` (bloc ajusté, projection et codage du moteur) et ses tests hors jeu | Terminée (2026-11-20) | — | D02, D03 | M | — |
| P2 | Carte `common/media/depthmaps/DEPTH_Artel.png` et `common/media/tileGeometry.txt` générées, contrôle : 0 pixel sans texel, cases d'Artel 200-223 laissées vides | Terminée (2026-11-20) | P1 | D01 | S | — |
| P3 | Documentation (architecture, spécifications, CHANGELOG) | Terminée (2026-11-20) | P2 | — | S | — |
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

## P4 — Contrôle en jeu

Fait par l'utilisateur (il lance lui-même les tests en jeu).
