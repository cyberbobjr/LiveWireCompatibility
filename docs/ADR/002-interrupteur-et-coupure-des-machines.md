# ADR-002 — Interrupteur marche/arrêt et coupure effective des machines

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-002-INTERRUPTEUR-ET-COUPURE-DES-MACHINES` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Accepté (2026-11-20) |
| Avancement | voir le [plan 002](../ADR-plans/plan-002-interrupteur-et-coupure-des-machines.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWireCompatibility` : chargeur, nouveaux modules (interrupteur, commande serveur, menu, types de garde), tous les profils ; Live Wire et les mods cibles ne changent pas |
| Documents liés | [ADR-001](001-compatibilite-mods-tiers.md) (D03 et D04 complétées), Live Wire ADR-002 (API consommateurs) |
| Références | Live Wire `LW_API.lua:466-512` (`registerConsumer`, `consumer`, `consumerPowered`, `inverterOfObject`, `invalidateDemand`, `ratedWatts`) ; vanilla `LuaTimedActionNew.java:110` (`isValid` relu à chaque mise à jour) ; rapports d'analyse du 2026-11-20 (ci-dessous) |
| Origine | demande de l'utilisateur du 2026-11-20, après un lyophilisateur Artel facturé 150 W à l'arrêt : « il faudrait un interrupteur marche/arrêt sur les machines […] fait en sorte que les machines […] vérifie si elles sont alimentées avant de pouvoir fonctionner […] Fait la même chose pour les autres appareils déclarés » |

## Contexte

Le lyophilisateur Artel est facturé 150 W en permanence (`LWC_Artel.lua:36-37`, moyenne D03 de l'ADR-001) : ni Artel
ni ce mod ne savent s'il tourne. Plus largement, beaucoup de machines des profils n'ont aucun interrupteur, et
plusieurs ignorent les coupures de Live Wire parce que leur test de courant est `local` (ADR-001, D04).

Analyse statique du 2026-11-20 (lecture seule du Workshop) :

- **Variantes chargées en 42.22** : Artel `42/`, FA2 `42.20/`, Machinery `42/`, PWS `42.1/`, Computer Mod `42/`,
  Project Arcade `common/`, True Moozic `42/`.
- **Le jeu relit `isValid` d'une action à chaque mise à jour** (`LuaTimedActionNew.java:110`, recherche dynamique
  dans la table) : envelopper la méthode d'une classe d'action refuse une action **et arrête** une action en cours.
- **Artel, sécheuse et sublimatrice** : le cycle se met en pause côté serveur, chaque minute de jeu, par
  `Pause.thaw(crd)` / `Pause.freeze(crd)` où `Pause = PMK.dryPause` est relu à chaque appel
  (`PMK_58z_SublimatorServer.lua:417-445`, `Events.EveryOneMinute` :481). Le test de courant est `local` (:82), mais
  la pause passe par une table globale : c'est le levier.
- **Leviers publics existants** (déjà enveloppés) : `Machinery.Service.isPowered` (partagé, appelé par
  `getOperationStatus` sur tous les chemins, serveur compris), `PWS.Power.isPowered` (partagé, lecture et journal
  serveur), `PMK.Well.isPowered`, `PMK.Trade.gridPowered`, `PMK.QBase.*`, `ComputerModPower.hasComputerPower`
  (client), `TMJukebox.hasPower` (client ; la boucle du juke-box arrête la lecture quand il répond faux).
- **FA2** : tous ses tests sont dans des fonctions globales. Comptoirs, vitrines et distributeurs ont déjà un mode
  `Off` natif (`ModData.CustomTemp`) ; hot-dog, pop-corn, fontaine, SlurpNBurp et tireuses passent par des fonctions
  `onUse…` globales puis des actions `Use…` dont `isValid` rend toujours vrai. La hotte n'a aucun levier.
- **Project Arcade** : tests `local`, aucun côté serveur ; points d'entrée globaux = actions de jeu
  (`ProjectArcade_PlayArcadeTimedAction`, `ProjectArcade_ClawTimedAction`, `ProjectArcade_PunchingTimedAction`) et
  `ProjectArcade_CoinPusher.OpenUI`. Le paiement a lieu avant l'action : bloquer seulement l'action ferait perdre la
  pièce, il faut bloquer avant (menu).
- **Interrupteurs natifs** : Computer Mod (bouton marche, `ComputerModPowerOn`), True Moozic (lecture/arrêt,
  `tmJukebox.isPlaying`), FA2 comptoirs/vitrines/distributeurs (mode `Off`).

## Décisions

- **D01 — Un interrupteur du mod pour chaque machine qui n'en a pas.** État dans la ModData de l'objet posé
  (`LWC_off = true` quand éteint) ; clé absente = allumé, donc les mondes existants ne changent pas. Les machines qui
  ont déjà un interrupteur natif (Computer Mod, juke-box True Moozic, comptoirs/vitrines/distributeurs FA2) n'en
  reçoivent pas un second : leur état natif fait foi. Le profil le déclare par consommateur (`switch = true`). Le
  ramassage d'une machine perd l'état (repose allumée), comme le reste de la ModData hors `movableData`.
- **D02 — Une seule définition de « machine alimentée ».** `powered(o) = LiveWire.API.consumerPowered(o) and not
  off(o)`. Toutes les gardes l'utilisent ; plus aucune garde n'appelle `consumerPowered` directement.
- **D03 — Facture.** Éteinte : 0 W, toujours. Allumée : la règle actuelle (`running` si lisible, sinon la moyenne
  d'ADR-001 D03). Pour la sécheuse et la sublimatrice Artel, une étape d'exploration lit côté serveur si un lot est
  en cours (`PMK.dryPause`) : si oui, facture la puissance de travail pendant le cycle et une veille hors cycle ; si
  l'état n'est pas lisible proprement, la moyenne reste.
- **D04 — Geste du joueur.** Menu contextuel de la machine : « Allumer » ou « Éteindre », avec la puissance dans
  l'infobulle (`ratedWatts`). Possible même sans courant. Le client marche jusqu'à la machine puis envoie une commande
  au serveur (`LWC` / `setSwitch`) ; le serveur vérifie que l'objet est un consommateur d'un profil actif avec
  `switch = true` et que le joueur est à portée, écrit la ModData, la transmet, puis invalide la mesure de l'onduleur
  (`inverterOfObject` → `invalidateDemand`). En solo, même chemin sans réseau.
- **D04 bis — Une machine éteinte ou coupée le dit.** Une utilisation refusée affiche au joueur « Machine éteinte » ou
  « Pas de courant » (traductions) ; les options de menu concernées restent visibles mais grisées.
- **D05 — Coupure effective par des gardes déclaratives, un type de garde par fichier.** Les gardes d'ADR-001 D04
  deviennent un registre de types (pattern Strategy, ouvert à l'extension) sous `LiveWireCompatibility/Gates/` :
  - `object`, `square` (existants) : test de courant du mod cible, réponse d'origine **et** `powered`.
  - `action` : méthodes `isValid` (et `isValidStart` si présente) d'une classe d'action ; la machine est lue dans un
    champ nommé par le profil. Faux si la machine n'est pas alimentée : refus, ou arrêt en cours d'action.
  - `call` : fonction globale qui reçoit la machine (position d'argument) ; si la machine n'est pas alimentée,
    l'original n'est pas appelé et la valeur de refus du profil est rendue, avec le message de D04 bis.
  - `menu` (client) : après le menu du mod cible, grise les options dont la cible est une machine non alimentée.
  - `custom` : fonction fournie par le profil quand aucun type ne convient (pause des lots Artel).
  Chaque garde s'installe une seule fois, préserve arguments et retours, et s'installe au plus tard possible
  (`OnInitWorld`, plus `OnGameStart` pour les menus clients).
  **Aucune boucle propre** : ni `OnTick`, ni `EveryOneMinute`, ni minuterie. Le mod réagit seulement aux appels des
  mods cibles, aux mesures de Live Wire, au menu et à sa commande. Deux gardes existantes sont appelées à chaque image
  par la boucle de leur mod cible (`TMJukebox.hasPower`, `ComputerModPower.hasComputerPower`) : leur travail reste
  constant et sans allocation (lecture d'une clé de ModData puis `consumerPowered`, seulement quand la réponse
  d'origine est vraie).
- **D06 — Couverture par machine.**

  | Mod | Machine | Interrupteur | Coupure (garde) | Côté |
  |---|---|---|---|---|
  | Artel | Moteur du puits | oui | `object` `PMK.Well.isPowered` : éteint = vitesse pompe à main | partagé |
  | Artel | Sécheuse, sublimatrice | oui | `custom` sur `PMK.dryPause.thaw` : le lot reste en pause | serveur |
  | Artel | Table de chimie | oui | `call` `PMK_CraftBenchPanel.isUsable` | client |
  | Artel | Poste de commerce | oui | `object` `PMK.Trade.gridPowered` : bascule sur sa batterie | partagé |
  | Artel | Quantum Base | oui | `object` `PMK.QBase.hasPower` : cellules verrouillées, sprite sombre | partagé |
  | FA2 | Comptoir chauffant, vitrines, distributeurs | natif (mode `Off`) | `call` `FA.updateMachineTemp` force `Off` ; `call` `onUse…` refuse un mode autre que `Off` | client |
  | FA2 | Hot-dog, pop-corn, fontaine, SlurpNBurp, tireuses | oui | `call` `onUse…` + `action` `Use…:isValid` | client |
  | FA2 | Hotte | non (exclue) | aucun levier ; facturée seulement avec un générateur allumé sur sa case | — |
  | Machinery | 8 machines | oui | `object` `Machinery.Service.isPowered` | partagé, serveur fait foi |
  | PWS | Station météo | oui | `object` `PWS.Power.isPowered` : pas de mesure, trou dans le journal | partagé |
  | Computer Mod | Ordinateur de bureau | natif | `object` `ComputerModPower.hasComputerPower` : extinction de l'écran | client |
  | Project Arcade | Bornes, flippers, pince, pousse-pièces, punching-ball | oui | `menu` (avant paiement) + `action` sur les actions de jeu + `call` `ProjectArcade_CoinPusher.OpenUI` | client |
  | True Moozic | Juke-box | natif (lecture) | `square` `TMJukebox.hasPower` : la boucle arrête la lecture | client |

- **D07 — Multijoueur.** La coupure s'applique là où le mod cible fait le travail. FA2, Project Arcade, Computer Mod,
  True Moozic et la table de chimie ne travaillent que côté client : la coupure y est côté client, contournable par
  un client modifié. Accepté : serveur entre amis, l'anti-triche n'est pas prioritaire. L'interrupteur, lui, est
  toujours écrit par le serveur.
- **D08 — Tests.** lupa hors jeu : état de l'interrupteur, `powered`, facture, validation de la commande serveur,
  chaque type de garde avec des doubles fidèles (classe d'action avec métatable, fonction globale, menu), profils
  (forme, ids, champs). Puis un passage en jeu nominal court en solo, puis en multijoueur (PZDevKit).

## Conséquences

- Le joueur éteint une machine qu'il n'utilise pas et ne paie plus rien pour elle ; une machine éteinte ou coupée par
  un disjoncteur ne fonctionne plus, sauf la hotte FA2 et le son d'ambiance des bornes Project Arcade (aucun levier).
- ADR-001 D04 (« une vérification `local` ne s'atteint pas : facturée mais ignore les circuits ») est dépassée pour
  Artel (sécheuse, sublimatrice, table de chimie), FA2 et Project Arcade : la coupure passe par d'autres points
  d'entrée publics.
- Le mod gagne une commande réseau, une clé de ModData et des textes joueur (traductions EN et FR ; repli anglais
  pour les autres langues) ; `docs/architecture.md` (« aucune commande réseau, aucune ModData ») est à mettre à jour.
- Une mise à jour d'un mod cible qui renomme une classe ou une fonction rend la garde inerte, sans erreur ; le journal
  le signale une fois (comme aujourd'hui pour `gate_not_found`).

## Hors portée

- Modifier Live Wire ou un mod cible, remplacer un de leurs fichiers.
- Une validation serveur des usages purement clients (D07).
- Couper la hotte FA2 et le son d'ambiance de Project Arcade.
