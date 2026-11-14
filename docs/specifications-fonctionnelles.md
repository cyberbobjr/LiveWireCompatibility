# Spécifications fonctionnelles

| Id | Fonctionnalité | Vu par le joueur |
|---|---|---|
| F01 | Facture des machines d'un mod pris en charge | La batterie se vide plus vite quand la machine tourne ; l'onduleur affiche la charge |
| F02 | Affichage dans le logiciel de gestion | La machine apparaît dans l'onglet Consommateurs, comme un appareil vanilla |
| F03 | Coupure par les circuits | Ouvrir le circuit « équipements » arrête la machine, **seulement** si le mod cible expose son test de courant |
| F04 | Détection automatique des mods pris en charge | Le joueur active LiveWire Compatibility une fois ; seules les machines des mods pris en charge et activés sont facturées |

## Comportement

- Solo et multijoueur : identique ; l'inscription a lieu sur le serveur et sur chaque client.
- Consommations estimées (ADR-001, D03), citées par profil dans [specifications-techniques.md](specifications-techniques.md).

## Limites connues

- Une machine dont le mod cible garde son test de courant `local` est facturée mais ignore les circuits.
- Un objet d'inventaire (jamais posé) ne peut pas être facturé : l'API LiveWire ne connaît que les objets posés
  (exemple : Vectrex Playable Console).
- Une machine sans état de marche lisible (Machinery, hot-dog de Functional Appliances 2) est facturée en moyenne
  dès qu'elle a du courant.
- Si le mod cible change ses sprites ou déplace sa fonction de courant, le profil devient inerte sans erreur ; un
  message `[LiveWireCompat]` en anglais apparaît dans `console.txt`.

## Mods pris en charge

### Artel Manufactory (Workshop 3794133594)

| Machine (Artel) | Sprites | Consommation (estimée) | Coupée par les circuits |
|---|---|---|---|
| Puits, étape moteur | `Artel_104`, `Artel_107` | 100 W en moyenne (pompe 500 W, une heure sur cinq) | oui (`PMK.Well.isPowered`) |
| Sécheuse électrique | `Artel_36`, `Artel_37` | 300 W en moyenne (2 kW par lots, marche illisible) | non (test `local`) |
| Sublimatrice | `Artel_52`, `Artel_53` | 150 W en moyenne (700 W par cycle, marche illisible) | non (test `local`) |
| Établi chimique | `Artel_56` | 30 W en moyenne (chauffe pendant la fabrication) | non (test `local`) |
| Station de commerce | `Artel_121` à `Artel_124` (deux moitiés) | 75 W par moitié, seulement sur le réseau ; rien sur sa batterie | oui (`PMK.Trade.gridPowered`), la batterie continue |
| Base quantique | sprites allumés `Artel_112`-`116`, `125`-`129`, `134`-`138`, `143` | 100 W tant qu'elle est allumée | oui (`PMK.QBase.squarePowered`) |

Déjà comptés par le jeu : réchaud électrique portable (`IsoStove`), projecteurs intelligents (`IsoLightSwitch`).
Non posés, donc non facturables : station de recharge, chauffage électrique, sac-réfrigérateur.
Analyse complète : [annexes/recherches/artel-manufactory.md](annexes/recherches/artel-manufactory.md).

### Deuxième liste (2026-11-13)

Machines, consommations et coupure par mod : [wiki/fr/01-fonctionnement.md](wiki/fr/01-fonctionnement.md) ;
sprites et tests de courant : [specifications-techniques.md](specifications-techniques.md) ; analyses :
[annexes/recherches/](annexes/recherches/).

| Mod cible | Profil | Coupé par les circuits |
|---|---|---|
| Functional Appliances 2 (3042138819) | `LWC_FunctionalAppliances2.lua` | non (aucun test public) |
| Computer Mod (3725497089) | `LWC_ComputerMod.lua` | côté client seulement |
| Plysken Weather Station (3781590169) | `LWC_PlyskenWeatherStation.lua` | oui |
| True Moozic (3632610172), juke-box | `LWC_TrueMoozic.lua` | oui |
| Machinery (3780027195) | `LWC_Machinery.lua` | oui |
| Project Arcade (3645980077) | `LWC_ProjectArcade.lua` | non (tests `local`) |

Sans profil : Plysken Battery Charger, Plysken Irrigation Pipes, Laptop Addon, Mumble Remover, More Machinery
Recipes, Video Game Consoles et ses addons, Palm Pilots, Spiffomon3D Prizes (rien à facturer) ; Badlands Power, Industrial Works (générateurs) ; Working Air Conditioner Units (déjà
facturé par LiveWire comme sèche-linge).
