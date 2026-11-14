# LiveWire Compatibility

Project Zomboid Build 42 mod. It declares the electric machines of other mods to
[LiveWire](https://github.com/cyberbobjr/LiveWire) through its public API (revision 6), so that the inverter bills
them, the management software lists them and, when the other mod allows it, the circuits switch them off.

- One mod, `batman_LiveWireCompatibility`: a loader and one profile per supported mod. A profile applies only when
  its target mod is enabled, so players enable this mod once.
- Requires LiveWire only. LiveWire itself is not modified.
- Documentation (French): [docs/](docs/README.md). Player guide: [wiki](docs/wiki/en/Home.md).

Tests: `python -B -m unittest discover -s tests` (needs `pip install lupa`).

License: MIT.
