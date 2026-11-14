# True Moozic (Workshop 3632610172) : machines électriques pour LiveWire

Analyse du 2026-11-13. Lecture seule de `108600\3632610172\mods\...`. Tous les constats sont **confirmés statiquement** (lecture du code et des scripts), rien n'a été testé en jeu. Les puissances sont des **estimations**.

## 0. Variante chargée et mods

- `TrueMoozic` : `108600\3632610172\mods\True Moozic B42+ - ...\42\mod.info` (`id=TrueMoozic`, `versionMin=42.13`). Seule variante B42 présente ; pas de dossier `42.x`. Le dossier `common\` contient les traductions et `tsarcraft_music.tiles.txt`. Le mod est chargé en 42.22 par son dossier `42`.
- `TMMumble` : `108600\3632610172\mods\TM Mumble Remover B42.13+ MP\42\mod.info` (`id=TMMumble`). Ajoute uniquement des sons (`sounds_TMRRemoveMumble.txt`) : **aucun objet, aucune électricité**. Verdict : rien à compter.

## 1. Inventaire des objets électriques ou alimentés

| Objet | Classe posée | Source de courant (code) | Déjà compté par LiveWire ? | Verdict |
|---|---|---|---|---|
| HiFi Stereo (`Tsarcraft.TM_HiFiStereo`) | `IsoRadio` (créé par `IsoRadio.new`, `worldContextBoombox.lua:79`) | secteur (`UsesBattery = FALSE`, `items_TM_HiFi.txt:28`) | **Oui** : famille `IsoRadio` (`LW_ApplianceFamilies.lua:66`), profil `radio` | **Déjà compté** |
| Boombox (`Tsarcraft.TCBoombox`, 9 couleurs) | `IsoRadio` (même création) | pile (`UsesBattery = TRUE`, `TCTrueItems.txt:63` et suivants) | Non : `LW_Appliances.lua:20` ignore les `IsoRadio` alimentés par pile | **Non facturable** (pile) |
| Lecteur CD portable (`items_TM_CDPlayer.txt`) | objet d'inventaire | pile (`UsesBattery = TRUE`, l.32 et suivants) | Sans objet (inventaire) | **Non facturable** |
| Walkman (`TM_Walkman`, `TCWalkman.fbx`) | objet d'inventaire | pile | Sans objet | **Non facturable** |
| Jukebox vanille convertie (`tm_jukebox`) | `IsoThumpable` après conversion (`TMJukeboxDefs.lua:56`), jukebox vanille non convertie : `IsoJukebox` présumé | secteur, test `TMJukebox.hasPower(square)` | Non : ni `IsoJukebox` ni `IsoThumpable` ne figurent dans `Fam.list` | **À profiler** (bloqué, voir section 3) |
| Enceinte bois / noire / petite enceinte (`Base.Mov_WoodSpeakerCabinet`, `Base.Mov_BlackSpeakerCabinet`, `Base.Speaker`) | objet posé ou inventaire | **aucune** : `TMSpeakerDefs.lua:12,18,20` enregistre seulement une correspondance sprite vers émetteur sonore, aucun test de courant | Non | **Non facturable** (passive) |
| Fil d'enceinte (`TM_WireBundle`) | inventaire | aucune | Sans objet | Non facturable |

Aucun autre objet électrique ajouté : pas de `registerConsumer`, pas de test `haveElectricity` hors jukebox.

## 2. HiFi Stereo : déjà compté

- Script : `items_TM_HiFi.txt:8-34`, `ItemType = Radio`, `UsesBattery = FALSE`, `UseWorldItem = TRUE`, `WorldStaticModel = TM_HiFiStereo_Ground` (`models_TM_HiFi.txt`, mesh `WorldItems/HiFiStereo`).
- Sprite posé : `tsarcraft_music_01_62` (`HiFiDefinitions.lua:25`, `TCMusic.WorldMusicPlayer["Tsarcraft.TM_HiFiStereo"]`). Le sprite de placement exact n'est pas dans le Lua au-delà de cette table.
- Synchronisation : `TCMusicWorldItemSync.lua:193` et `:405` (`instanceof(obj, "IsoRadio")`). La batterie n'existe pas pour ce modèle.
- Puissance : LiveWire applique déjà le profil `radio` (table `LW_Consumption.lua:20-27`). Aucun profil à ajouter. Remarque : le HiFi est un appareil d'éclairage et d'ampli plus fort qu'une radio ; si l'on veut un chiffre plus juste, c'est un réglage du profil `radio` de LiveWire, pas une compatibilité.
- Hypothèse non vérifiée : le mapping `UsesBattery` vers `getIsBatteryPowered()` côté Java n'a pas été relu.

## 3. Jukebox (vanille convertie) : à profiler, bloqué

**Électricité.** Le test est public et global : `TMJukebox.hasPower(square)` (`shared\TMJukeboxDefs.lua:398-407`). Il renvoie vrai si `square:haveElectricity()` (l.400) ou si la coupure programmée du sandbox n'est pas atteinte et que la case est intérieure (l.401-405). Les appels sont dans `client\RadioCom\TMJukeboxWindow.lua:598` et `:762`. Le test prend une **case** (kind `square`).

**État « en marche ».** `md.tmJukebox.isPlaying` (boolean, `TMJukeboxDefs.lua:132-135`, clé de modData `tmJukebox`). Lecture directe sans créer la donnée : `o:getModData().tmJukebox and o:getModData().tmJukebox.isPlaying == true`. Le jukebox ne joue que si `hasPower` est vrai (le fichier fait la vérification dans la fenêtre cliente).

**Identification des sprites.** Le code cherche les tuiles vanilles par la propriété de sprite `CustomName == "Jukebox"` (`TMJukeboxDefs.lua:46-54`), sans nommer les sprites. Les noms exacts ne sont donc pas dans le Lua. Le fichier `tsarcraft_music.tiles.txt` ne contient que des pianos (`CustomName = Piano`). Côté vanille, le moveable `Base.Mov_Jukebox` a `WorldObjectSprite = recreational_01_1` (`E:\pz-source-42.22\media\scripts\generated\items\moveable.txt`, environ l.1803-1810), mais la correspondance avec les tuiles de carte n'a pas pu être lue (`.tiles` binaires). **Confirmé : noms de sprites de carte non trouvés.**

**Puissance (sourcée).** Un jukebox à CD grand format annonce 50 W (Victrola Mayfield) à 60 W (Monstershop, modèle à CD grand format). Estimation retenue : **60 W en lecture**, 0 W sinon. Source : recherche web du 2026-11-13, pages produits (Victrola et Monstershop).

**Conclusion.** Pas de profil : les sprites de carte sont inconnus, et un `consumers` LiveWire exige une liste de sprites. Il faut d'abord relever les noms par un test en jeu (`pzdev lua` ou un scan de `getSprite():getName()` sur une case contenant un jukebox), ou par le fichier `.tiles` décodé.

## 4. Limites

- Les puissances des objets alimentés par pile ne sont pas comptées par LiveWire, ce qui est le comportement voulu.
- Le HiFi est compté au profil `radio` (40 W), sans estimation propre.
- Tout est statique : aucun test en jeu.

## Profil proposé

Aucun profil pour l'instant : sprites de carte inconnus (section 3). Le HiFi est déjà compté, et les autres objets ne tirent pas de courant ou sont alimentés par pile.
