# Plan 002 — Interrupteur marche/arrêt et coupure effective des machines

ADR : [ADR-002](../ADR/002-interrupteur-et-coupure-des-machines.md) (acceptée le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| I1 | Socle : module interrupteur (état ModData, `powered`), facture 0 W éteinte dans `P.definition`, champ `switch` des profils | À faire | — | D01, D02, D03 | M | — |
| I2 | Commande serveur `setSwitch` (validation, ModData, transmission, invalidation de la mesure) et menu « Allumer / Éteindre », traductions EN/FR | À faire | I1 | D04, D04 bis, D07 | M | I3 |
| I3 | Registre des types de garde `Gates/` : `object`, `square` repris de `wrapGate`, puis `action`, `call`, `custom` ; message de refus | À faire | I1 | D02, D04 bis, D05 | M | I2 |
| I4 | Garde `menu` côté client (options grisées), après exploration des champs d'option de `ISContextMenu` | À faire | I3 | D05 | S | I5, I6, I7 |
| I5 | Profil Artel : interrupteurs, gardes de D06, exploration `PMK.dryPause` et facture pendant le cycle (D03) | À faire | I3 | D03, D05, D06 | M | I4, I6, I7 |
| I6 | Profil FA2 : gardes `call` et `action`, hotte exclue | À faire | I3 | D05, D06 | S | I4, I5, I7 |
| I7 | Profils Machinery, PWS, Computer Mod, True Moozic : drapeaux `switch`, gardes existantes sur `powered` ; vérifier les sprites du juke-box | À faire | I3 | D01, D06 | S | I4, I5, I6 |
| I8 | Profil Project Arcade : `menu`, `action`, `call` sur le pousse-pièces | À faire | I4 | D05, D06 | S | — |
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

## I3 — Types de garde

Fichiers : `shared/LiveWireCompatibility/Gates/LWC_Gate<Kind>.lua` (un par type), registre dans `LWC_Gates.lua`,
`wrapGate` de `LWC_Profiles.lua` délègue au registre. Chaque garde : installation unique, arguments et retours
préservés, refus via `powered` (D02), message joueur côté client (D04 bis).

## I4 — Garde menu

Exploration d'abord : champs d'une option (`target`, `param1…`), `notAvailable` et infobulle dans `ISContextMenu`
42.22 (`E:\pz-source-42.22`). Puis la garde : handler inscrit après ceux des mods cibles.

## I5 — Artel

Exploration de `PMK.dryPause` (`recOf`, `isHeld`, clé `crd`) : retrouver la machine depuis `crd`, savoir si un lot
tourne. Garde `custom` sur `thaw` (serveur) ; facture pendant le cycle si l'état est lisible, sinon moyenne conservée.

## I6 à I8 — Autres profils

Gardes et leviers de la table D06 de l'ADR. Chaque profil garde ses tests de forme dans `tests/test_profile_files.py`.

## I10 — Passage en jeu

Liste nominale courte : éteindre et rallumer une machine de chaque mod (0 W dans « Consommateurs »), utilisation
refusée et message, lot Artel en pause puis repris, disjoncteur coupé = machine arrêtée. Codes de sortie, ligne
`summary` et dossier `runs/...` cités dans la fiche.
