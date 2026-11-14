# Computer Mod (Workshop 3725497089) et addon Laptop (Workshop 3798992436) : machines électriques pour LiveWire

Analyse du 2026-11-13. Lecture seule de `108600\3725497089\mods\ComputerMod\` et `108600\3798992436\mods\ComputerModLaptop\`. Tous les constats sont **confirmés statiquement**, rien n'a été testé en jeu. La puissance est une **estimation sourcée**.

## 0. Variante chargée et mods

- `ComputerModkum` : `108600\3725497089\mods\ComputerMod\42\mod.info` (`id=ComputerModkum`, `versionMin=42.20`). Seule variante B42 (`42`). Pas de dossier `42.x`, pas de `common`. Chargé en 42.22.
- `ComputerModLaptop` : `108600\3798992436\mods\ComputerModLaptop\42\mod.info` (`id=ComputerModLaptop`, `versionMin=42.20`, `require=ComputerModkum`). Même variante `42`.

## 1. Inventaire

| Objet | Type | Sprites ou item | Source de courant (code) | Déjà compté par LiveWire ? | Verdict |
|---|---|---|---|---|---|
| Ordinateur de bureau (type `desktop`) | objet posé | sprites `appliances_com_01_72` à `appliances_com_01_79` (`ComputerMod_ComputerTypes.lua:236-239`) | secteur ou générateur proche (`ComputerModPower.hasComputerPower`, `client\ComputerMod_Power.lua:144-156`) | Non : classe non dans `Fam.list`, un objet générique ne déclenche aucune famille | **À profiler** |
| Ordinateur portable (type `Laptop`, addon) | **objet d'inventaire** (`Laptop4861993`, `computer_laptop_items.txt:3-9`, `ItemType = base:normal`) | item uniquement, aucun sprite posé | pile (`LaptopBatteryNiMH1993`) et prise si `ComputerModLaptopPlugged` (`ComputerModLaptop_Core.lua:93-99`) | Sans objet (inventaire) | **Non facturable** |

Aucun autre objet électrique ajouté. `ComputerMod_RelayRepair.lua` est une procédure de réparation et non une machine.

## 2. Ordinateur de bureau (ComputerModkum)

- **Sprites posés (confirmé statiquement)** : `appliances_com_01_72`, `appliances_com_01_73`, `appliances_com_01_74`, `appliances_com_01_75`, `appliances_com_01_76`, `appliances_com_01_77`, `appliances_com_01_78`, `appliances_com_01_79`. Enregistrés dans `registry.registerType` (`shared\ComputerMod_ComputerTypes.lua:228-240`, type `desktop`, `dataOnItem = false`, donc les données sont dans le modData de l'objet posé).
- **Classe posée** : non vérifiée. Les sprites sont des tuiles vanilles de la famille `appliances_com_01_*` ; la classe Java n'a pas été relue. Hypothèse : objet générique, non compté par LiveWire (aucune famille ne le reconnaît).
- **État « en marche »** : clé de modData `ComputerModPowerOn` (boolean) sur l'objet posé. Lecture : `registry.getRawData` (`ComputerMod_ComputerTypes.lua:56-64`) renvoie `object:getModData()` pour ce type. Écrite par `client\ComputerMod_UI_System.lua:3986,4005,4203`, `shared\ComputerMod_Components.lua:389,406`, `server\ComputerMod_ComputerData_Server.lua:368`. Lecture seule côté addon : `data.ComputerModPowerOn == true` (`ComputerMod_Components_Server.lua:138`).
- **Fonction de test de courant** :
  - `ComputerModPower.hasComputerPower(computer)` : **globale publique**, argument **objet** (`client\ComputerMod_Power.lua:144-156`). Elle renvoie `hasGridPower(computer)` (l.115-142), c'est-à-dire `square:haveElectricity()` ou `square:hasGridPower()` avec pièce, ou un générateur actif à portée (l.137-141).
  - Limite 1 : le fichier est dans `media\lua\client\`. Il n'existe pas sur un serveur dédié. Le serveur utilise sa propre fonction locale `hasSquarePower(square)` (`server\ComputerMod_Network_Server.lua:93-104`) : **non atteignable** par un wrapper global. Un gate ne couperait donc que les contrôles côté client (fenêtre, menu).
  - Limite 2 : le cache de 1,5 s (`ComputerMod_Power.lua:5`) peut retarder la coupure.
- **Puissance (estimation sourcée)** : une étude de 1994 mesure un PC 486 DX-66 à 144 W en moyenne, dont 85 W pour le processeur et 60 W pour le moniteur (source : [ACEEE 1994, SS94 Panel9 Paper23](https://www.aceee.org/files/proceedings/1994/data/papers/SS94_Panel9_Paper23.pdf)). Des estimations récentes pour un 486 avec écran CRT de 15 à 17 pouces donnent 100 à 145 W en fonctionnement (source : [Tom's Hardware, consommation des écrans CRT](https://www.tomshardware.com/reviews/lcd-backlight-led-cfl,2683.html) et [dssw.co.uk, revue de consommation](https://www.dssw.co.uk/research/computer_energy_consumption.html)). **Estimation retenue : 120 W allumé, 0 W éteint.** L'écran est inclus dans ce chiffre.
- **Gates possibles** : `ComputerModPower.hasComputerPower`, kind `object`, à condition que le wrapper soit posé côté client.
- **Pour un wrapper serveur** : il faudrait `hasSquarePower` (`ComputerMod_Network_Server.lua:93`), qui est locale. Non atteignable tel quel.

## 3. Ordinateur portable (addon ComputerModLaptop)

- Objet d'**inventaire** : `Laptop4861993` (`computer_laptop_items.txt:3-9`, `ItemType = base:normal`, `WorldStaticModel = ComputerModLaptop4861993`). Aucun `Mov_` ni `WorldObjectSprite`, donc aucun sprite posé. Il n'est jamais un objet posé par LiveWire.
- Type enregistré : `Laptop.typeId`, `dataOnItem = true`, `itemTypes = {Laptop.itemType}` (`shared\ComputerModLaptop_Core.lua:101-121`). Il n'a pas de `spriteNames`.
- Courant : pile `LaptopBatteryNiMH1993` (`computer_laptop_items.txt:13-20`). Charge secteur si `ComputerModLaptopPlugged == true` et `gridPower == true` (`Core.lua:93-99`, `server\ComputerModLaptop_Server.lua:14-42`).
- **Limite signalée** : un portable lâché au sol est un objet monde (`IsoWorldInventoryObject`), branché sur une prise. Sa charge réseau n'est pas facturée par LiveWire, car LiveWire ne compte que les objets posés (règle de l'API). Non traité ici.
- Verdict : **non facturable**.

## 4. Profil proposé

Le bureau est un objet posé non compté, il consomme un courant gratuit : un profil est justifié. Le code Lua suivant est une proposition, à ne pas publier avant validation de la limite serveur (section 2) et d'un test en jeu.

```lua
-- LiveWire Compatibility: Computer Mod desktop (Workshop 3725497089, mod id ComputerModkum).
-- Analysis: docs/annexes/recherches/computer-mod.md. Desktop sprites appliances_com_01_72..79 are
-- generic world objects: LiveWire does not bill them. Power test ComputerModPower.hasComputerPower
-- is a client-side global (client/ComputerMod_Power.lua): the server uses a local function, so the
-- gate only cuts the client-side checks. 120 W while on (PC and CRT, estimate sourced to a 1994
-- study and reviews), 0 W off. The laptop addon is inventory: not billable, no profile.
require "LiveWireCompatibility/LWC_Profiles"

LiveWireCompat.Profiles.add({
    name = "ComputerMod",
    workshop = "3725497089",
    mods = { "ComputerModkum" },
    consumers = {
        { id = "ComputerModDesktop",
          sprites = { "appliances_com_01_72", "appliances_com_01_73", "appliances_com_01_74",
                      "appliances_com_01_75", "appliances_com_01_76", "appliances_com_01_77",
                      "appliances_com_01_78", "appliances_com_01_79" },
          watts = 120,
          running = function(o)
              local md = o.getModData and o:getModData() or nil
              return md ~= nil and md.ComputerModPowerOn == true
          end },
    },
    gates = {
        { path = "ComputerModPower.hasComputerPower", kind = "object", consumer = "ComputerModDesktop" },
    },
})
```

## 5. Limites

- Confirmé statiquement uniquement. Pas de test en jeu.
- Classe Java des sprites `appliances_com_01_72..79` non relue : le verdict « non compté » repose sur l'absence de famille correspondante.
- Le gate client ne protège pas le serveur. Une coupure réelle sur un dédié n'arrêterait pas les commandes réseau du bureau, qui passent par `hasSquarePower` locale.
- Le portable branché au secteur hors inventaire n'est pas couvert.
