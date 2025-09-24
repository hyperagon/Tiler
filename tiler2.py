"""
Fix the issue with the Tiles not ligning up vertically, do you even know what a tiled mesh is?
"""

import argparse
import math

def generate_triangle(x, y, tile_width, tile_height, inverted=False, fill="white", stroke="black", stroke_width=1):
    """Generate SVG path for a triangle centered at (x, y) with given dimensions."""
    if inverted:
        # Inverted triangle (pointing down)
        points = [
            (x, y + tile_height/2),              # Bottom point
            (x - tile_width/2, y - tile_height/2),  # Top left
            (x + tile_width/2, y - tile_height/2)   # Top right
        ]
    else:
        # Upright triangle (pointing up)
        points = [
            (x, y - tile_height/2),              # Top point
            (x - tile_width/2, y + tile_height/2),  # Bottom left
            (x + tile_width/2, y + tile_height/2)   # Bottom right
        ]
    return f'<polygon points="{points[0][0]},{points[0][1]} {points[1][0]},{points[1][1]} {points[2][0]},{points[2][1]}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'

def generate_square(x, y, tile_width, tile_height, fill="white", stroke="black", stroke_width=1):
    """Generate SVG path for a square/rectangle centered at (x, y) with given dimensions."""
    half_width = tile_width / 2
    half_height = tile_height / 2
    points = [
        (x - half_width, y - half_height),  # Top left
        (x + half_width, y - half_height),  # Top right
        (x + half_width, y + half_height),  # Bottom right
        (x - half_width, y + half_height)   # Bottom left
    ]
    return f'<polygon points="{points[0][0]},{points[0][1]} {points[1][0]},{points[1][1]} {points[2][0]},{points[2][1]} {points[3][0]},{points[3][1]}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'

def generate_hexagon(x, y, tile_width, tile_height, fill="white", stroke="black", stroke_width=1):
    """Generate SVG path for a hexagon centered at (x, y) with given dimensions."""
    radius_x = tile_width / 2
    radius_y = tile_height / 2
    points = []
    for i in range(6):
        angle = math.pi / 3 * i
        px = x + radius_x * math.cos(angle)
        py = y + radius_y * math.sin(angle)
        points.append((px, py))
    points_str = ' '.join([f"{p[0]},{p[1]}" for p in points])
    return f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'

def generate_svg(width, height, corners, offset_x, offset_y, tile_width, tile_height, fill, stroke, stroke_width):
    """Generate the full SVG content with tiled shapes."""
    # Choose the generator function based on number of corners
    if corners == 3:
        return generate_triangular_tiling(width, height, offset_x, offset_y, tile_width, tile_height, fill, stroke, stroke_width)
    elif corners == 4:
        return generate_square_tiling(width, height, offset_x, offset_y, tile_width, tile_height, fill, stroke, stroke_width)
    elif corners == 6:
        return generate_hexagonal_tiling(width, height, offset_x, offset_y, tile_width, tile_height, fill, stroke, stroke_width)
    else:
        raise ValueError("Number of corners must be 3, 4, or 6.")

def generate_triangular_tiling(width, height, offset_x, offset_y, tile_width, tile_height, fill, stroke, stroke_width):
    """Generate a triangular tiling pattern with upright and inverted triangles."""
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # For proper triangular tiling, we need to think in terms of triangle vertices, not centers
    # Use tile_width as the side length of the equilateral triangle
    side_length = tile_width
    triangle_height = side_length * math.sqrt(3) / 2
    
    # Calculate spacing between triangle vertices
    spacing_x = offset_x if offset_x > 0 else side_length
    spacing_y = offset_y if offset_y > 0 else triangle_height
    
    # Calculate how many tiles we need
    tiles_x = int(width / spacing_x) + 2
    tiles_y = int(height / spacing_y) + 2
    
    # Calculate starting position to center the pattern
    start_x = (width - (tiles_x - 1) * spacing_x) / 2
    start_y = (height - (tiles_y - 1) * spacing_y) / 2
    
    # Generate tiles by creating triangles that share vertices
    for row in range(tiles_y):
        for col in range(tiles_x):
            # Calculate base position for this triangle
            base_x = start_x + col * spacing_x
            base_y = start_y + row * spacing_y
            
            if row % 2 == 0:
                # Even rows: upright triangles
                if col % 2 == 0:
                    # Upright triangle pointing up
                    points = [
                        (base_x, base_y),  # Top vertex
                        (base_x - side_length/2, base_y + triangle_height),  # Bottom left
                        (base_x + side_length/2, base_y + triangle_height)   # Bottom right
                    ]
                else:
                    # Skip - this would create overlapping triangles
                    continue
            else:
                # Odd rows: inverted triangles
                if col % 2 == 1:
                    # Inverted triangle pointing down
                    points = [
                        (base_x, base_y + triangle_height),  # Bottom vertex
                        (base_x - side_length/2, base_y),  # Top left
                        (base_x + side_length/2, base_y)   # Top right
                    ]
                else:
                    # Skip - this would create overlapping triangles
                    continue
            
            points_str = ' '.join([f"{p[0]},{p[1]}" for p in points])
            svg_content += f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>\n'
    
    svg_content += '</svg>'
    return svg_content

def generate_square_tiling(width, height, offset_x, offset_y, tile_width, tile_height, fill, stroke, stroke_width):
    """Generate a square tiling pattern."""
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Calculate effective spacing (equal to tile dimensions for touching tiles)
    spacing_x = offset_x if offset_x > 0 else tile_width
    spacing_y = offset_y if offset_y > 0 else tile_height
    
    # Calculate how many tiles we need
    tiles_x = int(width / spacing_x) + 2
    tiles_y = int(height / spacing_y) + 2
    
    # Calculate starting position to center the pattern
    start_x = (width - (tiles_x - 1) * spacing_x) / 2
    start_y = (height - (tiles_y - 1) * spacing_y) / 2
    
    # Generate tiles in a grid
    for row in range(tiles_y):
        for col in range(tiles_x):
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            svg_content += generate_square(x, y, tile_width, tile_height, fill, stroke, stroke_width) + '\n'
    
    svg_content += '</svg>'
    return svg_content

def generate_hexagonal_tiling(width, height, offset_x, offset_y, tile_width, tile_height, fill, stroke, stroke_width):
    """Generate a hexagonal tiling pattern."""
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # For hexagons, the horizontal spacing is 3/4 of the width
    # and the vertical spacing is the height
    spacing_x = offset_x if offset_x > 0 else tile_width * 0.75
    spacing_y = offset_y if offset_y > 0 else tile_height
    
    # Calculate how many tiles we need
    tiles_x = int(width / spacing_x) + 2
    tiles_y = int(height / spacing_y) + 2
    
    # Calculate starting position to center the pattern
    start_x = (width - (tiles_x - 1) * spacing_x) / 2
    start_y = (height - (tiles_y - 1) * spacing_y) / 2
    
    # Generate tiles in a grid with offset rows
    for row in range(tiles_y):
        for col in range(tiles_x):
            x = start_x + col * spacing_x
            # Offset every other row by half the width
            if row % 2 == 1:
                x += tile_width * 0.375  # Half of the horizontal spacing
            y = start_y + row * spacing_y
            svg_content += generate_hexagon(x, y, tile_width, tile_height, fill, stroke, stroke_width) + '\n'
    
    svg_content += '</svg>'
    return svg_content

def main():
    parser = argparse.ArgumentParser(description="Generate an SVG file with tiled shapes.")
    parser.add_argument('--width', type=int, default=1280, help="Width of the SVG canvas (default: 1280)")
    parser.add_argument('--height', type=int, default=720, help="Height of the SVG canvas (default: 720)")
    parser.add_argument('--corners', type=int, choices=[3, 4, 6], required=True, help="Number of corners of the tile (3, 4, or 6)")
    parser.add_argument('--offset_x', type=int, default=0, help="Horizontal offset between tiles (default: 0)")
    parser.add_argument('--offset_y', type=int, default=0, help="Vertical offset between tiles (default: 0)")
    parser.add_argument('--tile_width', type=float, default=50, help="Width of each tile (default: 50)")
    parser.add_argument('--tile_height', type=float, default=50, help="Height of each tile (default: 50)")
    parser.add_argument('--fill', type=str, default="white", help="Fill color of the tiles (default: white)")
    parser.add_argument('--stroke', type=str, default="black", help="Stroke color of the tiles (default: black)")
    parser.add_argument('--stroke_width', type=float, default=1, help="Stroke width of the tiles (default: 1)")
    parser.add_argument('--output', type=str, default="output.svg", help="Output SVG file name (default: output.svg)")
    
    args = parser.parse_args()
    
    svg_content = generate_svg(
        args.width, args.height, args.corners, 
        args.offset_x, args.offset_y,
        args.tile_width, args.tile_height,
        args.fill, args.stroke, args.stroke_width
    )
    
    with open(args.output, 'w') as f:
        f.write(svg_content)
    
    print(f"SVG file '{args.output}' generated successfully.")

if __name__ == "__main__":
    main()
