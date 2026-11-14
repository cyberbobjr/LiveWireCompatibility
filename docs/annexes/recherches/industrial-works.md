# Industrial Works (Workshop 3680638986)

Analyse du 2026-11-13. Lecture seule de `108600\3680638986\mods\IndustrialWorks\42\`. Tous les constats sont
**confirmés statiquement**. Rien n'a été testé en jeu.

## 0. Variante chargée en 42.22

- `id=IndustrialWorks`, `name=Industrial Works`, `modversion=1.2`, `versionMin=42.14.1` (`42\mod.info` l.1-10).
- Seul dossier de version : `42/` (pas de `common/`, pas de `42.21/`). Variante chargée : **`42/`**.

## 1. Ce que fait le mod

Le mod ne pose aucun appareil. Il transforme deux tuiles vanille existantes en objets fonctionnels, déclenchés par
un clic contextuel (`client\GyWClientMP.lua:24-144`) puis une commande serveur `GyW_PlaceItem`
(`server\GyWServerMP.lua:201-211`) :

| Sprite vanille | Objet créé | Fonction |
|---|---|---|
| `industry_02_67` ou `CCO_INDUSTRY_01_1` | `IsoGenerator` (`Base.Generator_Yellow`) | Source de courant |
| `industry_02_73` | `IsoThumpable` avec `FluidContainer` (capacité 3000, récupération de pluie) | Réservoir d'eau |

## 2. Générateur : source, pas consommateur

- `GyWServerMP.lua:62-86` : `IsoGenerator.new(...)`, `setCondition(ZombRand(60,101))`, `setFuel(ZombRand(2,11))`,
  `setConnected(true)`, `setActivated(true)`, `setSprite(sprite)`.
- Le moteur traite un `IsoGenerator` comme source : `LiveWire\server\LiveWire\LW_Install.lua:68`
  (`instanceof(obj, "IsoGenerator")` renvoie `"backup"`). LiveWire traite donc déjà ces générateurs comme
  sources (`LW_Demand.lua` reproduit la règle du moteur pour la demande, `LW_Demand.lua:2-4`).
- La famille `fuel` (`LW_ApplianceFamilies.lua:83`, match `FUEL_AMOUNT`) n'a **pas de profil** (`profile` absent) :
  elle n'est jamais facturée. Le générateur ne peut donc pas être facturé comme consommateur.
- **Verdict : non facturable (source déjà gérée).**

## 3. Réservoir d'eau : non électrique

- `GyWServerMP.lua:122-139` : `IsoThumpable.new(cell, square, "industry_02_73", ...)`, `FluidContainer`,
  `setRainCatcher(1.0)`, `setCapacity(3000)`. Aucune alimentation, aucun `haveElectricity`.
- Aucune famille LiveWire ne matche (pas de conteneur `fridge`/`freezer`, pas de `FUEL_AMOUNT`).
- **Verdict : non facturable.**

## 4. Sprites et états

- Générateur : `industry_02_67`, `CCO_INDUSTRY_01_1`. Icône de menu : `media\textures\gen_industry_42x42.png`.
- Réservoir : `industry_02_73`. Icône : `media\textures\water_industry_42x42.png`.
- Test d'état : `GyWServerMP.lua:168-169` (`square:getGenerator()`) ; l'état d'un générateur reste celui du moteur.
- La fonction serveur `EveryOneMinute_GyW` (l. 150-194) ne fait que retirer la fumée toxique : sans effet sur la
  consommation.

## 5. Profil

**Aucun profil proposé** : aucun consommateur électrique, et le générateur est une source déjà traitée par LiveWire.

## 6. Limites

- Un générateur créé par ce mod est un `IsoGenerator` ; son comportement de réseau dépend du moteur (ce rapport ne
  l'a pas vérifié en jeu).
- Le mod est côté serveur (`GyWServerMP.lua:3`, `if isClient() then return end`) : aucun effet client sur la
  consommation.
