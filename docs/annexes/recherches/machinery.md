# Machinery (Workshop 3780027195) et More Machinery Recipes (Workshop 3807360837)

Analyse du 2026-11-13. Lecture seule des copies Workshop : `108600\3780027195\mods\Machinery\` et
`108600\3807360837\mods\MachineryRecipeMod\`. Tous les constats sont **confirmés statiquement** (lecture du code et
des scripts) sauf mention contraire. Rien n'a été testé en jeu.

Abréviations : `M\` = `108600\3780027195\mods\Machinery\42\media\`, `R\` = `108600\3807360837\mods\MachineryRecipeMod\42\media\`.

## 0. Variante chargée en 42.22

- Machinery : `id=Machinery`, `name=Machinery`, `versionMin=42.0` dans `Machinery\42\mod.info` (et `common\mod.info`
  identique). Les deux dossiers `42/` et `common/` existent ; aucun dossier `42.21/` ni `42.22/`. Variante chargée :
  **`42/`** (plus `common/` pour les tuiles et textures).
- More Machinery Recipes : `id=Rebbart_MachineryMoreRecipes`, dossier `MachineryRecipeMod`, `loadModAfter=Machinery`
  (`mod.info` racine l.12). Variante : **`42/`** (`42\mod.info`, sans `versionMin`).
- Le mod porte un `tiledef=machinery_pack 401` et `pack=machinery_pack` (`Machinery\42\mod.info` l.5-6).

## 1. Verdict

| Appareil (Machinery) | Électrique ? | Verdict LiveWire |
|---|---|---|
| Perceuse à colonne (`standingDrillPress`) | Oui | **À profiler** |
| Scie à ruban métal (`metalBandsaw`) | Oui | **À profiler** |
| Presse hydraulique (`hydraulicPress`) | Oui | **À profiler** |
| Tour à métal (`metalworkLathe`) | Oui | **À profiler** (une seule pièce par face) |
| Établi meuleuse (`benchGrinderStation`) | Oui | **À profiler** |
| Scie de table, variante Industrial | Oui | **À profiler** |
| Scie de table, variante Contractor | Oui | **À profiler** |
| Scie de table, variante Cabinet | Non : essence (`Fluid.Petrol`, `PetrolCan`) | Non facturable |
| Malaxeur à béton (`concreteMixer`) | Oui (moteur du tambour, `requiresElectricity`) + eau | **À profiler** |
| Bonbonne de propane (`propaneStorage`) | Non (`power.type = "none"`) | Non facturable |
| More Machinery Recipes | Aucun appareil ajouté (recettes seules) | Rien à profiler |

Aucune machine Machinery n'est déjà comptée par LiveWire : les familles de `LW_ApplianceFamilies.lua` ne matchent
ni par classe connue, ni par conteneur `fridge`/`freezer` (non concerné), ni par propriété `FuelAmount` (famille
`fuel` sans profil, donc non facturée).

## 2. Mécanisme électrique de Machinery

- **Définition du type d'énergie** : `Machinery.Registry`, `power.type` (`none`, `electric`, `fuel`, `fluid`) ;
  `Registry.lua:63-78` (champs `requiresElectricity`, `check`).
- **Test de courant** : `Service.isPowered(object)` dans `M\lua\shared\Machinery\Service.lua:128-134` :
  `square:haveElectricity()` puis `square:hasGridPower() and square:getRoom() ~= nil`.
  - Table `Machinery.Service` : `Service.lua:69-70` ; table globale `Machinery` : `Registry.lua:158`.
  - **Publique** (fonction de table globale). Appelée par `Service.hasRequiredPower` (`Service.lua:329-335`) et par
    `Service.getOperationStatus` (`Service.lua:981-982`, erreur `IGUI_Machinery_Error_NoPower`), et par l'interface
    (`R\lua\client\UI_modify.lua:185`).
  - LiveWire possède la même formule côté serveur (`LiveWire\server\LiveWire\LW_Computer.lua:74`) : la coupure
    LiveWire ne modifie donc vraisemblablement pas `haveElectricity()` (hypothèse à confirmer en jeu). Une garde est
    nécessaire pour qu'une coupure arrête la machine.
- **État sauvegardé** : `object:getModData().movableData.Machinery` (`Service.lua:351-353`, `Service.MOD_DATA_KEY = "Machinery"`
  à `Service.lua:72`). Champs : `machineId`, `parts`, `propaneUnits`, `drumUnits` (`Service.lua:41-45`).
  **Aucun drapeau « en marche »** : une opération est une action temporisée côté client
  (`client\Machinery\TimedActions\ISMachineAction.lua`) ; l'état « en marche » n'est donc **pas lisible depuis l'objet**.
  Les puissances doivent donc être des moyennes, comme pour Artel.
- **Pas de puissance** : aucun champ `watts` ni valeur de consommation dans le mod (recherche `power|electric|watt` sur
  `M\` : seulement des textes et des libellés).

## 3. Classe de l'objet posé

- Les machines sont des **meubles déplaçables** (`ISMoveableSpriteProps`, sprites `IsMoveAble`), posées par le
  moteur. `MoveableProps.lua:219` pose `IsMoveAble` et `GroupName`/`CustomName`. La classe Java dépend de la propriété
  de tuile `IsoType` (`E:\pz-source-42.22\media\lua\shared\Moveables\ISMoveableSpriteProps.lua:133`,
  valeur par défaut `"IsoObject"`).
- Aucun `IsoType` n'est écrit dans `M\` (Lua et `scripts`). Les propriétés des tuiles vanille (`industry_*`,
  `construction_01_*`) et de `machinery_pack.tiles` sont **binaires** : **classe non confirmée** (probablement
  `IsoObject`). Une vérification en jeu : `getObjects():get(i):getClass()` ou `instanceof(o, "IsoThumpable")`.
- Les entités (`scripts\entities\machinery_*.txt`, `SpriteConfig`, `CraftRecipe`) décrivent l'apparence et la
  recette de **construction** (`BuildMetalStructureSmall` ; `SkillRequired = ...;Electricity:n`), pas une consommation.

## 4. Sprites posés, par machine (confirmé statiquement)

Sources : `M\scripts\entities\machinery_*.txt` (lignes `row =`), `M\lua\shared\Machinery\MoveableProps.lua`
(définitions des faces N/S/E/W), `M\lua\shared\Machinery\Machines\*.lua` (`previewSprite`, `monitorSprites`).

### 4.1 Perceuse à colonne (`standingDrillPress`)

- Type : `power = { type = "electric" }` (`Machines\StandingDrillPress.lua:107-108`).
- Sprites, une tuile par face (`MoveableProps.lua:40-53`, `scripts\entities\machinery_standing_drill_press.txt`) :
  `industry_02_268` (W), `industry_02_269` (N), `industry_02_270` (S), `industry_02_271` (E).
- Une seule tuile (1x1) : facturer les quatre sprites, une seule instance par meuble.

### 4.2 Scie à ruban métal (`metalBandsaw`)

- Type : `power = { type = "electric" }` (`Machines\MetalBandsaw.lua:212-213`).
- Deux familles de sprites, une tuile chacune :
  - groupe `Metal` (`MoveableProps.lua:57-72`) : `industry_02_264` (W), `_265` (N), `_266` (E), `_267` (S) ;
  - groupe `Small Metal` (`MoveableProps.lua:74-89`) et entité `machinery_metal_bandsaw.txt` :
    `machinery_metal_bandsaw_01_0` (W), `_1` (N), `_2` (E), `_3` (S).
- Facturer les huit sprites (une tuile par objet).

### 4.3 Presse hydraulique (`hydraulicPress`)

- Type : `power = { type = "electric" }` (`Machines\HydraulicPress.lua:103-104`, `114-115`).
- Deux variantes de couleur, une tuile par face (`MoveableProps.lua:91-121`, entités `machinery_hydraulic_press.txt`) :
  - Industrial : `industry_03_48` (E), `_49` (S), `_50` (W), `_51` (N) ;
  - Dark Industrial (Blue) : `industry_03_52` (E), `_53` (S), `_54` (W), `_55` (N).
- Les sprites `industry_03_56` à `_63` sont des **sprites de moniteur** superposés (`monitorSpritesByPlacedSprite`,
  `HydraulicPress.lua:106-110`), pas des objets à facturer.

### 4.4 Tour à métal (`metalworkLathe`), multi-tuiles

- Type : `power = { type = "electric" }` (`Machines\MetalworkLathe.lua:61-62`, `72-73`).
- Footprint : **1x3 ou 3x1** selon la face (`MoveableProps.lua:125-155`). Chaque face est composée de trois tuiles.
  Variante standard (`Large Industrial`) :
  - W (1x3) : `industry_03_2`, `_1`, `_0` ; N (3x1) : `_3`, `_4`, `_5` ; S (3x1) : `_8`, `_9`, `_10` ; E (1x3) : `_13`, `_12`, `_11`.
  - Variante bleue (`White Industrial`) : W `_34`, `_33`, `_32` ; N `_35`, `_36`, `_37` ; S `_40`, `_41`, `_42` ; E `_45`, `_44`, `_43`.
- **Pièce à facturer : la tuile centrale de chaque face** (cohérente avec le moniteur du mod,
  `monitorSprites = { "industry_03_9" }` et `industry_03_40 -> industry_03_41`, `MetalworkLathe.lua:63-80`) :
  `industry_03_1` (W), `_4` (N), `_9` (S), `_12` (E), `_33` (W bleu), `_36` (N bleu), `_41` (S bleu), `_44` (E bleu).
- Les autres tuiles ne doivent pas être dans la liste de sprites du profil, sinon la tour serait facturée trois fois.

### 4.5 Établi meuleuse (`benchGrinderStation`)

- Type : `power = { type = "electric" }` (`Machines\BenchGrinderStation.lua:211-212`).
- Une tuile, quatre faces : `industry_04_20`, `_21`, `_23`, `_22` (`scripts\entities\machinery_bench_grinder_station.txt`,
  lignes 18, 25, 32, 39). Non présente dans `MoveableProps` : la pose passe par le moteur (`MoveableProps.lua:9`,
  commentaire « Bench Grinder, Concrete Mixer, table saws ... are moveable already »).
- Facturer les quatre sprites.

### 4.6 Scie de table (`tableSaw`), trois variantes

- Variantes : `TableSawIndustrial` (électrique, `Machines\TableSaw.lua:19-23`), `TableSawContractor`
  (électrique, `TableSaw.lua:39-43`), `TableSawCabinet` (essence, `TableSaw.lua:24-38`, `Fluid.Petrol`, `PetrolCan`).
- Sprites, une tuile par face :
  - Industrial : `machinery_table_saws_01_8` à `_11` (`machinery_table_saws.txt` l.17-38) ;
  - Contractor : `machinery_table_saws_01_0` à `_3` (l.154-175) ;
  - Cabinet (non facturée) : `machinery_table_saws_01_4` à `_7` (l.91-112).
- Le texte d'infobulle confirme : `Tooltip_Machinery_TableSaw_Industrial` et `_Contractor` = « runs on mains or generator
  power » ; `_Cabinet` = « gasoline powered » (`M\lua\shared\Translate\EN\Tooltip.json`, lignes 3-5).

### 4.7 Malaxeur à béton (`concreteMixer`)

- Type : `power = { type = "fluid", ... requiresElectricity = true }` (`Machines\ConcreteMixer.lua:124-144`) : l'eau
  et l'électricité sont exigées ensemble (le tambour a besoin du moteur).
- Une tuile, quatre faces : `construction_01_6`, `_7`, `_14`, `_15` (`scripts\entities\machinery_concrete_mixer.txt`
  l.30, 37, 44, 51). Non dans `MoveableProps` (déjà déplaçable).

## 5. Puissance

- **Aucune valeur dans le mod** (voir section 2).
- Valeurs proposées : **hypothèses, non sourcées** (pas de recherche web dans cette analyse). Elles reposent sur
  des plages usuelles de l'équipement réel équivalent : perceuse à colonne (0,5 à 0,75 kW nominal), meuleuse
  d'établi (0,25 à 0,75 kW), tour d'atelier (0,5 à 1 kW), pompe de presse (environ 1 kW), scie à ruban (environ
  1 kW), scie de table de chantier (1,5 à 2 kW), malaxeur (0,5 à 1 kW). La moyenne retenue applique un facteur
  d'utilisation (voir le profil). **À sourcer avant publication.**

## 6. Garde (`gates`) : limite de l'API actuelle

- `Machinery.Service.isPowered` est **partagée** par les sept consommateurs. `LWC_Profiles.lua:132` ne garde qu'**un
  seul** consommateur par chemin de fonction (`P.wrappers[gate.path]`), et le consommateur est fixé à la déclaration
  (`consumer = ...`, `LWC_Profiles.lua:133`, comparaison l.140).
- Conséquence : une seule garde possible aujourd'hui, pour une seule machine. Trois options (à décider) :
  - A. Étendre `wrapGate` pour résoudre le consommateur depuis l'objet (`consumer = nil` : tout consommateur enregistré).
    Modification de `LiveWireCompatibility` (hors de ce rapport).
  - B. Un profil par machine avec une garde distincte sur une fonction par machine : impossible, la fonction est commune.
  - C. Pas de garde : la coupure n'arrête pas les machines (elles restent facturées ou non selon `consumerPowered`).
    **Déconseillé**.

## Profil proposé

Fichier cible (non créé) : `LiveWireCompatibility\Contents\mods\batman_LiveWireCompatibility\42.21\media\lua\shared\LiveWireCompatibility\Profiles\LWC_Machinery.lua`.
Une seule pièce facturée par meuble (tuile centrale pour la tour). Pas de `running` : état non lisible. Les
puissances sont des moyennes **hypothétiques** (section 5). La garde est volontairement absente tant que la section 6
n'est pas tranchée.

```lua
-- LiveWire Compatibility: Machinery (Workshop 3780027195, mod id Machinery).
-- Analysis: docs/annexes/recherches/machinery.md. Watts are averages and not sourced yet (see the report).
-- Not billed: table saw Cabinet (petrol), propane storage (no electricity).
-- Metalwork lathe: only the centre tile of each face is listed, so one object = one consumer.
require "LiveWireCompatibility/LWC_Profiles"

LiveWireCompat.Profiles.add({
    name = "Machinery",
    workshop = "3780027195",
    mods = { "Machinery" },
    consumers = {
        { id = "MachineryStandingDrillPress", watts = 150,
          sprites = { "industry_02_268", "industry_02_269", "industry_02_270", "industry_02_271" } },
        { id = "MachineryMetalBandsaw", watts = 330,
          sprites = { "industry_02_264", "industry_02_265", "industry_02_266", "industry_02_267",
                      "machinery_metal_bandsaw_01_0", "machinery_metal_bandsaw_01_1",
                      "machinery_metal_bandsaw_01_2", "machinery_metal_bandsaw_01_3" } },
        { id = "MachineryHydraulicPress", watts = 300,
          sprites = { "industry_03_48", "industry_03_49", "industry_03_50", "industry_03_51",
                      "industry_03_52", "industry_03_53", "industry_03_54", "industry_03_55" } },
        { id = "MachineryMetalworkLathe", watts = 200,
          sprites = { "industry_03_1", "industry_03_4", "industry_03_9", "industry_03_12",
                      "industry_03_33", "industry_03_36", "industry_03_41", "industry_03_44" } },
        { id = "MachineryBenchGrinderStation", watts = 125,
          sprites = { "industry_04_20", "industry_04_21", "industry_04_22", "industry_04_23" } },
        { id = "MachineryTableSawIndustrial", watts = 500,
          sprites = { "machinery_table_saws_01_8", "machinery_table_saws_01_9",
                      "machinery_table_saws_01_10", "machinery_table_saws_01_11" } },
        { id = "MachineryTableSawContractor", watts = 500,
          sprites = { "machinery_table_saws_01_0", "machinery_table_saws_01_1",
                      "machinery_table_saws_01_2", "machinery_table_saws_01_3" } },
        { id = "MachineryConcreteMixer", watts = 350,
          sprites = { "construction_01_6", "construction_01_7", "construction_01_14", "construction_01_15" } },
    },
    -- No gates yet: see section 6 (one gate per power check path only).
})
```

## 7. More Machinery Recipes (Workshop 3807360837)

- Ajoute des **recettes**, pas des machines : `R\lua\shared\Machine Recipes\LatheRecipes.lua:105`
  (`Machinery.Registry.registerOperation("metalworkLathe", ...)`) et `PressRecipes.lua:516`
  (`... "hydraulicPress" ...`). Aucun `scripts\entities`, aucune tuile, aucune `MoveableProps` dans ce mod.
- `R\lua\client\UI_modify.lua` modifie l'interface : l. 183-197 lit `Machinery.Service.isPowered(self.entity)` pour
  l'affichage de la carte de recette. **Lecture seule, aucune consommation ajoutée.**
- **Verdict : rien à profiler.** Les machines concernées (tour et presse) sont déjà couvertes par le profil
  Machinery ci-dessus.

## 8. Limites

- Classe Java des machines posées : non confirmée (tuiles binaires, `IsoType` non lu).
- Puissances : hypothèses non sourcées. Aucun test en jeu.
- Coupure LiveWire et `haveElectricity()` : hypothèse à confirmer (LW_Computer.lua:74 suggère que LiveWire ne change
  pas le moteur).
- Consommateurs enregistrés sans état : LiveWire ne restaure pas l'état après une coupure (pas de famille `activation`).
  Sans état sauvegardé par Machinery, c'est sans conséquence.
