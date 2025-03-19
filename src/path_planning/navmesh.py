import math
import numpy as np
import triangle as tr
import networkx as nx


def padd_obstacle(obstacle, padding=10):
    """
    Expands the obstacle outward by a fixed padding amount, ensuring parallel side movement.

    Attributes:
        obstacle (list of tuples): List of (x, y) points defining the obstacle.
        padding (float): The amount to expand outward.

    Returns:
        list of tuples: New padded obstacle points.
    """
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

    return [(float(x), float(y)) for x, y in new_points]

def interpolate_points(lst, n):
    """
    Adds `n` evenly spaced points between each pair of consecutive points.
    
    :param lst: List of (x, y) tuples.
    :param n: Number of intermediate points to add between each pair.
    :return: New list with interpolated points.
    """
    if len(lst) < 2:
        return lst  # No interpolation needed if less than two points
    
    new_points = []
    
    for i in range(len(lst)):
        p1 = np.array(lst[i])
        p2 = np.array(lst[(i + 1)%len(lst)])
        
        new_points.append(tuple(p1))  # Add the original point
        dst = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
        if dst < 1: continue

        # Generate n interpolated points
        for j in range(1, n + 1):
            t = j / (n + 1)  # Interpolation fraction
            interpolated = (1 - t) * p1 + t * p2
            new_points.append(tuple(interpolated))  # Convert back to tuple

    #new_points.append(tuple(lst[-1]))  # Add the last original point
    return new_points

class NavMesh:
    def __init__(self, boundary, obstacles=[]):
        self.boundary = np.array(boundary)
        self.obstacles = [np.array(interpolate_points(obs, 2)) for obs in obstacles]
        self.vertices, self.triangles, self.portals = [], [], []
        self.graph = nx.Graph()
        self.shortest_path = None
        self._triangulate()
    
    def _triangulate(self):
        points = self.boundary.tolist()
        segments = [[i, (i + 1) % len(self.boundary)] for i in range(len(self.boundary))]
        holes = []
        for obs in self.obstacles:
            hole_center = np.mean(obs, axis=0)
            holes.append(hole_center.tolist())
            start_index = len(points)
            points.extend(obs.tolist())
            segments.extend([[start_index + i, start_index + (i + 1) % len(obs)] for i in range(len(obs))])
        data = {'vertices': np.array(points), 'segments': np.array(segments), 'holes': np.array(holes)}
        #triangulated = tr.triangulate(data, 'pa2')
        triangulated = tr.triangulate(data, 'pq30')
        if 'triangles' in triangulated:
            self.triangles = triangulated['triangles']
            self.vertices = triangulated['vertices']
            self._build_graph()

    def _build_graph(self):
        self.graph.clear()
        def _distance(p1, p2):
            """Helper function to calculate the Euclidean distance between two points."""
            return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        for i, tri in enumerate(self.triangles):
            for j in range(i + 1, len(self.triangles)):
                if self._share_edge(self.triangles[i], self.triangles[j]):
                    shared_edge = self._find_shared_edge(tri, self.triangles[j])
                    #edge_length = _distance(self.vertices[shared_edge[0]], self.vertices[shared_edge[1]])
                    p1 = np.mean([self.vertices[v] for v in tri], axis=0)
                    p2 = np.mean([self.vertices[v] for v in self.triangles[j]], axis=0)
                    edge_length = _distance(p1,p2)
                    self.graph.add_edge(i, j, weight=edge_length)
        

    def _share_edge(self, tri1, tri2):
        return len(set(tri1) & set(tri2)) == 2

    def find_shortest_path(self, start, end):
        start_triangle = self._find_triangle_containing_point(start)
        end_triangle = self._find_triangle_containing_point(end)
        if start_triangle is None:
            start_triangle = self._find_closest_triangle(start)
        if end_triangle is None:
            end_triangle = self._find_closest_triangle(end)
        shortest_path = nx.astar_path(self.graph, start_triangle, end_triangle)
        self.shortest_path = shortest_path
        portals = [(start, start)]
        for i in range(len(shortest_path) - 1):
            shared_edge = self._find_shared_edge(self.triangles[shortest_path[i]], self.triangles[shortest_path[i + 1]])
            if shared_edge:
                portals.append((self.vertices[shared_edge[0]], self.vertices[shared_edge[1]]))
        portals.append((end, end))
        self.portals = portals
        return self._funnel_algorithm(portals)


    def _triarea2(self, a, b, c):
        """
        Computes twice the signed area of the triangle formed by points a, b, and c in 2D.
        
        Parameters:
        a, b, c : tuple or list of floats (x, y)
        
        Returns:
        float : twice the signed area of the triangle
        """
        ax, ay = b[0] - a[0], b[1] - a[1]
        bx, by = c[0] - a[0], c[1] - a[1]
        return bx * ay - ax * by  # Determinant formula

    def _vdistsqr(self, a, b):
        """
        Computes the squared Euclidean distance between points a and b.
        
        Parameters:
        a, b : tuple or list of floats (x, y, [z])
        
        Returns:
        float : squared distance between a and b
        """
        return sum((ai - bi) ** 2 for ai, bi in zip(a, b))

    def _vequal(self, a, b, epsilon=0.001):
        """
        Checks if two points are approximately equal within a small tolerance.
        
        Parameters:
        a, b : tuple or list of floats (x, y, [z])
        epsilon : float, the tolerance (default 0.001)
        
        Returns:
        bool : True if points are approximately equal, False otherwise
        """
        return self._vdistsqr(a, b) < epsilon ** 2

    def _funnel_algorithm(self, portals, max_pts=30):
        nportals = len(portals)
        if nportals == 0:
            return [],0

        # Initialize scan state
        portal_apex = portals[0][0]
        portal_left = portals[1][0]
        portal_right = portals[1][1]
        apex_index = left_index = right_index = 0

        # Path points
        pts = [portal_apex]

        i = 1
        while i < nportals:
            if len(pts) >= max_pts:
                break

            left = portals[i][0]
            right = portals[i][1]
            
            # Update right vertex
            if self._triarea2(portal_apex, portal_right, right) >= 0.0: # - funnel widens
                if self._vequal(portal_apex, portal_right) or self._triarea2(portal_apex, portal_left, right) < 0.0:
                    portal_right = right
                    right_index = i
                else:
                    # Right over left, insert left to path and restart scan
                    pts.append(portal_left)
                    portal_apex = portal_left
                    apex_index = left_index
                    portal_left = portal_apex
                    portal_right = portal_apex
                    left_index = right_index = apex_index
                    i = apex_index+1
                    continue

            # Update left vertex
            if self._triarea2(portal_apex, portal_left, left) <= 0.0:
                if self._vequal(portal_apex, portal_left) or self._triarea2(portal_apex, portal_right, left) > 0.0:
                    portal_left = left
                    left_index = i
                else:
                    # Left over right, insert right to path and restart scan
                    pts.append(portal_right)
                    portal_apex = portal_right
                    apex_index = right_index
                    portal_left = portal_apex
                    portal_right = portal_apex
                    left_index = right_index = apex_index
                    i = apex_index+1
                    continue
            i += 1

        # Append last point to path
        if len(pts) < max_pts:
            pts.append(portals[-1][0])

        def total_path_distance(points):
            total_distance = 0
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                total_distance += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            return total_distance
        dist = total_path_distance(pts)
        
        return pts[1:], dist


    
    def _is_point_in_triangle(self, point, triangle):
        v0, v1, v2 = [self.vertices[v] for v in triangle]
        v2_v0, v1_v0, point_v0 = v2 - v0, v1 - v0, point - v0
        dot00, dot01, dot02 = np.dot(v2_v0, v2_v0), np.dot(v2_v0, v1_v0), np.dot(v2_v0, point_v0)
        dot11, dot12 = np.dot(v1_v0, v1_v0), np.dot(v1_v0, point_v0)
        inv_denom = 1 / (dot00 * dot11 - dot01 * dot01)
        u, v = (dot11 * dot02 - dot01 * dot12) * inv_denom, (dot00 * dot12 - dot01 * dot02) * inv_denom
        return u >= 0 and v >= 0 and (u + v <= 1)

    def _find_triangle_containing_point(self, point):
        for i, tri in enumerate(self.triangles):
            if self._is_point_in_triangle(point, tri):
                return i
        return None

    def _find_shared_edge(self, triangle_a, triangle_b):
        edges_a = [(triangle_a[i], triangle_a[(i+1) % 3]) for i in range(3)]
        edges_b = [(triangle_b[i], triangle_b[(i+1) % 3]) for i in range(3)]
        for edge_a in edges_a:
            if edge_a in edges_b or (edge_a[1], edge_a[0]) in edges_b:
                return edge_a
        return None

    def _find_closest_triangle(self, point):
        # Helper function to calculate the distance between two points
        def _distance(p1, p2):
            return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        
        min_distance = float('inf')
        closest_triangle_index = None
        
        # Iterate through all triangles
        for i, tri in enumerate(self.triangles):
            centroid = np.mean([self.vertices[v] for v in tri], axis=0)
            dist = _distance(point, centroid)  # Calculate the distance from the point to the centroid
            
            # Update the closest triangle if this one is closer
            if dist < min_distance:
                min_distance = dist
                closest_triangle_index = i
        
        return closest_triangle_index
