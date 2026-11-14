# Plysken Irrigation Pipes (Workshop 3739173520, id PIP)

Analyse du 2026-11-13, **confirmée statiquement** (copie Workshop en lecture seule, `108600\3739173520\mods\Plysken Irrigation Pipes\`). Rien n'a été testé en jeu.

## 1. Variante chargée en 42.22

- Dossiers : `42.1/`, `common/` (tiledef, viewpoint) et `mod.info` racine (`versionMin=42.0`, métadonnée).
- Règle de choix : `ZomboidFileSystem.java:454-466`. **`42.1/` est chargé en 42.22.**

## 2. Réponse à la question « pompe électrique ? »

**Non.** Le mod ne contient aucune pompe électrique. Le réseau d'irrigation est un système d'eau (`PIPWaterSystem.lua`, `PIPNetwork.lua`, `PIPBarrelRegistry.lua`) : tuyaux craftés, réservoirs (fûts) reliés, arrosage automatique des cultures.

## 3. Recherche de courant

- `grep -i` sur `42.1/media/lua` et `scripts` pour `haveElectricity`, `hasGridPower`, `isPowered`, `electric`, `generator`, `pump`, `powered`, `FuelAmount`, `power` : **une seule occurrence**, `lua/client/PIP/PIPContextMenu.lua:100`. C'est un commentaire qui cite `ISWorldObjectContextMenu.doAddFuelGenerator` comme modèle d'interface pour « tout verser » dans un fût (eau, pas carburant).
- Objets posés : les tuyaux (`BuildingObjects/PIPPipe.lua`, `scripts/PIP/items.txt:11`, `base:normal`) et les fûts (fûts de pluie vanille). Aucun ne porte de logique électrique.
- Le `WorldObjectSprite` du tuyau et le `PIP_WaterPipe` sont des objets d'eau. Aucun `IsoGenerator` ni `IsoLightSwitch`.

## 4. Verdict

- **Non concerné par LiveWire.** Aucun appareil électrique ajouté ou rendu fonctionnel. Les tuyaux et fûts sont des objets d'eau ; ils ne tirent aucun courant.
- **Pas de profil.** Rien à facturer ni à couper.

## Profil proposé

Non proposé : le mod ne consomme pas d'électricité.
