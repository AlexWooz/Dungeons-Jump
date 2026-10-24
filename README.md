# Jump for Minecraft Dungeons

A Blueprint mod for **Minecraft Dungeons** (Steam, v1.17.0.0, UE 4.22) that lets the hero jump, with the Minecraft Dungeons II keyboard layout: **Space** jumps about 2.5 blocks high and the forward roll moves from Space to **R**. The normal dodge stays on Mouse 4.

On controller, **LT** jumps. LT normally opens the quick-chat wheel (online only), so the wheel moves to **D-pad Left**.

**Status:** probe build, tested in camp on keyboard, mouse and controller. It shows a debug readout at all times, and the chat-wheel move hasn't been tested online yet. See [docs/TECHNICAL.md](docs/TECHNICAL.md).

## Install
1. Install Dungeons Blueprint Loader 1.0 (`Blueprint-Loader.pak`) in your `~mods` folder.
2. Put `Jump.pak` in `<Steam>\steamapps\common\MinecraftDungeons\Dungeons\Content\Paks\~mods\`.

To turn the mod off, remove the .pak. It is independent of [ThirdPersonCam](https://github.com/AlexWooz/Dungeons-ThirdPersonCam) and [AnalogMove](https://github.com/AlexWooz/Dungeons-AnalogMove).

## Building
Same setup as ThirdPersonCam: Dokucraft's Dungeons Mod Kit at `..\Dungeons-Mod-Kit`, UE 4.22. The Blueprint is generated headlessly with the Mod Kit's BPTool commandlet (`UE4Project\Source\DungeonsBPTools`, which needs `newbp`/`newlevel`), so the editor isn't needed. Keep it closed.
1. `.\tools\blueprint\build.ps1` recreates `BP_JumpProbe` from `tools\blueprint\gen.py`. Change `JUMP_HEIGHT` there to tune the jump.
   On a fresh Mod Kit, first run `.\tools\sync.ps1 -ToModKit` for the debug widget and loader levels.
2. Run the Mod Kit's `cook_assets.bat` (exit code 16 just means the Precooked folder is missing), then `.\tools\package.ps1`. That packs only this mod's assets; `package.bat` would also pack the other mods.
3. Run `.\tools\sync.ps1 -FromModKit` before committing.

### Layout
| Path | Contents |
|---|---|
| `ModKit/UE4Project/Content/Mods/Jump/` | `BP_JumpProbe` (all logic), `W_JumpDebug` (readout) |
| `ModKit/UE4Project/Content/BPLoader/{InGame,Lobby}/JMP_*.umap` | Loader levels that spawn the actor |
| `tools/blueprint/` | `gen.py` (the graph as paste text + ops) and `build.ps1` (newbp → addvar → paste) |
| `tools/sync.ps1`, `tools/package.ps1` | Copy files to and from the Mod Kit; pack this mod alone |
