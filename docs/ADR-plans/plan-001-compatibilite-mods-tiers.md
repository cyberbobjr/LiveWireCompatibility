# Plan 001 — Mod de compatibilité avec les appareils des autres mods

ADR : [ADR-001](../ADR/001-compatibilite-mods-tiers.md).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| M1 | Projet du mod (dépôt, `workshop.txt`, `mod.info`, tests), registre de profils, chargeur, enveloppe de coupure | Terminée (2026-11-13) | — | D01, D02, D04, D06 | M | M2 |
| M2 | Analyse d'Artel Manufactory (rapport D05) | Terminée (2026-11-13) | — | D05 | M | M1 |
| M3 | Profil Artel Manufactory et outil de vérification des sprites | Terminée (2026-11-13) | M1, M2 | D02, D03, D04, D06 | M | — |
| M4 | Documentation des profils, descriptions Steam traduites, `preview.png`, publication privée | À faire | M3 | D01 | S | — |
| M5 | Passage en jeu SP puis MP avec Artel | À faire | M3 | — | S | — |
| M6 | Analyse D05 de la deuxième liste (12 mods) et profils FA2, Computer Mod, PWS, True Moozic, Machinery, Project Arcade ; enveloppes multi-consommateurs et côté client | Terminée (2026-11-13) | M3 | D02, D03, D04, D05, D06 | M | — |
| M7 | Passage en jeu des profils de M6 (Functional Appliances 2 en priorité) | À faire | M8 | — | S | — |
| M8 | Mod unique : profils regroupés dans `batman_LiveWireCompatibility`, sous-mods retirés (D01, révision) | Terminée (2026-11-13) | M6 | D01, D02 | S | — |

## M1 — Squelette, registre, chargeur

Fichiers (projet `LiveWireCompatibility`) : `Contents/mods/batman_LiveWireCompatibility/42.21/mod.info`,
`media/lua/shared/LiveWireCompatibility/LWC_Profiles.lua` (registre et chargeur),
chaque profil s'ajoute lui-même depuis `Profiles/` (pas de liste centrale). Tests : `tests/test_profiles.py` (19).
Documentation selon `docs/structure-documentaire.md` : `docs/README.md`, architecture, spécifications, améliorations, wiki EN/FR.

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 19 tests`, `OK` ; `pz_workshop_project.py validate .` → sortie vide, code 0. Non commité.

## M2 — Analyse d'Artel

Rapport : appareils comptés par le moteur, appareils gratuits (sprites, état de marche lisible, consommation
source), fonctions de courant publiques.

Rapport : [annexes/recherches/artel-manufactory.md](../annexes/recherches/artel-manufactory.md), confirmé statiquement.

## M3 — Profil Artel

Fichiers : `Profiles/LWC_Artel.lua` (d'abord dans un sous-mod, regroupé en M8),
`tests/test_profile_files.py`, `tools/check_sprites.py`.
Consommations estimées (Artel n'en donne aucune) ; sécheuse, sublimatrice et établi facturés en moyenne et non coupés
(tests de courant `local`, voir C02).

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 29 tests`, `OK` ;
`python tools/check_sprites.py` → `Artel: 27 sprites found`, code 0. Non commité.

## M4 — Documentation

## M5 — En jeu

## M6 — Deuxième liste de mods

Rapports : `annexes/recherches/` (functional-appliances-2, computer-mod, plysken-weather-station, true-moozic,
machinery, plysken-battery-charger, plysken-irrigation-pipes, badlands-power, industrial-works,
air-conditioner-units), confirmés statiquement. Profils pour
FunctionalAppliances2, ComputerMod, PlyskenWeatherStation, TrueMoozic, Machinery, puis ProjectArcade (recherche
des mods de jeux vidéo installés : project-arcade, video-game-consoles). Chargeur : `consumer` en tableau,
`side = "client"`. `tools/check_sprites.py` lit désormais les `.tiles` du mod cible et du jeu.

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 35 tests`, `OK` ; `python tools/check_sprites.py`
→ sept profils, tous les sprites trouvés, code 0. Non commité, rien testé en jeu.

## M7 — En jeu

## M8 — Mod unique à détection automatique

Les sept profils sont dans `Contents/mods/batman_LiveWireCompatibility/42.21/media/lua/shared/LiveWireCompatibility/Profiles/` ;
les dossiers `batman_LiveWireCompatibility<Cible>` et le test de leur `mod.info` sont retirés. Le chargeur ne change
pas : il appliquait déjà un profil seulement si son mod cible est actif.

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 34 tests`, `OK` ; `python tools/check_sprites.py`
→ sept profils, tous les sprites trouvés, code 0. Non commité, rien testé en jeu.
