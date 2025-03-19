import pygame
import math

from rendering.camera import Camera

from utilities.states import AgentState, CropState, CropRowState
from utilities.utils import Vec2f
from utilities.configuration import AGENT_RADIUS, CROP_RADIUS, CHARGING_STATION_WIDTH, CHARGING_STATION_HEIGHT

color_default = (255,255,255)
color_negative = (0,0,0)
color_red = (158, 8, 8)
color_green = (1, 145, 1)
color_orange = (255, 178, 46)

COLORS = {
    "agent_discharged": (255,255,255,10),
    "target_outline": color_default,
    "path": color_negative,

    "navmesh": color_negative,

    "coordinate_system": color_default,

    "spawning_area": color_negative,

    "crop_row_assigned": color_red,
    "crop_row_free": color_green,

    "crop_unprocessed": color_red,
    "crop_scanning": (200,50,0),
    "crop_scanned": (100,100,0),
    "crop_processing": (50,200,0),
    "crop_processed": color_green,

    "obstacle": color_negative,

    "station_outline": color_negative,
    "station_free": color_green,
    "station_occupied": color_red,
    "station_text": color_default,

    "draggable": (255,0,0),

    "text": color_default,
}

#----- SCENE -----#

def render_agents(screen:pygame.surface, camera:Camera, agents):
    for i, agent_id in enumerate(agents):
        agent = agents[agent_id]
        color = agent.color if agent.state_machine.get_state()!=AgentState.DISCHARGED else COLORS["agent_discharged"]
        pos = camera.scene_to_screen_pos(agent.position)
        dir_end = camera.scene_to_screen_pos(agent.position + agent.direction*0.3)
        radius = camera.scene_to_screen_val(AGENT_RADIUS)
        pygame.draw.circle(screen, color, pos, radius)
        pygame.draw.aaline(screen, color, pos, dir_end, 1)

        # Task targets
        if agent.task is not None and agent.state_machine.get_state() != AgentState.DISCHARGED:
            target_size = 0.05
            size = camera.scene_to_screen_val(target_size)
            pos = camera.scene_to_screen_pos(agent.task.target.position)
            pygame.draw.circle(screen, COLORS["target_outline"], pos, size * 1.5)
            pygame.draw.circle(screen, color, pos, size)
        
        # Path
        if len(agent.path) > 0:
            line_width = 1
            path = [agent.position] + agent.path
            for i in range(len(path)-1):
                c = camera.scene_to_screen_pos(path[i])
                n = camera.scene_to_screen_pos(path[i+1])
                pygame.draw.line(screen, COLORS["path"], c, n, line_width)

def render_navmesh(screen:pygame.surface, camera:Camera, navmesh):
    line_width = 1 
    for tri in navmesh.triangles:
        pts = [navmesh.vertices[i] for i in tri]
        pts = [camera.scene_to_screen_pos(p) for p in pts]
        pygame.draw.polygon(screen, COLORS["navmesh"], pts, line_width)

def render_coordinate_system(screen:pygame.surface, camera:Camera, font:pygame.font):
    def draw_arrow(screen, start, end, color, width=2, arrow_size=10):
        # Draw the line
        pygame.draw.aaline(screen, color, start, end, width)
        # Calculate the angle of the arrow
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        # Calculate the points for the arrowhead
        arrow_point1 = (end[0] - arrow_size * math.cos(angle - math.pi / 6),
                        end[1] - arrow_size * math.sin(angle - math.pi / 6))
        arrow_point2 = (end[0] - arrow_size * math.cos(angle + math.pi / 6),
                        end[1] - arrow_size * math.sin(angle + math.pi / 6))
        # Draw the arrowhead
        pygame.draw.polygon(screen, color, [end, arrow_point1, arrow_point2])
    
    zero_pos = camera.scene_to_screen_pos((0,0))
    x_pos = camera.scene_to_screen_pos((1,0))
    y_pos = camera.scene_to_screen_pos((0,1))
    arrow_width = max(1, camera.scene_to_screen_val(0.05))
    arrow_size = camera.scene_to_screen_val(0.2)
    draw_arrow(screen, zero_pos, x_pos, COLORS["coordinate_system"], arrow_width, arrow_size)
    screen.blit(font.render("x", True,  COLORS["coordinate_system"]), x_pos)
    draw_arrow(screen, zero_pos, y_pos, COLORS["coordinate_system"], arrow_width, arrow_size)
    screen.blit(font.render("y", True,  COLORS["coordinate_system"]), y_pos)

def render_spawning_area(screen:pygame.surface, camera:Camera, config):
    ltp = config["left_top_pos"]
    wid = config["width"]
    hei = config["height"]
    ang = config["angle"]
    rtp = ltp.get_offset_position(wid, ang) # right top
    rbp = rtp.get_offset_position(hei, ang+90) # right bottom
    lbp = ltp.get_offset_position(hei, ang+90) # left bottom
    points = [camera.scene_to_screen_pos(pos) for pos in [ltp,rtp,rbp,lbp]]
    line_width = 1
    pygame.draw.polygon(screen, COLORS["spawning_area"], points, line_width)

def render_crop_field(screen:pygame.surface, camera:Camera, crop_field):
    for crop_id,crop in crop_field.crops_dict.items():
        if crop.state == CropState.UNPROCESSED:
            color = COLORS["crop_unprocessed"]
        elif crop.state == CropState.SCANNING:
            color = COLORS["crop_scanning"]
        elif crop.state == CropState.SCANNED:
            color = COLORS["crop_scanned"]
        elif crop.state == CropState.PROCESSING:
            color = COLORS["crop_processing"]
        elif crop.state == CropState.PROCESSED:
            color = COLORS["crop_processed"]
        else:
            color = color_negative
        pygame.draw.circle(screen, color, camera.scene_to_screen_pos(crop.position), camera.scene_to_screen_val(CROP_RADIUS))

def render_obstacles(screen:pygame.surface, camera:Camera, crop_field, draw_padded_obstacles=False):
    line_width = max(1, camera.scene_to_screen_val(0.1))
    for obs in crop_field.obstacles:
        points = [camera.scene_to_screen_pos(pos) for pos in obs]
        pygame.draw.polygon(screen, COLORS["obstacle"], points, 0)
    if draw_padded_obstacles:
        for obs in crop_field.padded_obstacles:
            points = [camera.scene_to_screen_pos(pos) for pos in obs]
            pygame.draw.polygon(screen, COLORS["obstacle"], points, 1)

def render_charging_stations(screen:pygame.surface, camera:Camera, stations, font:pygame.font):
    for i,station_id in enumerate(stations.keys()):
        station =stations[station_id]
        color = station.color
        # Main rect
        width = CHARGING_STATION_WIDTH
        height = CHARGING_STATION_HEIGHT
        left = station.position.x - width / 2
        top = station.position.y - height / 2
        # Indicator rect
        i_width = width
        i_height = 0.2
        i_left = station.position.x - width / 2
        i_top = station.position.y - height / 2 + height - i_height
        # Convert, draw
        width = camera.scene_to_screen_val(width)
        height = camera.scene_to_screen_val(height)
        left_top = camera.scene_to_screen_pos((left,top))
        rect = (left_top[0], left_top[1], width, height)
        pygame.draw.rect(screen, COLORS["station_outline"], rect)
        i_width = camera.scene_to_screen_val(i_width)
        i_height = camera.scene_to_screen_val(i_height)
        i_left_top = camera.scene_to_screen_pos((i_left,i_top))
        i_rect = (i_left_top[0], i_left_top[1], i_width, i_height)
        pygame.draw.rect(screen, color, i_rect)
        # Id
        text = font.render(f'{station.id.split('_')[1]}', True, COLORS["station_text"])
        screen.blit(text, (left_top))

def render_draggable_points(screen:pygame.surface, camera:Camera, draggable_objects):
    for id,pos in draggable_objects.items():
        pygame.draw.circle(screen, COLORS["draggable"], camera.scene_to_screen_pos(pos), 4)

def render_mouse_scene_pos(screen:pygame.surface, camera:Camera, font:pygame.font):
    screen_height = screen.get_size()[1]
    # Mouse position
    mouse_pos = Vec2f(pygame.mouse.get_pos())
    mouse_pos_render = font.render(f"Mouse pos: {mouse_pos}", True, COLORS["text"])
    screen.blit(mouse_pos_render, (0, screen_height-2*mouse_pos_render.get_height()))
    # Scene position of mouse
    scene_pos = camera.screen_to_scene_pos(mouse_pos)
    scene_pos_render = font.render(f"Scene pos: {scene_pos}", True, COLORS["text"])
    screen.blit(scene_pos_render, (0, screen_height-1*scene_pos_render.get_height()))


#----- GUI -----#

def render_gui_agents(gui, agents, draw_path=False, draw_task_target=False):
    color = COLORS["text"]
    gui.add_text("")
    gui.add_text_with_color("Agents: ", color)

    for i, agent_id in enumerate(agents):
        agent = agents[agent_id]
        p = agent.position
        d = agent.direction
        b = f"{agent.battery.get_soc():.2f}%"
        gui.add_text_with_color("▮", agent.color if agent.state_machine.get_state()!=AgentState.DISCHARGED else (255,255,255))
        gui.same_line()
        gui.add_text(f" {str(agent_id).ljust(8)}")
        gui.same_line()
        gui.add_text(f" P:{p}")
        gui.same_line()
        gui.add_text(f" D:{f'{d.get_angle("deg"):.2f}°'.rjust(8)}")
        gui.same_line()
        gui.add_text(f" V:{f'{agent.velocity_l:.2f}'.rjust(5)}")
        gui.same_line()
        gui.add_text(f" {str(agent.state_machine.get_state().value).ljust(12)}")
        gui.same_line()
        gui.add_text(f" {b.ljust(6)}")

        if draw_path:
            path = [target for target in agent.path]
            p = [f'{position}' for position in path]
            gui.add_text(str(p))
        if draw_task_target:
            gui.add_text("Task target: "+ str(agent.task.target_id if agent.task!=None else None))
            gui.add_text(f"{agent.task}")

def render_gui_field(gui, config):
    gui.add_text("")
    gui.add_text("Field: ")
    gui.add_text(f"▮ Left top position: {config["left_top_pos"]}")
    gui.add_text(f"▮ Angle: {config["angle"]}°")
    gui.add_text(f"▮ Number of rows: {config["n_rows"]}")
    gui.add_text(f"▮ Row spacing: {config["row_spacing"]}")
    gui.add_text(f"▮ Number of crops per row: {config["n_crops_per_row"]}")
    gui.add_text(f"▮ Crop spacing: {config["crop_spacing"]}")

def render_gui_stations(gui, stations):
    gui.add_text("")
    gui.add_text("Stations: ")
    for i, station_id in enumerate(stations):
        station = stations[station_id]
        p = station.position
        d = station.queue_direction.get_angle("deg")
        assigned =(" full".ljust(6), COLORS["station_occupied"]) if len(station.queue)>0 else (" empty".ljust(6), COLORS["station_free"])
        s_station_id = f" {str(station_id).ljust(8)}"
        s_position = f" P:{p}"
        s_direction = f" D:{f'{d:.2f}°'.rjust(8)}"
        s_queue = f' Queue: {len(station.queue)}'
        
        gui.add_text_with_color("▮", station.color)
        gui.same_line()
        gui.add_text(s_station_id)
        gui.same_line()
        gui.add_text(s_position)
        gui.same_line()
        gui.add_text(s_direction)
        gui.same_line()
        gui.add_text_with_color(assigned[0], assigned[1])
        gui.same_line()
        gui.add_text(s_queue)

def render_gui_spawning_area(gui, config):
    gui.add_text("")
    gui.add_text("Spawning area: ")
    gui.add_text(f"▮ Left top position: {config["left_top_pos"]}")
    gui.add_text(f"▮ Width: {config["width"]}")
    gui.add_text(f"▮ Height: {config["height"]}")
    gui.add_text(f"▮ Angle: {config["angle"]}°")

def render_gui_crop_field(gui, crop_field):
    gui.add_text("")
    gui.add_text("Crop rows:")
    for row_id in crop_field.rows_states.keys():
        row_state = crop_field.rows_states[row_id]
        row_assign = crop_field.rows_assign[row_id]
        assigned = ("assigned ".ljust(9), COLORS["crop_row_assigned"]) if row_assign!=False else ("free ".ljust(9), COLORS["crop_row_free"])
        
        gui.add_text_with_color("▮", COLORS["crop_processed"] if row_state==CropRowState.PROCESSED else COLORS["crop_unprocessed"])
        gui.same_line()
        gui.add_text(f"{str(row_id).ljust(6)}")
        gui.same_line()
        gui.add_text_with_color(assigned[0], assigned[1])
        for crop_id, crop in crop_field.crops_dict.items():
            if crop_id.split("_")[1] != row_id.split("_")[1]: continue
            if crop.state == CropState.UNPROCESSED:
                color = COLORS["crop_unprocessed"]
            elif crop.state == CropState.SCANNING:
                color = COLORS["crop_scanning"]
            elif crop.state == CropState.SCANNED:
                color = COLORS["crop_scanned"]
            elif crop.state == CropState.PROCESSING:
                color = COLORS["crop_processing"]
            elif crop.state == CropState.PROCESSED:
                color = COLORS["crop_processed"]
            else:
                color = color_negative
            gui.same_line()
            gui.add_text_with_color("▮", color)

def render_gui_tasks(gui, task_manager, n_agents):
    gui.add_text("")
    gui.add_text("Tasks: ")

    printed_agents = []
    max_val = len(task_manager.history)-1
    for i in range(max_val, -1, -1):
        if len(printed_agents) == n_agents: break
        task = task_manager.history[i]
        if task.agent_id in printed_agents: continue
        gui.add_text("▮")
        gui.same_line()
        gui.add_text(f" {str(task.id).rjust(3)}")
        gui.same_line()
        gui.add_text(f" {task.agent_id.ljust(8)}")
        gui.same_line()
        gui.add_text(f" {task.target_id.ljust(10)}")
        printed_agents.append(task.agent_id)
