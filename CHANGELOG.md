# Changelog

## Unreleased

### Added
- Switching a machine on or off now shows at once on the inverter screens and in LiveWire's Show consumers view, instead of up to ten game minutes later: our switch, the counters and vending machines of Functional Appliances 2, the desktop computer, the jukebox, and the start and end of an Artel dryer batch (needs the next LiveWire update).
- On/off switch: right-click a supported machine and choose Turn off or Turn on. A machine that is off draws no power and does not work. Machines with a button of their own (desktop computer, jukebox, buffet counters, displays and vending machines) keep it.
- No power, no machine: a machine that is off, unpowered or cut by a breaker refuses to work. Its menu options are greyed with the reason, and a use in progress stops.
- Artel Manufactory: the electric dryer and the freeze dryer pause their batch when the power goes, then resume; the chemistry table refuses to craft without power.
- Functional Appliances 2: hot dog roller, popcorn machine, soda fountain, SlurpNBurp and bar taps refuse to serve without power; counters and vending machines go back to Off.
- Project Arcade: games cannot start without power, before any coin is paid, and a game in progress stops when the power goes.

### Fixed
- Artel Manufactory, Project Arcade, Machinery (metal bandsaw) and Plysken Weather Station: machines that had no depth map are now highlighted in LiveWire's Show consumers view and when targeted, from every side, Artel's dryers included while they are loaded.
- Artel Manufactory: the electric dryer and the freeze dryer no longer draw power around the clock; they draw while a batch runs. East-facing chemistry tables are now billed, and a Quantum Base cut by a breaker no longer flickers back on.
- Project Arcade: sit-down cabinets facing east or south are now billed.
- Machinery: the metalwork lathe now stops when its power is cut, whichever part of it is used.
## 1.0.0 — 2026-11-14

### Added
- Profiles: the machines of a supported mod draw their power from LiveWire. Supported mods are detected on their own: enable this mod once.
- Artel Manufactory: well motor, electric dryer, freeze dryer, chemistry table, trade post and Quantum Base are billed; the circuits stop the well motor, the trade post and the Quantum Base.
- Functional Appliances 2: heated buffet counters, display counters, vending machines, hot dog roller, popcorn machine, soda fountain, SlurpNBurp, bar taps and exhaust hoods are billed.
- Computer Mod: a desktop computer is billed while switched on; the circuits cut it on the player's side.
- Plysken Weather Station: the station is billed; the circuits stop its readings.
- True Moozic: the jukebox is billed while it plays; the circuits stop it.
- Machinery: drill press, bandsaw, hydraulic press, lathe, bench grinder, table saws and concrete mixer are billed; the circuits stop them.
- Project Arcade: arcade cabinets, pinball tables, claw machines, coin pushers and punching machines are billed whenever they have power.
