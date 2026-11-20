# Knox Working Machines (Workshop 3841890337)

Analyse du 2026-11-20. Lecture seule de la copie Workshop `108600\3841890337\mods\KnoxWorkingMachines\`. Constats
**confirmés statiquement** sauf mention contraire ; rien n'a été testé en jeu. Abréviation : `K\` = `...\KnoxWorkingMachines\42\media\`.

## 0. Variante chargée en 42.22

`id=KnoxWorkingMachines`, `name=Knox Working Machines [B42.22]`, `versionMin=42.21.0` (`42\mod.info`). Seul `42/` est
chargé (`common/` vide). Lua : client `KWM_CarWashMenu.lua`, `KWM_PowerGate.lua` ; serveur `KWM_Attach.lua` ; partagé
`KWM_Moveables.lua`, `KWM_Sprites.lua`, `TimedActions/KWM_CarWashAction.lua`. Aucune tuile propre, aucun pack, aucune
carte de profondeur : **toutes les tuiles sont vanilla**. Option `KnoxWorkingMachines.RequirePower` (vrai par défaut).

## 1. Machines électriques (`KWM_PowerGate.lua:9-83`, `RequiresPower`)

Chaque machine est un meuble déplaçable avec une station (CraftBench) par face ; tours et fraiseuse sont faits de
**sections indépendantes** (une tuile = une entité `KWM_*`), pas d'un meuble de plusieurs cases.

| Machine | Sprites | Estimation |
|---|---|---|
| Perceuse à colonne | `industry_02_268`-`271` | 400 W en marche |
| Scie de table | `industry_02_152`-`155` | 1 500 W en marche |
| Tour vert (3 sections) | `industry_03_0`-`5`, `8`-`13` | 500 W par machine |
| Tour bleu (3 sections) | `industry_03_32`-`37`, `40`-`45` | 500 W par machine |
| Fraiseuse (4 sections) | `industry_03_48`-`63` | 750 W par machine |
| Presse hydraulique | `industry_02_46`, `47` | 750 W |
| Touret | `industry_04_20`-`23` | 370 W |
| Panneau de charge | `industry_02_163`-`175` sauf 166, 167 | 150 W |
| Ligne de mise en conserve | `industry_02_49`, `50`, `54`, `55` | 1 200 W |
| Pont élévateur | `location_business_machinery_01_0`, `2`, `11`, `13` | 1 500 W (intermittent) |
| Lavage auto (brosses, rideaux) | `location_business_machinery_01_6`, `14`, `36`, `37` | 1 000 W (hypothèse) |

Non électriques : poste de soudure, étaux, fours, râteliers de bouteilles, banc à pneus, fûts de carburant. Aucune machine
n'est facturée par le moteur (objets `IsoObject` sans conteneur réfrigéré ni carburant, `IsoObject.java:4800-4806`).

**Chevauchement avec Machinery** : 24 tuiles communes (perceuse, centres des tours, `industry_03_48`-`55`, touret), pas
toujours pour la même machine (`industry_03_48`-`55` : presse hydraulique pour Machinery, fraiseuse ici). Voir ADR-005.

## 2. Utilisation et tests de courant

- Fenêtre de station : vanilla `ISEntityUI.CanOpenWindowFor` (`ISEntityUI.lua:333`, global, client), que Knox enveloppe
  déjà (`KWM_PowerGate.lua:92-103`, test `haveElectricity() or hasGridPower()` l.98). `ISEntityUI.ValidateOpenWindows`
  la relance sur `OnElectricityChanged` (`ISEntityUI.lua:564, 753`).
- Lancement d'une fabrication : `ISEntityUI.GenericCraftStart` (`:71`) et `GenericCraftTransferAndStart` (`:89`), globales ;
  action `ISGenericCraftStart` (`shared/Entity/TimedActions/ISGenericCraftStart.lua:5`), sans test de courant.
- Lavage auto : test dans la fonction `local onFillMenu` (`KWM_CarWashMenu.lua:50-67`) ; l'option porte la machine et le
  véhicule ; l'action `KWM_CarWashAction` ne garde que le véhicule.
- Aucun état de marche propre, aucune ModData : pas d'interrupteur ; seul l'état de fabrication du moteur.
- Multijoueur : fenêtre et lancement côté client ; `complete` du lavage côté serveur.

## 3. Points d'interception retenus

1. `ISEntityUI.CanOpenWindowFor` (fenêtre) et `ISGenericCraftStart:isValid` (fabrication en cours), côté client.
2. Menu du lavage : garde `menu` (la machine est un paramètre de l'option).
3. Interrupteur du mod pour toutes les machines (aucun interrupteur propre).
