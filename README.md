# Tiler
A Tiled Mesh **SVG**/**RAWR** Builder, vibe-coded from 2025-09-24 to 2025-10-03.

Version 9+ supports **RAWR** and animation.

Each file starts with the initial prompt, it also shows how hard it is to get models to properly follow instrucriona.

## Features
- No **Dependencies** (**SVG**/**RAWR** is plain text after all)
- **Pyhon** script
- Outputs **SVG** files
- Outputs **RAWR** files which can be animated
- No *holes* between **Tiles**
- No *overlapping* **Tiles**

## Arguments
- **width** and **height** of the **document**
- how many **corners** each Tile has (3,4 or 6)
- **fill** and **stroke color**
- **stroke width**
- **Tile size** (width=height)
- **rotation**, this applies to all **Tiles** together not individually
- **format**, either *SVG* or *RAWR*
- **animation** (only supports a basic 0% to 100% scale per tile on v14)
