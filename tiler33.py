"""
I want to correct this code, tiles with rotation should still fill the screen

python tiler33.py -c 4 -r 45 -F rawr -a move-down
"""
import argparse
import math
import json
import uuid

ANIMATION_MAPPING = {
    'scale': 'scale',
    'opacity': 'opacity',
    'move': 'move',
}

# Mapping from abbreviations to full direction names
DIRECTION_MAPPING = {
    'north': 'north',
    'n': 'north',
    'u': 'north',
    'up': 'north',

    'south': 'south',
    's': 'south',
    'd': 'south',
    'down': 'south',

    'west': 'west',
    'w': 'west',
    'l': 'west',
    'left': 'west',

    'east': 'east',
    'e': 'east',
    'r': 'east',
    'right': 'right',
    
    'northeast': 'northeast',
    'ne': 'northeast',
    'ur': 'northeast',
    'upright': 'northeast',

    'northwest': 'northwest',
    'nw': 'northwest',
    'ul': 'northwest',
    'upleft': 'northwest',

    'southeast': 'southeast',
    'se': 'southeast',
    'dr': 'southeast',
    'downright': 'southeast',

    'southwest': 'southwest',
    'sw': 'southwest',
    'dl': 'southwest',
    'downleft': 'southwest',
}

def normalize_animation_type(animation_type):
    """Normalize animation type by converting abbreviations to full direction names."""
    if animation_type is None:
        return None
    
    # If it's a non-directional animation or a move animation, return as is
    if animation_type in ['scale', 'opacity']:
        return animation_type
    
    # Check if it's a directional animation (scale-<direction> or opacity-<direction>)
    parts = animation_type.split('-', 1)
    if len(parts) == 2:
        prefix, direction = parts
        if prefix in ANIMATION_MAPPING and direction in DIRECTION_MAPPING:
            return f"{prefix}-{DIRECTION_MAPPING[direction]}"
    
    # If it doesn't match any pattern, return the original
    return animation_type

def generate_animation_choices():
    """Generate all valid animation choices including abbreviations."""
    choices = ["scale", "opacity","move"]
    
    # Add directional scale and opacity animations with abbreviations
    for direction, abbrevs in [
        ('north', ['n', 'u', 'up']),
        ('south', ['s', 'd', 'down']),
        ('west', ['w', 'l', 'left']),
        ('east', ['e', 'r', 'right']),
        ('northeast', ['ne', 'ur', 'upright']),
        ('northwest', ['nw', 'ul', 'upleft']),
        ('southeast', ['se', 'dr', 'downright']),
        ('southwest', ['sw', 'dl', 'downleft'])
    ]:
        for prefix in ['scale', 'opacity','move']:
            choices.append(f"{prefix}-{direction}")
            for ab in abbrevs:
                choices.append(f"{prefix}-{ab}")
        
    return choices

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

def get_scale_keyframes(animate_enabled, animation_type=None, row=0, col=0, rows=1, cols=1, duration=1.0):
    """Get the scale keyframes for RAWR format."""
    if not animate_enabled:
        return {"value": {"x": 1, "y": 1}}
    
    # Calculate total frames (60 fps)
    total_frames = int(duration * 60)
    half_frames = total_frames // 2
    
    if animation_type == "scale" or animation_type is None:
        # Uniform scaling
        return {
            "keyframes": [
                {
                    "after": {"x": 1, "y": 1},
                    "before": {"x": 0, "y": 0},
                    "time": 0,
                    "value": {"x": 0, "y": 0}
                },
                {
                    "after": {"x": 1, "y": 1},
                    "before": {"x": 0, "y": 0},
                    "time": half_frames,
                    "value": {"x": 1, "y": 1}
                },
                {
                    "after": {"x": 1, "y": 1},
                    "before": {"x": 0, "y": 0},
                    "time": total_frames,
                    "value": {"x": 0, "y": 0}
                }
            ]
        }
    elif animation_type.startswith("scale-"):
        # Directional scaling
        # Calculate normalized position (0 to 1) based on direction
        if animation_type == "scale-north":
            # South to north: higher row index = lower position value
            position = (rows - 1 - row) / (rows - 1) if rows > 1 else 0
        elif animation_type == "scale-south":
            # North to south: higher row index = higher position value
            position = row / (rows - 1) if rows > 1 else 0
        elif animation_type == "scale-east":
            # West to east: higher col index = higher position value
            position = col / (cols - 1) if cols > 1 else 0
        elif animation_type == "scale-west":
            # East to west: higher col index = lower position value
            position = (cols - 1 - col) / (cols - 1) if cols > 1 else 0
        elif animation_type == "scale-northeast":
            # Southwest to northeast: higher row+col = higher position value
            position = (row + col) / (rows - 1 + cols - 1) if (rows > 1 or cols > 1) else 0
        elif animation_type == "scale-northwest":
            # Southeast to northwest: higher row + (cols-1-col) = higher position value
            position = (row + (cols - 1 - col)) / (rows - 1 + cols - 1) if (rows > 1 or cols > 1) else 0
        elif animation_type == "scale-southeast":
            # Northwest to southeast: higher (rows-1-row) + col = higher position value
            position = ((rows - 1 - row) + col) / (rows - 1 + cols - 1) if (rows > 1 or cols > 1) else 0
        elif animation_type == "scale-southwest":
            # Northeast to southwest: higher (rows-1-row) + (cols-1-col) = higher position value
            position = ((rows - 1 - row) + (cols - 1 - col)) / (rows - 1 + cols - 1) if (rows > 1 or cols > 1) else 0
        else:
            position = 0
        
        # Calculate keyTimes and values
        # Animation timeline:
        # 0.0: start at 0
        # position * 0.5: start scaling up
        # 0.5: reach 100%
        # 0.5 + position * 0.5: start scaling down
        # 1.0: back to 0
        
        inflation_start = int(position * half_frames)
        deflation_start = half_frames + int(position * half_frames)
        
        return {
            "keyframes": [
                {
                    "after": {"x": 1, "y": 1},
                    "before": {"x": 0, "y": 0},
                    "time": 0,
                    "value": {"x": 0, "y": 0}
                },
                {
                    "after": {"x": 1, "y": 1},
                    "before": {"x": 0, "y": 0},
                    "time": inflation_start,
                    "value": {"x": 0, "y": 0}
                },
                {
                    "after": {"x": 1, "y": 1},
                    "before": {"x": 0, "y": 0},
                    "time": half_frames,
                    "value": {"x": 1, "y": 1}
                },
                {
                    "after": {"x": 1, "y": 1},
                    "before": {"x": 0, "y": 0},
                    "time": deflation_start,
                    "value": {"x": 1, "y": 1}
                },
                {
                    "after": {"x": 1, "y": 1},
                    "before": {"x": 0, "y": 0},
                    "time": total_frames,
                    "value": {"x": 0, "y": 0}
                }
            ]
        }
    else:
        # For move or opacity animations, we don't scale, so return a constant scale of 1
        return {"value": {"x": 1, "y": 1}}

def get_move_keyframes(animate_enabled, animation_type=None, width=0, height=0, duration=1.0):
    """Get the position keyframes for RAWR format move animations of the entire grid."""
    if not animate_enabled or not animation_type or not animation_type.startswith("move-"):
        return {"value": {"x": width/2, "y": height/2}}  # Center position
    
    # Calculate the starting and ending positions based on direction
    # These are the absolute positions
    center_x, center_y = width/2, height/2
    
    if animation_type == "move-north":
        # Start from below the canvas, move up (north)
        start_x, start_y = center_x, center_y + height * 2
        end_x, end_y = center_x, center_y - height * 2
    elif animation_type == "move-south":
        # Start from above the canvas, move down (south)
        start_x, start_y = center_x, center_y - height * 2
        end_x, end_y = center_x, center_y + height * 2
    elif animation_type == "move-east":
        # Start from the left of the canvas, move right (east)
        start_x, start_y = center_x - width * 2, center_y
        end_x, end_y = center_x + width * 2, center_y
    elif animation_type == "move-west":
        # Start from the right of the canvas, move left (west)
        start_x, start_y = center_x + width * 2, center_y
        end_x, end_y = center_x - width * 2, center_y
    elif animation_type == "move-northeast":
        # Start from southwest, move to northeast
        start_x, start_y = center_x - width * 2, center_y + height * 2
        end_x, end_y = center_x + width * 2, center_y - height * 2
    elif animation_type == "move-northwest":
        # Start from southeast, move to northwest
        start_x, start_y = center_x + width * 2, center_y + height * 2
        end_x, end_y = center_x - width * 2, center_y - height * 2
    elif animation_type == "move-southeast":
        # Start from northwest, move to southeast
        start_x, start_y = center_x - width * 2, center_y - height * 2
        end_x, end_y = center_x + width * 2, center_y + height * 2
    elif animation_type == "move-southwest":
        # Start from northeast, move to southwest
        start_x, start_y = center_x + width * 2, center_y - height * 2
        end_x, end_y = center_x - width * 2, center_y + height * 2
    else:
        # Default: center position
        start_x, start_y = center_x, center_y
        end_x, end_y = center_x, center_y
    
    # Calculate total frames (60 fps)
    total_frames = int(duration * 60)
    half_frames = total_frames // 2
    
    # Calculate keyframes
    # Animation timeline:
    # 0.0: start at off-screen position
    # 0.5: reach final position (center)
    # 1.0: continue to off-screen position in the movement direction
    
    return {
        "keyframes": [
            {
                "after": {"x": 0, "y": 0},
                "before": {"x": 0, "y": 0},
                "time": 0,
                "value": {"x": start_x, "y": start_y}
            },
            {
                "after": {"x": 0, "y": 0},
                "before": {"x": 0, "y": 0},
                "time": half_frames,
                "value": {"x": center_x, "y": center_y}  # Center position
            },
            {
                "after": {"x": 0, "y": 0},
                "before": {"x": 0, "y": 0},
                "time": total_frames,
                "value": {"x": end_x, "y": end_y}
            }
        ]
    }

def generate_triangular_tiling_svg(width, height, size, rotation, fill, stroke, stroke_width, animate=None, duration=1.0):
    """Generate an SVG string with a triangular tiling pattern using <use> elements."""
    # Determine if animation is enabled and get the animation type
    animate_enabled = animate is not None
    animation_type = normalize_animation_type(animate) if animate_enabled else None
    
    # Calculate dimensions for equilateral triangles
    triangle_height = size * math.sqrt(3) / 2
    
    # Calculate exact expansion needed based on rotation
    angle_rad = math.radians(rotation)
    # Calculate the maximum expansion needed in any direction
    # For 45 degrees, we need more expansion than for other angles
    expansion_factor = 1.0 + max(abs(math.cos(angle_rad)), abs(math.sin(angle_rad))) * 1.5
    
    expanded_width = width * expansion_factor
    expanded_height = height * expansion_factor
    
    # Calculate grid dimensions with proper spacing
    horizontal_spacing = size / 2
    vertical_spacing = triangle_height
    
    # Calculate how many tiles we need to cover the expanded area
    # Add more extra tiles to ensure coverage at 45 degrees
    cols = math.ceil(expanded_width / horizontal_spacing) + 12  # More extra tiles
    rows = math.ceil(expanded_height / vertical_spacing) + 12   # More extra tiles
    
    # Starting position to center the pattern
    start_x = (expanded_width - (cols-1) * horizontal_spacing) / 2
    start_y = (expanded_height - (rows-1) * vertical_spacing) / 2
    
    # Create SVG with proper transformations
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Create a clipping path
    svg_content += f'<defs>\n'
    svg_content += f'<clipPath id="canvasClip">\n'
    svg_content += f'<rect x="0" y="0" width="{width}" height="{height}"/>\n'
    svg_content += f'</clipPath>\n'
    
    # Define tile shapes in the defs section with center at (0,0)
    # Upright triangle
    upright_points = [
        (0, -triangle_height/2),              # Top point
        (-size/2, triangle_height/2),         # Bottom left
        (size/2, triangle_height/2)          # Bottom right
    ]
    upright_points_str = ' '.join([f"{p[0]},{p[1]}" for p in upright_points])
    svg_content += f'<polygon id="upright-triangle" points="{upright_points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>\n'
    
    # Inverted triangle
    inverted_points = [
        (0, triangle_height/2),              # Bottom point
        (-size/2, -triangle_height/2),       # Top left
        (size/2, -triangle_height/2)         # Top right
    ]
    inverted_points_str = ' '.join([f"{p[0]},{p[1]}" for p in inverted_points])
    svg_content += f'<polygon id="inverted-triangle" points="{inverted_points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>\n'
    
    svg_content += f'</defs>\n'
    
    # Apply transformations with proper centering
    svg_content += f'<g clip-path="url(#canvasClip)">\n'
    
    # Add move animation to the entire grid if needed
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        move_values = f"0,{height * 2}; 0,0; 0,-{height * 2}" if animation_type == "move-north" else \
                     f"0,-{height * 2}; 0,0; 0,{height * 2}" if animation_type == "move-south" else \
                     f"-{width * 2},0; 0,0; {width * 2},0" if animation_type == "move-east" else \
                     f"{width * 2},0; 0,0; -{width * 2},0" if animation_type == "move-west" else \
                     f"-{width * 2},{height * 2}; 0,0; {width * 2},-{height * 2}" if animation_type == "move-northeast" else \
                     f"{width * 2},{height * 2}; 0,0; -{width * 2},-{height * 2}" if animation_type == "move-northwest" else \
                     f"-{width * 2},-{height * 2}; 0,0; {width * 2},{height * 2}" if animation_type == "move-southeast" else \
                     f"{width * 2},-{height * 2}; 0,0; -{width * 2},{height * 2}"
                     
        svg_content += f'<g>\n'
        svg_content += f'<animateTransform attributeName="transform" type="translate" '
        svg_content += f'values="{move_values}" dur="{duration}s" repeatCount="indefinite"/>\n'
    
    svg_content += f'<g transform="translate({width/2}, {height/2})">\n'
    svg_content += f'<g transform="rotate({rotation})">\n'
    svg_content += f'<g transform="translate({-expanded_width/2}, {-expanded_height/2})">\n'
    
    # Generate all tiles using <use> elements
    for row in range(rows):
        for col in range(cols):
            # Calculate position (center of the triangle)
            x = start_x + col * horizontal_spacing
            y = start_y + row * vertical_spacing
            
            # Alternate between upright and inverted triangles
            inverted = (row + col) % 2 == 1
            
            # Use the appropriate triangle
            triangle_id = "inverted-triangle" if inverted else "upright-triangle"
            
            # Calculate the position in the canvas coordinate system
            canvas_x = x - expanded_width/2 + width/2
            canvas_y = y - expanded_height/2 + height/2
            
            # Apply rotation to get the final position in the canvas
            final_x, final_y = rotate_point(canvas_x, canvas_y, width/2, height/2, rotation)
            
            # Calculate the row and column in the viewer's coordinate system
            viewer_row = final_y / vertical_spacing
            viewer_col = final_x / horizontal_spacing
            
            if animate_enabled and animation_type and (animation_type.startswith("scale") or animation_type == "scale"):
                # Add scale animation to the triangle with proper centering
                svg_content += f'<g transform="translate({x},{y})">\n'
                
                if animation_type == "scale":
                    # Uniform scaling
                    svg_content += f'<animateTransform attributeName="transform" type="scale" '
                    svg_content += f'values="0;1;0" dur="{duration}s" repeatCount="indefinite" additive="sum"/>\n'
                else:
                    # Directional scaling
                    position = 0
                    if animation_type == "scale-north":
                        position = (rows - 1 - viewer_row) / rows if rows > 0 else 0
                    elif animation_type == "scale-south":
                        position = viewer_row / rows if rows > 0 else 0
                    elif animation_type == "scale-east":
                        position = viewer_col / cols if cols > 0 else 0
                    elif animation_type == "scale-west":
                        position = (cols - 1 - viewer_col) / cols if cols > 0 else 0
                    elif animation_type == "scale-northeast":
                        position = (viewer_row + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                    elif animation_type == "scale-northwest":
                        position = (viewer_row + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                    elif animation_type == "scale-southeast":
                        position = ((rows - 1 - viewer_row) + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                    elif animation_type == "scale-southwest":
                                                position = ((rows - 1 - viewer_row) + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                    
                    inflation_start = position * 0.5
                    deflation_start = 0.5 + position * 0.5
                    
                    key_times = f"0; {inflation_start}; 0.5; {deflation_start}; 1"
                    values = "0; 0; 1; 1; 0"
                    
                    svg_content += f'<animateTransform attributeName="transform" type="scale" '
                    svg_content += f'keyTimes="{key_times}" values="{values}" dur="{duration}s" repeatCount="indefinite" additive="sum"/>\n'
                
                svg_content += f'<use href="#{triangle_id}"/>\n'
                svg_content += f'</g>\n'
            elif animate_enabled and animation_type and (animation_type.startswith("opacity") or animation_type == "opacity"):
                # Add opacity animation to the triangle for clear-fill-clear effect
                svg_content += f'<g transform="translate({x},{y})">\n'
                
                # Calculate normalized position (0 to 1) based on direction
                position = 0
                
                if animation_type == "opacity":
                    # Uniform opacity animation
                    svg_content += f'<animate attributeName="opacity" '
                    svg_content += f'values="0;1;0" dur="{duration}s" repeatCount="indefinite"/>\n'
                else:
                    # Directional opacity animation
                    if animation_type == "opacity-north":
                        position = (rows - 1 - viewer_row) / rows if rows > 0 else 0
                    elif animation_type == "opacity-south":
                        position = viewer_row / rows if rows > 0 else 0
                    elif animation_type == "opacity-east":
                        position = viewer_col / cols if cols > 0 else 0
                    elif animation_type == "opacity-west":
                        position = (cols - 1 - viewer_col) / cols if cols > 0 else 0
                    elif animation_type == "opacity-northeast":
                        position = (viewer_row + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                    elif animation_type == "opacity-northwest":
                        position = (viewer_row + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                    elif animation_type == "opacity-southeast":
                        position = ((rows - 1 - viewer_row) + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                    elif animation_type == "opacity-southwest":
                        position = ((rows - 1 - viewer_row) + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                    
                    # Calculate keyTimes and values
                    inflation_start = position * 0.5
                    deflation_start = 0.5 + position * 0.5
                    
                    key_times = f"0; {inflation_start}; 0.5; {deflation_start}; 1"
                    values = "0; 0; 1; 1; 0"
                    
                    svg_content += f'<animate attributeName="opacity" '
                    svg_content += f'keyTimes="{key_times}" values="{values}" dur="{duration}s" repeatCount="indefinite"/>\n'
                
                svg_content += f'<use href="#{triangle_id}"/>\n'
                svg_content += f'</g>\n'
            else:
                svg_content += f'<g transform="translate({x},{y})">\n'
                svg_content += f'<use href="#{triangle_id}"/>\n'
                svg_content += f'</g>\n'
    
    svg_content += '\n</g>\n'
    svg_content += '\n</g>\n'
    svg_content += '\n</g>\n'
    
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        svg_content += '\n</g>\n'
    
    svg_content += '\n</g>\n'
    svg_content += '\n</svg>'
    return svg_content

def generate_square_tiling(width, height, size, rotation, fill, stroke, stroke_width, animate=None, duration=1.0):
    """Generate a square tiling pattern using <use> elements."""
    # Determine if animation is enabled and get the animation type
    animate_enabled = animate is not None
    animation_type = normalize_animation_type(animate) if animate_enabled else None
    
    # Calculate how much we need to expand the grid
    expanded_width, expanded_height = calculate_expanded_dimensions(width, height, rotation)
    
    # Calculate grid dimensions with expansion
    cols = math.ceil(expanded_width / size) + 2
    rows = math.ceil(expanded_height / size) + 2
    
    # Starting position to center the pattern
    start_x = (width - (cols-1) * size) / 2
    start_y = (height - (rows-1) * size) / 2
    
    # Create SVG with proper transformations
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Define tile shape in the defs section with center at (0,0)
    svg_content += f'<defs>\n'
    half_size = size / 2
    square_points = [
        (-half_size, -half_size),  # Top left
        (half_size, -half_size),   # Top right
        (half_size, half_size),    # Bottom right
        (-half_size, half_size)    # Bottom left
    ]
    square_points_str = ' '.join([f"{p[0]},{p[1]}" for p in square_points])
    svg_content += f'<polygon id="square" points="{square_points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>\n'
    svg_content += f'</defs>\n'
    
    # Apply transformations
    svg_content += f'<g>\n'
    
    # Add move animation to the entire grid if needed
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        move_values = f"0,{height * 2}; 0,0; 0,-{height * 2}" if animation_type == "move-north" else \
                     f"0,-{height * 2}; 0,0; 0,{height * 2}" if animation_type == "move-south" else \
                     f"-{width * 2},0; 0,0; {width * 2},0" if animation_type == "move-east" else \
                     f"{width * 2},0; 0,0; -{width * 2},0" if animation_type == "move-west" else \
                     f"-{width * 2},{height * 2}; 0,0; {width * 2},-{height * 2}" if animation_type == "move-northeast" else \
                     f"{width * 2},{height * 2}; 0,0; -{width * 2},-{height * 2}" if animation_type == "move-northwest" else \
                     f"-{width * 2},-{height * 2}; 0,0; {width * 2},{height * 2}" if animation_type == "move-southeast" else \
                     f"{width * 2},-{height * 2}; 0,0; -{width * 2},{height * 2}"
                     
        svg_content += f'<g>\n'
        svg_content += f'<animateTransform attributeName="transform" type="translate" '
        svg_content += f'values="{move_values}" dur="{duration}s" repeatCount="indefinite"/>\n'
    
    if rotation != 0:
        # Add a group with rotation transformation centered in the canvas
        svg_content += f'<g transform="rotate({rotation} {width/2} {height/2})">\n'
    
    # Generate all tiles using <use> elements
    for row in range(rows):
        for col in range(cols):
            # Calculate position (center of the square)
            x = start_x + col * size + size/2
            y = start_y + row * size + size/2
            
            # Check if the square is at least partially inside the document after rotation
            if is_square_inside_after_rotation(x, y, size, width, height, rotation):
                # Calculate the position in the canvas coordinate system
                canvas_x = x
                canvas_y = y
                
                # Apply rotation to get the final position in the canvas
                final_x, final_y = rotate_point(canvas_x, canvas_y, width/2, height/2, rotation)
                
                # Calculate the row and column in the viewer's coordinate system
                viewer_row = final_y / size
                viewer_col = final_x / size
                
                if animate_enabled and animation_type and (animation_type.startswith("scale") or animation_type == "scale"):
                    # Add scale animation to the square with proper centering
                    svg_content += f'<g transform="translate({x},{y})">\n'
                    
                    if animation_type == "scale":
                        # Uniform scaling
                        svg_content += f'<animateTransform attributeName="transform" type="scale" '
                        svg_content += f'values="0;1;0" dur="{duration}s" repeatCount="indefinite" additive="sum"/>\n'
                    else:
                        # Directional scaling
                        position = 0
                        if animation_type == "scale-north":
                            position = (rows - 1 - viewer_row) / rows if rows > 0 else 0
                        elif animation_type == "scale-south":
                            position = viewer_row / rows if rows > 0 else 0
                        elif animation_type == "scale-east":
                            position = viewer_col / cols if cols > 0 else 0
                        elif animation_type == "scale-west":
                            position = (cols - 1 - viewer_col) / cols if cols > 0 else 0
                        elif animation_type == "scale-northeast":
                            position = (viewer_row + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "scale-northwest":
                            position = (viewer_row + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "scale-southeast":
                            position = ((rows - 1 - viewer_row) + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "scale-southwest":
                            position = ((rows - 1 - viewer_row) + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                        
                        inflation_start = position * 0.5
                        deflation_start = 0.5 + position * 0.5
                        
                        key_times = f"0; {inflation_start}; 0.5; {deflation_start}; 1"
                        values = "0; 0; 1; 1; 0"
                        
                        svg_content += f'<animateTransform attributeName="transform" type="scale" '
                        svg_content += f'keyTimes="{key_times}" values="{values}" dur="{duration}s" repeatCount="indefinite" additive="sum"/>\n'
                    
                    svg_content += f'<use href="#square"/>\n'
                    svg_content += f'</g>\n'
                elif animate_enabled and animation_type and (animation_type.startswith("opacity") or animation_type == "opacity"):
                    # Add opacity animation to the square for clear-fill-clear effect
                    svg_content += f'<g transform="translate({x},{y})">\n'
                    
                    # Calculate normalized position (0 to 1) based on direction
                    position = 0
                    
                    if animation_type == "opacity":
                        # Uniform opacity animation
                        svg_content += f'<animate attributeName="opacity" '
                        svg_content += f'values="0;1;0" dur="{duration}s" repeatCount="indefinite"/>\n'
                    else:
                        # Directional opacity animation
                        if animation_type == "opacity-north":
                            position = (rows - 1 - viewer_row) / rows if rows > 0 else 0
                        elif animation_type == "opacity-south":
                            position = viewer_row / rows if rows > 0 else 0
                        elif animation_type == "opacity-east":
                            position = viewer_col / cols if cols > 0 else 0
                        elif animation_type == "opacity-west":
                            position = (cols - 1 - viewer_col) / cols if cols > 0 else 0
                        elif animation_type == "opacity-northeast":
                            position = (viewer_row + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "opacity-northwest":
                            position = (viewer_row + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "opacity-southeast":
                            position = ((rows - 1 - viewer_row) + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "opacity-southwest":
                            position = ((rows - 1 - viewer_row) + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                        
                        # Calculate keyTimes and values
                        inflation_start = position * 0.5
                        deflation_start = 0.5 + position * 0.5
                        
                        key_times = f"0; {inflation_start}; 0.5; {deflation_start}; 1"
                        values = "0; 0; 1; 1; 0"
                        
                        svg_content += f'<animate attributeName="opacity" '
                        svg_content += f'keyTimes="{key_times}" values="{values}" dur="{duration}s" repeatCount="indefinite"/>\n'
                    
                    svg_content += f'<use href="#square"/>\n'
                    svg_content += f'</g>\n'
                else:
                    svg_content += f'<g transform="translate({x},{y})">\n'
                    svg_content += f'<use href="#square"/>\n'
                    svg_content += f'</g>\n'
    
    if rotation != 0:
        svg_content += '\n</g>\n'
    
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        svg_content += '\n</g>\n'
    
    svg_content += '\n</g>\n'
    svg_content += '\n</svg>'
    return svg_content

def generate_hexagonal_tiling(width, height, size, rotation, fill, stroke, stroke_width, animate=None, duration=1.0):
    """Generate a hexagonal tiling pattern using <use> elements."""
    # Determine if animation is enabled and get the animation type
    animate_enabled = animate is not None
    animation_type = normalize_animation_type(animate) if animate_enabled else None
    
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
    
    # Create SVG with proper transformations
    svg_content = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
    
    # Define tile shape in the defs section with center at (0,0)
    svg_content += f'<defs>\n'
    hex_points = []
    for i in range(6):
        angle = math.pi / 3 * i
        # Rotate by 30 degrees to get flat top
        angle += math.pi / 6
        px = hex_radius * math.cos(angle)
        py = hex_radius * math.sin(angle)
        hex_points.append((px, py))
    hex_points_str = ' '.join([f"{p[0]},{p[1]}" for p in hex_points])
    svg_content += f'<polygon id="hexagon" points="{hex_points_str}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>\n'
    svg_content += f'</defs>\n'
    
    # Apply transformations
    svg_content += f'<g>\n'
    
    # Add move animation to the entire grid if needed
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        move_values = f"0,{height * 2}; 0,0; 0,-{height * 2}" if animation_type == "move-north" else \
                     f"0,-{height * 2}; 0,0; 0,{height * 2}" if animation_type == "move-south" else \
                     f"-{width * 2},0; 0,0; {width * 2},0" if animation_type == "move-east" else \
                     f"{width * 2},0; 0,0; -{width * 2},0" if animation_type == "move-west" else \
                     f"-{width * 2},{height * 2}; 0,0; {width * 2},-{height * 2}" if animation_type == "move-northeast" else \
                     f"{width * 2},{height * 2}; 0,0; -{width * 2},-{height * 2}" if animation_type == "move-northwest" else \
                     f"-{width * 2},-{height * 2}; 0,0; {width * 2},{height * 2}" if animation_type == "move-southeast" else \
                     f"{width * 2},-{height * 2}; 0,0; -{width * 2},{height * 2}"
                     
        svg_content += f'<g>\n'
        svg_content += f'<animateTransform attributeName="transform" type="translate" '
        svg_content += f'values="{move_values}" dur="{duration}s" repeatCount="indefinite"/>\n'
    
    if rotation != 0:
        # Add a group with rotation transformation centered in the canvas
        svg_content += f'<g transform="rotate({rotation} {width/2} {height/2})">\n'
    
    # Generate all tiles using <use> elements
    for row in range(rows):
        for col in range(cols):
            # Calculate position (center of the hexagon)
            x = start_x + col * horizontal_spacing
            y = start_y + row * vertical_spacing
            
            # Offset every other row by half the horizontal spacing
            if row % 2 == 1:
                x += horizontal_spacing / 2
            
            # Check if the hexagon is at least partially inside the document after rotation
            if is_hexagon_inside_after_rotation(x, y, hex_radius, width, height, rotation):
                # Calculate the position in the canvas coordinate system
                canvas_x = x
                canvas_y = y
                
                # Apply rotation to get the final position in the canvas
                final_x, final_y = rotate_point(canvas_x, canvas_y, width/2, height/2, rotation)
                
                # Calculate the row and column in the viewer's coordinate system
                viewer_row = final_y / vertical_spacing
                viewer_col = final_x / horizontal_spacing
                
                if animate_enabled and animation_type and (animation_type.startswith("scale") or animation_type == "scale"):
                    # Add scale animation to the hexagon with proper centering
                    svg_content += f'<g transform="translate({x},{y})">\n'
                    
                    if animation_type == "scale":
                        # Uniform scaling
                        svg_content += f'<animateTransform attributeName="transform" type="scale" '
                        svg_content += f'values="0;1;0" dur="{duration}s" repeatCount="indefinite" additive="sum"/>\n'
                    else:
                        # Directional scaling
                        position = 0
                        if animation_type == "scale-north":
                            position = (rows - 1 - viewer_row) / rows if rows > 0 else 0
                        elif animation_type == "scale-south":
                            position = viewer_row / rows if rows > 0 else 0
                        elif animation_type == "scale-east":
                            position = viewer_col / cols if cols > 0 else 0
                        elif animation_type == "scale-west":
                            position = (cols - 1 - viewer_col) / cols if cols > 0 else 0
                        elif animation_type == "scale-northeast":
                            position = (viewer_row + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "scale-northwest":
                            position = (viewer_row + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "scale-southeast":
                            position = ((rows - 1 - viewer_row) + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "scale-southwest":
                            position = ((rows - 1 - viewer_row) + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                        
                        inflation_start = position * 0.5
                        deflation_start = 0.5 + position * 0.5
                        
                        key_times = f"0; {inflation_start}; 0.5; {deflation_start}; 1"
                        values = "0; 0; 1; 1; 0"
                        
                        svg_content += f'<animateTransform attributeName="transform" type="scale" '
                        svg_content += f'keyTimes="{key_times}" values="{values}" dur="{duration}s" repeatCount="indefinite" additive="sum"/>\n'
                    
                    svg_content += f'<use href="#hexagon"/>\n'
                    svg_content += f'</g>\n'
                elif animate_enabled and animation_type and (animation_type.startswith("opacity") or animation_type == "opacity"):
                    # Add opacity animation to the hexagon for clear-fill-clear effect
                    svg_content += f'<g transform="translate({x},{y})">\n'
                    
                    # Calculate normalized position (0 to 1) based on direction
                    position = 0
                    
                    if animation_type == "opacity":
                        # Uniform opacity animation
                        svg_content += f'<animate attributeName="opacity" '
                        svg_content += f'values="0;1;0" dur="{duration}s" repeatCount="indefinite"/>\n'
                    else:
                        # Directional opacity animation
                        if animation_type == "opacity-north":
                            position = (rows - 1 - viewer_row) / rows if rows > 0 else 0
                        elif animation_type == "opacity-south":
                            position = viewer_row / rows if rows > 0 else 0
                        elif animation_type == "opacity-east":
                            position = viewer_col / cols if cols > 0 else 0
                        elif animation_type == "opacity-west":
                            position = (cols - 1 - viewer_col) / cols if cols > 0 else 0
                        elif animation_type == "opacity-northeast":
                            position = (viewer_row + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "opacity-northwest":
                            position = (viewer_row + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "opacity-southeast":
                            position = ((rows - 1 - viewer_row) + viewer_col) / (rows + cols) if (rows + cols) > 0 else 0
                        elif animation_type == "opacity-southwest":
                            position = ((rows - 1 - viewer_row) + (cols - 1 - viewer_col)) / (rows + cols) if (rows + cols) > 0 else 0
                        
                        # Calculate keyTimes and values
                        inflation_start = position * 0.5
                        deflation_start = 0.5 + position * 0.5
                        
                        key_times = f"0; {inflation_start}; 0.5; {deflation_start}; 1"
                        values = "0; 0; 1; 1; 0"
                        
                        svg_content += f'<animate attributeName="opacity" '
                        svg_content += f'keyTimes="{key_times}" values="{values}" dur="{duration}s" repeatCount="indefinite"/>\n'
                    
                    svg_content += f'<use href="#hexagon"/>\n'
                    svg_content += f'</g>\n'
                else:
                    svg_content += f'<g transform="translate({x},{y})">\n'
                    svg_content += f'<use href="#hexagon"/>\n'
                    svg_content += f'</g>\n'
    
    if rotation != 0:
        svg_content += '\n</g>\n'
    
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        svg_content += '\n</g>\n'
    
    svg_content += '\n</g>\n'
    svg_content += '\n</svg>'
    return svg_content

def generate_svg(width, height, corners, tile_size, rotation, fill, stroke, stroke_width, animate=None, duration=1.0):
    """Generate the full SVG content with tiled shapes."""
    if corners == 3:
        return generate_triangular_tiling_svg(width, height, tile_size, rotation, fill, stroke, stroke_width, animate, duration)
    elif corners == 4:
        return generate_square_tiling(width, height, tile_size, rotation, fill, stroke, stroke_width, animate, duration)
    elif corners == 6:
        return generate_hexagonal_tiling(width, height, tile_size, rotation, fill, stroke, stroke_width, animate, duration)
    else:
        raise ValueError("Number of corners must be 3, 4, or 6.")

def generate_triangular_tiling(width, height, size, rotation, fill, stroke, stroke_width, animate=None, duration=1.0):
    """Generate a RAWR file with a triangular tiling pattern that has no holes or overlaps."""
    # Determine if animation is enabled and get the animation type
    animate_enabled = animate is not None
    animation_type = normalize_animation_type(animate) if animate_enabled else None
    
    # Create a base structure for the RAWR file
    glaxnimate_data = {
        "assets": {
            "__type__": "Assets",
            "colors": {
                "__type__": "NamedColorList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "compositions": {
                "__type__": "CompositionList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "fonts": {
                "__type__": "FontList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "gradient_colors": {
                "__type__": "GradientColorsList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "gradients": {
                "__type__": "GradientList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "images": {
                "__type__": "BitmapList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "name": "",
            "uuid": str(uuid.uuid4())
        },
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
    
    # Calculate dimensions for equilateral triangles
    triangle_height = size * math.sqrt(3) / 2
    
    # Calculate how much we need to expand the grid to cover the canvas after rotation
    expanded_width, expanded_height = calculate_expanded_dimensions(width, height, rotation)
    
    # For triangular tiling, we need to be more precise about the grid dimensions
    # Calculate grid dimensions with proper spacing for triangles
    horizontal_spacing = size / 2  # Horizontal distance between triangle centers
    vertical_spacing = triangle_height   # Vertical distance between triangle centers
    
    # Calculate how many tiles we need to cover the expanded area
    cols = math.ceil(expanded_width / horizontal_spacing) + 4  # Add extra tiles to ensure coverage
    rows = math.ceil(expanded_height / vertical_spacing) + 4   # Add extra tiles to ensure coverage
    
    # Starting position to center the pattern
    start_x = (expanded_width - (cols-1) * horizontal_spacing) / 2
    start_y = (expanded_height - (rows-1) * vertical_spacing) / 2
    
    # Create the grid composition
    grid_uuid = str(uuid.uuid4())
    grid_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": expanded_height,
        "locked": False,
        "name": "Triangle Grid",
        "shapes": [],
        "uuid": grid_uuid,
        "visible": True,
        "width": expanded_width
    }
    
    # Create the precomposed tile compositions
    # For uniform scaling, we create compositions with built-in animation
    # For directional scaling or opacity, we create compositions without animation
    
    # Upright triangle
    upright_triangle_uuid = str(uuid.uuid4())
    upright_triangle_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": triangle_height,
        "locked": False,
        "name": "Upright Triangle",
        "shapes": [
            {
                "__type__": "Layer",
                "animation": {
                    "__type__": "AnimationContainer",
                    "first_frame": 0,
                    "last_frame": int(duration * 60)
                },
                "auto_orient": False,
                "group_color": "#00000000",
                "locked": False,
                "mask": {
                    "__type__": "MaskSettings",
                    "inverted": False,
                    "mask": "NoMask"
                },
                "name": "Tile",
                "opacity": {
                    "value": 1
                },
                "parent": None,
                "render": True,
                "shapes": [
                    {
                        "__type__": "Group",
                        "auto_orient": False,
                        "group_color": "#00000000",
                        "locked": False,
                        "name": "Path",
                        "opacity": {
                            "value": 1
                        },
                        "shapes": [
                            {
                                "__type__": "Fill",
                                "color": {
                                    "value": fill
                                },
                                "fill_rule": "NonZero",
                                "group_color": "#00000000",
                                "locked": False,
                                "name": "Fill",
                                "opacity": {
                                    "value": 1
                                },
                                "use": None,
                                "uuid": str(uuid.uuid4()),
                                "visible": True
                            },
                            {
                                "__type__": "Stroke",
                                "cap": "ButtCap",
                                "color": {
                                    "value": stroke
                                },
                                "group_color": "#00000000",
                                "join": "MiterJoin",
                                "locked": False,
                                "miter_limit": 4,
                                "name": "Stroke",
                                "opacity": {
                                    "value": 1
                                },
                                "use": None,
                                "uuid": str(uuid.uuid4()),
                                "visible": True,
                                "width": {
                                    "value": stroke_width
                                }
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
                                        "points": [
                                            {
                                                "pos": {
                                                    "x": size/2,
                                                    "y": 0
                                                },
                                                "tan_in": {
                                                    "x": size/2,
                                                    "y": 0
                                                },
                                                "tan_out": {
                                                    "x": size/2,
                                                    "y": 0
                                                },
                                                "type": 0
                                            },
                                            {
                                                "pos": {
                                                    "x": size,
                                                    "y": triangle_height
                                                },
                                                "tan_in": {
                                                    "x": size,
                                                    "y": triangle_height
                                                },
                                                "tan_out": {
                                                    "x": size,
                                                    "y": triangle_height
                                                },
                                                "type": 1
                                            },
                                            {
                                                "pos": {
                                                    "x": 0,
                                                    "y": triangle_height
                                                },
                                                "tan_in": {
                                                    "x": 0,
                                                    "y": triangle_height
                                                },
                                                "tan_out": {
                                                    "x": 0,
                                                    "y": triangle_height
                                                },
                                                "type": 1
                                            }
                                        ]
                                    }
                                },
                                "uuid": str(uuid.uuid4()),
                                "visible": True
                            }
                        ],
                        "transform": {
                            "__type__": "Transform",
                            "anchor_point": {
                                "value": {
                                    "x": size/2,
                                    "y": triangle_height/2
                                }
                            },
                            "position": {
                                "value": {
                                    "x": size/2,
                                    "y": triangle_height/2
                                }
                            },
                            "rotation": {
                                "value": 0
                            },
                            "scale": {
                                "value": {
                                    "x": 1,
                                    "y": 1
                                }
                            }
                        },
                        "uuid": str(uuid.uuid4()),
                        "visible": True
                    }
                ],
                "transform": {
                    "__type__": "Transform",
                    "anchor_point": {
                        "value": {
                            "x": size/2,
                            "y": triangle_height/2
                        }
                    },
                    "position": {
                        "value": {
                            "x": size/2,
                            "y": triangle_height/2
                        }
                    },
                    "rotation": {
                        "value": 0
                    },
                    "scale": {
                        "value": {
                            "x": 1,
                            "y": 1
                        }
                    }
                },
                "uuid": str(uuid.uuid4()),
                "visible": True
            }
        ],
        "uuid": upright_triangle_uuid,
        "visible": True,
        "width": size
    }
    
    # Inverted triangle
    inverted_triangle_uuid = str(uuid.uuid4())
    inverted_triangle_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": triangle_height,
        "locked": False,
        "name": "Inverted Triangle",
        "shapes": [
            {
                "__type__": "Layer",
                "animation": {
                    "__type__": "AnimationContainer",
                    "first_frame": 0,
                    "last_frame": int(duration * 60)
                },
                "auto_orient": False,
                "group_color": "#00000000",
                "locked": False,
                "mask": {
                    "__type__": "MaskSettings",
                    "inverted": False,
                    "mask": "NoMask"
                },
                "name": "Tile",
                "opacity": {
                    "value": 1
                },
                "parent": None,
                "render": True,
                "shapes": [
                    {
                        "__type__": "Group",
                        "auto_orient": False,
                        "group_color": "#00000000",
                        "locked": False,
                        "name": "Path",
                        "opacity": {
                            "value": 1
                        },
                        "shapes": [
                            {
                                "__type__": "Fill",
                                "color": {
                                    "value": fill
                                },
                                "fill_rule": "NonZero",
                                "group_color": "#00000000",
                                "locked": False,
                                "name": "Fill",
                                "opacity": {
                                    "value": 1
                                },
                                "use": None,
                                "uuid": str(uuid.uuid4()),
                                "visible": True
                            },
                            {
                                "__type__": "Stroke",
                                "cap": "ButtCap",
                                "color": {
                                    "value": stroke
                                },
                                "group_color": "#00000000",
                                "join": "MiterJoin",
                                "locked": False,
                                "miter_limit": 4,
                                "name": "Stroke",
                                "opacity": {
                                    "value": 1
                                },
                                "use": None,
                                "uuid": str(uuid.uuid4()),
                                "visible": True,
                                "width": {
                                    "value": stroke_width
                                }
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
                                        "points": [
                                            {
                                                "pos": {
                                                    "x": 0,
                                                    "y": 0
                                                },
                                                "tan_in": {
                                                    "x": 0,
                                                    "y": 0
                                                },
                                                "tan_out": {
                                                    "x": 0,
                                                    "y": 0
                                                },
                                                "type": 0
                                            },
                                            {
                                                "pos": {
                                                    "x": size,
                                                    "y": 0
                                                },
                                                "tan_in": {
                                                    "x": size,
                                                    "y": 0
                                                },
                                                "tan_out": {
                                                    "x": size,
                                                    "y": 0
                                                },
                                                "type": 1
                                            },
                                            {
                                                "pos": {
                                                    "x": size/2,
                                                    "y": triangle_height
                                                },
                                                "tan_in": {
                                                    "x": size/2,
                                                    "y": triangle_height
                                                },
                                                "tan_out": {
                                                    "x": size/2,
                                                    "y": triangle_height
                                                },
                                                "type": 1
                                            }
                                        ]
                                    }
                                },
                                "uuid": str(uuid.uuid4()),
                                "visible": True
                            }
                        ],
                        "transform": {
                            "__type__": "Transform",
                            "anchor_point": {
                                "value": {
                                    "x": size/2,
                                    "y": triangle_height/2
                                }
                            },
                            "position": {
                                "value": {
                                    "x": size/2,
                                    "y": triangle_height/2
                                }
                            },
                            "rotation": {
                                "value": 0
                            },
                            "scale": {
                                "value": {
                                    "x": 1,
                                    "y": 1
                                }
                            }
                        },
                        "uuid": str(uuid.uuid4()),
                        "visible": True
                    }
                ],
                "transform": {
                    "__type__": "Transform",
                    "anchor_point": {
                        "value": {
                            "x": size/2,
                            "y": triangle_height/2
                        }
                    },
                    "position": {
                        "value": {
                            "x": size/2,
                            "y": triangle_height/2
                        }
                    },
                    "rotation": {
                        "value": 0
                    },
                    "scale": {
                        "value": {
                            "x": 1,
                            "y": 1
                        }
                    }
                },
                "uuid": str(uuid.uuid4()),
                "visible": True
            }
        ],
        "uuid": inverted_triangle_uuid,
        "visible": True,
        "width": size
    }
    
    # Add animation to the compositions if it's uniform scaling
    if animate_enabled and (animation_type == "scale" or animation_type is None):
        # Add uniform scaling animation to both triangle compositions
        upright_triangle_composition["shapes"][0]["transform"]["scale"] = get_scale_keyframes(
            animate_enabled, animation_type, 0, 0, 1, 1, duration
        )
        
        inverted_triangle_composition["shapes"][0]["transform"]["scale"] = get_scale_keyframes(
            animate_enabled, animation_type, 0, 0, 1, 1, duration
        )
    
    # Add triangle tiles to the grid
    for row in range(rows):
        for col in range(cols):
            # Calculate position (top-left corner of the tile)
            x = start_x + col * horizontal_spacing
            y = start_y + row * vertical_spacing
            
            # Calculate the actual center of the triangle
            center_x = x + size/2
            center_y = y + triangle_height/2
            
            # Calculate position in main composition (before rotation)
            x_main = center_x - expanded_width/2 + width/2
            y_main = center_y - expanded_height/2 + height/2
            
            # Alternate between upright and inverted triangles
            # This creates a proper triangular tiling without gaps or overlaps
            inverted = (row + col) % 2 == 1
            
            # Check if the triangle is at least partially inside the document after rotation
            if is_triangle_inside_after_rotation(x_main, y_main, size, inverted, width, height, rotation):
                # Use the appropriate triangle
                triangle_uuid = inverted_triangle_uuid if inverted else upright_triangle_uuid
                triangle_name = f"Inverted Triangle {row*cols + col + 1}" if inverted else f"Upright Triangle {row*cols + col + 1}"
                
                # Create a precomposed layer for this triangle
                precomp_layer = {
                    "__type__": "PreCompLayer",
                    "composition": triangle_uuid,
                    "group_color": "#00000000",
                    "locked": False,
                    "name": triangle_name,
                    "opacity": {"value": 1},
                    "size": {"height": triangle_height, "width": size},
                    "timing": {
                        "__type__": "StretchableTime",
                        "start_time": 0,
                        "stretch": 1
                    },
                    "transform": {
                        "__type__": "Transform",
                        "anchor_point": {"value": {"x": size/2, "y": triangle_height/2}},  # Center of the triangle
                        "position": {"value": {"x": x + size/2, "y": y + triangle_height/2}},  # Center position
                        "rotation": {"value": 0},
                        "scale": {"value": {"x": 1, "y": 1}}
                    },
                    "uuid": str(uuid.uuid4()),
                    "visible": True
                }
                
                # For directional scaling, add animation to the instance
                if animate_enabled and animation_type and animation_type.startswith("scale-"):
                    # Calculate the final position in the canvas after rotation
                    final_x, final_y = rotate_point(x_main, y_main, width/2, height/2, rotation)
                    
                    # Calculate the row and column in the viewer's coordinate system
                    viewer_row = final_y / vertical_spacing
                    viewer_col = final_x / horizontal_spacing
                    
                    precomp_layer["transform"]["scale"] = get_scale_keyframes(
                        animate_enabled, animation_type, viewer_row, viewer_col, rows, cols, duration
                    )
                
                # For clear-fill-clear animations, add opacity animation to the instance
                if animate_enabled and animation_type and (animation_type.startswith("opacity-") or animation_type == "opacity"):
                    # Calculate the final position in the canvas after rotation
                    final_x, final_y = rotate_point(x_main, y_main, width/2, height/2, rotation)
                    
                    # Calculate the row and column in the viewer's coordinate system
                    viewer_row = final_y / vertical_spacing
                    viewer_col = final_x / horizontal_spacing
                    
                    precomp_layer["opacity"] = get_opacity_keyframes(
                        animate_enabled, animation_type, viewer_row, viewer_col, rows, cols, duration
                    )
                
                grid_composition["shapes"].append(precomp_layer)
    
    # Create the main composition with the rotated grid
    main_uuid = str(uuid.uuid4())
    
    main_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": height,
        "locked": False,
        "name": "Main Composition",
        "shapes": [
            {
                "__type__": "PreCompLayer",
                "composition": grid_uuid,
                "group_color": "#00000000",
                "locked": False,
                "name": "Triangle Grid Layer",
                "opacity": {"value": 1},
                "size": {"height": expanded_height, "width": expanded_width},
                "timing": {
                    "__type__": "StretchableTime",
                    "start_time": 0,
                    "stretch": 1
                },
                "transform": {
                    "__type__": "Transform",
                    "anchor_point": {"value": {"x": expanded_width/2, "y": expanded_height/2}},
                    "position": {"value": {"x": width/2, "y": height/2}},
                    "rotation": {"value": rotation},
                    "scale": {"value": {"x": 1, "y": 1}}
                },
                "uuid": str(uuid.uuid4()),
                "visible": True
            }
        ],
        "uuid": main_uuid,
        "visible": True,
        "width": width
    }
    
    # Add move animation to the main composition if needed
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        main_composition["shapes"][0]["transform"]["position"] = get_move_keyframes(
            animate_enabled, animation_type, width, height, duration
        )
    
    # Add all compositions to the assets
    glaxnimate_data["assets"]["compositions"]["values"].append(main_composition)
    glaxnimate_data["assets"]["compositions"]["values"].append(upright_triangle_composition)
    glaxnimate_data["assets"]["compositions"]["values"].append(inverted_triangle_composition)
    glaxnimate_data["assets"]["compositions"]["values"].append(grid_composition)
    
    return glaxnimate_data

def generate_rawr_square_tiling(width, height, corners, tile_size, rotation, fill, stroke, stroke_width, animate=None, duration=1.0):
    """Generate a RAWR file with a grid of animated square tiles filling the entire canvas."""
    # Determine if animation is enabled and get the animation type
    animate_enabled = animate is not None
    animation_type = normalize_animation_type(animate) if animate_enabled else None
    
    # Create a base structure for the RAWR file
    glaxnimate_data = {
        "assets": {
            "__type__": "Assets",
            "colors": {
                "__type__": "NamedColorList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "compositions": {
                "__type__": "CompositionList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "fonts": {
                "__type__": "FontList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "gradient_colors": {
                "__type__": "GradientColorsList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "gradients": {
                "__type__": "GradientList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "images": {
                "__type__": "BitmapList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "name": "",
            "uuid": str(uuid.uuid4())
        },
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
    
    # --- FIX START ---
    # Calculate the diagonal of the canvas to determine the maximum expansion needed.
    # A grid of this size is guaranteed to cover the canvas at any rotation.
    canvas_diagonal = math.sqrt(width**2 + height**2)
    expanded_width = canvas_diagonal
    expanded_height = canvas_diagonal

    # Calculate grid dimensions needed to cover the expanded area.
    # Add extra padding to be absolutely certain there are no gaps.
    cols = math.ceil(expanded_width / tile_size) + 4
    rows = math.ceil(expanded_height / tile_size) + 4
    # --- FIX END ---
    
    # Starting position to center the pattern
    start_x = (expanded_width - (cols-1) * tile_size) / 2
    start_y = (expanded_height - (rows-1) * tile_size) / 2
    
    # Create the grid composition
    grid_uuid = str(uuid.uuid4())
    grid_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": expanded_height,
        "locked": False,
        "name": "Square Grid",
        "shapes": [],
        "uuid": grid_uuid,
        "visible": True,
        "width": expanded_width
    }
    
    # Create the precomposed tile composition
    tile_uuid = str(uuid.uuid4())
    tile_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": tile_size,
        "locked": False,
        "name": "Tile",
        "shapes": [
            {
                "__type__": "Layer",
                "animation": {
                    "__type__": "AnimationContainer",
                    "first_frame": 0,
                    "last_frame": int(duration * 60)
                },
                "auto_orient": False,
                "group_color": "#00000000",
                "locked": False,
                "mask": {
                    "__type__": "MaskSettings",
                    "inverted": False,
                    "mask": "NoMask"
                },
                "name": "Tile",
                "opacity": {
                    "value": 1
                },
                "parent": None,
                "render": True,
                "shapes": [
                    {
                        "__type__": "Layer",
                        "animation": {
                            "__type__": "AnimationContainer",
                            "first_frame": 0,
                            "last_frame": int(duration * 60)
                        },
                        "auto_orient": False,
                        "group_color": "#00000000",
                        "locked": False,
                        "mask": {
                            "__type__": "MaskSettings",
                            "inverted": False,
                            "mask": "NoMask"
                        },
                        "name": "Rectangle",
                        "opacity": {
                            "value": 1
                        },
                        "parent": None,
                        "render": True,
                        "shapes": [
                            {
                                "__type__": "Fill",
                                "color": {
                                    "value": fill
                                },
                                "fill_rule": "NonZero",
                                "group_color": "#00000000",
                                "locked": False,
                                "name": "Fill",
                                "opacity": {
                                    "value": 1
                                },
                                "use": None,
                                "uuid": str(uuid.uuid4()),
                                "visible": True
                            },
                            {
                                "__type__": "Stroke",
                                "cap": "ButtCap",
                                "color": {
                                    "value": stroke
                                },
                                "group_color": "#00000000",
                                "join": "MiterJoin",
                                "locked": False,
                                "miter_limit": 4,
                                "name": "Stroke",
                                "opacity": {
                                    "value": 1
                                },
                                "use": None,
                                "uuid": str(uuid.uuid4()),
                                "visible": True,
                                "width": {
                                    "value": stroke_width
                                }
                            },
                            {
                                "__type__": "Rect",
                                "group_color": "#00000000",
                                "locked": False,
                                "name": "Rectangle",
                                "position": {
                                    "value": {
                                        "x": 0,
                                        "y": 0
                                    }
                                },
                                "reversed": False,
                                "rounded": {
                                    "value": 0
                                },
                                "size": {
                                    "value": {
                                        "height": tile_size,
                                        "width": tile_size
                                    }
                                },
                                "uuid": str(uuid.uuid4()),
                                "visible": True
                            }
                        ],
                        "transform": {
                            "__type__": "Transform",
                            "anchor_point": {
                                "value": {
                                    "x": 0,
                                    "y": 0
                                }
                            },
                            "position": {
                                "value": {
                                    "x": tile_size/2,
                                    "y": tile_size/2
                                }
                            },
                            "rotation": {
                                "value": 0
                            },
                            "scale": {
                                "value": {
                                    "x": 1,
                                    "y": 1
                                }
                            }
                        },
                        "uuid": str(uuid.uuid4()),
                        "visible": True
                    }
                ],
                "transform": {
                    "__type__": "Transform",
                    "anchor_point": {
                        "value": {
                            "x": tile_size/2,
                            "y": tile_size/2
                        }
                    },
                    "position": {
                        "value": {
                            "x": tile_size/2,
                            "y": tile_size/2
                        }
                    },
                    "rotation": {
                        "value": 0
                    },
                    "scale": {
                        "value": {
                            "x": 1,
                            "y": 1
                        }
                    }
                },
                "uuid": str(uuid.uuid4()),
                "visible": True
            }
        ],
        "uuid": tile_uuid,
        "visible": True,
        "width": tile_size
    }
    
    # Add animation to the composition if it's uniform scaling
    if animate_enabled and (animation_type == "scale" or animation_type is None):
        # Add uniform scaling animation to the tile composition
        tile_composition["shapes"][0]["transform"]["scale"] = get_scale_keyframes(
            animate_enabled, animation_type, 0, 0, 1, 1, duration
        )
    
    # Add square tiles to the grid
    for row in range(rows):
        for col in range(cols):
            # Calculate position (top-left corner of the tile)
            x = start_x + col * tile_size
            y = start_y + row * tile_size
            
            # Calculate the actual center of the square
            center_x = x + tile_size/2
            center_y = y + tile_size/2
            
            # Calculate position in main composition (before rotation)
            x_main = center_x - expanded_width/2 + width/2
            y_main = center_y - expanded_height/2 + height/2
            
            # Check if the square is at least partially inside the document after rotation
            if is_square_inside_after_rotation(x_main, y_main, tile_size, width, height, rotation):
                # Create a precomposed layer for this tile
                precomp_layer = {
                    "__type__": "PreCompLayer",
                    "composition": tile_uuid,
                    "group_color": "#00000000",
                    "locked": False,
                    "name": f"Tile {row*cols + col + 1}",
                    "opacity": {"value": 1},
                    "size": {"height": tile_size, "width": tile_size},
                    "timing": {
                        "__type__": "StretchableTime",
                        "start_time": 0,
                        "stretch": 1
                    },
                    "transform": {
                        "__type__": "Transform",
                        "anchor_point": {"value": {"x": tile_size/2, "y": tile_size/2}},  # Center of the square
                        "position": {"value": {"x": x + tile_size/2, "y": y + tile_size/2}},  # Center position
                        "rotation": {"value": 0},
                        "scale": {"value": {"x": 1, "y": 1}}
                    },
                    "uuid": str(uuid.uuid4()),
                    "visible": True
                }
                
                # For directional scaling, add animation to the instance
                if animate_enabled and animation_type and animation_type.startswith("scale-"):
                    # Calculate the final position in the canvas after rotation
                    final_x, final_y = rotate_point(x_main, y_main, width/2, height/2, rotation)
                    
                    # Calculate the row and column in the viewer's coordinate system
                    viewer_row = final_y / tile_size
                    viewer_col = final_x / tile_size
                    
                    precomp_layer["transform"]["scale"] = get_scale_keyframes(
                        animate_enabled, animation_type, viewer_row, viewer_col, rows, cols, duration
                    )
                
                # For clear-fill-clear animations, add opacity animation to the instance
                if animate_enabled and animation_type and (animation_type.startswith("opacity-") or animation_type == "opacity"):
                    # Calculate the final position in the canvas after rotation
                    final_x, final_y = rotate_point(x_main, y_main, width/2, height/2, rotation)
                    
                    # Calculate the row and column in the viewer's coordinate system
                    viewer_row = final_y / tile_size
                    viewer_col = final_x / tile_size
                    
                    precomp_layer["opacity"] = get_opacity_keyframes(
                        animate_enabled, animation_type, viewer_row, viewer_col, rows, cols, duration
                    )
                
                grid_composition["shapes"].append(precomp_layer)
    
    # Create the main composition with the rotated grid
    main_uuid = str(uuid.uuid4())
    
    main_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": height,
        "locked": False,
        "name": "Main Composition",
        "shapes": [
            {
                "__type__": "PreCompLayer",
                "composition": grid_uuid,
                "group_color": "#00000000",
                "locked": False,
                "name": "Square Grid Layer",
                "opacity": {"value": 1},
                "size": {"height": expanded_height, "width": expanded_width},
                "timing": {
                    "__type__": "StretchableTime",
                    "start_time": 0,
                    "stretch": 1
                },
                "transform": {
                    "__type__": "Transform",
                    "anchor_point": {"value": {"x": expanded_width/2, "y": expanded_height/2}},
                    "position": {"value": {"x": width/2, "y": height/2}},
                    "rotation": {"value": rotation},
                    "scale": {"value": {"x": 1, "y": 1}}
                },
                "uuid": str(uuid.uuid4()),
                "visible": True
            }
        ],
        "uuid": main_uuid,
        "visible": True,
        "width": width
    }
    
    # Add move animation to the main composition if needed
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        main_composition["shapes"][0]["transform"]["position"] = get_move_keyframes(
            animate_enabled, animation_type, width, height, duration
        )
    
    # Add all compositions to the assets
    glaxnimate_data["assets"]["compositions"]["values"].append(main_composition)
    glaxnimate_data["assets"]["compositions"]["values"].append(tile_composition)
    glaxnimate_data["assets"]["compositions"]["values"].append(grid_composition)
    
    return glaxnimate_data

def generate_rawr_hexagonal_tiling(width, height, corners, tile_size, rotation, fill, stroke, stroke_width, animate=None, duration=1.0):
    """Generate a RAWR file with a hexagonal tiling pattern that has no holes or overlaps."""
    # Determine if animation is enabled and get the animation type
    animate_enabled = animate is not None
    animation_type = normalize_animation_type(animate) if animate_enabled else None
    
    # Create a base structure for the RAWR file
    glaxnimate_data = {
        "assets": {
            "__type__": "Assets",
            "colors": {
                "__type__": "NamedColorList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "compositions": {
                "__type__": "CompositionList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "fonts": {
                "__type__": "FontList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "gradient_colors": {
                "__type__": "GradientColorsList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "gradients": {
                "__type__": "GradientList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "images": {
                "__type__": "BitmapList",
                "name": "",
                "uuid": str(uuid.uuid4()),
                "values": []
            },
            "name": "",
            "uuid": str(uuid.uuid4())
        },
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
    
    # Calculate hexagon dimensions
    hex_radius = tile_size
    horizontal_spacing = hex_radius * math.sqrt(3)
    vertical_spacing = hex_radius * 1.5
    
    # Calculate how much we need to expand the grid to cover the canvas after rotation
    expanded_width, expanded_height = calculate_expanded_dimensions(width, height, rotation)
    
    # Calculate grid dimensions with expansion
    cols = math.ceil(expanded_width / horizontal_spacing) + 2
    rows = math.ceil(expanded_height / vertical_spacing) + 2
    
    # Starting position to center the pattern
    start_x = (expanded_width - (cols-1) * horizontal_spacing) / 2
    start_y = (expanded_height - (rows-1) * vertical_spacing) / 2
    
    # Create the grid composition
    grid_uuid = str(uuid.uuid4())
    grid_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": expanded_height,
        "locked": False,
        "name": "Hexagon Grid",
        "shapes": [],
        "uuid": grid_uuid,
        "visible": True,
        "width": expanded_width
    }
    
    # Create the precomposed tile composition
    tile_uuid = str(uuid.uuid4())
    hex_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": hex_radius * 2,
        "locked": False,
        "name": "Tile",
        "shapes": [
            {
                "__type__": "Layer",
                "animation": {
                    "__type__": "AnimationContainer",
                    "first_frame": 0,
                    "last_frame": int(duration * 60)
                },
                "auto_orient": False,
                "group_color": "#00000000",
                "locked": False,
                "mask": {
                    "__type__": "MaskSettings",
                    "inverted": False,
                    "mask": "NoMask"
                },
                "name": "Tile",
                "opacity": {
                    "value": 1
                },
                "parent": None,
                "render": True,
                "shapes": [
                    {
                        "__type__": "Group",
                        "auto_orient": False,
                        "group_color": "#00000000",
                        "locked": False,
                        "name": "PolyStar",
                        "opacity": {
                            "value": 1
                        },
                        "shapes": [
                            {
                                "__type__": "Fill",
                                "color": {
                                    "value": fill
                                },
                                "fill_rule": "NonZero",
                                "group_color": "#00000000",
                                "locked": False,
                                "name": "Fill",
                                "opacity": {
                                    "value": 1
                                },
                                "use": None,
                                "uuid": str(uuid.uuid4()),
                                "visible": True
                            },
                            {
                                "__type__": "Stroke",
                                "cap": "ButtCap",
                                "color": {
                                    "value": stroke
                                },
                                "group_color": "#00000000",
                                "join": "MiterJoin",
                                "locked": False,
                                "miter_limit": 4,
                                "name": "Stroke",
                                "opacity": {
                                    "value": 1
                                },
                                "use": None,
                                "uuid": str(uuid.uuid4()),
                                "visible": True,
                                "width": {
                                    "value": stroke_width
                                }
                            },
                            {
                                "__type__": "PolyStar",
                                "angle": {
                                    "value": 180
                                },
                                "group_color": "#00000000",
                                "inner_radius": {
                                    "value": hex_radius
                                },
                                "inner_roundness": {
                                    "value": 0
                                },
                                "locked": False,
                                "name": "PolyStar",
                                "outer_radius": {
                                    "value": hex_radius
                                },
                                "outer_roundness": {
                                    "value": 0
                                },
                                "points": {
                                    "value": 6
                                },
                                "position": {
                                    "value": {
                                        "x": 0,
                                        "y": 0
                                    }
                                },
                                "reversed": False,
                                "type": "Polygon",
                                "uuid": str(uuid.uuid4()),
                                "visible": True
                            }
                        ],
                        "transform": {
                            "__type__": "Transform",
                            "anchor_point": {
                                "value": {
                                    "x": 0,
                                    "y": 0
                                }
                            },
                            "position": {
                                "value": {
                                    "x": hex_radius,
                                    "y": hex_radius
                                }
                            },
                            "rotation": {
                                "value": 0
                            },
                            "scale": {
                                "value": {
                                    "x": 1,
                                    "y": 1
                                }
                            }
                        },
                        "uuid": str(uuid.uuid4()),
                        "visible": True
                    }
                ],
                "transform": {
                    "__type__": "Transform",
                    "anchor_point": {
                        "value": {
                            "x": hex_radius,
                            "y": hex_radius
                        }
                    },
                    "position": {
                        "value": {
                            "x": hex_radius,
                            "y": hex_radius
                        }
                    },
                    "rotation": {
                        "value": 0
                    },
                    "scale": {
                        "value": {
                            "x": 1,
                            "y": 1
                        }
                    }
                },
                "uuid": str(uuid.uuid4()),
                "visible": True
            }
        ],
        "uuid": tile_uuid,
        "visible": True,
        "width": hex_radius * 2
    }
    
    # Add animation to the composition if it's uniform scaling
    if animate_enabled and (animation_type == "scale" or animation_type is None):
        # Add uniform scaling animation to the hex composition
        hex_composition["shapes"][0]["transform"]["scale"] = get_scale_keyframes(
            animate_enabled, animation_type, 0, 0, 1, 1, duration
        )
    
    # Add hexagon tiles to the grid
    for row in range(rows):
        for col in range(cols):
            # Calculate position (top-left corner of the tile)
            x = start_x + col * horizontal_spacing
            y = start_y + row * vertical_spacing
            
            # Offset every other row by half the horizontal spacing
            if row % 2 == 1:
                x += horizontal_spacing / 2
            
            # Calculate the actual center of the hexagon
            center_x = x + hex_radius
            center_y = y + hex_radius
            
            # Calculate position in main composition (before rotation)
            x_main = center_x - expanded_width/2 + width/2
            y_main = center_y - expanded_height/2 + height/2
            
            # Check if the hexagon is at least partially inside the document after rotation
            if is_hexagon_inside_after_rotation(x_main, y_main, hex_radius, width, height, rotation):
                # Create a precomposed layer for this hexagon
                precomp_layer = {
                    "__type__": "PreCompLayer",
                    "composition": tile_uuid,
                    "group_color": "#00000000",
                    "locked": False,
                    "name": f"Composition Layer {row*cols + col + 1}",
                    "opacity": {"value": 1},
                    "size": {"height": hex_radius * 2, "width": hex_radius * 2},
                    "timing": {
                        "__type__": "StretchableTime",
                        "start_time": 0,
                        "stretch": 1
                    },
                    "transform": {
                        "__type__": "Transform",
                        "anchor_point": {"value": {"x": hex_radius, "y": hex_radius}},  # Center of the hexagon
                        "position": {"value": {"x": x + hex_radius, "y": y + hex_radius}},  # Center position
                        "rotation": {"value": 0},
                        "scale": {"value": {"x": 1, "y": 1}}
                    },
                    "uuid": str(uuid.uuid4()),
                    "visible": True
                }
                
                # For directional scaling, add animation to the instance
                if animate_enabled and animation_type and animation_type.startswith("scale-"):
                    # Calculate the final position in the canvas after rotation
                    final_x, final_y = rotate_point(x_main, y_main, width/2, height/2, rotation)
                    
                    # Calculate the row and column in the viewer's coordinate system
                    viewer_row = final_y / vertical_spacing
                    viewer_col = final_x / horizontal_spacing
                    
                    precomp_layer["transform"]["scale"] = get_scale_keyframes(
                        animate_enabled, animation_type, viewer_row, viewer_col, rows, cols, duration
                    )
                
                # For clear-fill-clear animations, add opacity animation to the instance
                if animate_enabled and animation_type and (animation_type.startswith("opacity-") or animation_type == "opacity"):
                    # Calculate the final position in the canvas after rotation
                    final_x, final_y = rotate_point(x_main, y_main, width/2, height/2, rotation)
                    
                    # Calculate the row and column in the viewer's coordinate system
                    viewer_row = final_y / vertical_spacing
                    viewer_col = final_x / horizontal_spacing
                    
                    precomp_layer["opacity"] = get_opacity_keyframes(
                        animate_enabled, animation_type, viewer_row, viewer_col, rows, cols, duration
                    )
                
                grid_composition["shapes"].append(precomp_layer)
    
    # Create the main composition with the rotated grid
    main_uuid = str(uuid.uuid4())
    
    main_composition = {
        "__type__": "Composition",
        "animation": {
            "__type__": "AnimationContainer",
            "first_frame": 0,
            "last_frame": int(duration * 60)
        },
        "fps": 60,
        "group_color": "#00000000",
        "height": height,
        "locked": False,
        "name": "Composition",
        "shapes": [
            {
                "__type__": "PreCompLayer",
                "composition": grid_uuid,
                "group_color": "#00000000",
                "locked": False,
                "name": "Hexagon Grid Layer",
                "opacity": {"value": 1},
                "size": {"height": expanded_height, "width": expanded_width},
                "timing": {
                    "__type__": "StretchableTime",
                    "start_time": 0,
                    "stretch": 1
                },
                "transform": {
                    "__type__": "Transform",
                    "anchor_point": {"value": {"x": expanded_width/2, "y": expanded_height/2}},
                    "position": {"value": {"x": width/2, "y": height/2}},
                    "rotation": {"value": rotation},
                    "scale": {"value": {"x": 1, "y": 1}}
                },
                "uuid": str(uuid.uuid4()),
                "visible": True
            }
        ],
        "uuid": main_uuid,
        "visible": True,
        "width": width
    }
    
    # Add move animation to the main composition if needed
    if animate_enabled and animation_type and animation_type.startswith("move-"):
        main_composition["shapes"][0]["transform"]["position"] = get_move_keyframes(
            animate_enabled, animation_type, width, height, duration
        )
    
    # Add all compositions to the assets
    glaxnimate_data["assets"]["compositions"]["values"].append(main_composition)
    glaxnimate_data["assets"]["compositions"]["values"].append(hex_composition)
    glaxnimate_data["assets"]["compositions"]["values"].append(grid_composition)
    
    return glaxnimate_data

def generate_rawr(width, height, corners, tile_size, rotation, fill, stroke, stroke_width, animate=None, duration=1.0):
    """Generate the full RAWR content with tiled shapes."""
    if corners == 3:
        return generate_triangular_tiling(width, height, tile_size, rotation, fill, stroke, stroke_width, animate, duration)
    elif corners == 4:
        return generate_rawr_square_tiling(width, height, corners, tile_size, rotation, fill, stroke, stroke_width, animate, duration)
    elif corners == 6:
        return generate_rawr_hexagonal_tiling(width, height, corners, tile_size, rotation, fill, stroke, stroke_width, animate, duration)
    else:
        raise ValueError("Number of corners must be 3, 4, or 6.")

def main():
    parser = argparse.ArgumentParser(description="Generate an SVG, HTML, or RAWR file with tiled shapes.")
    parser.add_argument('-w', '--width', type=int, default=1280, help="Width of the canvas (default: 1280)")
    parser.add_argument('-H', '--height', type=int, default=720, help="Height of the canvas (default: 720)")
    parser.add_argument('-c', '--corners', type=int, choices=[3, 4, 6], required=True, help="Number of corners of the tile (3, 4, or 6)")
    parser.add_argument('-s', '--tile_size', type=float, default=50, help="Size of each tile (default: 50)")
    parser.add_argument('-r', '--rotation', type=float, default=0, help="Rotation angle in degrees (default: 0)")
    parser.add_argument('-f', '--fill', type=str, default="white", help="Fill color of the tiles (default: white)")
    parser.add_argument('-t', '--stroke', type=str, default="black", help="Stroke color of the tiles (default: black)")
    parser.add_argument('-d', '--stroke_width', type=float, default=1, help="Stroke width of the tiles (default: 1)")
    parser.add_argument('-o', '--output', type=str, default="output", help="Output file name without extension (default: output)")
    parser.add_argument('-F', '--format', type=str, choices=["svg", "rawr", "html"], default="svg", help="Output format (svg, rawr, or html) (default: svg)")
    parser.add_argument('-a', '--animate', nargs='?', const='scale', 
                        choices=generate_animation_choices(),
                        help="Add animation to the tiles with optional direction (default: scale)")
    parser.add_argument('-D', '--duration', type=float, default=1.0, help="Duration of the whole animation in seconds (default: 1.0)")
    
    args = parser.parse_args()
    
    # Normalize the animation type
    args.animate = normalize_animation_type(args.animate)
    
    if args.format.lower() == "svg":
        svg_content = generate_svg(
            args.width, args.height, args.corners,
            args.tile_size, args.rotation, args.fill, args.stroke, args.stroke_width, args.animate, args.duration
        )
        
        output_file = f"{args.output}.svg"
        with open(output_file, 'w') as f:
            f.write(svg_content)
        
        print(f"SVG file '{output_file}' generated successfully.")
    
    elif args.format.lower() == "html":
        svg_content = generate_svg(
            args.width, args.height, args.corners,
            args.tile_size, args.rotation, args.fill, args.stroke, args.stroke_width, args.animate, args.duration
        )
        
        # Wrap SVG content with HTML tags
        html_content = f"<html><body>\n{svg_content}\n</body></html>"
        
        output_file = f"{args.output}.html"
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"HTML file '{output_file}' generated successfully.")
    
    elif args.format.lower() == "rawr":
        glaxnimate_data = generate_rawr(
            args.width, args.height, args.corners, args.tile_size, args.rotation,
            args.fill, args.stroke, args.stroke_width, args.animate, args.duration
        )

        output_file = f"{args.output}.rawr"
        with open(output_file, 'w') as f:
            json.dump(glaxnimate_data, f, indent=4)
        
        print(f"RAWR file '{output_file}' generated successfully.")

if __name__ == "__main__":
    main()
