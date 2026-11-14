# Badlands Power (Workshop 3804093735, id BadlandsPower)

Analyse du 2026-11-13, **confirmée statiquement** (copie Workshop en lecture seule, `108600\3804093735\mods\BadlandsPower\`). Rien n'a été testé en jeu.

Ce mod est une **source d'électricité**. LiveWire ne voit que `IsoGenerator` comme source, et c'est bien le cas ici : toutes les machines produisant du courant sont des `IsoGenerator`.

## 1. Variante chargée en 42.22

- Dossier `42/` (sans suffixe `.1`), `common/` (tiledef, pack) et `mod.info` racine (`versionMin=42.20.0`, métadonnée).
- Règle de choix : `ZomboidFileSystem.java:454-466`. `42` = 42000 <= 42022 : **`42/` est chargé en 42.22.**

## 2. Sources posées (IsoGenerator)

| Item (`42/media/scripts/badlandspower_items.txt`) | Sprite de pose | Tags | Rôle |
|---|---|---|---|
| `BL_BatteryBank` (l.3-14) | `badlands_power_01_0` (rack vide ; superposition de batteries `badlands_power_01_<20 + (n-1)*4 + orientation>`, `BadlandsPower_Bank.lua:~100`) | `base:generator` | Banque de batteries, source silencieuse |
| `BL_GenPropane` (l.20-31) | `badlands_power_01_4` | `base:generator` | Groupe propane portatif |
| `BL_GenWasteOil` (l.37-48) | `badlands_power_01_8` | `base:generator` | Groupe à huile usagée, stationnaire |
| `BL_GenScrap` (l.54-65) | `badlands_power_01_12` | `base:generator` | Groupe de fortune, portatif |
| `BL_GenDiesel` (l.71-82) | `badlands_power_01_16` | `base:generator` | Groupe « 10 kW » à châssis (tooltip EN : « Ten kilowatt frame generator ») |

- Les items sont `base:normal` avec un `WorldObjectSprite` : ils deviennent des objets posés à la pose.
- Création côté monde : `BadlandsPower_MapObjects.lua:22` (`IsoGenerator.new(item, cell, square)`) et `BadlandsPower_RoomSpawns.lua:54` (même appel, spawns de pièces).
- La banque : `BadlandsPower_Bank.lua:1-3` (« The bank is an IsoGenerator »), avec un conteneur `BLBatteryRack` (5 emplacements, `UNITS_PER_BATTERY = 2`, soit 10 unités = réservoir moteur).

## 3. Mécanisme d'alimentation des cases

- Une source alimente les cases **par le moteur vanille** : `IsoGenerator.setSurroundingElectricity` (IsoGenerator.java:251-290, reproduit dans `LW_Demand.lua:3`). Le mod n'écrit aucun `setHaveElectricity` de son côté.
- La banque n'a pas de carburant propre : sa jauge `fuel` reflète la somme de la charge des batteries (`BadlandsPower_Bank.lua:~84-100`). `BP.bankTick` (chaque minute en jeu) retire la consommation du moteur, au prorata, avec `DRAIN_MULT = 2.0`.
- **Recharge depuis l'extérieur** : `BP.hasOutsidePower(sq)` (`BadlandsPower_Bank.lua:94-96`) = `sq:haveElectricity()` ou (`sq:hasGridPower()` et `sq:getRoom() ~= nil`). Si la banque est arrêtée et que la case a du courant, elle recharge : `CHARGE_PER_HOUR = 0.10` par batterie et par heure en jeu (`BadlandsPower_Bank.lua:32`), soit plein en environ 10 heures.
- Usure : `WEAR_PER_CYCLE = 2` par décharge complète (`:33`).

## 4. État « en marche » et puissance

- État : `gen:isActivated()` (vanille). Clé ModData propre : `md.blWasOn` (`BadlandsPower_Bank.lua:295`, interne au mod). Carburant : `gen:getFuel()`.
- Puissance : seul `BL_GenDiesel` a un chiffre (10 kW, tooltip). Les autres n'ont pas de puissance écrite. La banque n'a pas de watts : sa grandeur est une charge (fraction par batterie), pas une puissance.

## 5. Consommateurs

- **Aucun consommateur propre** : le mod ne pose pas de machine électrique.
- **API consommateur pour les autres mods** : `BadlandsPower.consumers` (`lua/server/BadlandsPower_Consumers.lua:1-30`, `C.register`, `C.setDraw`, `C.isPowered`). Elle facture en unités de carburant par heure, côté serveur, les machines d'un autre mod : ordre réseau (gratuit) puis générateur à portée puis rien. **Point d'attention** : si un objet est facturé à la fois par cette API et par LiveWire, il y a double comptage. Aucun profil LiveWire ne doit viser un objet de la même famille.

## 6. Verdict

- **Source, déjà vue par LiveWire** : les cinq machines sont des `IsoGenerator`. LiveWire les traite comme sources (`LW_Backup.lua:67`, `LW_Demand.lua:2-3`). **Pas de profil consommateur** pour les groupes.
- **Point à décider** : la banque, en recharge depuis le réseau, est un **flux consommateur** sur le réseau public (`hasOutsidePower` : `hasGridPower` en intérieur). Cette recharge n'est pas facturée par LiveWire, car la banque est un `IsoGenerator` (côté source). Un profil consommateur sur la banque serait conceptuellement double (source et consommateur) et n'a pas de watts sourcés (la charge est en fraction de batterie, pas en puissance). Décision : laisser non facturée, ou ajouter une règle de recharge dans LiveWire (hors profil).

## Profil proposé

Non proposé. Les groupes et la banque sont des sources déjà reconnues par LiveWire. La recharge de la banque ne relève pas d'un profil : c'est une règle de source/recharge, à traiter côté LiveWire si l'on veut la facturer. Aucun code de profil n'est justifié pour ce mod en l'état.
