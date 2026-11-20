# Plan 005 — Tuiles partagées ; Knox Working Machines, STFO 3T et CamRecorder

ADR : [ADR-005](../ADR/005-tuiles-partagees-et-trois-nouveaux-mods.md) (acceptée le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| T1 | Analyses D05 des trois mods (`annexes/recherches/`) | Terminée (2026-11-20) | — | — | M | — |
| T2 | Cœur : `shared`/`owns`, inscription unique, `memberOf`/`consumerIdOf` utilisés par gardes, interrupteur et menu ; tests | Terminée (2026-11-20) | — | D01 | M | — |
| T3 | Profil Knox Working Machines ; tuiles partagées avec Machinery | À faire | T2 | D02, D03 | M | T4, T5 |
| T4 | Profil STFO (secteur seulement, batterie intacte) | À faire | T2 | D04 | M | T3, T5 |
| T5 | Profil CamRecorder ; ordinateur partagé avec Computer Mod | À faire | T2 | D02, D05 | M | T3, T4 |
| T6 | Profondeurs des nouvelles tuiles, documentation, CHANGELOG | À faire | T3 à T5 | D06 | S | — |
| T7 | Contrôle en jeu par l'utilisateur | À faire | T6 | — | S | — |

## T2 — Cœur

Fichiers : `LWC_Profiles.lua` (`P.shared`, `registerShared`, `memberOf`, `consumerIdOf`, `draw`), `LWC_Gates.lua`
(`G.idOf`), `Gates/LWC_GateNotify.lua`, `LWC_Switch.lua` (`switchable`), `client/LWC_SwitchMenu.lua` ;
`tests/test_shared.py`, test d'unicité de `tests/test_profile_files.py` (un sprite partagé sous le même `shared`).

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 195 tests`, `OK`.
