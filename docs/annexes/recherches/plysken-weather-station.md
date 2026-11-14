# Plysken Weather Station (Workshop 3781590169, id PWS)

Analyse du 2026-11-13, **confirmée statiquement** (copie Workshop en lecture seule, `108600\3781590169\mods\Plysken Weather Station\`). Rien n'a été testé en jeu.

## 1. Variante chargée en 42.22

- Dossiers présents : `42.1/` (avec `mod.info`), `common/` (tiledef, pack, viewpoint) et `mod.info` racine. Les trois `mod.info` sont identiques (`versionMin=42.20`, metadonnee seulement).
- Règle de choix du dossier de version : `E:\pz-source-42.22\java\zombie\ZomboidFileSystem.java:454-466` (`getModVersionDirName`) retient le dossier au plus haut entier <= 42.22 (`42.1` = 42001, `common` = 0 ignoré).
- Conclusion : **`42.1/` est la variante chargée en 42.22**, sans dossier concurrent. Confirmé dans le code Java ; la ligne de chargement dans `console.txt` reste à relever.

## 2. Objets posés

| Élément | Type | Constat |
|---|---|---|
| `WeatherStation` (station) | `base:moveable`, `WorldObjectSprite = pws_tileset_01_0` (`42.1/media/scripts/PWS/Items.txt:94-102`) | **Seul objet posé du mod.** |
| `Mast`, `Vane`, `Anemometer`, `RainGauge`, `Screen`, `Barometer`, `LoggerBox` | `base:normal` (`Items.txt:10-80`) | Inventaire : pièces assemblées, jamais posées seules. Non facturables. |
| `PWSMagazine` | `base:literature` | Non concerné. |
| Ordinateur de bureau | Objet **vanille** `appliances_com_01_*` | Reconnu par `PWSComputer.lua` (table `K.SPRITES`, `K.isComputer` l.60-70). Ce n'est pas un objet du mod. Pour LiveWire : pas une famille comptée, donc courant gratuit comme toute machine vanille non listée. Hors périmètre de ce profil. |

## 3. Sprites de la station

- `pws_tileset_01_0` : sprite de pose (`Items.txt:102`), **confirmé**. Le préfixe `pws_tileset_01_` est la clé d'identité (`42.1/media/lua/shared/PWS/PWSStation.lua:23-49`, `S.SPRITE_PREFIX`).
- `pws_tileset_01_1` : présent dans `common/media/texturepacks/pws_tileset.pack` (chaîne lue en binaire). Commentaire `PWSStation.lua:23` : « toutes les faces du sprite (S, E) commencent par ce motif ». **Hypothèse** : `_1` est la face E. Le `.tiles` binaire ne donne que la feuille `pws_tileset_01`.

## 4. Coupure de circuit

- Fonction de test : `PWS.Power.isPowered(obj)` (`42.1/media/lua/shared/PWS/PWSPower.lua:51-64`). **Publique** : `PWS` est une globale (`PWSPower.lua`, `PWS = PWS or {}`), `P` est `PWS.Power`. Argument : **l'objet** (la station).
- Union de trois tests : `obj:hasGridPower()` ; `obj:checkObjectPowered()` ; `sq:haveElectricity()` (via `obj:getSquare()`).
- Appels dynamiques : `PWSStation.lua:74` et `PWSComputer.lua:211` appellent `PWS.Power.isPowered(...)` par recherche de champ à chaque appel. Un wrapper posé sur `PWS.Power.isPowered` est donc vu.
- Variante case : `P.isSquarePowered(sq)` (l.~67), pour la pose. Non utilisée par un gate.
- Lecture de l'état « en marche » : **aucune clé ModData d'alimentation**. Seule la fonction `isPowered(obj)` renseigne. `PWSLog.lua:89` s'en sert pour écrire les trous du journal.

## 5. Puissance

- **Aucune valeur de puissance** dans le mod (recherche `watt`, `W`, `power` sans chiffre). La description Steam dit seulement « Needs power ».
- **Estimation (hypothèse, à valider)** : 15 W pour une station électronique extérieure (capteurs, enregistreur, écran). Pas de source externe. Décision à prendre.

## 6. Verdict

- **À profiler.** Objet posé, consommateur réel (il ne mesure que sous courant, `PWSStation.lua:70-76`). Non compté par LiveWire : pas de conteneur `fridge`/`freezer`, pas de `FuelAmount`, pas d'IsoGenerator (`LW_ApplianceFamilies.lua:27-83`).
- Cohérence avec le jeu : `PWSPower.lua` ne consomme rien lui-même ; la coupure de circuit est exactement ce que le mod prévoit (« plus de courant ⇒ plus de relevé »). Le gate est donc cohérent avec le comportement voulu.

## Profil proposé

Fichier cible (non créé) : `Contents\mods\batman_LiveWireCompatibility\42.21\media\lua\shared\LiveWireCompatibility\Profiles\LWC_PlyskenWeatherStation.lua`

```lua
-- LiveWire Compatibility: Plysken Weather Station (Workshop 3781590169, mod id PWS).
-- Analysis: docs/annexes/recherches/plysken-weather-station.md. The watts figure is an
-- assumption (PWS states none). The station is a moveable world object; its only
-- placed sprites are pws_tileset_01_0 (S face, confirmed) and pws_tileset_01_1 (E face,
-- assumed). The gate wraps the public PWS.Power.isPowered, called by PWS itself.
require "LiveWireCompatibility/LWC_Profiles"

LiveWireCompat.Profiles.add({
    name = "PlyskenWeatherStation",
    workshop = "3781590169",
    mods = { "PWS" },
    consumers = {
        { id = "PWSStation", sprites = { "pws_tileset_01_0", "pws_tileset_01_1" }, watts = 15,
          running = function(o)
              local p = PWS and PWS.Power
              return p ~= nil and p.isPowered ~= nil and p.isPowered(o) == true
          end },
    },
    gates = {
        { path = "PWS.Power.isPowered", kind = "object", consumer = "PWSStation" },
    },
})
```

Points à confirmer avant intégration :
- Valeur de 15 W (hypothèse), à valider.
- Sprite E `pws_tileset_01_1` (hypothèse) : à vérifier en jeu (`pzdev lua` sur le sprite de la face E) ou dans les tuiles.
- Le `running` appelle `isPowered` à chaque passage : coût à mesurer si le nombre de stations augmente.
- Le serveur dédié Linux exige la casse exacte de `PWS` et des chemins `PWS/` (`pws_tileset_01_` est une chaîne, pas un chemin).
