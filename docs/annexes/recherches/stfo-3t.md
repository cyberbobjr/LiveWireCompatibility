# STFO 3T: Traps, Turrets and Towers (Workshop 3838240933)

Analyse du 2026-11-20. Lecture seule de `108600\3838240933\mods\STFO\`. Constats **confirmés statiquement** sauf mention
contraire ; rien n'a été testé en jeu. Abréviations : `S\` = `...\STFO\42\media\`, `C\` = `...\STFO\common\media\`.

## 0. Variante chargée en 42.22

`id=STFO`, `versionMin=42.21`, `tiledef=simpletraps_01 6899`, `pack=simpletraps_01` (`42\mod.info`) ; `42/` et `common/`.
Lua : `client/SimpleTrapsClient.lua`, `SimpleTrapsViewpoint.lua` ; `server/SimpleTrapsServer.lua`, `SimpleTrapsLoot.lua` ;
`shared/SimpleTraps.lua`, `SimpleTrapsPlace.lua`, `SimpleTrapsSandbox.lua`, `TimedActions/*`. Tuiles
`C\simpletraps_01.tiles`, pack `C\texturepacks\simpletraps_01.pack` ; **aucune carte de profondeur**.

## 1. Modèle électrique propre

Un appareil est alimenté par le **secteur** (`SimpleTraps.hasMains(square)`, `S\lua\shared\SimpleTraps.lua:225-228` :
`haveElectricity()`, sinon pièce et réseau public) **ou par une batterie de voiture placée dedans**.
`SimpleTraps.power(obj)` (`:282-288`) rend `"mains"`, `"battery"` (charge > 0) ou `nil`. Aucun objet n'est facturé par le
moteur.

| Appareil | Sprites | Interrupteur propre | Estimation (secteur) |
|---|---|---|---|
| Électrificateur de clôture | `simpletraps_01_6` | non | 3 W |
| Détecteur de mouvement | `simpletraps_01_27` | non ; secteur seulement (`sensorPowered`, `:502-505`) | 2 W |
| Boîtier de portail | `simpletraps_01_28`, `50`, `51`, `52` | non | 5 W |
| Projecteur sur pied | `simpletraps_01_54` (têtes `34`-`41`) | oui | 300 W allumé |
| Lampe de chantier | `simpletraps_01_151` (têtes `152`-`159`) | oui | 150 W allumée |
| Projecteur de tour | socle `simpletraps_01_114` | oui | 300 W allumé |
| Tourelle automatique | socle `simpletraps_01_55` | oui | 40 W en veille |

Non électriques : fil-piège, plaques à pointes, pieux, pièges à mâchoires, mines, plates-formes, tours de guet (la tour 2×2
`_160`-`_175` ne consomme rien). La clôture elle-même (`_3`-`_5`) est alimentée par l'électrificateur.

## 2. Tests, boucles, état

- `SimpleTraps.power(obj)` est appelé par l'électrificateur (`:301`, `:1070`), le portail (`server:263`), le tir de la
  tourelle (`server:1243`), l'affichage du projecteur (`client:450`). `SimpleTraps.sensorPowered(sensor)` : serveur
  (`server:173`) et client (`client:452`). Toutes globales.
- Interrupteur propre (projecteurs, tourelle) : ModData `SimpleTrapsOn`, lu par `SimpleTraps.isOn(obj)` (`:914`), écrit
  par `SimpleTraps.serverSwitch(player, args)` sur le serveur (`server:901-931`, puis `transmitModData`) ; en solo le
  client l'appelle directement (`client:132-133`).
- Boucles : tir de la tourelle sur `OnTick` (serveur) ; décharge des batteries sur `EveryOneMinute` ; détection de clôture
  et de mouvement côté client sur `OnTick`.

## 3. Points d'interception retenus

1. `SimpleTraps.power(obj)` : seule la réponse `"mains"` est soumise à Live Wire ; machine non alimentée ⇒ repli sur la
   batterie si elle a de la charge, sinon `nil` (ADR-005, D04).
2. `SimpleTraps.sensorPowered(sensor)` (secteur seulement).
3. Signalement après `SimpleTraps.serverSwitch` (serveur).
