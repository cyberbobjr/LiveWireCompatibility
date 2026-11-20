# Plan 004 — Signaler à LiveWire chaque allumage et extinction

ADR : [ADR-004](../ADR/004-signaler-les-changements-a-livewire.md) (acceptée le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| S1 | Live Wire : API révision 10, `consumerChanged(obj)` (commit Live Wire `93d88e0`, décision D-68) | Terminée (2026-11-20) | — | — | S | — |
| S2 | `LWC_Switch.changed`, commande `changed` validée par le serveur, signal de l'interrupteur du mod | Terminée (2026-11-20) | S1 | D01, D02 | S | S3 |
| S3 | Type de garde `notify` (après l'appel d'origine, état facultatif) ; `G.wrap` reconnaît nos enveloppes empilées | Terminée (2026-11-20) | S1 | D03 | S | S2 |
| S4 | Profils : FA2 (trois fonctions de mode), Computer Mod (`transmitData`), True Moozic (`TMJukebox.transmit`), Artel (`PMK_StationApplyStage`) ; test d'audit : chaque machine a l'interrupteur du mod ou une garde `notify` | Terminée (2026-11-20) | S2, S3 | D04 | S | — |
| S5 | Contrôle en jeu par l'utilisateur : une machine éteinte passe en bleu tout de suite dans « Afficher les consommateurs » | À valider (contrôle en jeu par l'utilisateur) | S4 | — | S | — |

## S3 — Type de garde `notify`

Correction trouvée en chemin : deux de nos enveloppes empilées sur une même fonction (la pause des lots et `notify` sur
`PMK_StationApplyStage`) faisaient croire au second passage d'`OnInitWorld` que la première n'était plus en place, et
l'enveloppaient de nouveau. `G.wrap` remonte maintenant la pile de nos enveloppes (`G.inner`).

## S4 — Profils et audit

Machines sans interrupteur du mod et sans garde `notify` : la hotte FA2 seulement (aucun levier, ADR-002).

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 188 tests`, `OK` ; `luacheck Contents` → 0 avertissement,
0 erreur ; `python tools/check_sprites.py` → code 0.
