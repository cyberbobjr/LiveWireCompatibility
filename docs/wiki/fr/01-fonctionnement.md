# Fonctionnement

Certains mods ajoutent des machines électriques que le jeu ne compte pas : elles vérifient seulement que leur case a
du courant. Avec LiveWire, elles tourneraient gratuitement. Ce mod les déclare à LiveWire.

- **Facture :** l'onduleur compte ce que la machine consomme quand elle tourne, comme un frigo ou une cuisinière.
- **Interrupteur :** clic droit sur la machine, **Éteindre** ou **Allumer**. Éteinte, elle ne consomme plus rien et
  ne fonctionne plus. L'infobulle indique sa consommation en marche. Les machines qui ont déjà leur propre bouton
  (ordinateur, juke-box, comptoirs et distributeurs) le gardent. Une machine ramassée puis reposée revient allumée.
- **Sans courant, pas de machine :** une machine éteinte, sans courant ou coupée par un disjoncteur refuse de
  servir. Ses options de menu restent visibles mais grisées, avec la raison (« La machine est éteinte » ou « Pas de
  courant »), et une utilisation en cours s'arrête.
- **Logiciel de gestion :** la machine apparaît dans l'onglet Consommateurs.
- **Automatique :** activez LiveWire Compatibility une fois. Il repère les mods pris en charge que vous
  utilisez et ignore les autres ; rien d'autre à activer.

En multijoueur, l'interrupteur est enregistré par le serveur. Pour certains mods (Functional Appliances 2, Project
Arcade, Computer Mod, True Moozic, table de chimie d'Artel), la machine ne travaille que chez le joueur : c'est là
qu'elle est arrêtée.

## Mods pris en charge

### Artel Manufactory

| Machine | Consommation (estimée) | Interrupteur | Sans courant ou éteinte |
|---|---|---|---|
| Puits, étape moteur | 100 W en moyenne | oui | la pompe tourne à la vitesse d'une pompe à main |
| Sécheuse électrique | 2 000 W pendant un lot, 5 W sinon | oui | le lot se met en pause, puis reprend |
| Sublimatrice | 700 W pendant un lot, 5 W sinon | oui | le lot se met en pause, puis reprend |
| Établi chimique | 30 W en moyenne | oui | refuse de fabriquer |
| Station de commerce | 150 W sur le réseau, rien sur sa batterie | oui | passe sur sa batterie |
| Base quantique | 100 W tant qu'elle est allumée | oui | s'éteint, ses cellules se verrouillent |

Déjà comptés par le jeu : réchaud électrique portable, projecteurs intelligents. Jamais posés dans le monde, donc non facturés : station de recharge, chauffage électrique, sac-réfrigérateur.

### Functional Appliances 2

| Machine | Consommation (estimée) | Interrupteur | Sans courant ou éteinte |
|---|---|---|---|
| Comptoir chauffant (chaque segment) | chaud 800 W, tiède 400 W, froid 150 W ; rien à l'arrêt | le sien (réglage « Off ») | repasse sur Off, les autres réglages sont refusés |
| Comptoirs et vitrines (chaque case) | tiède 150 W, froid 200 W ; rien à l'arrêt | le sien (réglage « Off ») | idem |
| Distributeurs de friandises et de sodas | tiède 300 W, froid 200 W ; rien à l'arrêt | le sien (réglage « Off ») | idem |
| Grill à hot-dogs | 500 W | oui | refuse de servir |
| Machine à pop-corn | 200 W | oui | refuse de servir |
| Fontaine à soda | 200 W | oui | refuse de servir |
| Machine SlurpNBurp | 400 W | oui | refuse de servir |
| Tireuses à bière | 150 W | oui | refusent de servir |
| Hotte aspirante | 150 W quand un générateur tourne dessous | non | non gérée |

Non facturés : friteuses, cafetière, horloge, téléphones publics (Functional Appliances 2 ne leur demande pas de
courant).

### Computer Mod

| Machine | Consommation (estimée) | Interrupteur | Sans courant |
|---|---|---|---|
| Ordinateur de bureau | 120 W allumé | le sien (bouton marche) | l'écran s'éteint |

Le portable du Laptop Addon se porte dans l'inventaire : il n'est pas facturé.

### Plysken Weather Station

| Machine | Consommation (estimée) | Interrupteur | Sans courant ou éteinte |
|---|---|---|---|
| Station météo | 15 W | oui | cesse ses relevés (trou dans le journal) |

### True Moozic

| Machine | Consommation (estimée) | Interrupteur | Sans courant |
|---|---|---|---|
| Juke-box | 150 W pendant la lecture | le sien (lecture / arrêt) | la musique s'arrête |

Déjà comptée par LiveWire : la chaîne HiFi. Sur piles, donc non facturés : radiocassettes, lecteur CD, baladeur.

### Machinery

| Machine | Consommation (estimée, moyenne sur une journée d'atelier) | Interrupteur | Sans courant ou éteinte |
|---|---|---|---|
| Perceuse à colonne | 150 W | oui | refuse de travailler |
| Scie à ruban à métaux | 330 W | oui | refuse de travailler |
| Presse hydraulique | 300 W | oui | refuse de travailler |
| Tour à métaux | 200 W | oui | refuse de travailler |
| Touret à meuler | 125 W | oui | refuse de travailler |
| Scie de table industrielle | 500 W | oui | refuse de travailler |
| Scie de table de chantier | 500 W | oui | refuse de travailler |
| Bétonnière | 350 W | oui | refuse de travailler |

Non facturée : la scie de table Cabinet (essence). More Machinery Recipes n'ajoute que des recettes : rien à facturer.

### Project Arcade

| Machine | Consommation (estimée) | Interrupteur | Sans courant ou éteinte |
|---|---|---|---|
| Borne d'arcade verticale | 120 W | oui | option de jeu grisée avant de payer ; une partie en cours s'arrête |
| Borne d'arcade assise | 200 W | oui | idem |
| Flipper | 200 W | oui | idem |
| Pince à peluches | 100 W | oui | idem |
| Pousse-pièces | 150 W | oui | le panneau ne s'ouvre pas, ou se ferme avant de payer |
| Punching-ball | 60 W | oui | options grisées, scores compris |

Le son d'ambiance des bornes continue tant que leur case a du courant. Ses néons muraux sont des lampes, déjà
facturées par LiveWire.

## Déjà gérés par LiveWire

- **[B42] Working Air Conditioner Units :** une unité branchée devient un sèche-linge pour le jeu ; LiveWire la
  facture déjà et les circuits l'arrêtent déjà.
- **Badlands Power, Industrial Works :** leurs machines sont des générateurs, des sources que LiveWire connaît déjà.

## Non pris en charge

- **Vectrex Playable Console :** la console n'est jamais posée dans le monde ; LiveWire ne peut pas la facturer.
- **Plysken Battery Charger :** un chargeur à manivelle porté dans l'inventaire ; il ne consomme pas de courant.
- **Plysken Irrigation Pipes :** tuyaux et fûts, rien d'électrique.
- **Computer Mod: Laptop Addon :** le portable se porte dans l'inventaire.
- **True Moozic - Mumble Remover :** n'ajoute aucune machine.
- **Video Game Consoles** et ses addons de jeux : les consoles se posent au sol à côté d'une télévision, jamais
  comme un meuble, et les portables sont sur piles. La télévision, elle, est facturée par LiveWire.
- **Palm Pilots :** porté dans l'inventaire.
- **Spiffomon3D Prizes for Project Arcade :** ajoute seulement des lots.
