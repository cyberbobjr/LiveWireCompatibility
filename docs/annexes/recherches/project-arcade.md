# Project Arcade (Workshop 3645980077, id ProjectArcade)

Analyse D05 du 2026-11-13, **confirmée statiquement** (copie Workshop en lecture seule,
`108600\3645980077\mods\ProjectArcade\`, abrégé `M\`). Rien n'a été testé en jeu.

## Variante chargée

Dossiers `42.13/`, `42.15/` (médias seulement) et `common/` (Lua, tuiles, scripts). En 42.22, le jeu charge `common`
et `42.15`. Tout le Lua utile est dans `common`.

## Machines posées

Noms, faces et emprises lus dans `M\common\media\ProjectArcadeTiles.tiles` (décodé par `tools/check_sprites.py`).

| Machine | Sprites | Emprise | Pièce facturée |
|---|---|---|---|
| Bornes d'arcade (10 jeux × 4 faces) | `pa_arcades_0` à `_39` | 1 case | toutes |
| Borne `complex_t2` | `pa_complex_0`, `_1` | 1 case | toutes |
| Borne assise `complex_sw` | `pa_complex_2` à `_9` | 2 cases par face | la case `0,0` : `_2`, `_5`, `_6`, `_9` |
| Flippers (7 tables) | `pa_pinballs_0` à `_27` | 2 cases par face | la tête jouée par le mod (`PAMPlayGameMenu.lua:166-191`) : `0, 3, 4, 7, …, 24, 27` |
| Pince (claw machine) | `pa_recreational_2` à `_5` | 1 case | toutes |
| Pousse-pièces | `pa_recreational_6`, `_7` | 1 case | toutes |
| Punching-ball | `pa_recreational_0`, `_1` | 1 case | toutes |
| Néons muraux | `pa_decorations_8` à `_15` | mur | aucune : propriété `lightswitch`, objet `IsoLightSwitch` déjà facturé par LiveWire |

Les feuilles `*_on` et `*_overlay` sont des calques lumineux posés par-dessus (`ProjectArcade_WorldFiller.lua`) :
le sprite de base ne change pas. Le mod remplace sur la carte les bornes et flippers vanilla
(`recreational_01_16` à `_27`) par ces sprites (`server\ProjectArcade_ReplaceVanillaArcades.lua:83-96`).

## Courant

- Chaque fichier a sa propre fonction `local function machineHasPower(obj)` : `square:haveElectricity()` ou la grâce
  `ElecShutModifier` (`client\ProjectArcade_ClawMachine.lua:26`, `CoinPusher.lua:283`, `PAMPlayGameMenu.lua:370`,
  `PunchingMachine.lua:287`, `ArcadeAmbientSound.lua:137`). **Aucune n'est publique** : pas de coupure par les
  circuits possible.
- Pas d'état marche/arrêt : une machine sous tension joue son son d'ambiance (`ArcadeAmbientSound.lua`) et accepte
  les parties. Facturation dès qu'elle a du courant.

## Consommations (estimées, machines réelles de l'époque)

Borne verticale 120 W (moniteur CRT 19-25 pouces et carte en démonstration) ; borne assise 200 W ; flipper 200 W
(lampes, afficheur, bobines en démonstration) ; pince 100 W ; pousse-pièces 150 W ; punching-ball 60 W.

## Addon Spiffomon3D Prizes (3646127635)

Ajoute des peluches au lot de la pince : aucune machine, pas de sous-mod.

## Verdict

Sous-mod `batman_LiveWireCompatibilityProjectArcade`, sans enveloppe de test de courant.
