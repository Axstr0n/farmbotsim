import pygame
import math

from utilities.utils import Vec2f
from rendering.render import render_gui_crop_field, render_gui_field, render_gui_stations, render_gui_spawning_area
from preview.preview import Preview
from utilities.configuration import EDITOR_PREVIEW_PARAMS
EDITOR_PREVIEW_SIMULATION_PARAMS = EDITOR_PREVIEW_PARAMS["simulation"]
EDITOR_PREVIEW_RENDER_PARAMS = EDITOR_PREVIEW_PARAMS["render"]

def project_point_on_line_with_angle(p1: Vec2f, angle: float, p3: Vec2f):
    """
    Projects a point P3 onto a line defined by a point P1 and an angle.
    Computes the projected point and the distance from P1 to the projected point.

    Attributes:
        p1 (Vec2f): Point on the line
        angle (float): Angle of the line in degrees
        p3 (Vec2f): Point to be projected
    """
    x1, y1 = p1.x, p1.y
    x3, y3 = p3.x, p3.y

    # Convert angle to radians
    theta = math.radians(angle)

    # Direction vector of the line (dx, dy)
    dx = math.cos(theta)
    dy = math.sin(theta)

    # Vector P1 → P3
    vx, vy = x3 - x1, y3 - y1

    # Compute projection scalar t using dot product
    dot_product = vx * dx + vy * dy  # v • d
    # No need for division by |d|^2 since it's a unit vector

    # Compute projected point (Px, Py)
    Px = x1 + dot_product * dx
    Py = y1 + dot_product * dy

    # Compute distance from P1 to projected point
    distance = math.sqrt((Px - x1) ** 2 + (Py - y1) ** 2)

    return (Vec2f(Px, Py), distance)

def snap_to_circle_with_radius(p1: Vec2f, p2: Vec2f, radius: float):
    """
    Snaps P2 to the closest point on a circle centered at P1 with radius R
    and returns the angle of P1 -> Snapped Point.

    Attributes:
        p1 (Vec2f): Center of the circle
        p2 (Vec2f): Point to be snapped
        radius (float): Radius of the circle
    """
    x1, y1 = p1.x,p1.y
    x2, y2 = p2.x,p2.y

    # Compute direction vector P1 -> P2
    dx = x2 - x1
    dy = y2 - y1

    # Compute distance from P1 to P2
    distance = math.sqrt(dx**2 + dy**2)
    # Avoid division by zero (if P2 is exactly at P1, return any valid point on the circle)
    if distance == 0:
        return (x1 + radius, y1, 0.0)  # Default snap to the right with 0° angle
    
    # Compute the snapped point on the circle
    scale = radius / distance  # Normalize and scale to radius
    Px = x1 + dx * scale
    Py = y1 + dy * scale

    # Compute the angle from P1 to the new point
    angle = math.degrees(math.atan2(Py - y1, Px - x1))  # Convert to degrees

    return (Vec2f(Px, Py), angle)

def angle_to_direction(angle_deg: float):
    """Convert an angle in degrees to a normalized direction vector (dx, dy)."""
    angle_rad = math.radians(angle_deg)  # Convert degrees to radians
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    return Vec2f(dx, dy)


class SceneEditorPreview(Preview):
    def __init__(self, title="Preview"):
        super().__init__(EDITOR_PREVIEW_SIMULATION_PARAMS, title)

        # Dragging objects
        self.object_id = None
        self.is_dragging = False
        self.drag_offset = Vec2f(0, 0)
        
    def handle_events(self):
        events = super().handle_events()
        if events is False:  # Quit condition
            return False

        for event in events:  # Use the returned event list
            if event.type == pygame.KEYDOWN:
                mouse_pos = self.camera.screen_to_scene_pos(Vec2f(pygame.mouse.get_pos()))
                if event.key == pygame.K_s: # Add/Spawn station at mouse position
                    position = Vec2f(round(mouse_pos.x,2), round(mouse_pos.y,2))
                    station = {"position": position, "queue_direction": Vec2f(0,1)}
                    self.scene.config["charging_stations"].append(station)
                    self.scene.calculate_stations()
                if event.key == pygame.K_r: # Remove station at mouse position
                    for i,station in enumerate(self.scene.config["charging_stations"]):
                        position = station["position"]
                        if mouse_pos.distance_to(position) <= 0.2:
                            self.scene.config["charging_stations"].pop(i)
                            self.scene.calculate_stations()
                            break
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = event.pos
                    self.object_id = self.scene.get_object_at((mouse_x, mouse_y), self.camera)
                    if self.object_id == None:
                        pass
                    elif self.object_id.startswith(("station", "field", "sa")):
                        self.is_dragging = True
                        obj_x, obj_y = self.scene.draggable_objects[self.object_id]
                        self.drag_offset = Vec2f(self.camera.screen_to_scene_val(mouse_x) - obj_x,
                                                 self.camera.screen_to_scene_val(mouse_y) - obj_y)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.is_dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging and self.object_id:
                    mouse_x, mouse_y = event.pos
                    new_x = self.camera.screen_to_scene_val(mouse_x) - self.drag_offset.x
                    new_y = self.camera.screen_to_scene_val(mouse_y) - self.drag_offset.y
                    new_p = Vec2f(round(new_x,2), round(new_y,2))

                    if self.object_id.startswith("station"):
                        index = int(self.object_id.split("_")[1])
                        pos_ = self.scene.config["charging_stations"][index]["position"]
                        dir_ = self.scene.config["charging_stations"][index]["queue_direction"]
                        if "position" in self.object_id:
                            pos = new_p
                            self.scene.config["charging_stations"][index] = {"position":pos, "queue_direction": dir_}
                        elif "direction" in self.object_id:
                            radius = self.scene.station_objects[f'station_{index}'].waiting_offset
                            _,angle = snap_to_circle_with_radius(pos_, Vec2f(new_x,new_y), radius)
                            new_dir = angle_to_direction(angle)
                            new_dir = Vec2f(round(new_dir.x,2), round(new_dir.y,2))
                            self.scene.config["charging_stations"][index] = {"position": pos_, "queue_direction": new_dir}
                        self.scene.calculate_stations()

                    elif self.object_id.startswith("field"):
                        ltp = self.scene.config["field"]["left_top_pos"]
                        ang = self.scene.config["field"]["angle"]
                        nrows = self.scene.config["field"]["n_rows"]
                        rspa = self.scene.config["field"]["row_spacing"]
                        ncpr = self.scene.config["field"]["n_crops_per_row"]
                        cspa = self.scene.config["field"]["crop_spacing"]

                        rlen = (ncpr-1) * cspa # row length
                        flen = (nrows-1) * rspa # field length

                        if "field-left_top_pos" == self.object_id:
                            self.scene.config["field"]["left_top_pos"] = new_p
                        elif "field-angle" == self.object_id:
                            radius = math.sqrt(rlen**2 + flen**2)
                            _,angle = snap_to_circle_with_radius(ltp, new_p, radius)
                            extra = math.degrees( math.atan2(rlen, flen) )
                            self.scene.config["field"]["angle"] = round(angle - extra,2)
                        elif "field-n_rows" == self.object_id:
                            _,distance_ = project_point_on_line_with_angle(ltp, ang, new_p)
                            n_rows = int(distance_ / rspa)+1
                            self.scene.config["field"]["n_rows"] = max(3, n_rows)
                        elif "field-row_spacing" == self.object_id:
                            _,distance_ = project_point_on_line_with_angle(ltp, ang, new_p)
                            self.scene.config["field"]["row_spacing"] = max(0.3, round(distance_,4))
                        elif "field-n_crops_per_row" == self.object_id:
                            _,distance_ = project_point_on_line_with_angle(ltp, ang+90, new_p)
                            n_cpr = max(3,int(distance_ / cspa)+1)
                            self.scene.config["field"]["n_crops_per_row"] = round(n_cpr,2)
                        elif "field-crop_spacing" == self.object_id:
                            _,distance_ = project_point_on_line_with_angle(ltp, ang+90, new_p)
                            self.scene.config["field"]["crop_spacing"] = max(0.2, round(distance_,4))
                        
                        self.scene.calculate_crop_field()
                    
                    elif "sa" in self.object_id:
                        ltp = self.scene.config["spawning_area"]["left_top_pos"]
                        wid = self.scene.config["spawning_area"]["width"]
                        hei = self.scene.config["spawning_area"]["height"]
                        ang = self.scene.config["spawning_area"]["angle"]
                        if "sa_left_top_pos" == self.object_id:
                            self.scene.config["spawning_area"]["left_top_pos"] = new_p
                        elif "sa_width" == self.object_id:
                            _,distance_ = project_point_on_line_with_angle(ltp, ang, new_p)
                            self.scene.config["spawning_area"]["width"] = max(2, round(distance_,2))
                        elif "sa_height" == self.object_id:
                            _,distance_ = project_point_on_line_with_angle(ltp, ang+90, new_p)
                            self.scene.config["spawning_area"]["height"] = max(1, round(distance_,2))
                        elif "sa_angle" == self.object_id:
                            radius = math.sqrt(hei**2 + (wid)**2)
                            _,angle = snap_to_circle_with_radius(ltp, new_p, radius)
                            extra = math.degrees( math.atan2(hei, wid) )
                            self.scene.config["spawning_area"]["angle"] = round(angle - extra,2)
                        self.scene.calculate_spawning_area()

        return True
    
    def render(self):
        self.screen.fill((40,40,40))
        self.scene.render_static(self.screen, self.camera, draw_navmesh=EDITOR_PREVIEW_RENDER_PARAMS["draw_navmesh"], draw_graph=EDITOR_PREVIEW_RENDER_PARAMS["draw_graph"])
        self.scene.render_dynamic(self.screen, self.camera, render_drag_points=True)

        self.gui.begin_window(0,0,0,0,"EDITOR",3,380)

        self.gui.add_text("")
        self.gui.add_text("S - Spawn station")
        self.gui.add_text("R - Remove station")

        self.gui.add_text("")
        if self.gui.add_button("Save scene config"):
            self.scene.save_config()

        render_gui_field(self.gui, self.scene.config["field"])
        render_gui_stations(self.gui, self.scene.station_objects)
        render_gui_spawning_area(self.gui, self.scene.config["spawning_area"])
        render_gui_crop_field(self.gui, self.scene.crop_field)

        self.gui.end_window()
        self.gui.windows[0].active = True # Set window to active
        self.gui.draw()

        pygame.display.flip()


if __name__ == "__main__":

    editor = SceneEditorPreview("Scene Editor Preview")
    editor.run()

