"""
Now merge the scripts and add an option to output RAWR or SVG (default)
"""

import argparse
import math
import json
import uuid

# SVG functions
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

# RAWR functions
def is_shape_visible(vertices, position, rotation, width, height):
    """Check if a shape is at least partially visible within the document boundaries."""
    # Transform vertices to world coordinates
    world_vertices = []
    angle_rad = math.radians(rotation)
    pos_x, pos_y = position
    
    for vx, vy in vertices:
        # Rotate around (0,0)
        rx = vx * math.cos(angle_rad) - vy * math.sin(angle_rad)
        ry = vx * math.sin(angle_rad) + vy * math.cos(angle_rad)
        # Translate to world position
        world_x = rx + pos_x
        world_y = ry + pos_y
        world_vertices.append((world_x, world_y))
    
    # Check if any vertex is inside the document
    for x, y in world_vertices:
        if 0 <= x <= width and 0 <= y <= height:
            return True
    
    # Check if any edge intersects with the document boundaries
    n = len(world_vertices)
    for i in range(n):
        x1, y1 = world_vertices[i]
        x2, y2 = world_vertices[(i+1) % n]
        
        # Check intersection with left boundary (x=0)
        if line_intersects_edge(x1, y1, x2, y2, 'x', 0, 0, height):
            return True
        
        # Check intersection with right boundary (x=width)
        if line_intersects_edge(x1, y1, x2, y2, 'x', width, 0, height):
            return True
        
        # Check intersection with top boundary (y=0)
        if line_intersects_edge(x1, y1, x2, y2, 'y', 0, 0, width):
            return True
        
        # Check intersection with bottom boundary (y=height)
        if line_intersects_edge(x1, y1, x2, y2, 'y', height, 0, width):
            return True
    
    return False

def line_intersects_edge(x1, y1, x2, y2, edge_type, edge_value, min_val, max_val):
    """Check if a line segment intersects with a document boundary edge."""
    if edge_type == 'x':  # Vertical edge (left or right boundary)
        if (x1 <= edge_value and x2 >= edge_value) or (x1 >= edge_value and x2 <= edge_value):
            if x1 == x2:  # Vertical line
                if x1 == edge_value:  # Exactly on the boundary
                    y_min = min(y1, y2)
                    y_max = max(y1, y2)
                    if not (y_max < min_val or y_min > max_val):
                        return True
            else:
                # Calculate y-coordinate at x = edge_value
                t = (edge_value - x1) / (x2 - x1)
                if 0 <= t <= 1:
                    y = y1 + t * (y2 - y1)
                    if min_val <= y <= max_val:
                        return True
    else:  # edge_type == 'y' (top or bottom boundary)
        if (y1 <= edge_value and y2 >= edge_value) or (y1 >= edge_value and y2 <= edge_value):
            if y1 == y2:  # Horizontal line
                if y1 == edge_value:  # Exactly on the boundary
                    x_min = min(x1, x2)
                    x_max = max(x1, x2)
                    if not (x_max < min_val or x_min > max_val):
                        return True
            else:
                # Calculate x-coordinate at y = edge_value
                t = (edge_value - y1) / (y2 - y1)
                if 0 <= t <= 1:
                    x = x1 + t * (x2 - x1)
                    if min_val <= x <= max_val:
                        return True
    return False

def create_triangle_group(name, x, y, rotation, size, fill, stroke, stroke_width, inverted=False):
    """Create a triangle group using Path element with default outline"""
    # Generate UUIDs for group elements
    group_uuid = str(uuid.uuid4())
    fill_uuid = str(uuid.uuid4())
    path_uuid = str(uuid.uuid4())
    stroke_uuid = str(uuid.uuid4())
    
    # Calculate triangle vertices (equilateral triangle)
    height = size * math.sqrt(3) / 2
    
    # Create vertices based on orientation
    if inverted:
        vertices = [
            (0, height/2),              # Bottom point
            (-size/2, -height/2),       # Top left
            (size/2, -height/2)         # Top right
        ]
    else:
        vertices = [
            (0, -height/2),             # Top point
            (-size/2, height/2),        # Bottom left
            (size/2, height/2)          # Bottom right
        ]
    
    # Create vertex objects in the format expected by Glaxnimate
    points = []
    for i, (vx, vy) in enumerate(vertices):
        points.append({
            "pos": {"x": vx, "y": vy},
            "tan_in": {"x": vx, "y": vy},
            "tan_out": {"x": vx, "y": vy},
            "type": 0 if i == 0 else 1  # First point is type 0, others are type 1
        })
    
    # Create the shape group with guaranteed outline
    return {
        "__type__": "Group",
        "auto_orient": False,
        "group_color": "#00000000",
        "locked": False,
        "name": name,
        "opacity": {"value": 1},
        "shapes": [
            {
                "__type__": "Fill",
                "color": {"value": fill},
                "fill_rule": "NonZero",
                "group_color": "#00000000",
                "locked": False,
                "name": "Fill",
                "opacity": {"value": 1},
                "use": None,
                "uuid": fill_uuid,
                "visible": True
            },
            {
                "__type__": "Path",
                "closed": True,
                "group_color": "#00000000",
                "locked": False,
                "name": "Path",
                "reversed": False,
                "shape": {
                    "value": {
                        "closed": True,
                        "points": points
                    }
                },
                "uuid": path_uuid,
                "visible": True
            },
            {
                "__type__": "Stroke",
                "cap": "ButtCap",
                "color": {"value": stroke},
                "group_color": "#00000000",
                "join": "MiterJoin",
                "locked": False,
                "miter_limit": 4,
                "name": "Stroke",
                "opacity": {"value": 1},
                "use": None,
                "uuid": stroke_uuid,
                "visible": True,
                "width": {"value": stroke_width}
            }
        ],
        "transform": {
            "__type__": "Transform",
            "anchor_point": {"value": {"x": 0, "y": 0}},
            "position": {"value": {"x": x, "y": y}},
            "rotation": {"value": rotation},
            "scale": {"value": {"x": 1, "y": 1}}
        },
        "uuid": group_uuid,
        "visible": True
    }

def create_square_group(name, x, y, rotation, size, fill, stroke, stroke_width):
    """Create a square group using Rect element with default outline"""
    # Generate UUIDs for group elements
    group_uuid = str(uuid.uuid4())
    fill_uuid = str(uuid.uuid4())
    rect_uuid = str(uuid.uuid4())
    stroke_uuid = str(uuid.uuid4())
    
    # Create the shape group with guaranteed outline
    return {
        "__type__": "Group",
        "auto_orient": False,
        "group_color": "#00000000",
        "locked": False,
        "name": name,
        "opacity": {"value": 1},
        "shapes": [
            {
                "__type__": "Fill",
                "color": {"value": fill},
                "fill_rule": "NonZero",
                "group_color": "#00000000",
                "locked": False,
                "name": "Fill",
                "opacity": {"value": 1},
                "use": None,
                "uuid": fill_uuid,
                "visible": True
            },
            {
                "__type__": "Rect",
                "group_color": "#00000000",
                "locked": False,
                "name": "Rectangle",
                "position": {"value": {"x": -size/2, "y": -size/2}},
                "reversed": False,
                "rounded": {"value": 0},
                "size": {"value": {"height": size, "width": size}},
                "uuid": rect_uuid,
                "visible": True
            },
            {
                "__type__": "Stroke",
                "cap": "ButtCap",
                "color": {"value": stroke},
                "group_color": "#00000000",
                "join": "MiterJoin",
                "locked": False,
                "miter_limit": 4,
                "name": "Stroke",
                "opacity": {"value": 1},
                "use": None,
                "uuid": stroke_uuid,
                "visible": True,
                "width": {"value": stroke_width}
            }
        ],
        "transform": {
            "__type__": "Transform",
            "anchor_point": {"value": {"x": 0, "y": 0}},
            "position": {"value": {"x": x, "y": y}},
            "rotation": {"value": rotation},
            "scale": {"value": {"x": 1, "y": 1}}
        },
        "uuid": group_uuid,
        "visible": True
    }

def create_hexagon_group(name, x, y, rotation, radius, fill, stroke, stroke_width):
    """Create a hexagon group using PolyStar element with default outline"""
    # Generate UUIDs for group elements
    group_uuid = str(uuid.uuid4())
    fill_uuid = str(uuid.uuid4())
    polystar_uuid = str(uuid.uuid4())
    stroke_uuid = str(uuid.uuid4())
    
    # Create the shape group with guaranteed outline
    return {
        "__type__": "Group",
        "auto_orient": False,
        "group_color": "#00000000",
        "locked": False,
        "name": name,
        "opacity": {"value": 1},
        "shapes": [
            {
                "__type__": "Fill",
                "color": {"value": fill},
                "fill_rule": "NonZero",
                "group_color": "#00000000",
                "locked": False,
                "name": "Fill",
                "opacity": {"value": 1},
                "use": None,
                "uuid": fill_uuid,
                "visible": True
            },
            {
                "__type__": "PolyStar",
                "angle": {"value": 0},
                "group_color": "#00000000",
                "inner_radius": {"value": radius},
                "inner_roundness": {"value": 0},
                "locked": False,
                "name": "PolyStar",
                "outer_radius": {"value": radius},
                "outer_roundness": {"value": 0},
                "points": {"value": 6},
                "position": {"value": {"x": 0, "y": 0}},
                "reversed": False,
                "type": "Polygon",
                "uuid": polystar_uuid,
                "visible": True
            },
            {
                "__type__": "Stroke",
                "cap": "ButtCap",
                "color": {"value": stroke},
                "group_color": "#00000000",
                "join": "MiterJoin",
                "locked": False,
                "miter_limit": 4,
                "name": "Stroke",
                "opacity": {"value": 1},
                "use": None,
                "uuid": stroke_uuid,
                "visible": True,
                "width": {"value": stroke_width}
            }
        ],
        "transform": {
            "__type__": "Transform",
            "anchor_point": {"value": {"x": 0, "y": 0}},
            "position": {"value": {"x": x, "y": y}},
            "rotation": {"value": rotation},
            "scale": {"value": {"x": 1, "y": 1}}
        },
        "uuid": group_uuid,
        "visible": True
    }

def generate_rawr(width, height, corners, tile_size, rotation, fill, stroke, stroke_width):
    """Generate a RAWR file with tiled shapes"""
    # Generate UUIDs for top-level elements
    assets_uuid = str(uuid.uuid4())
    colors_uuid = str(uuid.uuid4())
    compositions_uuid = str(uuid.uuid4())
    composition_uuid = str(uuid.uuid4())
    fonts_uuid = str(uuid.uuid4())
    gradient_colors_uuid = str(uuid.uuid4())
    gradients_uuid = str(uuid.uuid4())
    images_uuid = str(uuid.uuid4())
    
    # Generate the grid of shapes
    shapes = []
    shape_index = 0
    
    if corners == 3:  # Triangular tiling
        # Calculate dimensions for equilateral triangles
        triangle_height = tile_size * math.sqrt(3) / 2
        horizontal_spacing = tile_size / 2
        vertical_spacing = triangle_height
        
        # Calculate grid dimensions with margin for rotation
        rows = math.ceil(height / vertical_spacing) + 4
        cols = math.ceil(width / horizontal_spacing) + 4
        
        # Starting position to center the pattern
        start_x = (width - (cols-1) * horizontal_spacing) / 2
        start_y = (height - (rows-1) * vertical_spacing) / 2
        
        for row in range(rows):
            for col in range(cols):
                # Calculate position
                x = start_x + col * horizontal_spacing
                y = start_y + row * vertical_spacing
                
                # Offset every other row
                if row % 2 == 1:
                    x += horizontal_spacing / 2
                
                # Alternate between up and down triangles
                inverted = (row + col) % 2 == 1
                
                # Create triangle vertices
                if inverted:
                    vertices = [
                        (0, triangle_height/2),              # Bottom point
                        (-tile_size/2, -triangle_height/2),  # Top left
                        (tile_size/2, -triangle_height/2)     # Top right
                    ]
                else:
                    vertices = [
                        (0, -triangle_height/2),             # Top point
                        (-tile_size/2, triangle_height/2),   # Bottom left
                        (tile_size/2, triangle_height/2)     # Bottom right
                    ]
                
                # Check if the shape is visible within the document
                if is_shape_visible(vertices, (x, y), rotation, width, height):
                    # Create the shape group
                    shape_group = create_triangle_group(
                        f"Triangle {shape_index}", x, y, rotation, 
                        tile_size, fill, stroke, stroke_width, inverted
                    )
                    shapes.append(shape_group)
                    shape_index += 1
    
    elif corners == 4:  # Square tiling
        # Calculate grid dimensions with margin for rotation
        rows = math.ceil(height / tile_size) + 4
        cols = math.ceil(width / tile_size) + 4
        
        # Starting position to center the pattern
        start_x = (width - (cols-1) * tile_size) / 2
        start_y = (height - (rows-1) * tile_size) / 2
        
        for row in range(rows):
            for col in range(cols):
                # Calculate position
                x = start_x + col * tile_size + tile_size/2
                y = start_y + row * tile_size + tile_size/2
                
                # Create square vertices
                vertices = [
                    (-tile_size/2, -tile_size/2),  # Top left
                    (tile_size/2, -tile_size/2),   # Top right
                    (tile_size/2, tile_size/2),    # Bottom right
                    (-tile_size/2, tile_size/2)    # Bottom left
                ]
                
                # Check if the shape is visible within the document
                if is_shape_visible(vertices, (x, y), rotation, width, height):
                    # Create the shape group
                    shape_group = create_square_group(
                        f"Square {shape_index}", x, y, rotation, 
                        tile_size, fill, stroke, stroke_width
                    )
                    shapes.append(shape_group)
                    shape_index += 1
    
    elif corners == 6:  # Hexagonal tiling
        # Calculate hexagon dimensions
        hex_radius = tile_size
        hex_width = hex_radius * math.sqrt(3)  # Width of hexagon (flat to flat)
        hex_height = hex_radius * 2  # Height of hexagon (point to point)
        
        # Calculate spacing between hexagon centers
        horizontal_spacing = hex_width
        vertical_spacing = hex_height * 0.75
        
        # Calculate grid dimensions with margin for rotation
        rows = math.ceil(height / vertical_spacing) + 4
        cols = math.ceil(width / horizontal_spacing) + 4
        
        # Starting position to center the pattern
        start_x = (width - (cols-1) * horizontal_spacing) / 2
        start_y = (height - (rows-1) * vertical_spacing) / 2
        
        for row in range(rows):
            for col in range(cols):
                # Calculate position
                x = start_x + col * horizontal_spacing
                y = start_y + row * vertical_spacing
                
                # Offset every other row
                if row % 2 == 1:
                    x += horizontal_spacing / 2
                
                # Create hexagon vertices
                vertices = []
                for i in range(6):
                    angle = math.pi / 3 * i  # 60 degrees in radians
                    # Rotate by 30 degrees to get flat top
                    angle += math.pi / 6
                    px = hex_radius * math.cos(angle)
                    py = hex_radius * math.sin(angle)
                    vertices.append((px, py))
                
                # Check if the shape is visible within the document
                if is_shape_visible(vertices, (x, y), rotation, width, height):
                    # Create the shape group
                    shape_group = create_hexagon_group(
                        f"Hexagon {shape_index}", x, y, rotation, 
                        hex_radius, fill, stroke, stroke_width
                    )
                    shapes.append(shape_group)
                    shape_index += 1
    
    else:
        raise ValueError("Number of corners must be 3, 4, or 6.")
    
    # Build the composition
    composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": 180
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": height,
        "locked": False,
        "name": "Composition",
        "shapes": shapes,
        "uuid": composition_uuid,
        "visible": True,
        "width": width
    }
    
    # Build the assets
    assets = {
        "__type__": "Assets",
        "colors": {
            "__type__": "NamedColorList",
            "name": "",
            "uuid": colors_uuid,
            "values": []
        },
        "compositions": {
            "__type__": "CompositionList",
            "name": "",
            "uuid": compositions_uuid,
            "values": [composition]
        },
        "fonts": {
            "__type__": "FontList",
            "name": "",
            "uuid": fonts_uuid,
            "values": []
        },
        "gradient_colors": {
            "__type__": "GradientColorsList",
            "name": "",
            "uuid": gradient_colors_uuid,
            "values": []
        },
        "gradients": {
            "__type__": "GradientList",
            "name": "",
            "uuid": gradients_uuid,
            "values": []
        },
        "images": {
            "__type__": "BitmapList",
            "name": "",
            "uuid": images_uuid,
            "values": []
        },
        "name": "",
        "uuid": assets_uuid
    }
    
    # Build the RAWR structure
    rawr_dict = {
        "assets": assets,
        "format": {
            "format_version": 8,
            "generator": "Glaxnimate",
            "generator_version": "0.5.4+appimage-dc26f367"
        },
        "info": {
            "author": "",
            "description": "",
            "keywords": []
        },
        "metadata": {}
    }
    
    return json.dumps(rawr_dict, indent=4)

def main():
    parser = argparse.ArgumentParser(description="Generate tiled shapes in SVG or RAWR format.")
    parser.add_argument('--width', type=int, default=1280, help="Width of the canvas (default: 1280)")
    parser.add_argument('--height', type=int, default=720, help="Height of the canvas (default: 720)")
    parser.add_argument('--corners', type=int, choices=[3, 4, 6], required=True, help="Number of corners of the tile (3, 4, or 6)")
    parser.add_argument('--tile_size', type=float, default=50, help="Size of each tile (default: 50)")
    parser.add_argument('--rotation', type=float, default=0, help="Rotation angle in degrees (default: 0)")
    parser.add_argument('--fill', type=str, default="white", help="Fill color of the tiles (default: white)")
    parser.add_argument('--stroke', type=str, default="black", help="Stroke color of the tiles (default: black)")
    parser.add_argument('--stroke_width', type=float, default=1, help="Stroke width of the tiles (default: 1)")
    parser.add_argument('--output', type=str, default="output", help="Output file name without extension (default: output)")
    parser.add_argument('--format', type=str, choices=['svg', 'rawr'], default='svg', help="Output format (svg or rawr, default: svg)")
    
    args = parser.parse_args()
    
    # Set the output filename with the appropriate extension
    output_file = f"{args.output}.{args.format}"
    
    if args.format == 'svg':
        svg_content = generate_svg(
            args.width, args.height, args.corners,
            args.tile_size, args.rotation, args.fill, args.stroke, args.stroke_width
        )
        
        with open(output_file, 'w') as f:
            f.write(svg_content)
        
        print(f"SVG file '{output_file}' generated successfully.")
    
    elif args.format == 'rawr':
        rawr_content = generate_rawr(
            args.width, args.height, args.corners,
            args.tile_size, args.rotation, args.fill, args.stroke, args.stroke_width
        )
        
        with open(output_file, 'w') as f:
            f.write(rawr_content)
        
        print(f"RAWR file '{output_file}' generated successfully.")

if __name__ == "__main__":
    main()
