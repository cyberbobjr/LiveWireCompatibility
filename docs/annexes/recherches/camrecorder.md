# CamRecorder (Workshop 3840702720)

Analyse du 2026-11-20. Lecture seule de `108600\3840702720\mods\CamRecorder\`. Constats **confirmés statiquement** sauf
mention contraire ; rien n'a été testé en jeu. Abréviation : `M\` = `...\CamRecorder\42\media\`.

## 0. Variante chargée en 42.22

`id=CamRecorder`, `versionMin=42.21`, `versionMax=42.22`, `javaJarFile=media/java/client/CamRecorder.jar`,
`require=\ZombieBuddy,\Viewpoint,\PZVoxelStudioViewpoint`. Seul `42/` est chargé. 53 fichiers Lua (client 32, serveur 11,
partagé 10). Aucune tuile propre ni carte de profondeur : tuiles vanilla `appliances_com_01_*`, `security_01_*` et un
sprite-texture pour la caméra fixée. Mods exigés présents : ZombieBuddy et Viewpoint (Java), PZVoxelStudioViewpoint (Lua).

## 1. Objets posés électriques

| Objet | Sprites | Facturé par le moteur | Estimation |
|---|---|---|---|
| Caméra de sécurité fixée | `media/textures/Item_CamRecorder_SecurityCamera.png` (`CamRecorderFixtures.lua:4`), une seule image | non | 5 W |
| Caméra Imekagi | `appliances_com_01_44`-`47` (`CamRecorderImekagi.lua:9`) | non | 12 W |
| Moniteurs de sécurité | `security_01_0`-`5` (`CamRecorderSecurityTerminal.lua:32-38`) | non | 45-60 W |
| PC de surveillance | `appliances_com_01_72`-`75` (`shared/PZVideoConsole.lua:40`) | non | 120 W allumé |
| Téléviseurs vanilla (sorties) | `IsoTelevision` | **oui** | — |

Les caméscopes au sol utilisent le même sprite que la caméra fixée mais fonctionnent sur piles (`CamRecorderPower.lua:30`) :
`PZVideoDevices.usesGrid` les distingue. Objets portés (caméscopes, cassettes, piles, détecteur) : non facturables.
**Chevauchement avec Computer Mod** : `appliances_com_01_72`-`75` (ordinateur de bureau vanilla). Voir ADR-005.

## 2. Tests de courant et état

- Caméras : `PZVideoPower.hasSupply(camera)` (`CamRecorderPower.lua:25-31`, global, client) ; l'objet posé est
  `camera.pzObject`. Serveur : `CamRecorderAccessServer.setRecording` (global) ; d'autres tests sont `local`.
- Moniteurs : `local powered` (`CamRecorderSecurityTerminal.lua:48-54`), exporté `T.powered` (`:55`) mais les appels
  internes utilisent la locale ; état `md.pzVideoTerminal.enabled` (faux = éteint), basculé par `T.setOption` (global).
- PC : `CamRecorderConsole.available(computer, player, range)` (`shared/PZVideoConsole.lua:60-65`, global, partagé, aussi
  sur le serveur `PZVideoServer.lua:278, 297, 651`) ; état `md.pzVideoConsoleEnabled` basculé par
  `PZVideoSecurityTerminal.toggleComputer` (global) → commande `consolePower` → `Console.setPower` (`:92-97`).
- Imekagi : `pzVideoCamera.powered`, basculé par une classe locale : pas de route globale.

## 3. Points d'interception retenus

1. `CamRecorderConsole.available` : PC (client et serveur).
2. `PZVideoPower.hasSupply(camera)` : caméras sur le secteur (machine = `camera.pzObject`).
3. `T.powered` pour les appels externes des moniteurs (couverture partielle) ; signalement après `T.setOption` et
   `toggleComputer`.
