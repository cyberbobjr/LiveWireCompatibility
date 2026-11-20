# ADR-006 — Contrôle de courant des stations de séchage Artel corrigé à la source

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-006-CORRECTIF-SOURCE-ARTEL` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Accepté (2026-11-20) |
| Avancement | voir le [plan 006](../ADR-plans/plan-006-correctif-source-artel.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWireCompatibility` : nouveau module `LWC_SourcePatch`, profil Artel, fichier de même chemin `media/lua/server/PMK_58z_SublimatorServer.lua`, `mod.info` (`loadModAfter`) |
| Documents liés | [ADR-002](termines/002-interrupteur-et-coupure-des-machines.md) (D06 Artel), [ADR-005](005-tuiles-partagees-et-trois-nouveaux-mods.md) |
| Références | Artel `server/PMK_58z_SublimatorServer.lua:82-88` (`squarePowered`, fonction locale), `:430`, `:467` ; Java `LuaManager.getModFileReader` (`LuaManager.java:4925-4958`, dossier de version puis `common`, UTF-8) ; Kahlua `loadstring` (`LuaCompiler.java:96, 109`) ; `.claude/pz-knowledge/mod-loading.md` (remplacement par même chemin, `loadModAfter` indicatif) |
| Origine | demande de l'utilisateur du 2026-11-20 : un lyophilisateur éteint ne montre pas « pas de courant » ; l'auteur d'Artel ne maintient plus le mod ; « faire en sorte que notre mod écrase le code fautif » |

## Contexte

Le veilleur serveur d'Artel décide qu'une station de séchage a du courant par une fonction **locale** `squarePowered(square)`
(`PMK_58z:82`) : aucune garde ne l'atteint. Les correctifs d'effets d'ADR-002 (pause des lots, refus de lancer, voyant de la
fenêtre) compensent sans toucher la décision d'Artel. Artel n'a pas de licence : son code n'est pas redistribuable.

## Décisions

- **D01 — Correctif à la source, sans copie.** Un fichier de LiveWire Compatibility porte le même chemin que celui d'Artel
  et le remplace. Il ne contient aucun code d'Artel : au chargement, il lit le fichier d'origine dans le dossier d'Artel
  (`getModFileReader`), y remplace une seule ligne, la déclaration de `squarePowered`, puis l'exécute (`loadstring`). La
  fonction d'Artel reste intacte et devient la réponse de base ; la nôtre y ajoute « et la station est alimentée par
  LiveWire et allumée ». Les numéros de ligne d'Artel sont conservés (remplacement sur une seule ligne).
- **D02 — Module générique.** `LWC_SourcePatch` (registre de correctifs par chemin, données déclarées dans le profil) sert à
  tout autre mod dont la vérification est locale. Un profil déclare `{ mod, path, edits = { { old, new } } }` ; chaque
  `old` doit apparaître exactement une fois.
- **D03 — Repli sûr.** Si un `old` n'apparaît pas exactement une fois ou si le texte corrigé ne compile pas, le fichier
  d'origine d'Artel s'exécute tel quel et un message en anglais l'indique ; si Artel n'est pas actif, rien. Les correctifs
  d'effets d'ADR-002 restent en place : ils couvrent ce repli et l'ordre de chargement inverse.
- **D04 — Ordre de chargement.** Le remplacement n'a lieu que si LiveWire Compatibility est chargé après Artel :
  `loadModAfter` cite `ArtelManufactory` (indication du sélecteur, pas une garantie). Au démarrage du monde, un correctif
  enregistré dont le mod est actif et qui n'a pas tourné est signalé dans la console.

## Conséquences

- Le joueur voit les réactions d'Artel lui-même (voyant, bandeau, lots figés, journaux serveur) pour une station éteinte
  ou coupée par LiveWire.
- Une mise à jour d'Artel est suivie automatiquement tant que la ligne remplacée existe ; sinon, repli D03.
