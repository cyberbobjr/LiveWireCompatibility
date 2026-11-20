# Plan 006 — Contrôle de courant des stations de séchage Artel corrigé à la source

ADR : [ADR-006](../ADR/006-correctif-source-artel.md) (acceptée le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| S1 | `LWC_SourcePatch` (registre, lecture, remplacement, repli, signalement) ; tests | Terminée (2026-11-20) | — | D02, D03, D04 | S | — |
| S2 | Profil Artel : correctif `PMK_58z`, `stationPowered` ; fichier de même chemin ; `loadModAfter` ; tests | Terminée (2026-11-20) | S1 | D01, D04 | S | — |
| S3 | Contrôle en jeu par l'utilisateur | À faire | S2 | — | S | — |

## S1 — `LWC_SourcePatch`

`shared/LiveWireCompatibility/LWC_SourcePatch.lua`, appel de `report()` dans `LWC_Profiles.applyAll` ;
`tests/test_source_patch.py` (classe `SourcePatch`) : modification appliquée et résultat du fichier rendu, `old` absent ou
double, texte qui ne compile pas, mod inactif, fichier illisible, signalement d'un correctif non exécuté.

## S2 — Artel

`Profiles/LWC_Artel.lua` (`LiveWireCompat.Artel.stationPowered`, déclaration du correctif), `server/PMK_58z_SublimatorServer.lua`
(fichier de même chemin, sans code d'Artel), `mod.info` (`loadModAfter=\batman_LiveWire,\ArtelManufactory`, indication d'ordre seulement : Artel reste facultatif) ;
`tests/test_source_patch.py` (classe `ArtelWatchdog`). Contrôle sur le vrai fichier d'Artel (lecture seule) : remplacement
trouvé, texte compilé, 496 lignes avant et après.

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 283 tests`, `OK` ; `python tools/check_sprites.py` → code 0.
