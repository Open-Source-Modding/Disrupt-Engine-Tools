# Disrupt Engine Tools

Extracted tools and source code from the Ubisoft internal development environment
for the Disrupt engine (Watch Dogs 1/2/Legion).  These scripts were authored by
Ubisoft developers during WD1/WD2/WDL production and shipped as part of the
`td_tools` directory in the 2020 Ubisoft leak.

This repo extracts the **format-relevant source code** — the pipeline tools,
parsers, and utilities that document how the engine reads and writes its
proprietary formats (`.xbg`, `.glm`, `.mab`, `.material.bin`, `.xbt`, `.hkx`).

## Contents

```
asset_pipeline/    Core format parsers and asset dependency resolution
  adp_lib.py       The master asset pipeline library (4261 lines)
  DDV/             Disrupt Dependency Viewer (PySide GUI)

animation/         Animation format tools
  mac_binary.py    MAC binary reader/writer (versions 7.0-11.0)

materials/         Material pipeline tools
  material_bank_parser.py
  MaterialReAssign/

meshes/            Mesh/geometry tools
  GLMinator/       GLM auditing and validation
  glm_maya.py      Maya GLM import

shaders/           Shader tools and parsers
  SlimShader/      Shader family compiler GUI
  disrupt_shader_parse.py   Maya shader XML parser

pipeline/          Full asset pipeline implementations
  Rumba/           Python 3 rewrite of the DDV asset system
  Materialist/     Material derivation hierarchy viewer

physics/           (placeholder for HKX/collision tools)

material_editing/  Material editing and override tools
  material_cubes_generator.py    Generate material cube maps
  material_override_generator.py Generate material overrides
  material_dependency_fetcher.py Fetch material dependency lists
  material_cubes/                Material cube generation tool

animation_tools/   Animation pipeline tools
  animation_report/      C# animation action list / CLO report
  prop_info_extractor.py Extract prop info with Perforce config

bin_tools/         Compiled dev-tool binaries (from leak `bin/tools/`)
  material_editor/       Disrupt.Materials.Editor.dll + standalone editor (authoritative .material.bin reference, WPF .NET)
  animation_dissect/    Dissect.exe animation viewer (x64 .NET)
  pak_viewer/           PakViewer.exe (native, needs Oodle oo2core)
  stringid/             StringIDTool.exe (string → FNV hash tool)
  archive_differ/       ArchiveDiffer_r64.exe (BigFile/FAT comparison)

world_tools/       World/level editing tools
  layer_to_prefab/       Convert world layers to prefabs
  snapshot_classifier.py Classify building/POI snapshots
  world_layer_draw.py    Draw world layer debug views
  xml_assembly_tester.py Test XML assembly files

meshes/            Mesh/geometry tools
  GLMinator/       GLM auditing and validation
  glm_maya.py      Maya GLM import
  lod_adjuster.py  LOD distance adjustment tool
```

## Relationship to other repos

- **blender-io-xbg** (`Open-Source-Modding/blender-io-xbg`) — Blender addon
  for importing/editing/exporting Disrupt engine models, built using knowledge
  from these tools
- **open-source-modding.github.io** — Published reference documentation
  derived from the leak (material descriptors, format specs)
- **Gibbed.Disrupt** — Binary object converters for `.fcb`/`.lib`/`.bin` files
