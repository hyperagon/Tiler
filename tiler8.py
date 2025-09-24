"""
Make a Tiled SVG generator in Python, meaning that it leaves NO HOLES without a tile and no overlaping tiles.

ok, one last thing, cut out all the tiles that are outside of the document, leaving those that are at least a little inside

Total prompts with all forms of explanations: 19
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
    """Generate SVG path for a regular hexagon with flat top."""
    points = []
    for i in range(6):
        angle = math.pi / 3 * i
        # Rotate by 30 degrees to get flat top
        angle += math.pi / 6
        px = x + size * math.cos(angle)
        py = y + size * math.sin(angle)
        points.append((px, py))
    points_str = ' '.join([f"{p[0]},{p[1]}" for p in points])
    return f'<polygon points="{points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'

def rotate_point(x, y, cx, cy, angle_degrees):
    """Rotate a point (x, y) around a center point (cx, cy) by the given angle in degrees."""
    angle_rad = math.radians(angle_degrees)
    cos_angle = math.cos(angle_rad)
    sin_angle = math.sin(angle_rad)
    
    # Translate point to origin
    tx = x - cx
    ty = y - cy
    
    # Rotate point
    rx = tx * cos_angle - ty * sin_angle
    ry = tx * sin_angle + ty * cos_angle
    
    # Translate back
    return rx + cx, ry + cy

def calculate_expanded_dimensions(width, height, rotation_degrees):
    """Calculate how much we need to expand the grid to cover the canvas after rotation."""
    if rotation_degrees == 0:
        return width, height
    
    # Convert rotation to radians
    angle = math.radians(rotation_degrees)
    
    # Calculate the maximum expansion needed in any direction
    # This is the maximum distance from the center to a corner after rotation
    half_diag = math.sqrt((width/2)**2 + (height/2)**2)
    
    # Calculate the required dimensions to cover the original canvas after rotation
    expanded_width = 2 * half_diag
    expanded_height = 2 * half_diag
    
    return expanded_width, expanded_height

def is_triangle_inside_after_rotation(x, y, size, inverted, width, height, rotation):
    """Check if a triangle is at least partially inside the document boundaries after rotation."""
    height_tri = size * math.sqrt(3) / 2
    
    # Get triangle points
    if inverted:
        points = [
            (x, y + height_tri/2),              # Bottom point
            (x - size/2, y - height_tri/2),     # Top left
            (x + size/2, y - height_tri/2)      # Top right
        ]
    else:
        points = [
            (x, y - height_tri/2),              # Top point
            (x - size/2, y + height_tri/2),     # Bottom left
            (x + size/2, y + height_tri/2)      # Bottom right
        ]
    
    # Apply rotation to points
    cx, cy = width/2, height/2
    rotated_points = []
    for px, py in points:
        rx, ry = rotate_point(px, py, cx, cy, rotation)
        rotated_points.append((rx, ry))
    
    # Check if any point is inside the document boundaries
    for px, py in rotated_points:
        if 0 <= px <= width and 0 <= py <= height:
            return True
    
    # Check if any edge intersects with the document boundaries
    for i in range(3):
        x1, y1 = rotated_points[i]
        x2, y2 = rotated_points[(i + 1) % 3]
        
        # Check intersection with left boundary (x = 0)
        if (x1 <= 0 and x2 >= 0) or (x1 >= 0 and x2 <= 0):
            if x1 != x2:  # Avoid division by zero
                y_at_x0 = y1 + (y2 - y1) * (0 - x1) / (x2 - x1)
                if 0 <= y_at_x0 <= height:
                    return True
        
        # Check intersection with right boundary (x = width)
        if (x1 <= width and x2 >= width) or (x1 >= width and x2 <= width):
            if x1 != x2:  # Avoid division by zero
                y_at_xwidth = y1 + (y2 - y1) * (width - x1) / (x2 - x1)
                if 0 <= y_at_xwidth <= height:
                    return True
        
        # Check intersection with top boundary (y = 0)
        if (y1 <= 0 and y2 >= 0) or (y1 >= 0 and y2 <= 0):
            if y1 != y2:  # Avoid division by zero
                x_at_y0 = x1 + (x2 - x1) * (0 - y1) / (y2 - y1)
                if 0 <= x_at_y0 <= width:
                    return True
        
        # Check intersection with bottom boundary (y = height)
        if (y1 <= height and y2 >= height) or (y1 >= height and y2 <= height):
            if y1 != y2:  # Avoid division by zero
                x_at_yheight = x1 + (x2 - x1) * (height - y1) / (y2 - y1)
                if 0 <= x_at_yheight <= width:
                    return True
    
    return False

def is_square_inside_after_rotation(x, y, size, width, height, rotation):
    """Check if a square is at least partially inside the document boundaries after rotation."""
    half_size = size / 2
    
    # Get square points
    points = [
        (x - half_size, y - half_size),  # Top left
        (x + half_size, y - half_size),  # Top right
        (x + half_size, y + half_size),  # Bottom right
        (x - half_size, y + half_size)   # Bottom left
    ]
    
    # Apply rotation to points
    cx, cy = width/2, height/2
    rotated_points = []
    for px, py in points:
        rx, ry = rotate_point(px, py, cx, cy, rotation)
        rotated_points.append((rx, ry))
    
    # Check if any point is inside the document boundaries
    for px, py in rotated_points:
        if 0 <= px <= width and 0 <= py <= height:
            return True
    
    # Check if any edge intersects with the document boundaries
    for i in range(4):
        x1, y1 = rotated_points[i]
        x2, y2 = rotated_points[(i + 1) % 4]
        
        # Check intersection with left boundary (x = 0)
        if (x1 <= 0 and x2 >= 0) or (x1 >= 0 and x2 <= 0):
            if x1 != x2:  # Avoid division by zero
                y_at_x0 = y1 + (y2 - y1) * (0 - x1) / (x2 - x1)
                if 0 <= y_at_x0 <= height:
                    return True
        
        # Check intersection with right boundary (x = width)
        if (x1 <= width and x2 >= width) or (x1 >= width and x2 <= width):
            if x1 != x2:  # Avoid division by zero
                y_at_xwidth = y1 + (y2 - y1) * (width - x1) / (x2 - x1)
                if 0 <= y_at_xwidth <= height:
                    return True
        
        # Check intersection with top boundary (y = 0)
        if (y1 <= 0 and y2 >= 0) or (y1 >= 0 and y2 <= 0):
            if y1 != y2:  # Avoid division by zero
                x_at_y0 = x1 + (x2 - x1) * (0 - y1) / (y2 - y1)
                if 0 <= x_at_y0 <= width:
                    return True
        
        # Check intersection with bottom boundary (y = height)
        if (y1 <= height and y2 >= height) or (y1 >= height and y2 <= height):
            if y1 != y2:  # Avoid division by zero
                x_at_yheight = x1 + (x2 - x1) * (height - y1) / (y2 - y1)
                if 0 <= x_at_yheight <= width:
                    return True
    
    return False

def is_hexagon_inside_after_rotation(x, y, size, width, height, rotation):
    """Check if a hexagon is at least partially inside the document boundaries after rotation."""
    # Get hexagon points
    points = []
    for i in range(6):
        angle = math.pi / 3 * i
        # Rotate by 30 degrees to get flat top
        angle += math.pi / 6
        px = x + size * math.cos(angle)
        py = y + size * math.sin(angle)
        points.append((px, py))
    
    # Apply rotation to points
    cx, cy = width/2, height/2
    rotated_points = []
    for px, py in points:
        rx, ry = rotate_point(px, py, cx, cy, rotation)
        rotated_points.append((rx, ry))
    
    # Check if any point is inside the document boundaries
    for px, py in rotated_points:
        if 0 <= px <= width and 0 <= py <= height:
            return True
    
    # Check if any edge intersects with the document boundaries
    for i in range(6):
        x1, y1 = rotated_points[i]
        x2, y2 = rotated_points[(i + 1) % 6]
        
        # Check intersection with left boundary (x = 0)
        if (x1 <= 0 and x2 >= 0) or (x1 >= 0 and x2 <= 0):
            if x1 != x2:  # Avoid division by zero
                y_at_x0 = y1 + (y2 - y1) * (0 - x1) / (x2 - x1)
                if 0 <= y_at_x0 <= height:
                    return True
        
        # Check intersection with right boundary (x = width)
        if (x1 <= width and x2 >= width) or (x1 >= width and x2 <= width):
            if x1 != x2:  # Avoid division by zero
                y_at_xwidth = y1 + (y2 - y1) * (width - x1) / (x2 - x1)
                if 0 <= y_at_xwidth <= height:
                    return True
        
        # Check intersection with top boundary (y = 0)
        if (y1 <= 0 and y2 >= 0) or (y1 >= 0 and y2 <= 0):
            if y1 != y2:  # Avoid division by zero
                x_at_y0 = x1 + (x2 - x1) * (0 - y1) / (y2 - y1)
                if 0 <= x_at_y0 <= width:
                    return True
        
        # Check intersection with bottom boundary (y = height)
        if (y1 <= height and y2 >= height) or (y1 >= height and y2 <= height):
            if y1 != y2:  # Avoid division by zero
                x_at_yheight = x1 + (x2 - x1) * (height - y1) / (y2 - y1)
                if 0 <= x_at_yheight <= width:
                    return True
    
    return False

def generate_triangular_tiling(width, height, size, rotation, fill, stroke, stroke_width):
    """Generate a triangular tiling pattern with NO HOLES and NO OVERLAPS."""
    # Calculate dimensions for equilateral triangles
    triangle_height = size * math.sqrt(3) / 2
    
    # Calculate how much we need to expand the grid
    expanded_width, expanded_height = calculate_expanded_dimensions(width, height, rotation)
    
    # Calculate grid dimensions with expansion
    cols = math.ceil(expanded_width / (size/2)) + 2
    rows = math.ceil(expanded_height / triangle_height) + 2
    
    # Starting position to center the pattern
    start_x = (width - (cols-1) * size/2) / 2
    start_y = (height - (rows-1) * triangle_height) / 2
    
    # Generate all tiles first
    tiles = []
    for row in range(rows):
        for col in range(cols):
            # Calculate position
            x = start_x + col * size/2
            y = start_y + row * triangle_height
            
            # Alternate between up and down triangles based on position
            inverted = (row + col) % 2 == 1
            
            # Check if the triangle is at least partially inside the document after rotation
            if is_triangle_inside_after_rotation(x, y, size, inverted, width, height, rotation):
                if inverted:
                    # Down-pointing triangle
                    tiles.append(generate_triangle(x, y, size, True, fill, stroke, stroke_width))
                else:
                    # Up-pointing triangle
                    tiles.append(generate_triangle(x, y, size, False, fill, stroke, stroke_width))
    
    # Create SVG with rotation applied to the entire group
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    if rotation != 0:
        # Add a group with rotation transformation centered in the canvas
        svg_content += f'<g transform="rotate({rotation} {width/2} {height/2})">\n'
        svg_content += '\n'.join(tiles)
        svg_content += '\n</g>\n'
    else:
        # No rotation, just add the tiles directly
        svg_content += '\n'.join(tiles)
    
    svg_content += '\n</svg>'
    return svg_content

def generate_square_tiling(width, height, size, rotation, fill, stroke, stroke_width):
    """Generate a square tiling pattern with NO HOLES and NO OVERLAPS."""
    # Calculate how much we need to expand the grid
    expanded_width, expanded_height = calculate_expanded_dimensions(width, height, rotation)
    
    # Calculate grid dimensions with expansion
    cols = math.ceil(expanded_width / size) + 2
    rows = math.ceil(expanded_height / size) + 2
    
    # Starting position to center the pattern
    start_x = (width - (cols-1) * size) / 2
    start_y = (height - (rows-1) * size) / 2
    
    # Generate all tiles first
    tiles = []
    for row in range(rows):
        for col in range(cols):
            # Calculate position
            x = start_x + col * size + size/2
            y = start_y + row * size + size/2
            
            # Check if the square is at least partially inside the document after rotation
            if is_square_inside_after_rotation(x, y, size, width, height, rotation):
                # Add square
                tiles.append(generate_square(x, y, size, fill, stroke, stroke_width))
    
    # Create SVG with rotation applied to the entire group
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    if rotation != 0:
        # Add a group with rotation transformation centered in the canvas
        svg_content += f'<g transform="rotate({rotation} {width/2} {height/2})">\n'
        svg_content += '\n'.join(tiles)
        svg_content += '\n</g>\n'
    else:
        # No rotation, just add the tiles directly
        svg_content += '\n'.join(tiles)
    
    svg_content += '\n</svg>'
    return svg_content

def generate_hexagonal_tiling(width, height, size, rotation, fill, stroke, stroke_width):
    """Generate a hexagonal tiling pattern with NO HOLES and NO OVERLAPS."""
    # Calculate hexagon dimensions
    hex_radius = size  # Distance from center to vertex
    hex_width = hex_radius * math.sqrt(3)  # Width of hexagon (flat to flat)
    hex_height = hex_radius * 2  # Height of hexagon (point to point)
    
    # Calculate how much we need to expand the grid
    expanded_width, expanded_height = calculate_expanded_dimensions(width, height, rotation)
    
    # Calculate spacing between hexagon centers
    horizontal_spacing = hex_width  # Horizontal distance between adjacent hexagon centers
    vertical_spacing = hex_height * 0.75  # Vertical distance between adjacent hexagon centers
    
    # Calculate grid dimensions with expansion
    cols = math.ceil(expanded_width / horizontal_spacing) + 2
    rows = math.ceil(expanded_height / vertical_spacing) + 2
    
    # Starting position to center the pattern
    start_x = (width - (cols-1) * horizontal_spacing) / 2
    start_y = (height - (rows-1) * vertical_spacing) / 2
    
    # Generate all tiles first
    tiles = []
    for row in range(rows):
        for col in range(cols):
            # Calculate position
            x = start_x + col * horizontal_spacing
            y = start_y + row * vertical_spacing
            
            # Offset every other row by half the horizontal spacing
            if row % 2 == 1:
                x += horizontal_spacing / 2
            
            # Check if the hexagon is at least partially inside the document after rotation
            if is_hexagon_inside_after_rotation(x, y, hex_radius, width, height, rotation):
                # Add hexagon
                tiles.append(generate_hexagon(x, y, hex_radius, fill, stroke, stroke_width))
    
    # Create SVG with rotation applied to the entire group
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    if rotation != 0:
        # Add a group with rotation transformation centered in the canvas
        svg_content += f'<g transform="rotate({rotation} {width/2} {height/2})">\n'
        svg_content += '\n'.join(tiles)
        svg_content += '\n</g>\n'
    else:
        # No rotation, just add the tiles directly
        svg_content += '\n'.join(tiles)
    
    svg_content += '\n</svg>'
    return svg_content

def generate_svg(width, height, corners, tile_size, rotation, fill, stroke, stroke_width):
    """Generate the full SVG content with tiled shapes."""
    if corners == 3:
        return generate_triangular_tiling(width, height, tile_size, rotation, fill, stroke, stroke_width)
    elif corners == 4:
        return generate_square_tiling(width, height, tile_size, rotation, fill, stroke, stroke_width)
    elif corners == 6:
        return generate_hexagonal_tiling(width, height, tile_size, rotation, fill, stroke, stroke_width)
    else:
        raise ValueError("Number of corners must be 3, 4, or 6.")

def main():
    parser = argparse.ArgumentParser(description="Generate an SVG file with tiled shapes.")
    parser.add_argument('--width', type=int, default=1280, help="Width of the SVG canvas (default: 1280)")
    parser.add_argument('--height', type=int, default=720, help="Height of the SVG canvas (default: 720)")
    parser.add_argument('--corners', type=int, choices=[3, 4, 6], required=True, help="Number of corners of the tile (3, 4, or 6)")
    parser.add_argument('--tile_size', type=float, default=50, help="Size of each tile (default: 50)")
    parser.add_argument('--rotation', type=float, default=0, help="Rotation angle in degrees (default: 0)")
    parser.add_argument('--fill', type=str, default="white", help="Fill color of the tiles (default: white)")
    parser.add_argument('--stroke', type=str, default="black", help="Stroke color of the tiles (default: black)")
    parser.add_argument('--stroke_width', type=float, default=1, help="Stroke width of the tiles (default: 1)")
    parser.add_argument('--output', type=str, default="output.svg", help="Output SVG file name (default: output.svg)")
    
    args = parser.parse_args()
    
    svg_content = generate_svg(
        args.width, args.height, args.corners,
        args.tile_size, args.rotation, args.fill, args.stroke, args.stroke_width
    )
    
    with open(args.output, 'w') as f:
        f.write(svg_content)
    
    print(f"SVG file '{args.output}' generated successfully.")

if __name__ == "__main__":
    main()
    
"""
Thank you for your patience and for guiding me through the process. I'm glad I could finally get it right! The key was understanding that you wanted to: 

     Generate a tiled pattern with the specified dimensions
     Rotate the entire pattern as a group
     Completely remove (not just clip) any tiles that would fall outside the document boundaries after rotation
     

The solution involved calculating where each tile would be after rotation and only including those that would be at least partially visible within the document. This ensures a clean result without any visual artifacts or partially clipped tiles. 
"""
