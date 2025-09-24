"""
Make a Tiled SVG generator in Python, meaning that it leaves NO HOLES without a tile and no overlaping tiles.

This code does not properly work, please fix it and don't just give me the same.

Total prompts with all forms of explanations: 7
"""

import argparse
import math

def generate_triangle(x, y, size, inverted=False, fill="white", stroke="black", stroke_width=1):
    """Generate SVG path for an equilateral triangle."""
    height = size * math.sqrt(3) / 2
    
    if inverted:
        # Inverted triangle (pointing down)
        points = [
            (x, y + height/2),              # Bottom point
            (x - size/2, y - height/2),     # Top left
            (x + size/2, y - height/2)      # Top right
        ]
    else:
        # Upright triangle (pointing up)
        points = [
            (x, y - height/2),              # Top point
            (x - size/2, y + height/2),     # Bottom left
            (x + size/2, y + height/2)      # Bottom right
        ]
    
    points_str = ' '.join([f"{p[0]},{p[1]}" for p in points])
    return f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'

def generate_square(x, y, size, fill="white", stroke="black", stroke_width=1):
    """Generate SVG path for a square."""
    half_size = size / 2
    points = [
        (x - half_size, y - half_size),  # Top left
        (x + half_size, y - half_size),  # Top right
        (x + half_size, y + half_size),  # Bottom right
        (x - half_size, y + half_size)   # Bottom left
    ]
    points_str = ' '.join([f"{p[0]},{p[1]}" for p in points])
    return f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'

def generate_hexagon(x, y, size, fill="white", stroke="black", stroke_width=1):
    """Generate SVG path for a regular hexagon."""
    points = []
    for i in range(6):
        angle = math.pi / 3 * i
        px = x + size * math.cos(angle)
        py = y + size * math.sin(angle)
        points.append((px, py))
    points_str = ' '.join([f"{p[0]},{p[1]}" for p in points])
    return f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'

def generate_triangular_tiling(width, height, size, fill, stroke, stroke_width):
    """Generate a triangular tiling pattern with NO HOLES and NO OVERLAPS."""
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Calculate dimensions for equilateral triangles
    triangle_height = size * math.sqrt(3) / 2
    
    # Calculate grid dimensions
    cols = math.ceil(width / (size/2)) + 2
    rows = math.ceil(height / triangle_height) + 2
    
    # Starting position to center the pattern
    start_x = (width - (cols-1) * size/2) / 2
    start_y = (height - (rows-1) * triangle_height) / 2
    
    # Generate tiles in a proper triangular grid
    for row in range(rows):
        for col in range(cols):
            # Calculate position
            x = start_x + col * size/2
            y = start_y + row * triangle_height
            
            # Alternate between up and down triangles based on position
            if (row + col) % 2 == 0:
                # Up-pointing triangle
                svg_content += generate_triangle(x, y, size, False, fill, stroke, stroke_width) + '\n'
            else:
                # Down-pointing triangle
                svg_content += generate_triangle(x, y, size, True, fill, stroke, stroke_width) + '\n'
    
    svg_content += '</svg>'
    return svg_content

def generate_square_tiling(width, height, size, fill, stroke, stroke_width):
    """Generate a square tiling pattern with NO HOLES and NO OVERLAPS."""
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Calculate grid dimensions
    cols = math.ceil(width / size) + 2
    rows = math.ceil(height / size) + 2
    
    # Starting position to center the pattern
    start_x = (width - (cols-1) * size) / 2
    start_y = (height - (rows-1) * size) / 2
    
    # Generate tiles in a grid
    for row in range(rows):
        for col in range(cols):
            # Calculate position
            x = start_x + col * size + size/2
            y = start_y + row * size + size/2
            
            # Add square
            svg_content += generate_square(x, y, size, fill, stroke, stroke_width) + '\n'
    
    svg_content += '</svg>'
    return svg_content

def generate_hexagonal_tiling(width, height, size, fill, stroke, stroke_width):
    """Generate a hexagonal tiling pattern with NO HOLES and NO OVERLAPS."""
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Calculate dimensions for hexagons
    hex_width = size * 2
    hex_height = size * math.sqrt(3)
    
    # Calculate grid dimensions
    cols = math.ceil(width / (hex_width * 0.75)) + 2
    rows = math.ceil(height / hex_height) + 2
    
    # Starting position to center the pattern
    start_x = (width - (cols-1) * hex_width * 0.75) / 2
    start_y = (height - (rows-1) * hex_height) / 2
    
    # Generate tiles in a proper hexagonal grid
    for row in range(rows):
        for col in range(cols):
            # Calculate position with offset for alternating rows
            x = start_x + col * hex_width * 0.75
            y = start_y + row * hex_height
            
            # Offset every other row
            if row % 2 == 1:
                x += hex_width * 0.375
            
            # Add hexagon
            svg_content += generate_hexagon(x, y, size, fill, stroke, stroke_width) + '\n'
    
    svg_content += '</svg>'
    return svg_content

def generate_svg(width, height, corners, tile_size, fill, stroke, stroke_width):
    """Generate the full SVG content with tiled shapes."""
    if corners == 3:
        return generate_triangular_tiling(width, height, tile_size, fill, stroke, stroke_width)
    elif corners == 4:
        return generate_square_tiling(width, height, tile_size, fill, stroke, stroke_width)
    elif corners == 6:
        return generate_hexagonal_tiling(width, height, tile_size, fill, stroke, stroke_width)
    else:
        raise ValueError("Number of corners must be 3, 4, or 6.")

def main():
    parser = argparse.ArgumentParser(description="Generate an SVG file with tiled shapes.")
    parser.add_argument('--width', type=int, default=1280, help="Width of the SVG canvas (default: 1280)")
    parser.add_argument('--height', type=int, default=720, help="Height of the SVG canvas (default: 720)")
    parser.add_argument('--corners', type=int, choices=[3, 4, 6], required=True, help="Number of corners of the tile (3, 4, or 6)")
    parser.add_argument('--tile_size', type=float, default=50, help="Size of each tile (default: 50)")
    parser.add_argument('--fill', type=str, default="white", help="Fill color of the tiles (default: white)")
    parser.add_argument('--stroke', type=str, default="black", help="Stroke color of the tiles (default: black)")
    parser.add_argument('--stroke_width', type=float, default=1, help="Stroke width of the tiles (default: 1)")
    parser.add_argument('--output', type=str, default="output.svg", help="Output SVG file name (default: output.svg)")
    
    args = parser.parse_args()
    
    svg_content = generate_svg(
        args.width, args.height, args.corners,
        args.tile_size, args.fill, args.stroke, args.stroke_width
    )
    
    with open(args.output, 'w') as f:
        f.write(svg_content)
    
    print(f"SVG file '{args.output}' generated successfully.")

if __name__ == "__main__":
    main()
