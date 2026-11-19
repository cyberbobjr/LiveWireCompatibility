# Architecture

## Vue d'ensemble

Un seul mod, `batman_LiveWireCompatibility` (ADR-001, D01). Il porte le chargeur, un profil par mod cible, un
interrupteur marche/arrêt et des gardes qui empêchent une machine non alimentée de fonctionner (ADR-002). Le joueur
l'active une fois : chaque profil s'applique tout seul quand son mod cible est actif. Aucun objet, recette ni tuile.
Les profils passent par l'API publique de LiveWire (`LiveWire.API`, révision 6 au moins) ; LiveWire et les mods
cibles ne sont pas modifiés.

```
Profiles/LWC_<Cible>.lua --add--> LWC_Profiles (registre)
                                   | Events.OnInitWorld
                                   v
             mod cible actif ? --oui--> LiveWire.API.registerConsumer(id, définition)   (0 W si éteinte)
                                   |--> LWC_Switch.enable(id)        si switch = true
                                   \--> LWC_Gates.install(garde)     un type par fichier sous Gates/
                               --non--> rien

Joueur : menu « Allumer / Éteindre » (client) --LWC/setSwitch--> serveur : ModData LWC_off, transmitModData
Mod cible : point d'entrée enveloppé --> LWC_Switch.powered(machine) = courant LiveWire ET allumée
```

## Arborescence

```
Contents/mods/batman_LiveWireCompatibility/
├── common/                          vide (structure B42)
└── 42.21/
    ├── mod.info                     require=\batman_LiveWire
    └── media/lua/
        ├── shared/LiveWireCompatibility/
        │   ├── LWC_Profiles.lua     registre des profils, validation, chargeur
        │   ├── LWC_Switch.lua       état de l'interrupteur, powered(), traitement d'une demande
        │   ├── LWC_Gates.lua        registre des types de garde et aides communes
        │   ├── Gates/               un fichier par type : Check (object, square), Action, Call, Menu, Custom
        │   └── Profiles/            un fichier par mod cible
        ├── shared/Translate/EN|FR/  ContextMenu.json, IG_UI.json
        ├── client/LiveWireCompatibility/LWC_SwitchMenu.lua   option de menu et action « Allumer / Éteindre »
        └── server/LiveWireCompatibility/LWC_SwitchServer.lua commande LWC/setSwitch
```

## Modules

| Module | Côté | Rôle |
|---|---|---|
| `LWC_Profiles.lua` | `shared` | `add` valide et range un profil ; `applyAll` (sur `Events.OnInitWorld`) inscrit les consommateurs des profils actifs, active leurs interrupteurs et installe leurs gardes ; `ratedWatts` pour l'infobulle |
| `LWC_Switch.lua` | `shared` | `isOff`, `powered`, `switchable`, `request` (client → commande, solo → direct), `handle` (autorité : vérifie la demande, écrit la ModData) |
| `LWC_Gates.lua` | `shared` | Registre des types (pattern Strategy) ; `resolve`, `wrap` (une seule fois), `blocked`, `machineOn`, `notify`, `onThisSide` |
| `Gates/LWC_Gate<Type>.lua` | `shared` | Un type de garde : `validate` et `install` (voir `specifications-techniques.md`) |
| `Profiles/LWC_<Cible>.lua` | `shared` | Table déclarative du mod cible ; seules logiques : petites fonctions qui lisent l'état du mod cible |
| `LWC_SwitchMenu.lua` | `client` | Option « Allumer / Éteindre », marche jusqu'à la machine, `LWC_SwitchAction` |
| `LWC_SwitchServer.lua` | `server` | `Events.OnClientCommand` → `Switch.handle` |

Tout le registre est en `shared` : LiveWire exige que le serveur et chaque client inscrivent les mêmes consommateurs
avant `OnInitGlobalModData`. `Events.OnInitWorld` est le dernier moment permis et vient après le chargement de tous les
fichiers Lua, donc après les tables des mods cibles, quel que soit l'ordre des mods. Un profil dont le mod cible est
absent ne lit rien de ce mod.

## Flux

- **Facture** : LiveWire mesure sa zone toutes les 10 minutes de jeu et appelle `powerConsumption(o)` de la
  définition (`LWC_Profiles.definition`) : 0 W si l'interrupteur est sur arrêt, `idle` si `running(o)` n'est pas
  vrai, sinon `watts`.
- **Interrupteur** : écrit seulement par l'autorité (serveur, ou le jeu solo), dans la ModData de l'objet, transmise
  aux clients.
- **Coupure** : un point d'entrée enveloppé du mod cible demande `Switch.powered(machine)` ; faux = test de courant
  faux, action refusée ou arrêtée, appel non exécuté, option de menu grisée.
- **Aucune boucle propre** (ni `OnTick` ni `Every*`) : le mod n'agit que lorsqu'il est appelé. Deux gardes
  existantes sont appelées à chaque image par leur mod cible (juke-box, ordinateur) ; leur travail reste constant.

## Points d'extension

- Ajouter un mod cible = ajouter un fichier `Profiles/LWC_<Cible>.lua`.
- Ajouter un type de garde = ajouter un fichier `Gates/LWC_Gate<Type>.lua` qui s'inscrit dans `LWC_Gates`, et sa
  ligne `require` dans `LWC_Profiles.lua`.
Le format est dans [specifications-techniques.md](specifications-techniques.md).

## Outillage

- Tests hors jeu : `python -B -m unittest discover -s tests` (lupa). `tests/test_profiles.py` (chargeur, gardes
  `object`/`square`, doubles de l'API LiveWire et `require` qui charge les vrais fichiers), `tests/test_switch.py`
  (interrupteur, commande, menu ; sources ASCII et sans `next()`), `tests/test_gates.py` (types `action`, `call`,
  `menu`, `custom`, côtés), `tests/test_profile_files.py` et un fichier de tests par profil.
- `python tools/check_sprites.py [--workshop DIR] [--game DIR]` : chaque sprite d'un profil doit être défini par un
  `.tiles` du mod cible ou du jeu, ou nommé dans le Lua ou les scripts du mod cible (lecture seule). Codes : 0 tout
  trouvé, 1 sprite absent, 2 mod absent. Hors CI.
