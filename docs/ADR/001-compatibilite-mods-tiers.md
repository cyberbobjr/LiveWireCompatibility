# ADR-001 — Mod de compatibilité avec les appareils des autres mods

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-001-COMPATIBILITE-MODS-TIERS` |
| Date de création et de mise à jour | 2026-11-13 (D01 révisée trois fois le même jour : mod autonome, un sous-mod par mod cible, puis mod unique à détection automatique) |
| Statut | Accepté (2026-11-13) |
| Avancement | voir le [plan 001](../ADR-plans/plan-001-compatibilite-mods-tiers.md) |
| Décideur | l'utilisateur |
| Portée | nouveau mod autonome `batman_LiveWireCompatibility` (projet, dépôt et objet Workshop propres) ; Live Wire n'est pas modifié |
| Documents liés | Live Wire : ADR-002 (API consommateurs, révision 6), wiki développeurs (`EN-15-developers`) |
| Références | Live Wire `shared/LiveWire/LW_API.lua` (`registerConsumer`, `consumerPowered`), `LW_Consumers.lua` |
| Origine | demande de l'utilisateur du 2026-11-13 : « écrit un petit mod de compatibilité, mais un mod "général", car je vais te donner une liste de mods à checker et à rendre compatible avec LiveWire » |

## Contexte

L'API de Live Wire (son ADR-002, révision 6) permet à un auteur d'inscrire ses appareils. Beaucoup d'auteurs ne le feront pas, ou pas tout de
suite. Premier cas analysé (confirmé statiquement) : Artel Manufactory (Workshop 3794133594). Ses lampes et son
réchaud électrique sont des objets vanilla, donc déjà facturés. Ses machines propres (séchoir électrique,
sublimateur, chargeur, capteurs, établi, puits, Quantum Base, comptoir) testent seulement `square:haveElectricity()`.
Le moteur ne les compte pas (l'auteur l'écrit dans `PMK_71_SteamCore.lua`), Live Wire non plus : elles tirent un
courant gratuit.

Ces machines ignorent aussi les circuits du tableau. Live Wire n'enlève pas le courant d'une case : l'ancre de
l'onduleur alimente toute sa zone, lampes et équipements sur les mêmes cases. Couper un circuit, c'est éteindre
chaque appareil que Live Wire connaît (`LW_Circuits.lua`, « isolation of native appliance services »). Une machine
qui ne regarde que la case continue donc de tourner. Seule `LiveWire.API.consumerPowered(obj)` dit la vérité.

L'utilisateur va fournir une liste de mods à vérifier. Il faut un endroit unique, extensible, pour les rendre
compatibles sans toucher à ces mods.

## Décisions

- **D01 — Un mod autonome, séparé de Live Wire.** Projet `Zomboid/Workshop/LiveWireCompatibility`, dépôt et objet
  Workshop propres. `id=batman_LiveWireCompatibility`, titre affiché « LiveWire Compatibility ».
  `require=atman_LiveWire`. Il n'utilise que l'API publique de Live Wire (révision 6 au moins) et Live Wire ne
  change pas. *Révision du 2026-11-13* : la première version de D01 en faisait un sous-mod livré avec Live Wire ;
  l'utilisateur a demandé un nouveau mod (« je te demande de créer un nouveau mod, pas d'enrichir le mod LiveWire »).
  *Précision du 2026-11-13, remplacée le même jour* : un sous-mod par mod cible (`batman_LiveWireCompatibility<Cible>`),
  à activer à la main. *Révision du 2026-11-13* : **un mod unique qui détecte seul les mods cibles**. L'utilisateur :
  « ça fait beaucoup de sous-mod à activer/désactiver à la main. Et si on faisait un mod unique qui détecte
  automatiquement les mods pour brancher ou non sur l'API ? ». Tous les profils sont dans
  `batman_LiveWireCompatibility` ; chacun ne s'applique que si son mod cible est actif (D02). Le joueur active ce
  mod une fois.
- **D02 — Un profil déclaratif par mod cible, aucune chaîne de `if`.** Un fichier par mod cible :
  `shared/LiveWireCompatibility/Profiles/LWC_<Cible>.lua`, qui dépose une table dans un registre. Un chargeur unique lit
  chaque profil et l'applique seulement si l'un des `id` du mod cible est actif (`getActivatedMods():contains`). Il
  passe **uniquement par l'API publique** (`registerConsumer`), jamais par les tables internes de Live Wire. Ajouter
  un mod revient à ajouter un fichier. Forme du profil :

  ```lua
  { mods = { "ArtelManufactory" },             -- ids de mod.info ; un seul actif suffit
    consumers = {
      { id = "ArtelElectricDryer",             -- id passé à registerConsumer, préfixé par la cible
        sprites = { "Artel_..._0", ... },      -- une seule pièce par meuble de plusieurs cases
        watts = 1200,                          -- nombre, ou function(o) -> W
        running = function(o) ... end,         -- facultatif : lit l'état du mod cible
        category = "other", circuit = "equipment",
        gate = { table = "...", fn = "..." } } } } -- facultatif, voir D04
  ```

- **D03 — Consommation estimée, sourcée.** La valeur vient d'abord du mod cible (texte, code ou description), sinon
  d'un appareil réel équivalent ; le profil cite la source en commentaire. Si `running` est lisible (ModData, fonction
  publique), la machine ne consomme qu'en marche ; sinon le profil donne une moyenne sur un cycle d'usage, notée
  comme telle.
- **D04 — Coupure par les circuits seulement par une fonction publique du mod cible.** Quand le mod cible expose sa
  vérification de courant dans une table globale (Artel : `PMK.Well.isPowered`, `PMK.QBase.hasPower`,
  `PMK.Trade.isPowered`, `Sensors.squarePowered` ; le chargeur, le séchoir, le sublimateur et l'établi restent à
  vérifier, leur test est `local` dans au moins un fichier), le profil la nomme dans `gate`. Le chargeur l'enveloppe une seule fois (garde contre une double
  inscription, arguments et retours préservés) : la réponse d'origine **et** `consumerPowered`. Une vérification
  `local` ne s'atteint pas : la machine est facturée mais ignore les circuits. Le profil et le wiki le disent. On ne
  remplace jamais un fichier d'un autre mod et on ne recopie pas son code.
  *Précision du 2026-11-13* : un même test peut servir plusieurs machines du profil (`consumer` accepte un tableau
  d'ids, cas de `Machinery.Service.isPowered`) ; un test défini dans le Lua client du mod cible porte
  `side = "client"` et n'est ni enveloppé ni signalé absent sur un serveur dédié (cas de Computer Mod).
  *Complément du 2026-11-20* : l'[ADR-002](termines/002-interrupteur-et-coupure-des-machines.md) ajoute un interrupteur et
  d'autres types de garde (actions, fonctions d'usage, menus) : une machine dont le test de courant est `local` est
  désormais coupée par un autre point d'entrée public quand il existe.
- **D05 — Analyse avant profil.** Chaque mod de la liste reçoit d'abord un court rapport : appareils déjà comptés
  (objets vanilla), appareils gratuits, fonctions de courant publiques ou non, état de marche lisible. Le profil
  suit. Un mod entièrement vanilla ne reçoit pas de profil.
- **D06 — Tests hors jeu.** Le chargeur est testé avec lupa (profil actif ou non, refus de l'API, enveloppe unique,
  coupure respectée). Chaque profil a un test de forme. Les noms de sprites sont vérifiés par un outil local qui lit le
  `.tiles` de la copie Workshop **en lecture seule** ; cet outil ne tourne pas en CI et rien du mod cible n'est versionné.

## Conséquences

- Les machines des mods listés pèsent sur l'onduleur et la batterie comme les appareils vanilla ; les joueurs voient
  leur nom dans « Consommateurs ».
- Coupure par circuit : complète seulement si le mod cible expose sa fonction de courant. Sinon, facture seule.
- Une mise à jour d'un mod cible (sprite renommé, fonction déplacée) rend son profil inerte sans erreur. L'outil de
  vérification des sprites le détecte.
- Un auteur qui finit par inscrire lui-même ses appareils rend son profil inutile : `registerConsumer` refuse alors
  le doublon (`duplicate_sprite`), et le profil le retire au cycle suivant.

## Mods analysés (D05)

- **Artel Manufactory** (Workshop 3794133594) : lampes et réchaud déjà comptés ; machines propres gratuites. Profil prévu.
- **Vectrex Playable Console** (Workshop 3310855080) : la console est un objet d'inventaire, jamais posé ; seule la recette « jouer » exige `square:haveElectricity()` (`VPC_RecipeCallbacks.lua:269`). L'API ne facture que des objets posés : pas de profil. Facturer une charge brève liée à une action (≈ 30 W pendant une partie) demanderait une autre API, hors portée.
- **Functional Appliances 2** (3042138819) : tuiles vanilla rendues électriques (comptoirs, vitrines, distributeurs, hot-dog, pop-corn, fontaine, SlurpNBurp, tireuses, hottes), aucune comptée par LiveWire, aucun test public. Profil sans coupure.
- **Computer Mod** (3725497089) : ordinateur de bureau gratuit ; test public côté client seulement. Profil. Son **Laptop Addon** (3798992436) : objet d'inventaire, pas de profil.
- **Plysken Weather Station** (3781590169) : station posée gratuite, test public `PWS.Power.isPowered`. Profil.
- **True Moozic** (3632610172) : chaîne HiFi déjà comptée (`IsoRadio`), radiocassettes sur piles ; juke-box vanilla rendu jouable, gratuit, test public `TMJukebox.hasPower`. Profil. Mumble Remover : aucun objet.
- **Machinery** (3780027195) : huit machines électriques gratuites, un test public commun. Profil. **More Machinery Recipes** (3807360837) : recettes seules.
- **Project Arcade** (3645980077) : bornes, flippers, pince, pousse-pièces, punching-ball posés, gratuits, toujours allumés sous tension ; tests de courant `local`. Profil sans coupure. Addon Spiffomon3D Prizes (3646127635) : lots seulement.
- **Video Game Consoles** (2831786301) et ses addons de jeux, **Palm Pilots** (3776531193) : consoles posées au sol comme objets d'inventaire ou sur piles. Pas de profil (même cas que Vectrex).
- **Plysken Battery Charger** (3793465866), **Plysken Irrigation Pipes** (3739173520) : rien de posé ni d'électrique. Pas de profil.
- **Badlands Power** (3804093735), **Industrial Works** (3680638986) : générateurs `IsoGenerator`, sources déjà connues de LiveWire. Pas de profil.
- **[B42] Working Air Conditioner Units** (3784995595) : l'unité branchée devient un `IsoClothingDryer`, déjà facturée et coupée par LiveWire (famille sèche-linge). Pas de profil.

## Hors portée

- Libérer un appareil du registre (noté dans l'ADR-002 de Live Wire).
- Toute modification de Live Wire : ce mod n'utilise que son API publique.
- Modifier un mod tiers ou en livrer une copie corrigée.
