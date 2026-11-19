# Améliorations et idées

Ce document propose ; rien n'est autorisé sans validation de l'utilisateur.

## Améliorations de code

| Id | Problème | Correction proposée | Priorité | Effort |
|---|---|---|---|---|
| C01 | `check_sprites.py` cherche les noms dans le Lua et les scripts, pas dans le `.tiles` binaire | Décoder le format `tdef` pour lire les noms de tuiles | basse | M |
| C02 | Établi chimique d'Artel facturé en moyenne (sécheuse et sublimatrice : réglé par l'ADR-002, facture pendant un lot) | Lire la fabrication en cours du panneau d'établi, ou de son infusion (`DryingCraftLogic`) | basse | S |

## Idées de fonctionnalités

| Id | Idée | Intérêt joueur | Faisabilité | Dépendances | Effort |
|---|---|---|---|---|---|
| I01 | `display(o)` par profil : nom de la machine dans l'onglet Consommateurs | voir « Séchoir électrique » au lieu de « Autre » | API révision 6 | traductions | S |
| I02 | `summary(objects)` par profil : total par réseau | voir combien de machines tournent | API révision 6 | — | S |
| I03 | Option sandbox : multiplicateur des consommations estimées | régler la difficulté | simple | — | S |
| I04 | Option sandbox : désactiver un profil | éviter un conflit | simple | — | S |
| I05 | Commande admin qui liste les profils actifs et leurs refus | diagnostic serveur | simple | — | S |
| I06 | Charges brèves liées à une action (console Vectrex) | facturer une partie de jeu | demande une nouvelle API LiveWire | ADR LiveWire | M |
| I07 | Profil généré depuis une liste de sprites fournie par un joueur | ajouter un mod sans code | moyen | — | M |
| I08 | Avertissement en jeu quand un mod cible a changé (profil inerte) | comprendre une machine gratuite | moyen | — | S |
| I09 | Page du wiki par mod pris en charge, avec ses consommations | transparence | simple | — | S |
| I10 | Proposer aux auteurs des mods cibles d'inscrire eux-mêmes leurs machines | fin du profil, coupure complète | relationnel | — | S |
