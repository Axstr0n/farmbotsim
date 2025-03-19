import math
import numpy as np

class Vec2f:
    __slots__ = ('x', 'y')
    # def __init__(self, x:float, y:float):
    #     self.x = x
    #     self.y = y
    
    def __init__(self, x_or_list: float | tuple | list, y: float = None):
        if isinstance(x_or_list, (tuple, list, np.ndarray)) and len(x_or_list) == 2:
            self.x, self.y = x_or_list
        elif isinstance(x_or_list, (int, float)) and y is not None:
            self.x = x_or_list
            self.y = y
        else:
            raise ValueError(f"Input should be a tuple/list of two elements or two separate values but it is {type(x_or_list)}")


    def __add__(self, other):
        if isinstance(other, Vec2f):
            return Vec2f(self.x + other.x, self.y + other.y)
        if isinstance(other, float|int):
            return Vec2f(self.x + other, self.y + other)
        raise TypeError("Operand must be of type Vec2f")

    def to_list(self):
        """Return the Vec2f as a tuple (x, y)"""
        return [self.x, self.y]

    def __mul__(self, other):
        if isinstance(other, Vec2f):
            return Vec2f(self.x * other.x, self.y * other.y)
        if isinstance(other, float|int):
            return Vec2f(self.x * other, self.y * other)

    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __truediv__(self, other):
        if isinstance(other, Vec2f):
            return Vec2f(self.x / other.x, self.y / other.y)
        elif isinstance(other, (int, float)):
            return Vec2f(self.x / other, self.y / other)
        else:
            raise TypeError(f"Unsupported type for division: {type(other)}")

    def __repr__(self):
        return f"Vec2f(x={self.x:.2f}, y={self.y:.2f})"

    def __str__(self):
        return f"({self.x:.2f}, {self.y:.2f})"

    def __eq__(self, other):
        if isinstance(other, Vec2f):
            return self.x == other.x and self.y == other.y
        return False

    def __neg__(self):
        return Vec2f(-self.x, -self.y)

    def __sub__(self, other):
        if isinstance(other, Vec2f):
            return Vec2f(self.x - other.x, self.y - other.y)
        raise TypeError("Operand must be of type Vec2f")

    def magnitude(self):
        return (self.x**2 + self.y**2)**0.5

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize a vector with magnitude 0")
        return Vec2f(self.x / mag, self.y / mag)
    
    def rotate(self, angle:float):
        """Rotate the vector by a given angle (in radians)."""
        cos_theta = math.cos(angle)
        sin_theta = math.sin(angle)
        x_new = self.x * cos_theta - self.y * sin_theta
        y_new = self.x * sin_theta + self.y * cos_theta
        return Vec2f(x_new, y_new)
    
    def __iter__(self):
        return iter((self.x, self.y))

    def get_angle(self, type:str):
        # Angle in radians
        angle_rad = math.atan2(self.y, self.x)
        # Convert to degrees (optional)
        angle_deg = math.degrees(angle_rad)
        if type == "rad": return angle_rad
        if type == "deg": return angle_deg
        else: raise TypeError("Invalid type for angle")

    def is_close(self, other, tolerance=1e-5):
        if isinstance(other, Vec2f):
            return abs(self.x - other.x) < tolerance and abs(self.y - other.y) < tolerance
        return False
    
    def distance_to(self, other) -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def direction_to(self, other: "Vec2f") -> "Vec2f":
        """Calculate the unit direction vector pointing towards another Vec2f."""
        dx = other.x - self.x
        dy = other.y - self.y
        magnitude = math.sqrt(dx ** 2 + dy ** 2)
        
        if magnitude == 0:
            return Vec2f(0, 0)  # Avoid division by zero, return zero vector
        
        return Vec2f(dx / magnitude, dy / magnitude)
    
    def get_offset_position(self, length: float, angle_degrees: float):
        """Calculate a new position based on the starting position, a given length, and an angle."""
        angle_radians = math.radians(angle_degrees)  # Convert angle to radians
        x2 = self.x + length * math.cos(angle_radians)
        y2 = self.y + length * math.sin(angle_radians)
        return Vec2f(x2,y2)

class Target:
    """
    A class representing Target.

    Attributes:
        position (Vec2f): Position of the target
        direction (Vec2f): Direction of target
    """
    def __init__(self, position:Vec2f, direction:Vec2f):
        self.position = position
        self.direction = direction
    
    def __str__(self):
        return f'p={self.position}, d={self.direction}'

    def __repr__(self):
        return f'Target(position={self.position},direction={self.direction})'


import colorsys
def generate_colors(n, hue_offset=0.1):
    """Generates n colors with hue offset"""
    colors = []
    for i in range(n):
        hue = (i / n + hue_offset) % 1  # Apply offset and keep within [0,1]
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)  # Convert to RGB
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    return colors

import numpy as np
def padd_obstacle(obstacle, padding):
    """
    Expands the obstacle outward by a fixed padding amount, ensuring parallel side movement.

    Attributes:
        obstacle (list of Vec2f / tuple): List of Vec2f(x, y) points defining the obstacle.
        padding (float): The amount to expand outward.

    Returns:
        list of tuples: New padded obstacle points.
    """
    if isinstance(obstacle[0], Vec2f):
        obstacle = [(p.x,p.y) for p in obstacle] # from list of vec2f to list of tuple
    obstacle = np.array(obstacle)  # Convert to numpy array for easier math
    num_points = len(obstacle)

    # Compute edge normals
    normals = np.array([
        np.array([-edge[1], edge[0]]) / np.linalg.norm(edge)
        for edge in (obstacle - np.roll(obstacle, -1, axis=0))
    ])

    # Compute vertex shifts
    new_points = [
        tuple(obstacle[i] + (normals[i - 1] + normals[i]) / np.linalg.norm(normals[i - 1] + normals[i]) * padding)
        for i in range(num_points)
    ]

    return [Vec2f(float(x), float(y)) for x, y in new_points]
