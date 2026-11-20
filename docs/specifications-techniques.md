# Spécifications techniques

## Dépendances

- `batman_LiveWireCompatibility` : `require=\batman_LiveWire`, `loadModAfter=\batman_LiveWire,\ArtelManufactory` (ordre
  seulement, ADR-006 D04 : `loadModAfter` ne rend pas Artel obligatoire). Aucun mod cible n'est exigé : chaque profil s'applique seulement si l'un de ses `mods` est actif. API LiveWire révision 6 au moins
  (`LiveWire.API.revision`) ; sinon rien n'est inscrit et un message est écrit.
- Fonctions de l'API utilisées : `registerConsumer(id, définition)`, `consumer(obj)`, `consumerPowered(obj)`.

## Interrupteur (ADR-002, D01-D04)

- État : ModData de l'objet posé, `LWC_off = true` quand la machine est éteinte ; clé absente = allumée (machines
  posées avant 1.1.0 incluses). Ramasser la machine perd l'état. Seuls les consommateurs `switch = true` en ont un.
- `LiveWireCompat.Switch.powered(o)` = `consumerPowered(o)` **et** pas éteinte : la seule définition de « machine
  alimentée », utilisée par toutes les gardes.
- Facture : éteinte = 0 W (ni `watts` ni `idle`), à la mesure suivante de LiveWire (10 minutes de jeu au plus).
- Geste : menu contextuel « Allumer » / « Éteindre » (`client/LWC_SwitchMenu.lua`), infobulle « Consomme N W en
  marche » quand `watts` est connu. Le joueur marche jusqu'à la machine, puis `LWC_SwitchAction` (10 ticks, sans
  `complete`) appelle `Switch.request`.
- Commande : `sendClientCommand(player, "LWC", "setSwitch", { x, y, z, sprite, off })` en MP ; appel direct en solo.
  Le serveur (`server/LWC_SwitchServer.lua`, ignoré par un client MP) cherche sur la case un objet de ce sprite qui a
  un interrupteur, vérifie la portée (2,5 cases, même étage), écrit la ModData et `transmitModData()`. Refus écrits
  dans la console : `bad_request`, `no_machine`, `out_of_reach`.
- Chaque basculement prévient Live Wire (`Switch.changed`, ADR-004) : sur l'autorité `LiveWire.API.consumerChanged(obj)`
  (révision 10, remesure immédiate des réseaux qui servent la machine) ; sur un client, commande `LWC` / `changed`
  `{ x, y, z, sprite }`, que le serveur valide (consommateur inscrit de ce sprite sur la case, joueur à 10 cases au plus)
  avant d'appeler l'API. Sans révision 10, rien : la mesure suivante (10 minutes de jeu au plus) le montre.
- Aucune boucle propre : ni `OnTick`, ni `Every*`.

## Format d'un profil

```lua
LiveWireCompat.Profiles.add({
    name = "Artel",                          -- unique, sert aux messages
    mods = { "ArtelManufactory" },           -- ids de mod.info ; un seul actif suffit
    consumers = {
        { id = "ArtelElectricDryer",         -- id LiveWire, préfixé par la cible
          sprites = { "Artel_..." },         -- une seule pièce par meuble de plusieurs cases
          watts = 1200,                      -- nombre ou function(o) -> W, en marche
          running = function(o) ... end,     -- facultatif
          idle = 0,                          -- W à l'arrêt, défaut 0
          switch = true,                     -- facultatif : interrupteur de ce mod (ADR-002)
          category = "other", circuit = "equipment",  -- facultatifs, comme registerConsumer
          couldBePowered = function(o) ... end },     -- facultatif
    },
    gates = {                                -- facultatif, voir « Types de garde »
        { kind = "object",                   -- type de garde
          path = "PMK.Well.isPowered",       -- chemin pointé depuis une globale
          arg = 1,                           -- champs propres au type
          consumer = "ArtelWell",            -- id, ou tableau d'ids si un point d'entrée sert plusieurs machines
          side = "client" },                 -- facultatif : "client" ou "server"
    },
})
```

Refus de `add` : `invalid_profile` (dont un type de garde inconnu ou ses champs invalides), `duplicate_profile`.

## Types de garde (ADR-002, D05)

Registre `LWC_Gates.lua`, un fichier par type sous `Gates/`. Une garde « bloque » une machine quand elle est l'un
de ses consommateurs et que `Switch.powered` est faux. Chaque fonction est enveloppée une seule fois (registre des
enveloppes, clé = chemin ou chemin:méthode), arguments et retours préservés.

| Type | Champs | Effet |
|---|---|---|
| `object` | `path`, `arg` (défaut 1) | test de courant du mod cible : sa réponse, puis `false` si la machine (argument `arg`) est bloquée |
| `square` | `path`, `arg` | idem, la machine est cherchée sur la case passée en argument |
| `action` | `path` (classe d'action), `field` ou `machine(action)` | `isValidStart` et `isValid` de la classe rendent `false` : action refusée ou arrêtée (le jeu relit `isValid` à chaque mise à jour, `LuaTimedActionNew.java:110`) ; message une fois par action |
| `call` | `path`, `arg` ou `machine(...)`, `player`, `allow(...)`, `refuse`, `instead(original, ...)` | la fonction n'est pas exécutée : rend `refuse` (ou le résultat de `instead`) ; `allow` laisse passer certains appels (choisir « arrêt ») |
| `menu` | `name` | client : après les menus des mods cibles (`OnFillWorldObjectContextMenu`), grise les options dont `target` ou `param1..10` est une machine bloquée, sous-menus compris ; infobulle = raison |
| `custom` | `name`, `install(gate, G)` | installeur fourni par le profil, quand aucun type ne convient |
| `notify` | `path`, `arg` ou `machine(...)`, `state(machine)` | ne refuse rien : après l'appel d'origine, prévient Live Wire (`Switch.changed`) que la machine a changé ; avec `state`, seulement quand cet état change (ADR-004) |

Côtés : `side = "client"` n'est pas installé sur un serveur dédié, `side = "server"` pas sur un client MP ; les
deux s'installent en solo. Message au joueur (client seulement, `setHaloNote`) : `IGUI_LWC_MachineOff` si la
machine est éteinte, sinon `IGUI_LWC_NoPower`.

## Application (`Events.OnInitWorld`)

1. API absente ou révision < 6 : message, rien d'autre.
2. Pour chaque profil dont un mod est actif (`getActivatedMods():contains`) : `registerConsumer` pour chaque
   consommateur. `duplicate_consumer` (second `OnInitWorld`) est ignoré ; tout autre refus est écrit une fois.
   Un consommateur `switch = true` inscrit reçoit l'interrupteur.
3. Chaque garde de ce côté (`side`) est installée une seule fois (le registre garde l'enveloppe posée ; un second
   passage la reconnaît). Une garde absente du mod cible est signalée, sans erreur.

## Profondeurs B42 des sprites sans profondeur (ADR-003)

`common/media/depthmaps/` livre une carte par jeu de tuiles dont un sprite de profil n'a aucune profondeur (ni case non vide
dans une carte du jeu ou d'un mod, ni renvoi) : `DEPTH_Artel.png` (40 cases), `DEPTH_pa_arcades.png` (22),
`DEPTH_pa_complex.png` (4), `DEPTH_pa_recreational.png` (8), `DEPTH_machinery_metal_bandsaw_01.png` (4),
`DEPTH_pws_tileset_01.png` (2). Seules ces cases sont remplies ; une carte existante d'un jeu de tuiles garde ses cases et
fixe les dimensions (le moteur fusionne case par case, `TilesetDepthTexture.mergeTileset`, aux dimensions minimales). Le
moteur ne les charge qu'avec `common/media/tileGeometry.txt`. Les images qu'Artel superpose à ses stations chargées (`overlays` du profil) prennent la profondeur de leur machine.
Chaque sprite est un bloc carré centré sur sa case ajusté à sa
silhouette ; aucun pixel du sprite sans texel. Sans profondeur, le jeu ne dessinait pas la surbrillance de ces machines de
face (« Afficher les consommateurs », menu contextuel).

## Journaux (console, anglais)

- `[LiveWireCompat] LiveWire API revision 6 or later not found: nothing registered`
- `[LiveWireCompat] <profil>: consumer <id> not registered (<raison>)`
- `[LiveWireCompat] <profil>: power check <chemin ou nom> not wrapped (gate_not_found)`
- `[LiveWireCompat] switch request refused (<raison>)` (serveur)
- `[LiveWireCompat] source patch applied: <mod>:<chemin>` ; `source patch not applied (<raison>), original file runs: …` ;
  `cannot read <mod> <chemin>: nothing run` ; `source patch not run for <mod> <chemin>: load batman_LiveWireCompatibility after <mod>`

## Correctifs de source (ADR-006)

`LWC_SourcePatch` : un profil déclare `SourcePatch.add({ mod, path, edits = { { old, new } } })` ; un fichier du mod au même
chemin que celui de la cible appelle `return LiveWireCompat.SourcePatch.run(path)`. Le fichier de la cible est lu dans
son dossier (`getModFileReader`), chaque `old` doit apparaître une seule fois, le texte modifié s'exécute (`loadstring`) ;
sinon le fichier d'origine s'exécute tel quel (`SourcePatch.applied[path]` : `true`, `edit_not_found`, `compile_error`,
`unreadable`). `SourcePatch.report()` (fin de `applyAll`) signale un correctif d'un mod actif qui n'a pas tourné (ordre de
chargement). Correctif livré : Artel `media/lua/server/PMK_58z_SublimatorServer.lua`, déclaration de `squarePowered`
remplacée sur une seule ligne par `LiveWireCompat.Artel.stationPowered(square, réponse d'Artel)` ; `loadModAfter` cite
`ArtelManufactory`.

## Profils livrés

| Fichier | Mod cible | `mods` | Interrupteur (`switch`) | Gardes |
|---|---|---|---|---|
| `Profiles/LWC_Artel.lua` | Artel Manufactory (3794133594) | `ArtelManufactory` | les six | `PMK.Well.isPowered`, `PMK.Trade.gridPowered` (object) ; `PMK.QBase.squarePowered` (square) ; `custom` serveur : pause des lots (`PMK.dryPause.thaw` + `PMK_StationApplyStage`), état suivi par `PMK.QBase.rebuild` ; `call` client `PMK_CraftBenchPanel.isUsable` |
| `Profiles/LWC_FunctionalAppliances2.lua` | Functional Appliances 2 (3042138819) | `FunctionalAppliances2` | hot-dog, pop-corn, fontaine, SlurpNBurp, tireuses | `call` client `FA.updateMachineTemp` (passe en Off), `onUse…` des sept tables FA ; `action` `UseHotDogMachine`, `UsePopcornMachine`, `UseSodaFountain`, `UseBarTaps` (client : un serveur n'appelle pas `isValid`) |
| `Profiles/LWC_ComputerMod.lua` | Computer Mod (3725497089) | `ComputerModkum` | natif | `ComputerModPower.hasComputerPower` (object, client) |
| `Profiles/LWC_PlyskenWeatherStation.lua` | Plysken Weather Station (3781590169) | `PWS` | oui | `PWS.Power.isPowered` (object) |
| `Profiles/LWC_TrueMoozic.lua` | True Moozic (3632610172) | `TrueMoozic` | natif | `TMJukebox.hasPower` (square, client) |
| `Profiles/LWC_Machinery.lua` | Machinery (3780027195) | `Machinery` | les huit | `Machinery.Service.isPowered` (object, les huit) |
| `Profiles/LWC_ProjectArcade.lua` | Project Arcade (3645980077) | `ProjectArcade` | les six | `menu` client (dont la pince, lue dans les objets cliqués) ; `action` client sur les quatre actions de jeu ; `call` client `ProjectArcade_CoinPusher.OpenUI`, `ProjectArcade_CoinPusherUI.beginPlay` |
| `Profiles/LWC_KnoxWorkingMachines.lua` | Knox Working Machines (3841890337) | `KnoxWorkingMachines` | toutes | `ISEntityUI.CanOpenWindowFor` (object, arg 2, client), `ISHandcraftAction` (action, `isoObject`, client), menu du lavage auto ; tuiles partagées avec Machinery |
| `Profiles/LWC_STFO.lua` | STFO 3T (3838240933) | `STFO` | électrificateur, détecteur, boîtier de portail (projecteurs et tourelle : le leur, `notify` sur `SimpleTraps.serverSwitch`) | `SimpleTraps.power` (call : le secteur coupé rend la batterie, éteint rend rien), `SimpleTraps.sensorPowered` (object) |
| `Profiles/LWC_CamRecorder.lua` | CamRecorder (3840702720) | `CamRecorder` | caméra fixée (Imekagi, moniteurs, PC : le leur, `notify`) | `CamRecorderConsole.available` (object), `PZVideoPower.hasSupply` (call, client), `PZVideoSecurityTerminal.powered` (object, client), `CamRecorderAccessServer.setRecording` (call, serveur) ; ordinateur partagé avec Computer Mod |

Tuiles partagées (ADR-005) : un consommateur peut porter `shared = "<Id>"` et `owns(o)`. Le chargeur inscrit un seul
consommateur LiveWire par `shared` (sprites des profils actifs) ; chaque objet appartient au premier membre dont `owns`
est vrai, sinon au membre sans `owns` (`Profiles.memberOf`, `consumerIdOf`), qui décide consommation, interrupteur,
gardes et nom. Groupes livrés : `VanillaDesktop` (Computer Mod, repli ; CamRecorder), `VanillaDrillPress`, `VanillaLathe`,
`VanillaIndustry03Mill`, `VanillaBenchGrinder` (Machinery, repli ; Knox Working Machines).

Machines de plusieurs cases : un profil facture une pièce par meuble ; `Gates.billed` retrouve cette pièce depuis
n'importe quelle autre (grille de sprites, ou entité multi-cases B42 `SpriteConfig.getAllMultiSquareObjects`), avec
une seule liste réutilisée.

Mods analysés sans profil (rapports dans `annexes/recherches/`) : Vectrex Playable Console (objet d'inventaire),
Plysken Battery Charger (inventaire, manivelle), Plysken Irrigation Pipes (rien d'électrique), Computer Mod Laptop
Addon (inventaire), True Moozic Mumble Remover (aucun objet), More Machinery Recipes (recettes seules), Badlands Power
et Industrial Works (générateurs `IsoGenerator`, sources déjà connues de LiveWire), [B42] Working Air Conditioner
Units (unité branchée remplacée par un `IsoClothingDryer` : famille sèche-linge de LiveWire, facturée et coupée),
Video Game Consoles et ses addons de jeux (consoles posées au sol comme objets d'inventaire, portables sur piles),
Palm Pilots (inventaire), Spiffomon3D Prizes (lots de la pince).

Sprites vanilla : plusieurs profils facturent des tuiles de carte vanilla auxquelles leur mod cible donne un usage
électrique (Functional Appliances 2, Computer Mod, juke-box de True Moozic). Le profil n'est appliqué qu'avec ce mod
cible ; sans lui, ces tuiles restent gratuites.

Le champ `workshop` d'un profil (identifiant Workshop du mod cible) sert seulement à `tools/check_sprites.py`.

## Traductions

`media/lua/shared/Translate/EN|FR/ContextMenu.json` (`ContextMenu_LWC_TurnOn`, `ContextMenu_LWC_TurnOff`) et
`IG_UI.json` (`IGUI_LWC_MachineOff`, `IGUI_LWC_NoPower`, `IGUI_LWC_RatedWatts`). Autres langues : repli anglais. Le nom
affiché dans le logiciel de gestion reste celui de la catégorie LiveWire.

## Compatibilités vérifiées

Aucune vérifiée en jeu.
