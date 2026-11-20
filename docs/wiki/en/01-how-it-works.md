# How it works

Some mods add electric machines the game does not count: they only check that their square has power. With
LiveWire they would run for free. This mod declares them to LiveWire.

- **Billing:** the inverter counts what the machine draws while it runs, like a fridge or a stove.
- **Switch:** right-click the machine, **Turn off** or **Turn on**. Switched off, it draws nothing and does not
  work. The tooltip shows what it draws while running. Machines that already have their own button (computer,
  jukebox, counters and vending machines) keep it. A machine picked up and placed again comes back on.
- **No power, no machine:** a machine that is switched off, has no power or is cut by a breaker refuses to work.
  Its menu options stay visible but greyed, with the reason ("The machine is switched off" or "No power"), and a
  use in progress stops.
- **Management software:** the machine is listed in the Consumers tab.
- **Automatic:** enable LiveWire Compatibility once. It finds the supported mods you use and leaves the
  others alone; nothing else to enable.

In multiplayer the server records the switch. For some mods (Functional Appliances 2, Project Arcade, Computer Mod,
True Moozic, Artel's chemistry table) the machine only works on the player's side: that is where it is stopped.

## Supported mods

### Artel Manufactory

| Machine | Draw (estimate) | Switch | Without power or switched off |
|---|---|---|---|
| Well, motor stage | 100 W on average | yes | pumps at hand-pump speed |
| Electric dryer | 2,000 W during a batch, 5 W otherwise | yes | the batch pauses, then resumes |
| Freeze dryer | 700 W during a batch, 5 W otherwise | yes | the batch pauses, then resumes |
| Chemistry table | 30 W on average | yes | refuses to craft |
| Trade post | 150 W on grid power, nothing on its own battery | yes | runs on its battery |
| Quantum Base | 100 W while lit | yes | goes dark, its cells lock |

Already counted by the game: portable electric stove, smart floodlights. Never placed in the world, so not billed: battery charging station, electric heater, cooler bag.

### Functional Appliances 2

| Machine | Draw (estimate) | Switch | Without power or switched off |
|---|---|---|---|
| Heated buffet counter (each segment) | hot 800 W, warm 400 W, cold 150 W; nothing when off | its own ("Off" setting) | goes back to Off, other settings refused |
| Display counters and glass displays (each tile) | warm 150 W, cold 200 W; nothing when off | its own ("Off" setting) | same |
| Snack and soda vending machines | warm 300 W, cold 200 W; nothing when off | its own ("Off" setting) | same |
| Hot dog roller | 500 W | yes | refuses to serve |
| Popcorn machine | 200 W | yes | refuses to serve |
| Soda fountain | 200 W | yes | refuses to serve |
| SlurpNBurp machine | 400 W | yes | refuses to serve |
| Bar taps | 150 W | yes | refuse to serve |
| Exhaust hood | 150 W while a generator runs under it | no | not handled |

Not billed: deep fryers, coffee machine, wall clock and payphones (Functional Appliances 2 needs no power for them).

### Computer Mod

| Machine | Draw (estimate) | Switch | Without power |
|---|---|---|---|
| Desktop computer | 120 W while switched on | its own (power button) | the screen shuts down |

The laptop of the Laptop Addon is carried in the inventory: it is not billed.

### Plysken Weather Station

| Machine | Draw (estimate) | Switch | Without power or switched off |
|---|---|---|---|
| Weather station | 15 W | yes | stops recording (gap in the log) |

### True Moozic

| Machine | Draw (estimate) | Switch | Without power |
|---|---|---|---|
| Jukebox | 150 W while it plays | its own (play / stop) | the music stops |

Already counted by LiveWire: the HiFi stereo. On batteries, so not billed: boomboxes, CD player, walkman.

### Machinery

| Machine | Draw (estimate, average over a work day) | Switch | Without power or switched off |
|---|---|---|---|
| Drill press | 150 W | yes | refuses to work |
| Metal bandsaw | 330 W | yes | refuses to work |
| Hydraulic press | 300 W | yes | refuses to work |
| Metalwork lathe | 200 W | yes | refuses to work |
| Bench grinder | 125 W | yes | refuses to work |
| Industrial table saw | 500 W | yes | refuses to work |
| Contractor table saw | 500 W | yes | refuses to work |
| Concrete mixer | 350 W | yes | refuses to work |

Not billed: the Cabinet table saw (petrol). More Machinery Recipes adds recipes only: nothing to bill.

### Project Arcade

| Machine | Draw (estimate) | Switch | Without power or switched off |
|---|---|---|---|
| Upright arcade cabinet | 120 W | yes | play option greyed before paying; a game in progress stops |
| Sit-down arcade cabinet | 200 W | yes | same |
| Pinball table | 200 W | yes | same |
| Claw machine | 100 W | yes | same |
| Coin pusher | 150 W | yes | the panel does not open, or closes before paying |
| Punching machine | 60 W | yes | options greyed, high scores included |

The cabinets' ambient sound goes on while their square has power. Its wall neon lights are lamps, already billed by
LiveWire.

### Knox Working Machines

| Machine | Draw (estimate, average over a work day) | Switch | Without power or switched off |
|---|---|---|---|
| Drill press | 100 W | yes | the station window does not open; a craft in progress stops |
| Table saw | 375 W | yes | same |
| Lathe (3 sections) | 42 W per section | yes | same |
| Milling machine (4 sections) | 47 W per section | yes | same |
| Hydraulic press | 188 W | yes | same |
| Bench grinder | 93 W | yes | same |
| Charging panel | 38 W | yes | same |
| Canning line | 150 W per section | yes | same |
| Vehicle lift | 188 W per post | yes | same |
| Car wash (brush, curtain) | 125 W per part | yes | "Wash" greyed |

Knox reuses vanilla tiles, some of them also used by Machinery: with both mods enabled, each machine follows the rules of
the mod that placed it. Not electric: welding cart, vises, furnaces, gas racks, tire bench, drums.

### STFO 3T: Traps, Turrets and Towers

| Device | Draw (estimate, on mains) | Switch | Without LiveWire power |
|---|---|---|---|
| Fence energizer | 3 W | yes | runs on its battery if it has one, else the fence is dead |
| Motion sensor | 2 W | yes | stops detecting (mains only) |
| Gate control box | 5 W | yes | runs on its battery, else no longer drives the gate |
| Floodlight stand | 300 W when lit | its own | runs on its battery, else goes dark |
| Work light | 150 W when lit | its own | same |
| Tower searchlight | 300 W when lit | its own | same |
| Auto-turret | 40 W on standby | its own | runs on its battery, else stops firing |

Only the mains goes through LiveWire: a device running on its own car battery is not billed. Switched off with our
switch, a device does not work at all, battery or not. Traps, mines and watchtowers draw nothing.

### CamRecorder

| Device | Draw (estimate) | Switch | Without power |
|---|---|---|---|
| Fixed security camera | 5 W | yes | stops filming, recording does not start |
| Imekagi camera | 20 W when on | its own | stops filming |
| Security monitors | 50 W (desk), 100 W (wall), when on | their own | screen off (partly: see limits) |
| Surveillance PC | 120 W when on | its own | cannot be used |

Floor camcorders run on batteries: not billed. TVs used as outputs are already billed by LiveWire. The surveillance PC is
the vanilla desktop computer, like Computer Mod's: each computer follows the rules of the mod that uses it.
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
