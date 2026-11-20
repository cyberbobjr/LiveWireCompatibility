# ADR-004 — Signaler à LiveWire chaque allumage et extinction

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-004-SIGNALER-LES-CHANGEMENTS-A-LIVEWIRE` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Accepté (2026-11-20) |
| Avancement | voir le [plan 004](../ADR-plans/plan-004-signaler-les-changements-a-livewire.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWireCompatibility` : `LWC_Switch`, commande serveur, type de garde `notify`, profils ; Live Wire révision 10 de l'API (`consumerChanged`, décision D-68 de Live Wire) |
| Documents liés | [ADR-002](termines/002-interrupteur-et-coupure-des-machines.md) |
| Références | Live Wire `LW_API.lua` (`API.consumerChanged`), `LW_Simulation.lua:918` (mesure toutes les dix minutes de jeu) |
| Origine | demande de l'utilisateur du 2026-11-20 : une machine Artel éteinte reste « allumée » (verte) dans l'onduleur un moment ; « ajouter cette fonction à l'API, vérifie aussi que toutes les machines […] utilisent bien l'API lors de l'extinction/allumage » |

## Contexte

Live Wire ne mesure la consommation qu'une fois toutes les dix minutes de jeu ; un allumage ou une extinction ne se voit
qu'à la mesure suivante. La révision 10 de son API ajoute `consumerChanged(obj)` (autorité seulement), qui remesure tout de
suite les réseaux qui servent l'objet. Audit des profils (2026-11-20) : les allumages et extinctions passent par
- l'interrupteur de ce mod (toutes les machines `switch = true`), écrit par l'autorité ;
- les interrupteurs propres aux mods cibles, côté joueur : mode `Off` des comptoirs, vitrines et distributeurs FA2
  (`FAHeatedCounter.onUseHeatedCounter`, `FADisplayCounter.onUseDisplayCounter`, `FAVendingMachine.onUseVendingMachine`,
  `HeatedCountersMenu.lua:87-119` : mode écrit puis `transmitModData`), bouton marche de Computer Mod
  (`setComputerPowerOn`, `ComputerMod_UI_System.lua:3983-3996`, qui finit par `ComputerModComputerTypes.transmitData`),
  lecture et arrêt du juke-box (`TMJukebox.transmit`, appelé à chaque changement, `TMJukeboxWindow.lua:609, 619`) ;
- la mise en route d'un lot Artel (sécheuse, sublimatrice : facturées pendant un lot), vue côté serveur chaque minute par
  `PMK_StationApplyStage`.

## Décisions

- **D01 — `LWC_Switch.changed(o)`** : sur l'autorité, `LiveWire.API.consumerChanged(o)` (si l'API l'offre) ; sur un client,
  commande `LWC` / `changed` `{ x, y, z, sprite }`. Le serveur cherche sur la case un consommateur inscrit de ce sprite, à
  10 cases au plus du joueur, et appelle l'API. Sans révision 10, rien (mesure au pas de dix minutes, comme avant).
- **D02 — L'interrupteur du mod signale** chaque écriture (`Switch.handle`).
- **D03 — Type de garde `notify`** : enveloppe une fonction du mod cible ; après l'appel d'origine (arguments et retours
  préservés), signale la machine (sa pièce facturée) quand elle est l'un des consommateurs de la garde. Champ `state`
  facultatif : signale seulement quand l'état lu change (clé par case), pour les fonctions appelées à chaque petite
  modification. Aucune boucle propre.
- **D04 — Couverture** : FA2 (les trois fonctions de mode, client), Computer Mod (`ComputerModComputerTypes.transmitData`,
  état `ComputerModPowerOn`, client), True Moozic (`TMJukebox.transmit`, état `isPlaying`), Artel (`PMK_StationApplyStage`,
  état « lot en cours », serveur). Les autres machines n'ont que l'interrupteur du mod (D02). La hotte FA2 n'a ni
  interrupteur ni levier (ADR-002).

## Conséquences

- L'onduleur et « Afficher les consommateurs » suivent un allumage ou une extinction tout de suite, au lieu de dix minutes
  de jeu au plus.
- Une commande réseau de plus (`changed`), bornée à la portée du joueur ; son seul effet est une remesure.
