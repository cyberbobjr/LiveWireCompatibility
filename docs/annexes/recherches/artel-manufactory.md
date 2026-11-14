# Artel Manufactory (B42, 42/) : machines électriques pour LiveWire

Base : `D:\SteamLibrary\steamapps\workshop\content\108600\3794133594\mods\ArtelManufactory\42\media\`
(abrégé `M\`). Lecture seule. Tous les constats sont **confirmés statiquement** (lecture du code). Rien n'a été testé en jeu.
Les puissances sont des **estimations**. Les noms de sprites sont lus dans le Lua et les scripts ; `Artel.tiles` est binaire et
n'a pas été décodé entièrement (voir section Limites).

## 0. Réponses aux questions transverses

- **`PMK` est une table globale.** `PMK = PMK or {}` sans `local` : `M\lua\shared\PMK_00_Core.lua:4`. Chaque module ajoute ses sous-tables.
- **La charge `C` est exportée.** `M\lua\shared\PMK_85_ChargerCore.lua:90-91` : `local C = {}` puis `PMK.Charger = C`.
  Fonctions publiques : `C.squarePowered` (l.313), `C.hasPower(item, pl)` (l.316), `C.squareOf(item, pl)` (l.286-299).
- **`Sensors` est une vraie globale, pas `PMK.Sensors`.** `M\lua\shared\PMK_100_SensorCore.lua:46` : `Sensors = Sensors or {}`.
- Autres exports confirmés : `PMK.Well` (`PMK_80_WellCore.lua:81`), `PMK.QBase` (`PMK_87c_QuantumBaseCore.lua:120`),
  `PMK.Trade` (`PMK_91h_TradePower.lua:65`, et d'autres fichiers `PMK_91*`), `PMK.Heater` (`PMK_78_HeaterCore.lua:52`),
  `PMK.Cold` (`PMK_80_ColdStorage.lua:60`). Pas d'export pour la sublimatrice, la sécheuse, l'établi (fonctions `local`).

## 1. Tableau de synthèse

| Machine | Type de placement | Facturée par le moteur ? | Fonction de test de courant (accessible ?) | État lisible depuis l'objet |
|---|---|---|---|---|
| Puits, moteur (stade 3) | Objet monde, sprite changeant par étape | Non (`haveElectricity` / `hasGridPower`) | `PMK.Well.isPowered(obj)` : **public** | Sprite `Artel_104`/`Artel_107` (moteur) + `isPowered` |
| Sécheuse électrique | Objet monde (Mov_) | Non | `squarePowered` **local** (client l.65 ; serveur `PMK_58z` l.82) | Sprite de stade + modData `PMK_EDryerNoPower` |
| Sublimatrice | Objet monde (Mov_) | Non | `squarePowered` **local** (client `PMK_58` l.60 ; serveur `PMK_58z` l.82) | Sprite de base (stades non dessinés) |
| Établi chimique (craft bench) | Objet monde (Mov_ + entité) | Non | `squarePowered` **local** (`PMK_57` l.361), valeur dans le panneau `self.powered` | Aucune donnée monde : état dans le panneau client seulement |
| Station de recharge | **Objet inventaire** (`base:normal`) | Sans objet | `PMK.Charger.hasPower(item, pl)` public | Non applicable : pas de sprite |
| Station de commerce | Objet monde, **2 moitiés** | Non | `PMK.Trade.isPowered(obj)` public (+ `gridPowered`) | Sprites `Artel_121`/`123` (ancres) + modData `PMK_TrChg` |
| Base quantique (module mural) | Objet monde, 1 tuile par face | Non | `PMK.QBase.hasPower(obj)` public | Sprites clair/sombre (`112..120`, `125..133`, `134..142`) |
| Capteurs / projecteurs intelligents | Objet monde (IsoLightSwitch) | Probablement déjà facturés (lightswitch) | `Sensors.lightPowered(obj)` global | Sprites `Artel_200..207`, `216..223` |
| Chauffage électrique portable | **Objet inventaire**, batterie (auto-batterie) | Sans objet | Pas de contrôle réseau | Non applicable |
| Sac-réfrigérateur (`PMK_80_ColdStorage`) | **Objet inventaire**, piles | Sans objet | Pas de contrôle réseau | Non applicable |
| Cellier (`PMK_81/82`) | Objet monde | Non électrique dans le code | Pas de `haveElectricity` trouvé | Non applicable |
| Scieuse/extrudeuse/sceller (`PMK_31/39`) | Objet monde | Aucune gestion de courant dans le Lua | Clés `NoPower` présentes seulement dans les traductions, jamais utilisées | Non applicable |
| Réchaud électrique portable | Objet monde (`IsoStove`) | **Oui** (IsoStove) | Moteur | Passer |

## 2. Fiches par machine

### 2.1 Puits à pompe (Well) - machine électrique, étape moteur seulement

1. **Nom affiché / rôle** : puits avec pompe. Trois étapes : tuyau (`PMK_ArtelWellPipe`), pompe à main (`PMK_ArtelWellHand`),
   moteur (`PMK_ArtelWellMotor`). Seule l'étape moteur tire du courant.
2. **Sprites** (`M\lua\shared\PMK_80_WellCore.lua:103-108`) :
   - Étape 1 tuyau : S = `Artel_102`, E = `Artel_105`.
   - Étape 2 pompe à main : S = `Artel_103`, E = `Artel_106`.
   - **Étape 3 moteur (la seule électrique) : S = `Artel_104`, E = `Artel_107`.**
   - Un seul objet par colonne : le sprite change à chaque étape. Facturer seulement `Artel_104` et `Artel_107`.
   - Commentaire l.25-26 et l.93-101 : une grille à deux faces (S et E).
   - Table inverse `STAGE_BY_SPRITE` / `FACE_BY_SPRITE` (l.114-127).
3. **État « en marche » lisible depuis l'objet** : oui, par sprite (`Artel_104`/`107` = moteur) puis `Well.isPowered(obj)`.
   - `Well.isPowered(obj)` (l.430-432) prend **l'objet monde** (il appelle `getSquare`).
   - `Well.stageOf(obj)` (l.164) lit le sprite. `Well.faceOf(obj)` (l.~127) lit la face.
   - `motorFast = (stage >= LAST_STAGE) and Well.isPowered(obj)` (l.389) : le moteur est actif seulement sur étape 3 et sous tension.
   - ModData : clé `Well.MD_KEY = "PMK_Well"` (l.212) avec `{t, w, p}` (eau, l.489). **Aucune clé d'état de courant.**
4. **Chaîne de test** : `PMK.Well.isPowered(obj)` (l.430) -> `Well.squarePowered(square)` (l.423-428, public) ->
   `square:haveElectricity()` puis `square:hasGridPower() and square:getRoom()`. Public via `PMK.Well`.
   Commentaire l.421-422 : « un-pour-un avec la station de recharge et la sécheuse ».
5. **Puissance** : aucune valeur dans le code. Estimation : moteur de pompe 300-500 W en marche (500 W retenu), 0 W sinon.
   Le mod veut seulement dire « moteur sous tension = 2× plus vite » (`Well.FILL_SPEED.motor = 0.5`, l.415-419).
6. **Vanilla ?** Non (non vanille).

### 2.2 Sécheuse électrique (ElectricDryer) - `PMK_54`

1. **Nom / rôle** : sécheuse électrique à étapes (`Artel.Mov_PMKElectricDryer`). Sèche par lots, avec pause sans courant.
2. **Sprites** :
   - Sprite de placement (Mov_) : **`Artel_36`** (`M\scripts\PMK_drying_Items.txt:297-304`).
   - Config de stades (`M\lua\shared\PMK_54s_ElectricDryerStage.lua:257-259`) :
     - face S : `Artel_36` (base), `Artel_38` (fraîche), `Artel_42` (sèche) ;
     - face E : `Artel_37` (base), `Artel_39` (fraîche), `Artel_43` (sèche).
   - Sprites **morts** (commentaire l.250-254) : `Artel_32..35` et `Artel_40/41`.
   - Pour facturer une fois par face : **`Artel_36` (S) et `Artel_37` (E)**. Les autres sprites sont des états (fraîche/sèche)
     du même objet et ne doivent pas être comptés en plus.
   - **Non vérifié** : la géométrie multi-tuiles exacte (SpriteGridPos) dans `M\scripts\PMK_drying_Entity.txt`.
3. **État « en marche » lisible** : partiel.
   - `md.PMK_EDryerNoPower` (`M\lua\client\PMK_54_ElectricDryer.lua:46`) : drapeau modData « sans courant » lu par l'interface
     (`PMK_55a_VanillaWindowPatch.lua:504`, `PMK_55_ElectricDryerPanel.lua:2592`).
   - État de séchage : dans le composant de séchage (`PMK_53_Drying`, `PMK_54s`), pas tracé en détail ici.
4. **Chaîne de test** : `squarePowered(square)` **local** (`M\lua\client\PMK_54_ElectricDryer.lua:65-69`) ; même formule que
   la station. Le serveur utilise la copie locale de `PMK_58z_SublimatorServer.lua:82-86`, appelée dans la boucle de pause
   commune aux deux `kind` (`PMK_58z` l.430, journal `drypause: %s`). **Non accessible depuis un global.**
   Le fichier `PMK_54_ElectricDryer.lua` ne l'appelle pas (définition seule trouvée) : la vérification réelle est dans `PMK_58z`.
5. **Puissance** : estimation. Sécheuse électrique à résistance 2 000 W en marche (2 kW), 0 W en veille.
6. **Vanilla ?** Non.

### 2.3 Sublimatrice (freeze dryer) - `PMK_58`

1. **Nom / rôle** : lyophilisateur (`Artel.Mov_PMKSublimator`).
2. **Sprites** :
   - Placement (Mov_) : **`Artel_52`** (`M\scripts\PMK_subl_Items.txt:961-968`).
   - Config (`M\lua\shared\PMK_58s_SublimatorStage.lua`, lignes 37-42) : base `Artel_52` (S), `Artel_53` (E) ;
     stades (non dessinés, réservés) `Artel_48..51`.
   - Commentaire l.17-20 : « арт стадий ещё не нарисован » : seules les bases existent.
   - À facturer : **`Artel_52` (S) et `Artel_53` (E)**. Les sprites 48-51 ne sont pas utilisés pour l'instant.
3. **État « en marche »** : pas de drapeau monde identifié. Pause = `PMK.dryPause` (`M\lua\shared\PMK_54p_DryingPause.lua:156`,
   `Pause.freeze/thaw/isHeld(crd)` l.168-198, clés par coordonnées, pas par objet). **Non lisible depuis l'objet seul.**
   Sprite de base = toujours présent ; la marche se lit par la pause `Pause.isHeld(crd)` (non public, fonction de module).
4. **Chaîne de test** : `squarePowered(square)` **local** (`PMK_58_Sublimator.lua:60-64` client ;
   `PMK_58z_SublimatorServer.lua:82-86` serveur). Non accessible.
5. **Puissance** : estimation. Lyophilisateur domestique 700 W en marche, 5 W en veille.
6. **Vanilla ?** Non.

### 2.4 Établi chimique (craft bench) - `PMK_57`

1. **Nom / rôle** : établi de chimie électrique (`Artel.Mov_PMKChemTable`), craft avec interface de panneau.
2. **Sprites** :
   - Placement (Mov_) : **`Artel_56`** (`M\scripts\PMK_chem_Items.txt:23-30`).
   - Entité (`M\scripts\PMK_chem_Entity.txt`) : lignes `row = Artel_56 Artel_57` (l.136), `row = Artel_58` (l.143),
     `row = Artel_59` (l.144). Commentaire l.19-21 : « Artel_56..59 ».
   - **Non vérifié** : quelle paire correspond à quelle face. Pour facturer une fois : `Artel_56` (anneau de base).
3. **État « en marche »** : **non lisible depuis le monde.** Le booléen `self.powered` est dans le panneau client
   (`PMK_57` l.2400 : `self.powered = squarePowered(call(self.entity, "getSquare"))`, relecture toutes les 500 ms).
4. **Chaîne de test** : `squarePowered(square)` **local** (`M\lua\client\PMK_57_CraftBenchPanel.lua:361-365`). Non accessible.
5. **Puissance** : estimation. Établi chauffé 300 W en marche, 0 W en veille.
6. **Vanilla ?** Non.

### 2.5 Station de recharge (Battery Charging Station) - `PMK_85` / `PMK_86`

1. **Nom / rôle** : 6 emplacements de batteries (`Artel.BatteryCharger`). **Objet inventaire**, pas un objet posé.
2. **Sprites** : **aucun**. `M\scripts\PMK_elec_Items.txt:8-76` : `item BatteryCharger`, `ItemType = base:normal`, `Icon = BatteryStation_PMK`,
   `WorldStaticModel = BatteryStation_PMK`. Pas de `WorldObjectSprite`. Le commentaire l.11-12 dit « модель BatteryStation_PMK »,
   et la ligne `WorldObjectSprite = appliances_television_01_8` (l.77) appartient au bloc **voisin**
   (cassette TV). Lire ce bloc avant de conclure.
3. **État** : `PMK.Charger.hasPower(item, pl)` (`PMK_85:316-319`) prend un **objet**, l'item, pas le carré.
   Le carré vient de `C.squareOf` (l.286-299) : sol (`getWorldItem`), conteneur parent, ou joueur.
4. **Chaîne** : `PMK.Charger.hasPower` (public) -> `squarePowered(square)` local, `PMK_85:307-312`
   (`haveElectricity`, puis `hasGridPower and getRoom`), exporté en `C.squarePowered` (l.313).
5. **Puissance** : estimation 6 chargeurs à 3 W = 20-30 W en charge ; 0 W sans batterie.
6. **Conclusion** : **pas de sprite à facturer ; à traiter seulement si LiveWire gère les objets d'inventaire posés** (non prévu).

### 2.6 Station de commerce (Trade Post) - `PMK_91h` et voisins

1. **Nom / rôle** : station de commerce (`Artel.Mov_PMKTradePost`), avec batterie auto logée dans un emplacement.
2. **Sprites** (`M\scripts\PMK_trade_Items.txt:257-264` : `WorldObjectSprite = Artel_121`) :
   - **Deux objets par station** (une moitié par face) : orientation A = `Artel_121` + `Artel_122` ; orientation B = `Artel_123` + `Artel_124`.
   - **Ancres** : `Artel_121` et `Artel_123` (`PMK_91h_TradePower.lua:137,151,159` et `T.ANCHOR_SPRITE`, commentaire l.128-152).
   - À facturer **une fois par station** : `Artel_121` et `Artel_123`. Ne pas facturer `122` et `124`.
   - Les modData sont sur **une** moitié. Le code sait trouver la moitié qui les porte (`postScore`, l.~150-175).
3. **État « en marche »** : oui, par fonction publique : `PMK.Trade.isPowered(obj)` (l.334-336) renvoie `grid` ou `batt`.
   - `T.powerSource(obj)` (l.322-330) : `"grid"`, `"batt"` ou `"none"`.
   - ModData (l.90-92, `MD_PREFIX = "PMK_Tr"` l.156) : `PMK_TrBat` (type de batterie), `PMK_TrChg` (charge 0..1), `PMK_TrBTime` (heure).
   - **Attention pour la facturation** : quand il y a du courant réseau, le poste ne décharge pas sa batterie (l.277-280). Sur batterie seule, il ne tire pas le réseau.
4. **Chaîne** : `PMK.Trade.isPowered(obj)` (public) -> `T.powerSource` -> `T.gridPowered(obj)` (l.226-232, public, carré) puis
   `T.battSync(obj)` (l.258, public). `T.gridPowered` est une fonction publique.
5. **Puissance** : estimation. Station de communication 150 W en marche, 10 W en veille. Non indiqué dans le mod.
6. **Vanilla ?** Non.

### 2.7 Base quantique (module mural) - `PMK_87c` / `PMK_88*`

1. **Nom / rôle** : « Quantum Base », module mural à 4 cellules (`QB.CELLS`, `PMK_87_QuantumCore.lua`) à 5 états 0..4, avec tiroir d'éclairage.
2. **Sprites** (`M\lua\shared\PMK_87c_QuantumBaseCore.lua:140-156`) :
   - **Face S** : clairs `Artel_112` (état 0), `113`, `114`, `115`, `116` (état 4) ; sombres `117..120` (états 1..4).
   - **Face E** : clairs `125..129` ; sombres `130..133`.
   - **Face W** : clairs `134..138` ; sombres `139..142`.
   - **Face N** : un seul `Artel_143` pour tous les états (sombre et clair).
   - Commentaire l.52-62 : « ТЁМНЫЕ КЛОНЫ НЕТ ЭЛЕКТРИЧЕСТВА » : les sprites sombres = **pas de courant**. Les sprites sombres
     **ne sont pas** des sprites facturables (à exclure, l'état est déjà dans le clair).
   - Chaque face a `0..4` ; à facturer **une fois par face** : `Artel_112` (S), `125` (E), `134` (W), `143` (N).
     Comme chaque face a un seul objet, on compte un objet par case, pas par état.
   - **Coquilles de coffres** `Artel_108..111` (`Q.SPRITES`, `PMK_87_QuantumCore.lua:78-81`) : ce sont les anciens coffres quantiques
     (migration), pas la base. Ils n'ont pas de test de courant.
3. **État « en marche »** : **oui, lisible depuis le sprite** (clair = sous tension, sombre = non alimentée),
   et par fonction publique `PMK.QBase.hasPower(obj)` (l.288-291, prend **l'objet**, appelle `getSquare`).
   `QB.cellCount(obj)` donne le nombre de cellules (l.378-384).
4. **Chaîne** : `PMK.QBase.hasPower(obj)` (public) -> `QB.squarePowered(sq)` (`PMK_87c` l.278-285) -> `PMK.Charger.squarePowered`
   si présent (l.281), sinon `haveElectricity` / `hasGridPower and getRoom`.
   Appelant : `M\lua\client\PMK_88a_QuantumBaseContext.lua:219` ; `PMK_88c_QuantumBaseActions.lua:194`.
5. **Puissance** : estimation sans référence réelle. 1 000 W en marche (cellule de champ), 50 W en veille. Entièrement fictif.
6. **Vanilla ?** Non.

### 2.8 Capteurs et projecteurs intelligents (`PMK_100`, `PMK_101`, `PMK_102`)

1. **Nom / rôle** : projecteur à détecteur de mouvement, projecteur intelligent, petit prototype intelligent (sol et mur).
2. **Sprites** (`M\lua\shared\PMK_100_SensorCore.lua:83-113` et `142-156`) :
   - Projecteur intelligent, cyan, 4 faces : `Artel_200` (E), `201` (S), `202` (W), `203` (N).
   - Projecteur à détecteur de mouvement, orange, 4 faces : `Artel_204` (E) ... `207` (N). Mort (ancien `auto`/`motion`).
   - Petit intelligent sol : `Artel_216` (E) ... `219` (N) ; petit intelligent mur : `Artel_220` (E) ... `223` (N).
   - Projecteurs de base **sans** pilotage (`BASE_SPRITES`, l.176-181) : `Artel_208..215`.
   - À facturer une fois par face : `200, 201, 202, 203` (et équivalents 204, 216, 220 si orange ou petit).
3. **État** : `Sensors.lightPowered(obj, square)` (l.618-625, **global**, prend l'objet) et `Sensors.resolvePower(obj, noRelay)`
   (l.591-611, global, renvoie `powered, mains, charge`). `Sensors.mainsPowered(obj)` (l.291-301) prend l'objet.
4. **Chaîne** : `Sensors.mainsPowered` appelle `canSwitchLight` (méthode de l'objet `IsoLightSwitch`), puis `Sensors.squarePowered`
   (l.227-232, global) en repli. Le code appelle `setUseBatteryDirect` et `canSwitchLight`, donc **l'objet est un IsoLightSwitch**.
5. **Puissance** : estimation. Projecteur LED 30 W en marche (réseau), 0,5 W en veille, petit prototype 15 W.
6. **Facturé par le moteur ?** **Probablement oui**, par la propriété `lightswitch` (voir section 3). **À confirmer** : le décodage
   de `Artel.tiles` n'a pas relié les 24 occurrences de `lightswitch` aux sprites.

### 2.9 Objets vérifiés hors liste (non électriques ou batterie seule)

- **Chauffage électrique portable** (`PMK_78`, `PMK_79`) : **item inventaire** (`Artel.ElectricHeater`, `Artel.CampingHeater`),
  alimenté par une batterie auto (`Base.CarBattery1`, `PMK_78:68-69`) ou 4 piles. Pas de courant réseau (grep : aucun `haveElectricity`).
  Puissance estimée 1 500 W au maximum (batterie).
- **Sac-réfrigérateur** (`PMK_80_ColdStorage`, `PMK_83b`) : **item inventaire** à piles `Base.Battery` (`Cold.BAG_BATTERY`, l.84).
  Aucun contrôle réseau. Non concerné.
- **Cellier** (`PMK_81`, `PMK_82`) : aucune occurrence de `haveElectricity` / `hasGridPower` ; **non électrique dans le code** (non vérifié exhaustivement).
- **Scieuse à barre** (`Mov_PMKBarExtruder`, `sportpit_Items.txt:432-439`, `Artel_12`) et **sceller** (`Mov_PMKFactoryCanSealer`,
  `machines_Items.txt:3331-3344`, `Artel_8`) : traductions `IGUI_Artel_BarExtruderNoPower` / `IGUI_Artel_FactorySealerNoPower`
  existent, **mais aucune clé n'est appelée** dans le Lua. Pas de contrôle de courant trouvé : ces machines ne sont **pas** électriques
  dans le code. À confirmer en jeu avant d'en faire des cibles.

## 3. Objets déjà facturés par le moteur (sans effort)

- **Lampes et projecteurs `lightswitch`** : la propriété `lightswitch` apparaît **24 fois** dans `Artel.tiles` (décodage non relié aux sprites).
  Les projecteurs `Artel_200..223` sont des `IsoLightSwitch` (appels `canSwitchLight` / `setUseBatteryDirect`, `PMK_100` l.227-300).
- **Réchaud électrique portable** : `Artel.tiles` contient `IsoType = IsoStove`, `container = stove`, `Material = Electric`
  (`Artel.tiles`, chaînes lues), item `Artel.Mov_PortableElectricStove` avec `WorldObjectSprite = Artel_0`
  (`M\scripts\PMK_elec_Items.txt:134-141`). **Déjà facturé** (IsoStove), à ignorer.
- **Réfrigérateurs / congélateurs (`container = fridge/freezer`)** : **aucun trouvé**. `Fridge` n'apparaît que comme `Material` (scelleuse,
  extrudeuse, `Artel.tiles`), jamais comme `container`. Pas de sprite à classer dans cette catégorie.
- **Feu / lanterne / radio** : `IsoFireplace` (4-5 occurrences) = feu de camp et réchaud à carburant, non électriques.

## 4. Projets de facturation (synthèse à transmettre à LiveWire)

Sprites à facturer, une fois par objet posé :

| Machine | Sprites à facturer (une fois par face) | À ignorer |
|---|---|---|
| Puits (moteur) | `Artel_104` (S), `Artel_107` (E) | `102`, `103`, `105`, `106` |
| Sécheuse | `Artel_36` (S), `Artel_37` (E) | `38..43`, `32..35`, `40/41` |
| Sublimatrice | `Artel_52` (S), `Artel_53` (E) | `48..51` (non dessinés) |
| Établi chimique | `Artel_56` (à confirmer par face) | `57..59` (à confirmer) |
| Station de commerce | `Artel_121` (ancre A), `Artel_123` (ancre B) | `122`, `124` |
| Base quantique | `Artel_112` (S), `Artel_125` (E), `Artel_134` (W), `Artel_143` (N) | Tous les autres : états `113..120`, `126..133`, `135..142` |
| Projecteurs intelligents | `200..203`, `216..219`, `220..223` (`204..207` si orange) | `208..215` (base, sans pilotage) |
| Charge | Aucun (objet inventaire) | |
| Chauffage, sac, cellier, scieuse, sceller | Aucun (inventaire ou non électrique) | |

Hypothèses à confirmer en jeu avant publication : géométrie multi-tuiles (établi, sécheuse, sublimatrice) ; orientation `Artel_122/124`.

## 5. Limites

- `Artel.tiles` est binaire (`tdef` version 1). Le sprite ↔ propriété (`lightswitch`, `container`) n'a pas été décodé. Les numéros de sprite viennent des fichiers Lua et des scripts.
- Les puissances sont des estimations ; aucune valeur écrite dans le mod.
- Aucun test en jeu. Les statuts sont confirmés **statiquement**.
- `PMK_54_ElectricDryer.lua:65` définit `squarePowered`, mais la vérification effective est dans `PMK_58z` (boucle de pause commune). Non tracé de bout en bout.
- L'établi : correspondance face/sprite non vérifiée.
- Le drapeau `PMK_EDryerNoPower` : lieu d'écriture non tracé (probablement serveur).
