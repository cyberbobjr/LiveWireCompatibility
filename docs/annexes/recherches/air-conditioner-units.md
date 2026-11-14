# Air Conditioner Units, AirCond42 (Workshop 3784995595)

Analyse du 2026-11-13. Lecture seule de `108600\3784995595\mods\AirCond42\`. Tous les constats sont **confirmés
statiquement** sauf mention contraire. Rien n'a été testé en jeu.

## 0. Variante chargée en 42.22

- `id=AirCond42`, `name=[B42] Working Air Conditioner Units`, `versionMin=42.0`, `require=RC_RealisticColdMod`
  (`42\mod.info` l.1-7). Variante : **`42/`** (Lua), plus `common/` (textures, sons, `AnimSets`).
- Versions : `CHANGELOG_v16.txt` est le plus récent ; la description du `mod.info` indique encore « stable v13 ».
  Le code analysé est celui du dossier `42/`.

## 1. Appareil et sprites

- Sprites d'unité posée (`42\media\lua\client\AirCond.lua:21-22`) : `AC_SPRITE_1 = "industry_01_4"` (orientation H),
  `AC_SPRITE_2 = "industry_01_5"` (orientation V). Choix par `detectOrientationAC` (`42\media\lua\shared\ACUtils.lua`).
- Une unité est **une tuile** (le mod pose le sprite vanille, il n'a pas de footprint multi-tuiles).
- Le mod est vanille-compatible : l'objet vanille est remplacé à l'attache (voir section 2).

## 2. Attache : l'unité devient un sèche-linge

- `42\media\lua\client\Actions\TAConnectAC.lua`, `TAConnectAC:perform()` :
  - `cd = IsoClothingDryer.new(self.square:getCell(), self.square, getSprite(spriteName))` (l.~35) ;
  - `cd:setActivated(false)`, `cd:createContainersFromSpriteProperties()` ;
  - l'objet vanille est retiré, `self.square:AddSpecialObject(cd)`, `VirtualAC.Add(cd)`.
- Le commentaire `AirCond.lua:154-155` l'explique : « we need clothing dryer because this way game will count is
  as electrical appliance ». Le mod contourne donc la liste d'appareils du moteur en empruntant la classe sèche-linge.
- `isConnectedAC(obj)` (`ACUtils.lua`) : `obj:getObjectName() == "ClothingDryer"` et sprite `industry_01_4/5`.
  `isUnconnectedAC` : tout le reste avec le même sprite.

## 3. Ce que LiveWire compte aujourd'hui

- Une unité connectée est un `IsoClothingDryer` : `LiveWire\...\shared\LiveWire\LW_ApplianceFamilies.lua:78-79`
  (`class = "IsoClothingDryer", kind = "dryer", category = "laundry", profile = "dryer"`), avec `activation`
  `isActivated` / `setActivated` (champ `on`, `change = "DRYER_STATE"`).
- **Verdict : déjà compté** comme sèche-linge, mais avec **la puissance du profil sèche-linge**, pas celle d'une
  climatisation. Valeurs du profil `dryer` (`LW_Consumption.lua:20-29`) : **5000 W** (profil 1), 3000 W (profil 2),
  45 W (profil 4). Un profil 1 surestime vraisemblablement une climatisation.
- Une unité non connectée (objet vanille, pas un sèche-linge) n'est pas facturée : aucune famille ne matche.

## 4. État « en marche » et électricité

- État : `IsoClothingDryer:isActivated()`, écrit par `ACToggle` (`AirCond.lua:25-42`, `object:setActivated(state)`),
  et remis à `false` si la case n'a plus de courant (`AirCond.lua:69-71`).
- Test de courant du mod : `square:haveElectricity() or world:isHydroPowerOn()` (`AirCond.lua:61`, `:251`), donc
  l'énergie hydroélectrique compte aussi. Hors réseau moteur, une unité est éteinte par le mod lui-même.
- Refroidissement côté serveur : `42\media\lua\server\AirCondCoolingServer.lua` (non détaillé ici : hors besoin LiveWire).
- Pas de drapeau ModData lu par le mod pour l'état : `isActivated()` suffit.

## 5. Profil proposé

Justification : le profil sèche-linge (5000 W au profil 1) est une mauvaise estimation pour une climatisation. Un profil
dédié remplace le profil sèche-linge pour les unités connectées, grâce à la priorité des consommateurs enregistrés
(`LW_ApplianceFamilies.lua:58-60`, « a registered consumer comes first »).

La puissance de **1000 W est une hypothèse non sourcée** (ordre de grandeur d'une climatisation de fenêtre ou
mobile en marche). À sourcer avant publication.

Fichier cible (non créé) : `LiveWireCompatibility\...\Profiles\LWC_AirCond42.lua`.

```lua
-- LiveWire Compatibility: AirCond42 (Workshop 3784995595, mod id AirCond42).
-- Analysis: docs/annexes/recherches/air-conditioner-units.md. Watts are a guess, not sourced yet.
-- Connected units are IsoClothingDryer objects (class borrowed by the mod); unconnected units keep the
-- same sprite names but are not dryers, so running() is false for them and they stay free.
require "LiveWireCompatibility/LWC_Profiles"

LiveWireCompat.Profiles.add({
    name = "AirCond42",
    workshop = "3784995595",
    mods = { "AirCond42" },
    consumers = {
        { id = "AirCond42Unit", sprites = { "industry_01_4", "industry_01_5" }, watts = 1000,
          running = function(o)
              return instanceof(o, "IsoClothingDryer") and o:isActivated() == true
          end },
    },
})
```

**Point à décider** : un consommateur enregistré est « sans état » (`LW_ApplianceFamilies.lua:54`). Avec ce profil,
LiveWire ne restaure plus l'état marche/arrêt d'une unité après une coupure (la famille `dryer` a une `activation`
aujourd'hui). Le mod AirCond42 coupe déjà l'unité quand il n'y a plus de courant (`AirCond.lua:69-71`), donc
l'impact est probablement faible, mais à confirmer en jeu. Sans ce profil, la sur-facturation de 5000 W reste.

## 6. Limites

- Puissance : hypothèse (1000 W), non mesurée, non sourcée.
- Classe `IsoClothingDryer` : confirmée par le code (`TAConnectAC.lua`), pas par un test en jeu.
- Interaction `haveElectricity` / coupure LiveWire : non vérifiée en jeu (voir `machinery.md`, section 2).
- Aucun test en jeu, aucun démarrage du jeu.
