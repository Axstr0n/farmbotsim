
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


FONT_PATH = "../assets/fonts/dejavu-sans-mono/DejaVuSansMono.ttf"


BASE_PARAMS = {
    "simulation": {
        "simulation_step": 1,
        "n_agents": 3,
        "fps": 60,
        "render_interval": 1,
        "date_time": "01.01.2025 00:00:00",
    },
    "render": {
        "scene": {
            "crop_field": True,
            "coordinate_system": True,
            "spawning_area": True,
            "obstacles": True,
            "charging_stations": True,
            "agents": True,
            "navmesh": False,
            "graph": False,
            "drag_points": False,
            "mouse_scene_pos": True,
            "fps": True,
        },
        "gui": {
            "draw": True,
            "step_count": True,
            "date_time": True,
            "field_params": False,
            "spawning_area_params": False,
            "agent_stats": True,
            "station_stats": True,
            "crop_field_stats": True,
            "tasks": True,
        }
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
    "simulation.date_time": "01.03.2025 00:00:00",
    "simulation.n_agents": 4,
    "simulation.render_interval": 10,
})
EDITOR_PREVIEW_PARAMS = get_params({
    "simulation.n_agents": 0,
    "render.scene.drag_points": True,
    "render.gui.step_count": False,
    "render.gui.date_time": False,
    "render.gui.field_params": True,
    "render.gui.spawning_area_params": True,
    "render.gui.agent_stats": False,
    "render.gui.crop_field_stats": False,
    "render.gui.tasks": False
})
NAVMESH_PREVIEW_PARAMS = get_params({
    "simulation.n_agents": 2,
    "render.scene.navmesh": True,
    "render.gui.station_stats": False,
    "render.gui.crop_field_stats": False,
    "render.gui.tasks": False
})
TASK_PREVIEW_PARAMS = get_params({
    "simulation.n_agents": 4,
})
