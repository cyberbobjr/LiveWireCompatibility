# Vectrex Playable Console (Workshop 3310855080)

Analyse D05 du 2026-11-13, confirmée statiquement (copie Workshop, lecture seule).

- `id=VectrexPlayableConsole`. Console, cartouches et périphériques sont des objets d'inventaire
  (`VPC_items_consoles.txt`), jamais posés : aucune tuile, aucun sprite d'objet posé.
- Seules les recettes « jouer » exigent du courant :
  `Vectrex_Scripts.OnCanPerform.RequireElectricityToPerform(craftRecipeData, character)`
  (`VPC_RecipeCallbacks.lua:269`), qui teste la case du joueur (`haveElectricity` si `AllowExteriorGenerator`, sinon
  le réseau public à l'intérieur).
- L'API LiveWire ne facture que des objets posés : **aucun profil**. Une charge brève liée à une action (≈ 30 W
  pendant une partie) demanderait une nouvelle API LiveWire (idée I06).
