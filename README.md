# Tiler
A Tiled Mesh **SVG**/**RAWR** Builder, vibe-coded from 2025-09-24 to 2025-10-03.

Version 9+ supports **RAWR** and animation.

Each file starts with the initial prompt, it also shows how hard it is to get models to properly follow instrucriona.

## Features
- No **Dependencies** (**SVG**/**RAWR** is plain text after all)
- **Pyhon** script
- Outputs **SVG** files
- Outputs **RAWR** files
- Outputs **HTML** files (just a wrapped **SVG**)
- All outputs can be animated
- No *holes* between **Tiles**
- No *overlapping* **Tiles**, this applies to *fill*, not *stroke*

## Arguments
- --help/-h
- --**width**/-w  and **height**/-H of the **document**
- how many --**corners**/-c each Tile has (3,4 or 6)
- --**fill**/-f and **stroke**/-t colors
- --**stroke_width**/-d
- --**tile_size**/s (width=height)
- --**rotation**/-r, this applies to all **Tiles** together not individually
- --**format**/-F, either *SVG* or *RAWR*
- --**animate** (only supports a basic 0% to 100% scale per tile on v14 but you can just edit the **Tile** composition)
- --**output**/-o name of the file
