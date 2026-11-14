# Video Game Consoles (Workshop 2831786301), ses addons, et Palm Pilots (3776531193)

Analyse D05 du 2026-11-13, **confirmée statiquement** (copies Workshop en lecture seule). Rien n'a été testé en jeu.

## Video Game Consoles (`id=Video_Game_Consoles`, variante `42/`)

- Consoles de salon (SNES, NES, Atari, Genesis, Sega CD, CD-i) : objets d'inventaire `base:normal`
  (`42\media\scripts\Video_Game_Consoles_items.txt:9-76`), posés **au sol** comme objets d'inventaire, jamais comme
  tuiles.
- Consoles portables (Game Boy, Game Gear, Lynx) : `base:Drainable`, sur piles.
- Courant : les recettes « jouer » testent la case du joueur, puis cherchent la console au sol et un téléviseur
  dans un rayon (`42\media\lua\shared\VGC_Scripts.lua:69-130`, fonction `local`). Le téléviseur vanilla
  (`IsoTelevision`) est déjà facturé par LiveWire quand il est allumé.
- **Pas de sous-mod** : l'API LiveWire ne facture que des objets posés à sprite de tuile ; une console au sol n'en
  a pas. Même cas que Vectrex (idée I06 : charge brève liée à une action).

## Addons de jeux

More Game Boy Games (3418352842), More NES Games (3413237147), More SEGA Games (3423725989), More SNES Games et
Expansion (3408186716) : cartouches seulement. Pas de sous-mod.

## Palm Pilots (`id=PalmPilots`, 3776531193)

Assistant de poche porté dans l'inventaire, aucun test de courant dans son Lua. Pas de sous-mod.
