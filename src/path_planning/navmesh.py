import math
import numpy as np
import triangle as tr
import networkx as nx

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __eq__(self, other):
        return self.x==other.x and self.y==other.y
    
    def __repr__(self):
        return f'Point(x={round(self.x,2)}, y={round(self.y,2)})'

class Segment:
    def __init__(self, p1:Point, p2:Point):
        self.p1 = p1
        self.p2 = p2
    
    def __eq__(self, other):
        if self.p1==other.p1 and self.p2==other.p2: return True
        if self.p1==other.p2 and self.p2==other.p1: return True
        return False
    
    def __repr__(self):
        return f'Segment(p1={self.p1}, p2={self.p2})'

class Polygon:
    def __init__(self, points:list[Point]):
        self.points = points
        if self.is_clockwise():
            self.points = list(reversed(points))
        self.create()
    
    def create(self):
        self.segments = []
        for i in range(len(self.points)):
            self.segments.append(Segment(self.points[i], self.points[(i+1)%len(self.points)]))
        self.center = self.calculate_center()

    def calculate_center(self):
        if len(self.points) < 3:
            raise ValueError("A polygon must have at least 3 points")

        points = self.points + [self.points[0]]
        A = 0  # Signed area
        Cx = 0
        Cy = 0

        for i in range(len(points) - 1):
            x0, y0 = points[i].x, points[i].y
            x1, y1 = points[i + 1].x, points[i + 1].y

            cross_product = (x0 * y1) - (x1 * y0)
            A += cross_product
            Cx += (x0 + x1) * cross_product
            Cy += (y0 + y1) * cross_product

        A *= 0.5
        if A == 0:
            raise ValueError("Degenerate polygon (area is zero)")

        Cx /= (6 * A)
        Cy /= (6 * A)

        return Point(Cx, Cy)

    def contains_segment(self, segment:Segment):
        for segment_ in self.segments:
            if segment_ == segment: return True
        return False
    
    def is_point_in_poly(self, point: Point):
        # Ray-casting algorithm to check if the point is inside the polygon
        count = 0
        x_intersect = point.x
        y_intersect = point.y
        
        for segment in self.segments:
            p1, p2 = segment.p1, segment.p2
            
            # Check if the point is on a horizontal ray
            if min(p1.y, p2.y) < y_intersect <= max(p1.y, p2.y):
                # Find where the ray intersects the segment
                x_at_y = p1.x + (y_intersect - p1.y) * (p2.x - p1.x) / (p2.y - p1.y)
                
                if x_at_y > x_intersect:
                    count += 1
        
        # Point is inside the polygon if the count of intersections is odd
        return count % 2 == 1
    
    def is_convex(self):
        # A polygon with fewer than 3 points is not a polygon
        if len(self.points) < 3:
            return False
        
        # For a polygon to be convex, the cross product of consecutive edges
        # should have the same sign (all positive or all negative)
        
        # Initialize with None to detect the first sign
        sign = None
        
        n = len(self.points)
        for i in range(n):
            # Get three consecutive points
            p1 = self.points[i]
            p2 = self.points[(i + 1) % n]
            p3 = self.points[(i + 2) % n]
            
            # Calculate vectors from p2 to p1 and p2 to p3
            v1_x, v1_y = p1.x - p2.x, p1.y - p2.y
            v2_x, v2_y = p3.x - p2.x, p3.y - p2.y
            
            # Calculate cross product of these vectors
            cross_product = v1_x * v2_y - v1_y * v2_x
            
            # If cross product is 0, the three points are collinear
            # Some definitions of convexity allow collinear points, others don't
            # Here we're allowing collinear points
            #if cross_product != 0:
            if abs(cross_product) >= 0.000001:
                current_sign = 1 if cross_product > 0 else -1
                
                # If sign is not initialized, set it
                if sign is None:
                    sign = current_sign
                # If the sign changes, the polygon is not convex
                elif sign != current_sign:
                    return False
        
        # If we've gone through all points without finding a sign change, the polygon is convex
        return True

    def _get_area(self):
        # Calculate the signed area using the shoelace formula (cross product method)
        area = 0
        n = len(self.points)
        for i in range(n):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % n]  # Wrap around to the first point
            area += p1.x * p2.y - p2.x * p1.y
        
        return area
    
    def get_area(self):
        return abs(self._get_area())

    def is_clockwise(self):
        # If the area is negative, the points are in clockwise order.
        return self._get_area() < 0

    def __repr__(self):
        return f'Polygon(points={self.points})'
    

class NavMesh:
    def __init__(self, boundary, points=[], obstacles=[]):
        self.boundary = np.array(boundary)
        self.obstacles = [np.array(obs) for obs in obstacles]
        self.vertices, self.triangles, self.portals = [], [], []
        self.graph = nx.Graph()
        self.polygons = []
        self._triangulate(points)
    
    def _triangulate(self, extra_points):
        # Make points
        points = self.boundary.tolist()
        points.extend(extra_points)
        # Make segments
        segments = [[i, (i + 1) % len(self.boundary)] for i in range(len(self.boundary))]
        # Make holes in navmesh
        holes = []
        for obs in self.obstacles:
            hole_center = np.mean(obs, axis=0)
            holes.append(hole_center.tolist())
            start_index = len(points)
            points.extend(obs.tolist())
            segments.extend([[start_index + i, start_index + (i + 1) % len(obs)] for i in range(len(obs))])
        # Pack and triangulate
        data = {'vertices': np.array(points), 'segments': np.array(segments), 'holes': np.array(holes)}
        triangulated = tr.triangulate(data, 'p')
        #triangulated = tr.triangulate(data, 'pq30')
        if 'triangles' in triangulated:
            self.triangles = triangulated['triangles']
            self.vertices = triangulated['vertices']
            # Round vertices
            precision = 8
            self.vertices = [[round(v[0], precision), round(v[1], precision)] for v in self.vertices]
            # Generate polygons
            self.polygons = []
            for tri in self.triangles:
                pts = []
                for index in tri:
                    pts.append(Point(self.vertices[index][0], self.vertices[index][1]))
                polygon = Polygon(pts)
                self.polygons.append(polygon)
            self._optimize()
            self._build_graph()

    def _optimize(self):
        """ Combines polygons to make navmesh faster """
        # Get segments of all polygons
        segments = []
        for poly in self.polygons:
            for segment in poly.segments:
                if segment in segments: continue
                segments.append(segment)

        def find_polygons_with_segment(segment, polygons):
            found_polys = []
            for poly in polygons:
                if poly.contains_segment(segment): found_polys.append(poly)
            return found_polys

        def merge_polys(poly1, poly2):
            common_segment = None
            for segment in poly1.segments:
                if poly2.contains_segment(segment):
                    common_segment = segment
                    break
            if common_segment is None: raise ValueError("No common segment - Shouldn't happen")

            # get common segment of poly1
            common_seg_1 = None
            for seg in poly1.segments:
                if seg == common_segment:
                    common_seg_1 = seg
                    break
            # find indexes of segment for poly1
            segment_indexes_1 = []
            for i, p in enumerate(poly1.points):
                if p in (common_segment.p1, common_segment.p2): segment_indexes_1.append(i)
            if len(segment_indexes_1) != 2: raise ValueError("Not 2 point for segment - Shouldn't happen")
            segment_end_index_1 = segment_indexes_1[0] if common_seg_1.p2==poly1.points[segment_indexes_1[0]] else segment_indexes_1[1]
            new_points = []
            # add poly1 points
            for i in range(len(poly1.points)):
                index = (segment_end_index_1 + i) % len(poly1.points)
                new_points.append(poly1.points[index])

            # get common segment of poly2
            common_seg_2 = None
            for seg in poly2.segments:
                if seg == common_segment:
                    common_seg_2 = seg
                    break
            # find indexes of segment for poly2
            segment_indexes_2 = []
            for i, p in enumerate(poly2.points):
                if p in (common_segment.p1, common_segment.p2): segment_indexes_2.append(i)
            if len(segment_indexes_2) != 2: raise ValueError("Not 2 point for segment - Shouldn't happen")
            segment_end_index_2 = segment_indexes_2[0] if common_seg_2.p2==poly2.points[segment_indexes_2[0]] else segment_indexes_2[1]
            # add poly2 points
            for i in range(len(poly2.points)):
                index = (segment_end_index_2 + i) % len(poly2.points)
                point = poly2.points[index]
                if point not in new_points: new_points.append(point)

            if len(new_points) != len(poly1.points) + len(poly2.points) - 2: raise ValueError("Final list is missing points")

            return Polygon(new_points)

        
        for i, segment in enumerate(segments):
            polys_with_segment = find_polygons_with_segment(segment, self.polygons)
            if len(polys_with_segment) > 2:
                raise ValueError("More than 2 poly have common segment. Shouldn't happen")
            if len(polys_with_segment) != 2: continue # boundary / hole segment
            merged_poly = merge_polys(polys_with_segment[0], polys_with_segment[1])
            if not merged_poly.is_convex(): continue
            if abs(polys_with_segment[0].get_area()+polys_with_segment[1].get_area()-merged_poly.get_area()) > 0.00002:
                raise ValueError(f"Area of merged poly should be same: {polys_with_segment[0].get_area()+polys_with_segment[1].get_area()} != {merged_poly.get_area()}")
            self.polygons.remove(polys_with_segment[0])
            self.polygons.remove(polys_with_segment[1])
            self.polygons.append(merged_poly)


    def _build_graph(self):
        self.graph.clear()
        def distance(p1, p2):
            """Helper function to calculate the Euclidean distance between two points."""
            return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
        
        for i, poly1 in enumerate(self.polygons):
            for j in range(i+1, len(self.polygons)):
                poly2 = self.polygons[j]
                if self._find_shared_segment(poly1, poly2) is not None:
                    p1 = poly1.center
                    p2 = poly2.center
                    edge_length = distance(p1,p2)
                    self.graph.add_edge(i, j, weight=edge_length)
        

    def find_shortest_path(self, start, end):
        start = Point(start[0], start[1])
        end = Point(end[0], end[1])
        start_poly = self._find_poly_containing_point(start)
        end_poly = self._find_poly_containing_point(end)
        if start_poly is None:
            start_poly = self._find_closest_poly(start)
        if end_poly is None:
            end_poly = self._find_closest_poly(end)
        shortest_path = nx.astar_path(self.graph, start_poly, end_poly)
        portals = [(start, start)]
        for i in range(len(shortest_path) - 1):
            shared_segment = self._find_shared_segment(self.polygons[shortest_path[i]], self.polygons[shortest_path[i + 1]])
            if shared_segment:
                portals.append((shared_segment.p1, shared_segment.p2))
        portals.append((end, end))
        self.portals = portals
        return self._funnel_algorithm(portals)

    def _triarea2(self, a:Point, b:Point, c:Point):
        """
        Computes twice the signed area of the triangle formed by points a, b, and c in 2D.
        
        Parameters:
        a, b, c : tuple or list of floats (x, y)
        
        Returns:
        float : twice the signed area of the triangle
        """
        ax, ay = b.x - a.x, b.y - a.y
        bx, by = c.x - a.x, c.y - a.y
        return bx * ay - ax * by  # Determinant formula

    def _vdistsqr(self, a:Point, b:Point):
        """
        Computes the squared Euclidean distance between points a and b.
        
        Parameters:
        a, b : tuple or list of floats (x, y, [z])
        
        Returns:
        float : squared distance between a and b
        """
        return (a.x - b.x) ** 2 + (a.y - b.y) ** 2

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
                p1 = points[i]
                p2 = points[i + 1]
                total_distance += math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
            return total_distance
        dist = total_path_distance(pts)

        # to tuples
        pts = [(p.x,p.y) for p in pts]
        
        return pts[1:], dist

    def _find_shared_segment(self, poly1, poly2):
        for segment1 in poly1.segments:
            for segment2 in poly2.segments:
                if segment1 == segment2: return segment1
        return None

    def _find_poly_containing_point(self, point):
        for i, poly in enumerate(self.polygons):
            if poly.is_point_in_poly(point):
                return i
        return None

    def _find_closest_poly(self, point:Point):
        # Helper function to calculate the distance between two points
        def _distance(p1, p2):
            return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
        
        min_distance = float('inf')
        closest_poly_index = None
        
        # Iterate through all polys
        for i, poly in enumerate(self.polygons):
            dist = _distance(point, poly.center)
            
            if dist < min_distance:
                min_distance = dist
                closest_poly_index = i
        
        return closest_poly_index
