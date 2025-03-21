import pygame
from collections import deque
import numpy as np
import math
import os
import json

from utilities.utils import Vec2f
from utilities.utils import generate_colors, padd_obstacle
from rendering.camera import Camera
from path_planning.navmesh import NavMesh
from utilities.states import AgentState, CropState, CropRowState
from utilities.configuration import CROP_SCAN_TIME, CROP_PROCESS_TIME, FONT_PATH, CHARGING_STATION_WAITING_OFFSET

from rendering.render import render_coordinate_system,render_navmesh,render_graph,render_crop_field,render_obstacles,render_charging_stations,render_spawning_area,render_draggable_points,render_mouse_scene_pos

class Crop:
    def __init__(self, id:str, position:Vec2f, required_scan_time:int, required_process_time:int, row_id:str, state:CropState=CropState.UNPROCESSED):
        self.id = id
        self.position = position
        self.state = state
        self.worked_time = 0
        self.required_scan_time = required_scan_time
        self.required_process_time = required_process_time

    def process(self):
        if self.state == CropState.PROCESSED:
            return
        
        self.worked_time += 1
        if self.state == CropState.UNPROCESSED and self.worked_time > 0:
            self.state = CropState.SCANNING
        elif self.state == CropState.SCANNING and self.worked_time >= self.required_scan_time:
            self.state = CropState.SCANNED
            self.worked_time = 0
        elif self.state == CropState.SCANNED and self.worked_time > 0:
            self.state = CropState.PROCESSING
        if  self.state == CropState.PROCESSING and self.worked_time >= self.required_process_time:
            self.state = CropState.PROCESSED
    
    def quit_work(self):
        match self.state:
            case CropState.UNPROCESSED: pass
            case CropState.SCANNING: self.state = CropState.UNPROCESSED
            case CropState.SCANNED: self.state = CropState.SCANNED
            case CropState.PROCESSING: self.state = CropState.SCANNED
            case CropState.PROCESSED: self.state = CropState.PROCESSED
        self.worked_time = 0
        # if self.state == CropState.PROCESSED:
    
    def __repr__(self):
        return f'Crop(id={self.id}, position={self.position}, state={self.state}, worked_time={self.worked_time})'

class CropField:
    def __init__(self, config):
        self.rows_states = {}
        self.rows_assign = {}
        self.crops_dict = {}
        _ = self.reset(config)

    def reset(self, config:dict):
        left_top_pos = config["left_top_pos"]
        angle = config["angle"]
        n_rows = config["n_rows"]
        row_spacing = config["row_spacing"]
        n_crops_per_row = config["n_crops_per_row"]
        crop_spacing = config["crop_spacing"]
        row_length = (n_crops_per_row-1) * crop_spacing
        field_length = (n_rows-1) * row_spacing

        self.n_rows = n_rows
        self.n_crops_per_row = n_crops_per_row

        self.rows_states = {f'row_{i}':CropRowState.UNPROCESSED for i in range(n_rows)}
        self.rows_assign = {f'row_{i}':False for i in range(n_rows)}

        # Generate CropRows with Crops
        top_pos = left_top_pos
        for i,row_id in enumerate(self.rows_states.keys()):
            for n in range(n_crops_per_row):
                pos = top_pos.get_offset_position(n*crop_spacing, angle+90)
                crop_id = f'crop_{i}_{n}'
                self.crops_dict[crop_id] = Crop(
                    id=crop_id,
                    position=pos,
                    required_scan_time=CROP_SCAN_TIME,
                    required_process_time=CROP_PROCESS_TIME,
                    row_id=row_id
                )
            top_pos = top_pos.get_offset_position(row_spacing, angle)

        # Init obstacles
        self.obstacles = []
        obstacle_width = 0.08
        height_offset = 0.2
        pos1 =  left_top_pos.get_offset_position(row_spacing/2, angle)
        pos1 = pos1.get_offset_position(-height_offset, angle+90)
        for i in range(n_rows):
            pos2 = pos1.get_offset_position(row_length+2*height_offset, angle+90)
            p1 = pos1.get_offset_position(-obstacle_width/2, angle)
            p2 = pos1.get_offset_position( obstacle_width/2, angle)
            p3 = pos2.get_offset_position( obstacle_width/2, angle)
            p4 = pos2.get_offset_position(-obstacle_width/2, angle)
            self.obstacles.append([p1,p2,p3,p4])
            pos1 = pos1.get_offset_position(row_spacing, angle)
        padding = 0.05
        self.padded_obstacles = [padd_obstacle(obs,padding) for obs in self.obstacles]

        # Extra surrond points for better navmesh
        offset = 0.5
        ltp = left_top_pos.get_offset_position(-offset, angle)
        ltp = ltp.get_offset_position(-offset, angle+90)
        mtp = ltp.get_offset_position(field_length/2 + offset, angle)
        rtp = ltp.get_offset_position(field_length + 2*offset, angle)
        lbp = ltp.get_offset_position(row_length+2*offset, angle+90)
        mbp = lbp.get_offset_position(field_length/2 + offset, angle)
        rbp = rtp.get_offset_position(row_length+2*offset, angle+90)
        self.surround_extra_points = [ltp,rtp,lbp,rbp]
        self.surround_extra_points = [tuple(p) for p in self.surround_extra_points]

        # For editor
        draggable_objects = {}
        draggable_objects["field-left_top_pos"] = left_top_pos
        draggable_objects["field-angle"] = left_top_pos.get_offset_position(field_length, angle).get_offset_position(row_length, angle+90)
        draggable_objects["field-n_rows"] =  left_top_pos.get_offset_position(row_spacing*(n_rows-1), angle)
        draggable_objects["field-row_spacing"] = left_top_pos.get_offset_position(row_spacing, angle)
        draggable_objects["field-n_crops_per_row"] =  left_top_pos.get_offset_position(crop_spacing*(n_crops_per_row-1), angle+90)
        draggable_objects["field-crop_spacing"] = left_top_pos.get_offset_position(crop_spacing, angle+90)

        return draggable_objects
    
    def update_field(self):
        for row_id, row_state in self.rows_states.items():
            if row_state == CropRowState.PROCESSED: continue
            state = CropRowState.PROCESSED
            for n in range(0,self.n_crops_per_row):
                crop = self.crops_dict[f"crop_{row_id.split("_")[1]}_{n}"]
                if crop.state != CropState.PROCESSED:
                    state = CropRowState.UNPROCESSED
                    break
            self.rows_states[row_id] = state
            if state == CropRowState.PROCESSED:
                self.rows_assign[row_id] = False

    def get_available_crops(self, agent_id=None):

        def get_edge_crops_in_row(row_id):
            crops = set()
            for n in range(0,self.n_crops_per_row):
                _crop = self.crops_dict[f"crop_{row_id.split("_")[1]}_{n}"]
                if _crop.state != CropState.PROCESSED:
                    crops.add(_crop)
                    break
            for n in range(self.n_crops_per_row-1, -1, -1):
                _crop = self.crops_dict[f"crop_{row_id.split("_")[1]}_{n}"]
                if _crop.state != CropState.PROCESSED:
                    crops.add(_crop)
                    break
            
            return crops

        crops = set()
        if agent_id:
            for row_id,row_assign in self.rows_assign.items():
                if row_assign == agent_id:
                    crops = get_edge_crops_in_row(row_id)
                    if len(crops) > 0: return crops

        for row_id, row_assign in self.rows_assign.items():
            if row_assign != False and row_assign != agent_id: continue
            crops.update(get_edge_crops_in_row(row_id))
        return crops

    def is_processed(self):
        for row_id, state in self.rows_states.items():
            if state != CropRowState.PROCESSED: return False
        return True

class ChargingStation:
    """
    A class representing a Charging Station.

    Attributes:
        id (str): Id of charging station
        position (Vec2f): Position of charging station
        queue_direction (Vec2f): Direction of waiting queue from station position
        color (tuple): RGB color
    """
    def __init__(self, id: str, position: Vec2f, queue_direction: Vec2f, waiting_offset: float, color:tuple):
        self.id = id
        self.position = position
        self.queue_direction = queue_direction
        self.agent_direction = queue_direction.rotate(math.pi)
        self.waiting_offset = waiting_offset
        self.queue = deque()
        self.color = color

    def request_charge(self, agent):
        """Assigns an agent to charge or queues them if the station is occupied."""
        self.queue.append(agent)
        # print(f'{agent.id} requested charging')
        return self.get_waiting_position(len(self.queue)-1)
    
    def release_agent(self, agent):
        if agent in self.queue:
            self.queue.remove(agent)
        for i,agent in enumerate(self.queue):
            agent.task.target.position = self.get_waiting_position(i)

    def get_waiting_position(self, queue_index):
        """Returns a waiting position based on queue index (e.g., spacing out agents)."""
        distance_ = queue_index * self.waiting_offset
        return self.position + self.queue_direction*distance_

    def __repr__(self):
        return f'ChargingStation(id={self.id}, position={self.position}, queue_direction={self.queue_direction}, color={self.color})'


class ConfigLoader:
    def __init__(self, file_path, default_config):
        self.file_path = file_path
        self.default_config = default_config
        self.config = None

    def load(self):
        # Check if the config file exists
        if not os.path.exists(self.file_path):
            # If the file doesn't exist, use the default config and save it to the file
            self.config = self._parse_json_with_vec2f(self.default_config)
            self.save_config()
        else:
            # If the file exists, load and process the config from the file
            with open(self.file_path, 'r') as file:
                self.config = json.load(file)
                self.config = self._parse_json_with_vec2f(self.config)

    def _parse_json_with_vec2f(self, data):
        # Recursively check if it's a list/tuple of length 2, then convert to Vec2f
        if isinstance(data, list):
            if len(data) == 2 and all(isinstance(i, (int, float)) for i in data):
                return Vec2f(data[0], data[1])
            return [self._parse_json_with_vec2f(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._parse_json_with_vec2f(value) for key, value in data.items()}
        return data

    def save_config(self):
        # Save the config as a JSON file
        with open(self.file_path, 'w') as file:
            #json.dump(self.config, file, cls=Vec2fEncoder, indent=4)
            json.dump(self.config, file, cls=Vec2fEncoder,indent=4, separators=(",", ": "))
            #json.dump(self.config, file, default=str, indent=4)
        print("Config saved")

    def get_config(self):
        return self.config

class Vec2fEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Vec2f):
            # If the object is a Vec2f, return its list representation
            return obj.to_list()
        # For other types, use the default encoder
        return super().default(obj)

class Scene:
    """
    A class representing a Scene.

    Attributes:
        config (dict): Dictionary that has data for scene configurement
    """
    def __init__(self, config: dict=None):
        
        super().__init__()
        self.config_file_path = "config.json"
        
        self.loader = ConfigLoader(self.config_file_path, config)
        self.loader.load()
        self.config = self.loader.get_config()

        self.draggable_objects = {} # string: pos

        self.reset()

    def reset(self):
        # Init spawning area
        self.calculate_spawning_area()
        # Init lines
        self.calculate_crop_field()
        # Init charging stations
        self.calculate_stations()

    def calculate_crop_field(self):
        self.crop_field = CropField(self.config["field"])
        obstacles = []
        for obs in self.crop_field.padded_obstacles:
            obstacles.append([(p.x,p.y) for p in obs])
        #obstacles = [(p.x, p.y) for obs in self.crop_field.obstacles for p in obs
        extra_points = self.crop_field.surround_extra_points
        self.navmesh = NavMesh([(0,0),(9,0),(9,7),(0,7)], points=extra_points, obstacles=obstacles)
        self.draggable_objects = {key: value for key, value in self.draggable_objects.items() if "field" not in key}
        self.draggable_objects.update(self.crop_field.reset(self.config["field"]))

    def calculate_stations(self):
        self.draggable_objects = {key: value for key, value in self.draggable_objects.items() if "station" not in key}
        charging_stations = self.config["charging_stations"]
        self.station_colors = generate_colors(len(charging_stations), 0.2)
        self.stations = [f'station_{i}' for i in range(len(charging_stations))]
        self.station_objects = {
            station_id: ChargingStation(
                id=station_id,
                position=data["position"],
                queue_direction=data["queue_direction"],
                waiting_offset=CHARGING_STATION_WAITING_OFFSET,
                color=self.station_colors[i]
            )
            for i, (station_id, data) in enumerate(zip(self.stations, charging_stations))
        }
        
        # For editor
        for station_id, station in self.station_objects.items():
            position_id = f'{station_id}_position'
            self.draggable_objects[position_id] = station.position
            direction_id = f'{station_id}_direction'
            self.draggable_objects[direction_id] = station.get_waiting_position(1)

    def calculate_spawning_area(self):
        left_top_pos = self.config["spawning_area"]["left_top_pos"]
        width = self.config["spawning_area"]["width"]
        height = self.config["spawning_area"]["height"]
        angle = self.config["spawning_area"]["angle"]

        top_right = left_top_pos.get_offset_position(width, angle)
        bot_left = left_top_pos.get_offset_position(height, angle+90)
        bot_right = bot_left.get_offset_position(width, angle)

        # For editor
        self.draggable_objects["sa_left_top_pos"] = left_top_pos
        self.draggable_objects["sa_width"] = top_right
        self.draggable_objects["sa_height"] = bot_left
        self.draggable_objects["sa_angle"] = bot_right

    def render_static(self, static_surface:pygame.Surface, camera:Camera, draw_navmesh:bool=False, draw_graph=False):
        font = pygame.font.Font(FONT_PATH, 10)

        if draw_navmesh: render_navmesh(static_surface, camera, self.navmesh)
        if draw_graph: render_graph(static_surface, camera, self.navmesh)

        render_coordinate_system(static_surface, camera, font)

        render_spawning_area(static_surface, camera, self.config["spawning_area"])
        
        render_obstacles(static_surface, camera, self.crop_field, draw_padded_obstacles=False)

        render_charging_stations(static_surface, camera, self.station_objects, font)

    def render_dynamic(self, dynamic_surface:pygame.Surface, camera:Camera, render_drag_points:bool=False):
        render_crop_field(dynamic_surface, camera, self.crop_field)
        if render_drag_points:
            render_draggable_points(dynamic_surface, camera, self.draggable_objects)
        font = pygame.font.Font(FONT_PATH, 10)
        render_mouse_scene_pos(dynamic_surface, camera, font)

    def get_object_at(self, mouse_pos, camera:Camera):
        mouse_pos = camera.screen_to_scene_pos(Vec2f(mouse_pos))
        for id, pos in self.draggable_objects.items():
            if mouse_pos.is_close(pos, 0.2):
                return id
        return None

    def save_config(self):
        self.loader.save_config()

