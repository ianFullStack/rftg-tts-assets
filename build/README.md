# Build outputs

- `RollForTheGalaxy_Published.json` — **the new-game save.** Every fix applied,
  all assets pointed at this repo's raw URLs, no stored script state so it
  begins at setup. This is the file uploaded to the Workshop item.
- `RollForTheGalaxy_Recovered.json` — a rescued mid-game save (has
  `LuaScriptState`, so it resumes in the "playing" phase).
- `RollForTheGalaxy_Fixed.json` — intermediate: fixes applied but assets still
  pointing at the original dead Pastebin/imgur URLs. Works only on a machine
  whose TTS cache happens to hold those files. Not for distribution.

To restore a save, copy the file into:
`Documents\My Games\Tabletop Simulator\Saves\`
