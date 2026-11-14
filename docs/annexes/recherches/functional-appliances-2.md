# Functional Appliances 2 (B42, 42.20) : appareils électriques pour LiveWire

Base : `108600\3042138819\mods\FunctionalAppliances2\` (abrégé `FA2\`). Lecture seule. Tous les constats sont
**confirmés statiquement** (lecture du Lua et du code Java décompilé de référence), sauf mention « hypothèse ».
Rien n'a été testé en jeu. Les puissances sont des **estimations**.

## 0. Réponses aux questions transverses

- **Variante chargée en 42.22 : `42.20`.** `FA2\42.20\mod.info` porte `versionMin=42.20`. Confirmé statiquement :
  le moteur choisit le dossier de version au nom le plus haut compris entre le minimum requis et la version du jeu
  (`E:\pz-source-42.22\java\zombie\ZomboidFileSystem.java:454-467`), puis ne charge que `common\media` et
  `<version>\media` (`:481-495`). Donc `FA2\42.16\` n'est pas chargé, et la racine `FA2\media\` (sans dossier de
  version, sans `common`) n'est pas chargée non plus selon ce code. Aucun dossier `common` n'existe.
- **Ce que FA 2 fait du courant.** FA 2 ne consomme rien. Il teste `square:haveElectricity()` (méthode Java :
  réseau ou générateur) ou une grâce `SandboxVars.ElecShutModifier` (nuits survécues), en ligne, dans les menus :
  par exemple `FA2\42.20\media\lua\client\PopcornMachineMenu.lua:4` et `:32`. Ces variables sandbox sont vanille
  (non définies par le mod).
- **État d'une machine.** `ModData.CustomTemp` ∈ {`Off`, `Cold`, `Warm`, `Hot`}, écrit par
  `FA.updateMachineTemp` (`FA2\42.20\media\lua\client\FAMapObjects.lua:102-129`). Il passe à `Off` quand le test de
  courant échoue, mais **seulement à la prochaine mise à jour** de l'objet (chargement de la case, action du menu).
  C'est donc le dernier état connu, pas un état en direct.
- **Portes (gates) : aucune possible en l'état.** Aucune fonction publique de FA 2 ne renvoie un booléen de courant :
  les tests sont dans des fonctions anonymes des menus. La seule fonction globale liée, `FA.updateMachineTemp`,
  renvoie la machine (pas un booléen). Un wrapper « gate » la ferait renvoyer `false` : `FAInitContextMenus.lua:41-50`
  réaffecte `thisObject = FA.updateMachineTemp(thisObject)` puis appelle `doBuildMenu(..., thisObject)`, qui
  planterait sur `false`. **Ne pas wrapper cette fonction.**
- **Limite de fond.** `haveElectricity()` est une méthode Java de `IsoGridSquare`. LiveWire ne peut pas la couper
  depuis Lua : une coupure de circuit LiveWire arrête le wattage facturé, mais FA 2 continue de voir le courant.

## 1. Tableau de synthèse

| Appareil (menu FA 2) | Sprites posés (noms exacts) | Classe Java | Déjà compté par LiveWire ? | État lisible | Portes | Verdict |
|---|---|---|---|---|---|---|
| Comptoir chauffant (`FAHeatedCounter`) | `location_restaurant_generic_01_16` à `_23` | non confirmée | Non (hypothèse : aucune famille ne correspond, à vérifier par `applianceKind`) | `ModData.CustomTemp` | aucune | **à profiler** |
| Vitrine réfrigérée ou chauffée (`FADisplayCounter`) | `location_restaurant_generic_01_24..29`, `_32..37` ; `location_shop_generic_01_32..35` ; `location_restaurant_pie_01_48..51` ; `location_restaurant_seahorse_01_56..59` ; `location_restaurant_pizzawhirled_01_64..67` | non confirmée | Non (hypothèse, voir section 3 pour le conteneur) | `ModData.CustomTemp` | aucune | **à profiler** |
| Distributeurs snack (`FAVendingMachine`) | `location_shop_accessories_01_16`, `_17`, `_28`, `_29` | non confirmée | Non | `ModData.CustomTemp` | aucune | **à profiler** |
| Distributeurs soda (`FAVendingMachine`) | `location_shop_accessories_01_18`, `_19`, `_30`, `_31` | non confirmée | Non | `ModData.CustomTemp` | aucune | **à profiler** |
| Machine à hot-dog (`FAHotDogMachine`) | `location_shop_fossoil_01_10`, `_11` (vanille probable) ; `_72`, `_73` (nouveaux selon `FATiles.lua:49`) | non confirmée | Non | aucun (pas de mode) | aucune | **à profiler** |
| Machine à pop-corn (`FAPopcornMachine`) | `location_entertainment_theatre_01_17` (vanille, `FATiles.lua:57`) | non confirmée | Non | aucun | aucune | **à profiler** |
| Fontaine à soda (`FASodaFountain`, « Tabletop Soda ») | `location_shop_accessories_01_8`, `_9`, `_12`, `_13` (vanille, `FATiles.lua:70`) | non confirmée | Non | aucun | aucune | **à profiler** |
| SlurpNBurp (`FASodaFountain`, « SlurpBurp ») | `location_shop_zippee_01_56`, `_57` (vanille) ; `_60`, `_61` (nouveaux, `FATiles.lua:62`) | non confirmée | Non | aucun | aucune | **à profiler** |
| Robinets de bar (`FABarTaps`) | `location_restaurant_bar_01_32` à `_35` (`_32` cité `BarTapsMenu.lua:10`) | non confirmée | Non | aucun | aucune | **à profiler** (liste à confirmer) |
| Hotte de ventilation (`FAExhaustVents`) | `appliances_cooking_01_68` à `_71` (vanille) | à vérifier | inconnu | aucun | aucune | **à vérifier**, non profilée |
| Générateur (`SiloGenerator`) | `IsoGenerator` | source | non applicable | `isActivated()` | non applicable | **non facturable** (source) |
| Friteuses, cafetière, horloge murale, téléphones publics | divers | non confirmée | Non | aucun | aucune : ces menus ne contiennent aucun test `haveElectricity` | **non facturable** selon FA 2 |
| Bancs, panneaux, liège, porte-serviettes, distributeurs de papier, support de queue | divers | non concernée | non applicable | aucun | aucune | **non concerné** |

Les 10 fichiers qui contiennent `haveElectricity` ou `AllowExteriorGenerator` (grep sur `42.20\media\lua`) sont
`FAServer.lua`, `FAMapObjects.lua`, `VendingMachinesMenu.lua`, `FAExhaustVents.lua`, `BarTapsMenu.lua`,
`SodaFountainMenu.lua`, `HeatedCountersMenu.lua`, `DisplayCountersMenu.lua`, `PopcornMachineMenu.lua`,
`HotDogMachineMenu.lua`. `FAServer.lua` n'a pas été lu.

## 2. Fiches

### 2.1 Comptoirs chauffants et vitrines (`FAMapObjects.lua`, `HeatedCountersMenu.lua`, `DisplayCountersMenu.lua`)
- **Routage** : `FAInitContextMenus.lua:41-48`. Les sprites sont des listes en dur dans `FAMapObjects.lua:17-60`.
- **Modes** : `Warm` (1.5), `Hot` (1.61), `Cold` (0.1), `Off` (1). Un mode non `Off` exige le courant
  (`HeatedCountersMenu.lua:95-104`, `FAMapObjects.lua:107-120`).
- **Mode par défaut** (confirmé statiquement) : `FAMapObjects.lua:67-79` met `Warm` sur les comptoirs hors cuisines
  froides, `Cold` dans les salles de glaces ou épiceries.
- **Puissance (estimation)** : comptoir chauffant `Hot` 800 W, `Warm` 400 W, `Cold` 150 W (ordre de grandeur d'un bac
  chauffant commercial). Vitrine `Warm` 150 W, `Cold` 200 W (ordre de grandeur d'une vitrine réfrigérée).
- **Lecture** : `running = mode ~= "Off"`. Pas de porte.

### 2.2 Distributeurs snack et soda (`FAMapObjects.lua:3-15`, `VendingMachinesMenu.lua:58-69`)
- Sprites : `_16`, `_17`, `_28`, `_29` (snack, groupe « Snack Vending » dans `FATiles.lua:390-410`) ; `_18`, `_19`,
  `_30`, `_31` (soda, `FATiles.lua:361-388`). Les deux groupes sont vanille (`FATiles.lua:361`, `:390`).
- Modes : `Warm` (1.5) et `Cold` (0.25). Le texte du choix `Cold` exige le courant.
- **Puissance (estimation)** : 200 W en `Cold`, 300 W en `Warm`.

### 2.3 Machines sans mode stocké (hot-dog, pop-corn, soda, SlurpNBurp, robinets)
- **Aucun état stocké** : `FAHotDogMachine` et `FAPopcornMachine` règlent seulement la température du conteneur selon
  le courant (`HotDogMachineMenu.lua:4-8`, `PopcornMachineMenu.lua:4-8`). La fontaine à soda ne garde pas d'état
  (`SodaFountainMenu.lua:245`).
- **Conséquence** : pas de lecture « en marche ». Seul un **tirage constant** est possible, ce qui facture aussi
  l'inactivité.
- **Puissance (estimations)** : hot-dog 200 W, pop-corn 200 W, fontaine à soda 200 W, SlurpNBurp 250 W, robinets 150 W.
- **Robinets** : la porte d'usage est `BarTapsMenu.lua:144`. Seuls `_32` à `_35` sont retenus : les autres sprites de
  `FATiles.lua:275-359` (bars brun, noir, bois) sont des comptoirs, rôle non confirmé.

### 2.4 Hotte de ventilation (`FAExhaustVents.lua`) : à vérifier, non profilée
- Sprites `appliances_cooking_01_68` à `_71`, vanille. Le code ne fait que lever la toxicité d'un bâtiment, et seulement
  si un générateur actif est présent (`:74-89`). Aucun wattage dans le Lua.
- Si la classe vanille de ces sprites est `IsoStove`, LiveWire les compte déjà. Sinon, un profil d'environ 60 W serait
  possible. **Non tranché : classe non vérifiée.**

### 2.5 Sources et non-consommateurs
- `SiloGenerator` : génère du courant (`IsoGenerator`, `isActivated()` à `FAExhaustVents.lua:80`). Ce n'est pas un
  consommateur.
- Friteuses, cafetière, horloge murale, téléphones publics : aucune occurrence de `haveElectricity` dans leurs fichiers.
  FA 2 ne les rend pas électriques, donc non facturables.

## 3. Objets déjà facturés par le moteur (à vérifier)

- Aucune famille native ne couvre explicitement ces sprites. Les conteneurs déclarés par FA 2 sont `hotdogMachine`,
  `popcornMachine`, `slurpNBurp`, `bulletinBoard`, `pegBoard`, `poolCueStand`, `napkinDispenser`, `papertowelDispenser`
  (`FATiles.lua:78-120`). Aucun n'est `fridge` ni `freezer`.
- **Point à vérifier en jeu** : les conteneurs vanille des vitrines et des comptoirs (`location_restaurant_generic`,
  `location_shop_generic`, etc.) ne sont pas lus ici. Si l'un est `fridge` (ou `freezer`), `hasFridgeContainer` de
  LiveWire le compte déjà (`LW_ApplianceFamilies.lua:82`) : le profil ferait alors un double comptage.
- Pas d'`IsoStove`, `IsoRadio`, `IsoTelevision`, `IsoLightSwitch` ni `FuelAmount` dans le Lua de FA 2 pour ces sprites.

## 4. Projets de facturation (synthèse à transmettre à LiveWire)

| Consommateur | Sprites | Watts (estimation) | Lecture |
|---|---|---|---|
| `FA2Buffet` | `restaurant_generic_01_16..23` | Hot 800 / Warm 400 / Cold 150 | `running` = mode non `Off` |
| `FA2Display` | `restaurant_generic_01_24..29`, `_32..37`, `shop_generic_01_32..35`, `pie_01_48..51`, `seahorse_01_56..59`, `pizzawhirled_01_64..67` | Warm 150 / Cold 200 | `running` = mode non `Off` |
| `FA2Vending` | `shop_accessories_01_16..19`, `_28..31` | Warm 300 / Cold 200 | `running` = mode non `Off` |
| `FA2HotDog` | `shop_fossoil_01_10, _11, _72, _73` | 200 constant | pas de lecture |
| `FA2Popcorn` | `entertainment_theatre_01_17` | 200 constant | pas de lecture |
| `FA2SodaFountain` | `shop_accessories_01_8, _9, _12, _13` | 200 constant | pas de lecture |
| `FA2SlurpNBurp` | `shop_zippee_01_56, _57, _60, _61` | 250 constant | pas de lecture |
| `FA2BarTap` | `restaurant_bar_01_32..35` | 150 constant | pas de lecture |

**Portes : aucune.** Hotte : en attente de vérification de classe.

## 5. Limites

- `FA.tiles` (et `42.20\media\FA.tiles`) est binaire : le grep ne trouve aucun nom de sprite. La nouveauté des
  sprites repose uniquement sur les commentaires de `FATiles.lua` (« verified new sprites », « verified no new
  sprites »), donc **hypothèse** tant que le binaire n'est pas décodé.
- Les puissances sont des estimations d'équipement commercial. Aucune source web n'a été consultée.
- Les modes sont des dernières valeurs connues (mise à jour à l'ouverture et aux actions). Un `running` peut être en
  retard après une coupure.
- Les appareils à tirage constant facturent aussi l'inactivité : c'est un surcoût volontaire, à arbitrer.
- Tous les objets portant ces sprites sont concernés, y compris ceux posés par la carte de base : `FAMapObjects`
  s'applique à chaque instance (`MapObjects.OnLoadWithSprite`, `FAMapObjects.lua:141-145`).
- Le profil n'est actif qu'avec `FunctionalAppliances2`, ce qui satisfait la règle sur les tuiles vanille réutilisées.
- `FAServer.lua` (un `haveElectricity`) n'a pas été lu.
- Aucun test en jeu. Aucun fichier du mod n'a été modifié.

## Profil proposé

Fichier prévu : `Contents\mods\batman_LiveWireCompatibility\42.21\media\lua\shared\LiveWireCompatibility\Profiles\LWC_FunctionalAppliances2.lua`
(non créé : ce rapport ne modifie aucun autre fichier). Code ASCII uniquement.

```lua
-- LiveWire Compatibility: Functional Appliances 2 (Workshop 3042138819, mod id FunctionalAppliances2).
-- Analysis: docs/annexes/recherches/functional-appliances-2.md. Variant loaded in 42.22: 42.20.
-- Every draw below is an estimate. No gates: FA 2 has no public power test.
-- Not listed on purpose: exhaust hoods (vanilla sprites, class not checked), generator (source),
-- deep fryers, coffee machine, wall clock, payphones (no electricity check in FA 2).
require "LiveWireCompatibility/LWC_Profiles"

-- Appends "<prefix><n>" for each n from `from` to `to` to `out` (new table if nil).
local function range(prefix, from, to, out)
    out = out or {}
    for n = from, to do out[#out + 1] = prefix .. n end
    return out
end

-- Appends "<prefix><n>" for each number of the array `ids` to `out` (new table if nil).
local function list(prefix, ids, out)
    out = out or {}
    for _, n in ipairs(ids) do out[#out + 1] = prefix .. n end
    return out
end

-- FA 2 stores its mode in ModData.CustomTemp: "Off", "Cold", "Warm" or "Hot".
-- It becomes "Off" when power is lost, but only at the object's next update,
-- so this is the last known state, not a live reading.
local function mode(o)
    local md = o:getModData()
    return md and md.CustomTemp or "Off"
end

local function running(o)
    return mode(o) ~= "Off"
end

-- Watts while running, by mode. A mode missing from the table draws 0.
local function byMode(watts)
    return function(o)
        return watts[mode(o)] or 0
    end
end

local buffetSprites = range("location_restaurant_generic_01_", 16, 23)

local displaySprites = range("location_restaurant_generic_01_", 24, 29)
range("location_restaurant_generic_01_", 32, 37, displaySprites)
range("location_shop_generic_01_", 32, 35, displaySprites)
range("location_restaurant_pie_01_", 48, 51, displaySprites)
range("location_restaurant_seahorse_01_", 56, 59, displaySprites)
range("location_restaurant_pizzawhirled_01_", 64, 67, displaySprites)

local vendingSprites = list("location_shop_accessories_01_", { 16, 17, 18, 19, 28, 29, 30, 31 })
local hotdogSprites = list("location_shop_fossoil_01_", { 10, 11, 72, 73 })
local popcornSprites = range("location_entertainment_theatre_01_", 17, 17)
local sodaFountainSprites = list("location_shop_accessories_01_", { 8, 9, 12, 13 })
local slurpSprites = list("location_shop_zippee_01_", { 56, 57, 60, 61 })
local barTapSprites = range("location_restaurant_bar_01_", 32, 35)

LiveWireCompat.Profiles.add({
    name = "FunctionalAppliances2",
    workshop = "3042138819",
    mods = { "FunctionalAppliances2" },
    consumers = {
        -- Heated buffet counter: hot 800 W, warm 400 W, cold 150 W (estimates).
        { id = "FA2Buffet", sprites = buffetSprites,
          watts = byMode({ Hot = 800, Warm = 400, Cold = 150 }), running = running },
        -- Display counter: warm 150 W, cold 200 W (estimates).
        { id = "FA2Display", sprites = displaySprites,
          watts = byMode({ Warm = 150, Cold = 200 }), running = running },
        -- Snack and soda vending machines: warm 300 W, cold 200 W (estimates).
        { id = "FA2Vending", sprites = vendingSprites,
          watts = byMode({ Warm = 300, Cold = 200 }), running = running },
        -- Hot dog machine: no stored mode, drawn constantly while powered (estimate).
        { id = "FA2HotDog", sprites = hotdogSprites, watts = 200 },
        -- Popcorn machine: no stored mode, drawn constantly (estimate).
        { id = "FA2Popcorn", sprites = popcornSprites, watts = 200 },
        -- Soda fountain: no stored mode, drawn constantly (estimate).
        { id = "FA2SodaFountain", sprites = sodaFountainSprites, watts = 200 },
        -- SlurpNBurp frozen drink machine: no stored mode, drawn constantly (estimate).
        { id = "FA2SlurpNBurp", sprites = slurpSprites, watts = 250 },
        -- Bar tap cooler: no stored mode, drawn constantly (estimate).
        { id = "FA2BarTap", sprites = barTapSprites, watts = 150 },
    },
})
```
