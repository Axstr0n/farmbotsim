from enum import Enum

class AgentState(Enum):
    IDLE = "Idle"
    TRAVEL_FAST = "TravelFast"
    TRAVEL_SLOW = "TravelSlow"
    WORK_SCAN = "WorkScan"
    WORK_PROCESS = "WorkProcess"
    CHARGING = "Charging"
    DISCHARGED = "Discharged"

class CropRowState(Enum):
    UNPROCESSED = "unprocessed"
    PROCESSED = "processed"

class CropState(Enum):
    UNPROCESSED = "unprocessed"
    SCANNING = "scanning"
    SCANNED = "scanned"
    PROCESSING = "processing"
    PROCESSED = "processed"