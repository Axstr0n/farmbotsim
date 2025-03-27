import pygame

from utilities.utils import Vec2f


class Camera:
    def __init__(self):
        self.zoom_level = 70.0            # Start zoom level
        self.zoom_factor = 1.1            # Zoom factor
        self.min_zoom = 30                # Minimum zoom level
        self.max_zoom = 200.0             # Maximum zoom level
        self.offset = Vec2f(0,0)          # Offset to track view changes
        self.dragging = False             # Flag to track if the middle mouse button is held down
        self.last_zoom_level = self.zoom_level
        self.last_mouse_pos = Vec2f(0, 0) # Last position of mouse
    
    def handle_event(self, event):
        mouse_pos = Vec2f(pygame.mouse.get_pos())

        # Mouse wheel scroll to zoom
        if event.type == pygame.MOUSEWHEEL:
            def adjust_for_zoom():
                self.offset += (mouse_pos - self.offset) * (1 - self.zoom_level / new_zoom_level)
                self.last_zoom_level = self.zoom_level
                self.zoom_level = new_zoom_level

            if event.y > 0:  # Scroll up (zoom in)
                if self.zoom_level < self.max_zoom:
                    new_zoom_level = self.zoom_level * self.zoom_factor
                    adjust_for_zoom()
            elif event.y < 0:  # Scroll down (zoom out)
                if self.zoom_level > self.min_zoom:
                    new_zoom_level = self.zoom_level / self.zoom_factor
                    adjust_for_zoom()

        # Middle mouse button press to start panning
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2:  # Middle mouse button
                self.dragging = True
                self.last_mouse_pos = Vec2f(event.pos)  # Record the position when dragging starts

        # Middle mouse button release to stop panning
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:  # Middle mouse button
                self.dragging = False

        # While dragging, update the offset based on mouse movement
        if event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_pos = Vec2f(event.pos)
                delta = mouse_pos - self.last_mouse_pos  # Calculate movement delta
                self.offset -= delta  # Adjust the offset
                self.last_mouse_pos = mouse_pos  # Update last mouse position for next movement

    def scene_to_screen_pos(self, p:Vec2f): # output tuple for render
        if isinstance(p, Vec2f):
            return tuple((p * self.zoom_level) - self.offset)
        elif len(p)==2:
            return (int(p[0] * self.zoom_level - self.offset.x), 
                    int(p[1] * self.zoom_level  -self.offset.y))
        raise ValueError(f"Parameter p ({type(p)}) can't be processed")
    
    def scene_to_screen_val(self, v:float):
        return int(v * self.zoom_level)
    
    def screen_to_scene_pos(self, p:Vec2f):
        return (p + self.offset) / self.zoom_level
    
    def screen_to_scene_val(self, v:float):
        return v / self.zoom_level

