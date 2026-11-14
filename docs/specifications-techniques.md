# Spécifications techniques

## Dépendances

- `batman_LiveWireCompatibility` : `require=\batman_LiveWire`, `loadModAfter=\batman_LiveWire`. Aucun mod cible
  n'est exigé : chaque profil s'applique seulement si l'un de ses `mods` est actif. API LiveWire révision 6 au moins
  (`LiveWire.API.revision`) ; sinon rien n'est inscrit et un message est écrit.
- Fonctions de l'API utilisées : `registerConsumer(id, définition)`, `consumer(obj)`, `consumerPowered(obj)`.

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
          category = "other", circuit = "equipment",  -- facultatifs, comme registerConsumer
          couldBePowered = function(o) ... end },     -- facultatif
    },
    gates = {                                -- facultatif
        { path = "PMK.Well.isPowered",       -- chemin pointé depuis une globale
          arg = 1,                           -- position de l'argument utile, défaut 1
          kind = "object",                   -- "object" ou "square"
          consumer = "ArtelWell",            -- id, ou tableau d'ids si un test sert plusieurs machines
          side = "client" },                 -- facultatif : test défini dans le Lua client du mod cible
    },
})
```

Refus de `add` : `invalid_profile`, `duplicate_profile`.

## Application (`Events.OnInitWorld`)

1. API absente ou révision < 6 : message, rien d'autre.
2. Pour chaque profil dont un mod est actif (`getActivatedMods():contains`) : `registerConsumer` pour chaque
   consommateur. `duplicate_consumer` (second `OnInitWorld`) est ignoré ; tout autre refus est écrit une fois.
3. Chaque `gate` est enveloppé une seule fois (le registre garde l'enveloppe posée ; un second passage la reconnaît).
   Un `gate` `side = "client"` n'est ni enveloppé ni signalé absent sur un serveur dédié (`isServer()`) : son mod
   cible ne le charge que chez les clients.

## Enveloppe d'un test de courant

`wrapper(...)` : `r = original(...)` ; si `r` est faux, rendre `r`. Sinon prendre l'argument `arg` ; si `kind =
"square"`, chercher sur la case un objet dont `LiveWire.API.consumer(o)` est l'un des ids de `consumer`. Si l'objet
n'est pas l'un de ces consommateurs, rendre `r`. Sinon rendre `r` si `consumerPowered(objet)`, `false` sinon. Arguments et autres
retours ne sont pas modifiés.

## Journaux (console, anglais)

- `[LiveWireCompat] LiveWire API revision 6 or later not found: nothing registered`
- `[LiveWireCompat] <profil>: consumer <id> not registered (<raison>)`
- `[LiveWireCompat] <profil>: power check <chemin> not wrapped (gate_not_found)`

## Profils livrés

| Fichier | Mod cible | `mods` | Consommateurs | Tests de courant enveloppés |
|---|---|---|---|---|
| `Profiles/LWC_Artel.lua` | Artel Manufactory (3794133594) | `ArtelManufactory` | `ArtelWellMotor`, `ArtelElectricDryer`, `ArtelSublimator`, `ArtelChemTable`, `ArtelTradePost`, `ArtelQuantumBase` | `PMK.Well.isPowered` (objet), `PMK.Trade.gridPowered` (objet), `PMK.QBase.squarePowered` (case) |
| `Profiles/LWC_FunctionalAppliances2.lua` | Functional Appliances 2 (3042138819) | `FunctionalAppliances2` | `FA2HeatedCounter`, `FA2DisplayCounter`, `FA2VendingMachine`, `FA2HotDogMachine`, `FA2PopcornMachine`, `FA2SodaFountain`, `FA2SlurpNBurp`, `FA2BarTap`, `FA2ExhaustHood` | aucun (tests en ligne) |
| `Profiles/LWC_ComputerMod.lua` | Computer Mod (3725497089) | `ComputerModkum` | `ComputerModDesktop` | `ComputerModPower.hasComputerPower` (objet, client seulement) |
| `Profiles/LWC_PlyskenWeatherStation.lua` | Plysken Weather Station (3781590169) | `PWS` | `PWSStation` | `PWS.Power.isPowered` (objet) |
| `Profiles/LWC_TrueMoozic.lua` | True Moozic (3632610172) | `TrueMoozic` | `TMJukebox` | `TMJukebox.hasPower` (case) |
| `Profiles/LWC_Machinery.lua` | Machinery (3780027195) | `Machinery` | `MachineryDrillPress`, `MachineryMetalBandsaw`, `MachineryHydraulicPress`, `MachineryLathe`, `MachineryBenchGrinder`, `MachineryTableSawIndustrial`, `MachineryTableSawContractor`, `MachineryConcreteMixer` | `Machinery.Service.isPowered` (objet, les huit) |
| `Profiles/LWC_ProjectArcade.lua` | Project Arcade (3645980077) | `ProjectArcade` | `PAArcadeCabinet`, `PASitDownCabinet`, `PAPinball`, `PAClawMachine`, `PACoinPusher`, `PAPunchingMachine` | aucun (tests `local`) |

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

Aucune pour l'instant : le nom affiché dans le logiciel de gestion est celui de la catégorie LiveWire.

## Compatibilités vérifiées

Aucune vérifiée en jeu.
