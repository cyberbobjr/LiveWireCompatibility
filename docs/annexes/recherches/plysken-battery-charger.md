# Plysken Battery Charger (Workshop 3793465866, id PBC)

Analyse du 2026-11-13, **confirmée statiquement** (copie Workshop en lecture seule, `108600\3793465866\mods\Plysken Battery Charger\`). Rien n'a été testé en jeu.

## 1. Variante chargée en 42.22

- Dossiers : `42.1/` et `mod.info` racine (identiques, `versionMin=42.20`, métadonnée).
- Règle de choix : `ZomboidFileSystem.java:454-466` (voir le rapport PWS). **`42.1/` est chargé en 42.22.**

## 2. Objets : aucun objet posé

| Élément | Type | Constat |
|---|---|---|
| `PBC_CrankCharger` (chargeur à manivelle) | `ItemType = base:normal`, `Weight = 1.2`, `Icon = PBC_CrankCharger` (`42.1/media/scripts/PBC/PBC_Items.txt:34-39`) | **Objet d'inventaire.** Aucun `WorldObjectSprite` dans `scripts/PBC/`. Il n'est pas posable. |
| `PBC_RechargeableBattery` | `base:drainable` (`PBC_Items.txt:90-99`) | Inventaire. Pile rechargeable, aucune tuile. |
| Pile vanille (`Battery`) | `base:drainable` (`PBC_Battery.txt:54-63`) | Inventaire. |

Le chargeur est actionné à la manivelle : **aucune électricité**. Il ne produit ni ne consomme de courant du réseau.

## 3. Lecture du code

- `grep` sur `lua/` : aucune occurrence de `haveElectricity`, `hasGridPower`, `isPowered`, `generator`, `FuelAmount`, `getSprite`, `Mov_` ni `IsoObject` dans le code de recharge.
- Seule mention d'objets posés : `PBC_TrackRadio.lua:5-113` (batterie dans une radio posée, `p:getWorldObjects()`). Cette radio est un `IsoRadio`, déjà comptée par LiveWire selon la description fournie (famille non relue dans ce passage). Le mod ne lui ajoute aucun courant.
- Les `PBC_Server.lua` et `PBC_Core.lua` ne touchent qu'aux données de pile et de manivelle.

## 4. Puissance

Aucune. Pas de consommation électrique dans le mod.

## 5. Verdict

- **Non facturable.** Aucun objet posé, aucun courant. Le chargeur est un outil à manivelle, la pile un item.
- **Pas de profil** : l'API LiveWire ne facture que des objets posés, et ce mod n'en ajoute aucun. Il n'y a pas de courant à couper.

## Profil proposé

Non proposé : aucun objet posé et aucune consommation électrique à décrire. Un profil « charge de pile » demanderait une API LiveWire pour les actions brèves (idée I06 du rapport `vectrex-playable-console.md`), sans objet posé à viser.
