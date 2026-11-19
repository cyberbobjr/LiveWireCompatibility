# Plan 002 — Interrupteur marche/arrêt et coupure effective des machines

ADR : [ADR-002](../ADR/002-interrupteur-et-coupure-des-machines.md) (acceptée le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| I1 | Socle : module interrupteur (état ModData, `powered`), facture 0 W éteinte dans `P.definition`, champ `switch` des profils | Terminée (2026-11-20) | — | D01, D02, D03 | M | — |
| I2 | Commande serveur `setSwitch` (validation, ModData, transmission, invalidation de la mesure) et menu « Allumer / Éteindre », traductions EN/FR | Terminée (2026-11-20) | I1 | D04, D04 bis, D07 | M | I3 |
| I3 | Registre des types de garde `Gates/` : `object`, `square` repris de `wrapGate`, puis `action`, `call`, `custom` ; message de refus | Terminée (2026-11-20) | I1 | D02, D04 bis, D05 | M | I2 |
| I4 | Garde `menu` côté client (options grisées), après exploration des champs d'option de `ISContextMenu` | Terminée (2026-11-20) | I3 | D05 | S | I5, I6, I7 |
| I5 | Profil Artel : interrupteurs, gardes de D06, exploration `PMK.dryPause` et facture pendant le cycle (D03) | Terminée (2026-11-20) | I3 | D03, D05, D06 | M | I4, I6, I7 |
| I6 | Profil FA2 : gardes `call` et `action`, hotte exclue | Terminée (2026-11-20) | I3 | D05, D06 | S | I4, I5, I7 |
| I7 | Profils Machinery, PWS, Computer Mod, True Moozic : drapeaux `switch`, gardes existantes sur `powered` ; vérifier les sprites du juke-box | Terminée (2026-11-20) | I3 | D01, D06 | S | I4, I5, I6 |
| I8 | Profil Project Arcade : `menu`, `action`, `call` sur le pousse-pièces | Terminée (2026-11-20) | I4 | D05, D06 | S | — |
| I9 | Documentation : architecture, spécifications, wiki EN/FR, `CHANGELOG.md`, renvoi depuis ADR-001 D04 | À faire | I2, I5-I8 | — | S | — |
| I10 | Passage en jeu nominal : solo puis multijoueur (PZDevKit) | À faire | I9 | D08 | M | — |

## I1 — Socle

Fichiers : `shared/LiveWireCompatibility/LWC_Switch.lua` (nouveau : `isOff(o)`, `powered(o)`, `hasSwitch(id)`),
`LWC_Profiles.lua` (`definition` : 0 W si éteinte ; validation du champ `switch`), `tests/test_switch.py`.
Critère : une machine `switch = true` éteinte rend 0 W et `powered` faux ; clé absente = allumée.

## I2 — Commande et menu

Fichiers : `server/LiveWireCompatibility/LWC_SwitchServer.lua` (commande `LWC` / `setSwitch`),
`client/LiveWireCompatibility/LWC_SwitchMenu.lua` (marche jusqu'à la machine, puis commande ; solo sans réseau),
`shared/Translate/EN|FR/IG_UI.json` et `ContextMenu.json`. Refus serveur : objet introuvable, pas un consommateur d'un
profil actif à interrupteur, joueur hors de portée.

Précision : Live Wire relit la consommation de chaque objet à chaque mesure (toutes les 10 minutes de jeu) ; une invalidation n'est donc pas nécessaire (`inverterOfObject` ne vaut que pour l'objet onduleur lui-même, `LW_API.lua:137`). Le changement est facturé à la mesure suivante.

## I3 — Types de garde

Fichiers : `shared/LiveWireCompatibility/Gates/LWC_Gate<Kind>.lua` (un par type), registre dans `LWC_Gates.lua`,
`wrapGate` de `LWC_Profiles.lua` délègue au registre. Chaque garde : installation unique, arguments et retours
préservés, refus via `powered` (D02), message joueur côté client (D04 bis).

Fait : `LWC_Gates.lua` (registre et aides), `Gates/LWC_GateCheck.lua` (object, square), `LWC_GateAction.lua`, `LWC_GateCall.lua`, `LWC_GateMenu.lua`, `LWC_GateCustom.lua` ; côtés `client` et `server`. Tests : `tests/test_gates.py`, `tests/test_switch.py`.

Preuve du vert (I1 à I4, un seul commit) : `python -B -m unittest discover -s tests` → `Ran 84 tests`, `OK` ; `luacheck Contents` → 0 erreur (seul avertissement : `instanceof`, global du jeu) ; `pz_workshop_project.py validate .` → code 0.

## I4 — Garde menu

Exploration d'abord : champs d'une option (`target`, `param1…`), `notAvailable` et infobulle dans `ISContextMenu`
42.22 (`E:\pz-source-42.22`). Puis la garde : handler inscrit après ceux des mods cibles.

Exploration : options `options[1..numOptions-1]`, champs `target`, `param1..10`, `subOption`, `notAvailable`, `toolTip` (`ISContextMenu.lua:849-884`) ; `OnPreFill` puis `OnFill` (`ISWorldObjectContextMenu.lua:190, 213`) : notre handler sur `OnFill` passe après les menus de FA2 et Project Arcade.

## I5 — Artel

Fichiers : `Profiles/LWC_Artel.lua`, `tests/test_artel.py` (classe Artel sortie de `tests/test_profile_files.py`).
Les six machines ont l'interrupteur. Facture réelle (D03) : un lot est lisible sur l'autorité depuis l'objet
(composant `DryingCraftLogic`, `getActiveCraftCount() > 0`, drapeau Artel `PMK_EDryerNoPower` absent) : sécheuse
2000 W, sublimatrice 700 W pendant un lot, 5 W sinon. Gardes : `PMK.Well.isPowered`, `PMK.Trade.gridPowered`,
`PMK.QBase.squarePowered` (gardée plutôt que `hasPower` : le choix du sprite sombre l'appelle directement) ;
`custom` serveur « Artel drying pause » (`thaw` note le lot, `PMK_StationApplyStage` décide geler ou dégeler
selon la machine : un lot ne connaît pas sa station) ; `custom` serveur sur `PMK.QBase.rebuild` (l'état de
l'interrupteur suit le nouvel objet, `Switch.write`) ; `call` client `PMK_CraftBenchPanel.isUsable` (table de
chimie). Corrections de données : table de chimie facturée aussi face est (`Artel_58`), clones sombres de la Quantum
Base inscrits.

Preuve du vert : `python -B -m unittest tests.test_artel tests.test_profile_files` → `Ran 32 tests`, `OK` ;
`python tools/check_sprites.py` → `Artel: 40 sprites found`, code 0.

Non couvert : l'infusion de la table de chimie (autre `DryingCraftLogic`) n'est pas mise en pause par Artel ; les
boutons du panneau de chimie restent dessinés actifs (le clic est refusé avec le message).

## I6 — Functional Appliances 2

Fichiers : `Profiles/LWC_FunctionalAppliances2.lua`, `tests/test_fa2.py`. Interrupteur : hot-dog, pop-corn,
fontaine, SlurpNBurp, tireuses. Gardes `call` client sur les `onUse…` (le choix « Off » passe toujours) et
`FA.updateMachineTemp` (passe en Off par la branche d'arrêt de FA2) ; `action` sur `UseHotDogMachine`,
`UsePopcornMachine`, `UseSodaFountain`, `UseBarTaps`, des deux côtés (classes `shared` avec `complete()`).
Hotte : ni interrupteur ni garde.

Preuve du vert : `python -B -m unittest tests.test_fa2 tests.test_profile_files` → `Ran 16 tests`, `OK`.

## I7 — Machinery, PWS, Computer Mod, True Moozic

Fichiers : les quatre profils, `tests/test_small_profiles.py`. Interrupteur : huit machines Machinery, station PWS.
Interrupteurs natifs gardés : Computer Mod, juke-box (garde `TMJukebox.hasPower` limitée au client, seul appelant).
Sprites du juke-box vérifiés : `recreational_01_0` et `_1` sont les deux seules tuiles `CustomName=Jukebox` du
jeu. Tour à métal : Machinery passe souvent une autre tuile que la tuile facturée ; résolu dans le cœur
(`Gates.billed` : grille de sprites ou entité multi-cases B42).

Preuve du vert : `python -B -m unittest tests.test_small_profiles tests.test_profile_files` → `Ran 20 tests`,
`OK` ; `check_sprites` → Machinery 44, PWS 2, ComputerMod 8, TrueMoozic 2, code 0.

## I8 — Project Arcade

Fichiers : `Profiles/LWC_ProjectArcade.lua`, `tests/test_project_arcade.py`. Interrupteur sur les six machines.
Gardes client : `menu` (bornes, flippers, punching-ball ; pince par une lecture dédiée de l'option, la machine
n'étant que dans la fermeture), `action` sur les quatre actions de jeu, `call` sur
`ProjectArcade_CoinPusher.OpenUI` et `ProjectArcade_CoinPusherUI.beginPlay` (ferme le panneau avant paiement).
Correction de données : borne assise facturée sur la pièce que le mod fait jouer (`pa_complex_3`, `4`, `6`, `9`).

Preuve du vert : `python -B -m unittest tests.test_project_arcade tests.test_profile_files` → `Ran 21 tests`,
`OK` ; `check_sprites` → `ProjectArcade: 68 sprites found`.

Limite : « Voir les scores » du punching-ball est grisé aussi quand la machine est éteinte (même paramètre).

## I10 — Passage en jeu

Liste nominale courte : éteindre et rallumer une machine de chaque mod (0 W dans « Consommateurs »), utilisation
refusée et message, lot Artel en pause puis repris, disjoncteur coupé = machine arrêtée. Codes de sortie, ligne
`summary` et dossier `runs/...` cités dans la fiche.
