# Spécifications fonctionnelles

| Id | Fonctionnalité | Vu par le joueur |
|---|---|---|
| F01 | Facture des machines d'un mod pris en charge | La batterie se vide plus vite quand la machine tourne ; l'onduleur affiche la charge |
| F02 | Affichage dans le logiciel de gestion | La machine apparaît dans l'onglet Consommateurs, comme un appareil vanilla |
| F03 | Coupure par les circuits | Ouvrir le circuit « équipements » arrête la machine (ADR-002 : par le test de courant du mod cible, ses actions, ses fonctions d'usage ou son menu) |
| F04 | Détection automatique des mods pris en charge | Le joueur active LiveWire Compatibility une fois ; seules les machines des mods pris en charge et activés sont facturées |
| F05 | Interrupteur marche/arrêt (ADR-002) | Clic droit « Éteindre » / « Allumer » sur une machine sans bouton propre ; éteinte, elle ne consomme rien et ne fonctionne pas |
| F06 | Pas de courant, pas de machine (ADR-002) | Une machine éteinte, sans courant ou coupée refuse de servir : options grisées avec la raison, utilisation en cours arrêtée, message au-dessus du personnage |

## Comportement

- Solo et multijoueur : identique ; l'inscription a lieu sur le serveur et sur chaque client.
- Consommations estimées (ADR-001, D03), citées par profil dans [specifications-techniques.md](specifications-techniques.md).

## Limites connues

- Hotte de Functional Appliances 2 et son d'ambiance des bornes Project Arcade : aucun point d'entrée, ni interrupteur ni
  coupure.
- Machines qui ne travaillent que chez le joueur (FA2, Project Arcade, Computer Mod, True Moozic, table de chimie
  Artel) : coupure côté client seulement en multijoueur (ADR-002, D07).
- L'état de l'interrupteur est perdu quand la machine est ramassée : elle revient allumée.
- Un objet d'inventaire (jamais posé) ne peut pas être facturé : l'API LiveWire ne connaît que les objets posés
  (exemple : Vectrex Playable Console).
- Une machine sans état de marche lisible (Machinery, hot-dog de Functional Appliances 2) est facturée en moyenne
  tant qu'elle est allumée et a du courant.
- Si le mod cible change ses sprites ou déplace sa fonction de courant, le profil devient inerte sans erreur ; un
  message `[LiveWireCompat]` en anglais apparaît dans `console.txt`.

## Mods pris en charge

### Artel Manufactory (Workshop 3794133594)

| Machine (Artel) | Sprites | Consommation (estimée) | Sans courant ou éteinte |
|---|---|---|---|
| Puits, étape moteur | `Artel_104`, `Artel_107` | 100 W en moyenne (pompe 500 W, une heure sur cinq) | vitesse de pompe à main (`PMK.Well.isPowered`) |
| Sécheuse électrique | `Artel_36`, `Artel_37` | 2 000 W pendant un lot, 5 W sinon | lot en pause (`PMK.dryPause`) |
| Sublimatrice | `Artel_52`, `Artel_53` | 700 W pendant un lot, 5 W sinon | lot en pause (`PMK.dryPause`) |
| Établi chimique | `Artel_56`, `Artel_58` | 30 W en moyenne (chauffe pendant la fabrication) | refuse de fabriquer (client) |
| Station de commerce | `Artel_121` à `Artel_124` (deux moitiés) | 75 W par moitié, seulement sur le réseau ; rien sur sa batterie | sur sa batterie (`PMK.Trade.gridPowered`) |
| Base quantique | `Artel_112` à `143` (sprites allumés et sombres) | 100 W tant qu'elle est allumée | éteinte, cellules verrouillées (`PMK.QBase.squarePowered`) |

Déjà comptés par le jeu : réchaud électrique portable (`IsoStove`), projecteurs intelligents (`IsoLightSwitch`).
Non posés, donc non facturables : station de recharge, chauffage électrique, sac-réfrigérateur.
Analyse complète : [annexes/recherches/artel-manufactory.md](annexes/recherches/artel-manufactory.md).

### Deuxième liste (2026-11-13)

Machines, consommations et coupure par mod : [wiki/fr/01-fonctionnement.md](wiki/fr/01-fonctionnement.md) ;
sprites et tests de courant : [specifications-techniques.md](specifications-techniques.md) ; analyses :
[annexes/recherches/](annexes/recherches/).

| Mod cible | Profil | Interrupteur | Coupure |
|---|---|---|---|
| Functional Appliances 2 (3042138819) | `LWC_FunctionalAppliances2.lua` | hot-dog, pop-corn, fontaines, tireuses ; mode Off natif ailleurs | client ; hotte non gérée |
| Computer Mod (3725497089) | `LWC_ComputerMod.lua` | natif | client |
| Plysken Weather Station (3781590169) | `LWC_PlyskenWeatherStation.lua` | oui | partagée |
| True Moozic (3632610172), juke-box | `LWC_TrueMoozic.lua` | natif | client |
| Machinery (3780027195) | `LWC_Machinery.lua` | oui | partagée, le serveur fait foi |
| Project Arcade (3645980077) | `LWC_ProjectArcade.lua` | oui | client (menu avant paiement, actions, pousse-pièces) |

Sans profil : Plysken Battery Charger, Plysken Irrigation Pipes, Laptop Addon, Mumble Remover, More Machinery
Recipes, Video Game Consoles et ses addons, Palm Pilots, Spiffomon3D Prizes (rien à facturer) ; Badlands Power, Industrial Works (générateurs) ; Working Air Conditioner Units (déjà
facturé par LiveWire comme sèche-linge).
