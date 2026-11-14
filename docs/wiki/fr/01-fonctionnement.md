# Fonctionnement

Certains mods ajoutent des machines électriques que le jeu ne compte pas : elles vérifient seulement que leur case a
du courant. Avec LiveWire, elles tourneraient gratuitement. Ce mod les déclare à LiveWire.

- **Facture :** l'onduleur compte ce que la machine consomme quand elle tourne, comme un frigo ou une cuisinière.
- **Logiciel de gestion :** la machine apparaît dans l'onglet Consommateurs.
- **Circuits :** ouvrir le circuit « équipements » arrête la machine seulement si son mod laisse les autres mods voir
  son test de courant. Sinon, la machine est facturée mais continue de tourner.
- **Automatique :** activez LiveWire Compatibility une fois. Il repère les mods pris en charge que vous
  utilisez et ignore les autres ; rien d'autre à activer.

## Mods pris en charge

### Artel Manufactory

| Machine | Consommation (estimée) | Arrêtée par les circuits |
|---|---|---|
| Puits, étape moteur | 100 W en moyenne | oui |
| Sécheuse électrique | 300 W en moyenne | non |
| Sublimatrice | 150 W en moyenne | non |
| Établi chimique | 30 W en moyenne | non |
| Station de commerce | 150 W sur le réseau, rien sur sa batterie | oui (sa batterie continue) |
| Base quantique | 100 W tant qu'elle est allumée | oui |

Déjà comptés par le jeu : réchaud électrique portable, projecteurs intelligents. Jamais posés dans le monde, donc non facturés : station de recharge, chauffage électrique, sac-réfrigérateur.

### Functional Appliances 2

| Machine | Consommation (estimée) | Arrêtée par les circuits |
|---|---|---|
| Comptoir chauffant (chaque segment) | chaud 800 W, tiède 400 W, froid 150 W ; rien à l'arrêt | non |
| Comptoirs et vitrines (chaque case) | tiède 150 W, froid 200 W ; rien à l'arrêt | non |
| Distributeurs de friandises et de sodas | tiède 300 W, froid 200 W ; rien à l'arrêt | non |
| Grill à hot-dogs | 500 W dès qu'il a du courant | non |
| Machine à pop-corn | 200 W dès qu'elle a du courant | non |
| Fontaine à soda | 200 W dès qu'elle a du courant | non |
| Machine SlurpNBurp | 400 W dès qu'elle a du courant | non |
| Tireuses à bière | 150 W dès qu'elles ont du courant | non |
| Hotte aspirante | 150 W quand un générateur tourne dessous | non |

Functional Appliances 2 n'a pas de test de courant visible par les autres mods : ces machines sont facturées mais
ignorent les circuits. Non facturés : friteuses, cafetière, horloge, téléphones publics (Functional Appliances 2 ne
leur demande pas de courant).

### Computer Mod

| Machine | Consommation (estimée) | Arrêtée par les circuits |
|---|---|---|
| Ordinateur de bureau | 120 W allumé | oui, côté joueur (un serveur dédié garde son propre test) |

Le portable du Laptop Addon se porte dans l'inventaire : il n'est pas facturé.

### Plysken Weather Station

| Machine | Consommation (estimée) | Arrêtée par les circuits |
|---|---|---|
| Station météo | 15 W dès qu'elle a du courant | oui (elle cesse ses relevés) |

### True Moozic

| Machine | Consommation (estimée) | Arrêtée par les circuits |
|---|---|---|
| Juke-box | 150 W pendant la lecture | oui |

Déjà comptée par LiveWire : la chaîne HiFi. Sur piles, donc non facturés : radiocassettes, lecteur CD, baladeur.

### Machinery

| Machine | Consommation (estimée, moyenne sur une journée d'atelier) | Arrêtée par les circuits |
|---|---|---|
| Perceuse à colonne | 150 W | oui |
| Scie à ruban à métaux | 330 W | oui |
| Presse hydraulique | 300 W | oui |
| Tour à métaux | 200 W | oui |
| Touret à meuler | 125 W | oui |
| Scie de table industrielle | 500 W | oui |
| Scie de table de chantier | 500 W | oui |
| Bétonnière | 350 W | oui |

Non facturée : la scie de table Cabinet (essence). More Machinery Recipes n'ajoute que des recettes : rien à facturer.

### Project Arcade

| Machine | Consommation (estimée) | Arrêtée par les circuits |
|---|---|---|
| Borne d'arcade verticale | 120 W dès qu'elle a du courant | non |
| Borne d'arcade assise | 200 W dès qu'elle a du courant | non |
| Flipper | 200 W dès qu'il a du courant | non |
| Pince à peluches | 100 W dès qu'elle a du courant | non |
| Pousse-pièces | 150 W dès qu'il a du courant | non |
| Punching-ball | 60 W dès qu'il a du courant | non |

Les machines restent allumées tant qu'elles ont du courant. Project Arcade n'a pas de test de courant visible
par les autres mods : elles sont facturées mais ignorent les circuits. Ses néons muraux sont des lampes, déjà
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
