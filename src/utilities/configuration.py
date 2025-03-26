
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
