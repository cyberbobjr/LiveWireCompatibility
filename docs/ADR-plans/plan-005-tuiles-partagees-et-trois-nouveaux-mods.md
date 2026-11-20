# Plan 005 — Tuiles partagées ; Knox Working Machines, STFO 3T et CamRecorder

ADR : [ADR-005](../ADR/005-tuiles-partagees-et-trois-nouveaux-mods.md) (acceptée le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| T1 | Analyses D05 des trois mods (`annexes/recherches/`) | Terminée (2026-11-20) | — | — | M | — |
| T2 | Cœur : `shared`/`owns`, inscription unique, `memberOf`/`consumerIdOf` utilisés par gardes, interrupteur et menu ; tests | Terminée (2026-11-20) | — | D01 | M | — |
| T3 | Profil Knox Working Machines ; tuiles partagées avec Machinery | Terminée (2026-11-20) | T2 | D02, D03 | M | T4, T5 |
| T4 | Profil STFO (secteur seulement, batterie intacte) | Terminée (2026-11-20) | T2 | D04 | M | T3, T5 |
| T5 | Profil CamRecorder ; ordinateur partagé avec Computer Mod | Terminée (2026-11-20) | T2 | D02, D05 | M | T3, T4 |
| T6 | Profondeurs des nouvelles tuiles, documentation, CHANGELOG | Terminée (2026-11-20) | T3 à T5 | D06 | S | — |
| T7 | Contrôle en jeu par l'utilisateur | À faire | T6 | — | S | — |

## T2 — Cœur

Fichiers : `LWC_Profiles.lua` (`P.shared`, `registerShared`, `memberOf`, `consumerIdOf`, `draw`), `LWC_Gates.lua`
(`G.idOf`), `Gates/LWC_GateNotify.lua`, `LWC_Switch.lua` (`switchable`), `client/LWC_SwitchMenu.lua` ;
`tests/test_shared.py`, test d'unicité de `tests/test_profile_files.py` (un sprite partagé sous le même `shared`).

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 195 tests`, `OK`.

Correction du 2026-11-20 (T5) : un membre partagé qui déclare `couldBePowered` faisait boucler la recherche (LiveWire
appelle `couldBePowered`, qui rappelait LiveWire) ; `P.memberIn(group, o)` ne repasse plus par LiveWire, et le double de
LiveWire de `tests/test_shared.py` appelle `couldBePowered` comme le vrai.

## T3 — Knox Working Machines

`Profiles/LWC_KnoxWorkingMachines.lua`, `tests/test_knox.py` ; `Profiles/LWC_Machinery.lua` reçoit `shared` sur quatre
consommateurs (repli, consommations inchangées). Knox possède un objet dont l'entité est `KWM_*` (`getEntityScript():getName()`,
`GameEntity.java:148`) et qui n'a pas de données Machinery. Gardes : `ISEntityUI.CanOpenWindowFor`, `ISHandcraftAction`
(les stations Knox sont des CraftBench, `ISEntityUI.lua:107-130`), menu du lavage auto. Limite : une machine encore jamais
utilisée par Machinery appartient à Knox quand les deux mods sont actifs.

## T4 — STFO

`Profiles/LWC_STFO.lua`, `tests/test_stfo.py`. `SimpleTraps.power` : le secteur coupé rend la batterie chargée de
l'appareil ; éteint avec notre interrupteur, rien (correction de l'orchestrateur, ADR-002 D01). Têtes de projecteur et de
tourelle : objets distincts, non facturés.

## T5 — CamRecorder

`Profiles/LWC_CamRecorder.lua`, `tests/test_camrecorder.py` ; `Profiles/LWC_ComputerMod.lua` partagé (`VanillaDesktop`,
repli). Live Wire (commit `4ae8020`) : `Consumers.of` se replie sur `getSpriteName()` pour un sprite rechargé sans nom sur
un serveur dédié (caméra fixée, sprite-texture) ; même repli dans `LWC_Switch`. `tools/check_sprites.py` accepte un
sprite-texture présent dans le mod cible. Limites : moniteurs partiellement coupés (appels internes à une fonction
`local`) ; un PC jamais ouvert appartient à Computer Mod jusqu'à son premier allumage.

## T6 — Profondeurs et documentation

`tools/build_depth.py` → `DEPTH_simpletraps_01.png` (13 sprites ; `simpletraps_01_114` est une tuile vide) ; Knox et
CamRecorder utilisent des tuiles vanilla déjà pourvues. Outils : sprites-textures et tuiles vides ignorés. Wiki FR/EN,
spécifications, architecture, ADR-001, CHANGELOG.

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 261 tests in 0.718s OK` ; `python tools/check_sprites.py` → 10 profils, code 0 ;
`python tools/check_depth.py` → code 0 ; `python tools/build_depth.py` → code 0 ; `luacheck Contents` → 0 avertissement.
