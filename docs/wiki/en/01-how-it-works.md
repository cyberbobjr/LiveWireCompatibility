# How it works

Some mods add electric machines the game does not count: they only check that their square has power. With
LiveWire they would run for free. This mod declares them to LiveWire.

- **Billing:** the inverter counts what the machine draws while it runs, like a fridge or a stove.
- **Management software:** the machine is listed in the Consumers tab.
- **Circuits:** opening the equipment circuit stops the machine only when its mod lets other mods see its power
  check. Otherwise the machine is billed but keeps running.
- **Automatic:** enable LiveWire Compatibility once. It finds the supported mods you use and leaves the
  others alone; nothing else to enable.

## Supported mods

### Artel Manufactory

| Machine | Draw (estimate) | Stopped by the circuits |
|---|---|---|
| Well, motor stage | 100 W on average | yes |
| Electric dryer | 300 W on average | no |
| Freeze dryer | 150 W on average | no |
| Chemistry table | 30 W on average | no |
| Trade post | 150 W on grid power, nothing on its own battery | yes (its battery keeps working) |
| Quantum Base | 100 W while lit | yes |

Already counted by the game: portable electric stove, smart floodlights. Never placed in the world, so not billed: battery charging station, electric heater, cooler bag.

### Functional Appliances 2

| Machine | Draw (estimate) | Stopped by the circuits |
|---|---|---|
| Heated buffet counter (each segment) | hot 800 W, warm 400 W, cold 150 W; nothing when off | no |
| Display counters and glass displays (each tile) | warm 150 W, cold 200 W; nothing when off | no |
| Snack and soda vending machines | warm 300 W, cold 200 W; nothing when off | no |
| Hot dog roller | 500 W whenever powered | no |
| Popcorn machine | 200 W whenever powered | no |
| Soda fountain | 200 W whenever powered | no |
| SlurpNBurp machine | 400 W whenever powered | no |
| Bar taps | 150 W whenever powered | no |
| Exhaust hood | 150 W while a generator runs under it | no |

Functional Appliances 2 has no power check other mods can see: these machines are billed but ignore the circuits.
Not billed: deep fryers, coffee machine, wall clock and payphones (Functional Appliances 2 needs no power for them).

### Computer Mod

| Machine | Draw (estimate) | Stopped by the circuits |
|---|---|---|
| Desktop computer | 120 W while switched on | yes, on the player's side (a dedicated server keeps its own check) |

The laptop of the Laptop Addon is carried in the inventory: it is not billed.

### Plysken Weather Station

| Machine | Draw (estimate) | Stopped by the circuits |
|---|---|---|
| Weather station | 15 W whenever powered | yes (it stops recording) |

### True Moozic

| Machine | Draw (estimate) | Stopped by the circuits |
|---|---|---|
| Jukebox | 150 W while it plays | yes |

Already counted by LiveWire: the HiFi stereo. On batteries, so not billed: boomboxes, CD player, walkman.

### Machinery

| Machine | Draw (estimate, average over a work day) | Stopped by the circuits |
|---|---|---|
| Drill press | 150 W | yes |
| Metal bandsaw | 330 W | yes |
| Hydraulic press | 300 W | yes |
| Metalwork lathe | 200 W | yes |
| Bench grinder | 125 W | yes |
| Industrial table saw | 500 W | yes |
| Contractor table saw | 500 W | yes |
| Concrete mixer | 350 W | yes |

Not billed: the Cabinet table saw (petrol). More Machinery Recipes adds recipes only: nothing to bill.

### Project Arcade

| Machine | Draw (estimate) | Stopped by the circuits |
|---|---|---|
| Upright arcade cabinet | 120 W whenever powered | no |
| Sit-down arcade cabinet | 200 W whenever powered | no |
| Pinball table | 200 W whenever powered | no |
| Claw machine | 100 W whenever powered | no |
| Coin pusher | 150 W whenever powered | no |
| Punching machine | 60 W whenever powered | no |

The machines stay lit as long as they have power. Project Arcade has no power check other mods can see: they
are billed but ignore the circuits. Its wall neon lights are lamps, already billed by LiveWire.

## Already handled by LiveWire

- **[B42] Working Air Conditioner Units:** a connected unit becomes a clothes dryer for the game, so LiveWire
  already bills it and the circuits already stop it.
- **Badlands Power, Industrial Works:** their machines are generators, power sources that LiveWire already knows.

## Not supported

- **Vectrex Playable Console:** the console is never placed in the world, so LiveWire cannot bill it.
- **Plysken Battery Charger:** a hand-cranked charger carried in the inventory; it uses no power.
- **Plysken Irrigation Pipes:** pipes and barrels, nothing electric.
- **Computer Mod: Laptop Addon:** the laptop is carried in the inventory.
- **True Moozic - Mumble Remover:** adds no machine.
- **Video Game Consoles** and its game addons: consoles are dropped on the floor next to a TV, never placed as
  furniture, and handhelds run on batteries. The TV itself is billed by LiveWire.
- **Palm Pilots:** carried in the inventory.
- **Spiffomon3D Prizes for Project Arcade:** adds prizes only.
