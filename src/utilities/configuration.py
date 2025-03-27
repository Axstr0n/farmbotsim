
# AGENT
AGENT_RADIUS = 0.06

# MOVEMENT
converter_kmh_ms = (0.2777777778)
MAX_FORWARD_VELOCITY = 10 * converter_kmh_ms # m/s
MAX_ANGULAR_VELOCITY = 0.1 * converter_kmh_ms # m/s
MAX_FORWARD_WORKING_VELOCITY = 3 * converter_kmh_ms # m/s
WHEEL_DISTANCE = 0.2 # m
WHEEL_RADIUS = 0.05 # m

# TOLERANCE
TOLERANCE_DISTANCE = 0.005 # m
TOLERANCE_ANGLE = 0.1 # °

# CROP
CROP_RADIUS = 0.1
CROP_SCAN_TIME = 1 * 60 # s
CROP_PROCESS_TIME = 2 * 60 # s

# CHARGING STATION
CHARGING_STATION_WIDTH = 0.5
CHARGING_STATION_HEIGHT = 0.5
CHARGING_STATION_WAITING_OFFSET = 1

# BATTERY
BATTERY_DISCHARGE_STATE_IDLE = 10
BATTERY_DISCHARGE_STATE_TRAVEL = 2*350
BATTERY_DISCHARGE_STATE_WORK_SCAN = 100
BATTERY_DISCHARGE_STATE_WORK_PROCESS = 400


CONFIG = {
    "spawning_area": {
        "left_top_pos": [3,4],
        "width": 4,
        "height": 1,
        "angle": 0.0
    },
    "field": {
        "left_top_pos": [3,0.5],
        "angle": 0.0,
        "n_rows": 4,
        "row_spacing": 0.5,
        "n_crops_per_row": 3,
        "crop_spacing": 0.3
    },
    "charging_stations": [
        {"position": [1.00,2.00], "queue_direction": [0.00,1.0]},
        {"position": [7.5,1.0], "queue_direction": [-0.00,1.0]}
    ]
}

FONT_PATH = "../assets/fonts/dejavu-sans-mono/DejaVuSansMono.ttf"


BASE_PARAMS = {
    "simulation": {
        "simulation_step": 1,
        "n_agents": 3,
        "fps": 60,
        "date_time": "01.03.2025 00:00:00",
        "scene_config": CONFIG
    },
    "render": {
        "draw_step_count": True,
        "draw_date_time": True,
        "draw_navmesh": True,
        "draw_graph": True,
        "draw_fps": True,
        "draw_stats": True,
        "draw_agent_stats": True,
        "draw_path": True,
        "draw_task_target":True,
        "draw_station_stats": True,
        "draw_row_stats": True,
        "draw_tasks": True,
    }
}

from copy import deepcopy
def get_params(overrides=None):
    """Returns a deep copy of BASE_PARAMS with optional overrides."""
    params = deepcopy(BASE_PARAMS)
    if overrides:
        for key, value in overrides.items():
            keys = key.split(".")  # Support nested keys like "render.draw_graph"
            d = params
            for k in keys[:-1]:
                d = d[k]  # Traverse nested dictionaries
            d[keys[-1]] = value  # Set the final key to new value
    return params

ENV_PARAMS = get_params({
    "simulation.n_agents": 4,
    "render.draw_navmesh": False,
    "render.draw_graph": False,
    "render.draw_fps": False,
    "render.draw_path": False,
    "render.draw_task_target": False
})
EDITOR_PREVIEW_PARAMS = get_params({
    "simulation.n_agents": 0,
    "render.draw_graph": False
})
NAVMESH_PREVIEW_PARAMS = get_params({
    "simulation.n_agents": 2,
    "render.draw_graph": False,
    "render-draw_task_target": False
})
TASK_PREVIEW_PARAMS = get_params({
    "simulation.n_agents": 4,
    "render.draw_navmesh": False,
    "render.draw_graph": False,
    "render.draw_path": False,
})
