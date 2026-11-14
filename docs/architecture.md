# Architecture

## Vue d'ensemble

Un seul mod, `batman_LiveWireCompatibility` (ADR-001, D01). Il porte le chargeur et un profil par mod cible. Le
joueur l'active une fois : chaque profil s'applique tout seul quand son mod cible est actif. Aucun objet, recette ni
tuile. Les profils passent par l'API publique de LiveWire (`LiveWire.API`, révision 6 au moins) ; LiveWire n'est
pas modifié.

```
Profiles/LWC_<Cible>.lua --add--> LWC_Profiles (registre)
                                   | Events.OnInitWorld
                                   v
             mod cible actif ? --oui--> LiveWire.API.registerConsumer(id, définition)
                                   \--> enveloppe des tests de courant publics (gates)
                               --non--> rien
```

## Arborescence

```
Contents/mods/batman_LiveWireCompatibility/
├── common/                          vide (structure B42)
└── 42.21/
    ├── mod.info                     require=\batman_LiveWire
    └── media/lua/shared/LiveWireCompatibility/
        ├── LWC_Profiles.lua         registre, validation, chargeur, enveloppe des tests de courant
        └── Profiles/                un fichier par mod cible (LWC_Artel.lua, LWC_FunctionalAppliances2.lua…)
```

## Modules

| Module | Côté | Rôle |
|---|---|---|
| `LWC_Profiles.lua` | `shared` | `add` valide et range un profil ; `applyAll` (sur `Events.OnInitWorld`) applique chaque profil dont un mod est actif (`getActivatedMods():contains`) ; `wrapGate` enveloppe une fois un test de courant public du mod cible |
| `Profiles/LWC_<Cible>.lua` | `shared` | Table déclarative du mod cible, ajoutée par `LiveWireCompat.Profiles.add` ; aucune logique hors des fonctions `running`/`watts` qui lisent l'état du mod cible |

Tout est en `shared` : LiveWire exige que le serveur et chaque client inscrivent les mêmes consommateurs avant
`OnInitGlobalModData`. `Events.OnInitWorld` est le dernier moment permis et vient après le chargement de tous les
fichiers Lua, donc après les tables des mods cibles, quel que soit l'ordre des mods. Un profil dont le mod cible est
absent ne lit rien de ce mod : ses fonctions `running`/`watts` ne sont appelées que par LiveWire, pour des objets
inscrits.

## Flux

- **Facture** : LiveWire mesure sa zone toutes les 10 minutes de jeu et appelle `powerConsumption(o)` de la définition
  (`LWC_Profiles.definition`), qui rend `idle` si `running(o)` n'est pas vrai, sinon `watts`.
- **Coupure** : un test de courant enveloppé rend d'abord la réponse d'origine ; si elle est vraie et que l'objet (ou
  la machine trouvée sur la case) est un consommateur du profil, il ajoute `LiveWire.API.consumerPowered`.
- Aucune commande réseau, aucune ModData, aucune persistance propre.

## Points d'extension

Ajouter un mod cible = ajouter un fichier `Profiles/LWC_<Cible>.lua`. Le format est dans
[specifications-techniques.md](specifications-techniques.md).

## Outillage

- Tests hors jeu : `python -B -m unittest discover -s tests` (lupa). `tests/test_profiles.py` couvre le chargeur avec
  un double fidèle de l'API LiveWire.
- `tests/test_profile_files.py` charge chaque fichier `Profiles/` (un profil par fichier, sprites et ids uniques,
  enveloppes rattachées à un consommateur du profil) et vérifie le profil Artel contre un double de ses tables.
- `python tools/check_sprites.py [--workshop DIR] [--game DIR]` : chaque sprite d'un profil doit être défini par un
  `.tiles` du mod cible ou du jeu, ou nommé dans le Lua ou les scripts du mod cible (lecture seule). Codes : 0 tout
  trouvé, 1 sprite absent, 2 mod absent. Hors CI.
