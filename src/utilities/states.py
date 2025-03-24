from enum import Enum

class CropRowState(Enum):
    UNPROCESSED = "unprocessed"
    PROCESSED = "processed"

class CropState(Enum):
    UNPROCESSED = "unprocessed"
    SCANNING = "scanning"
    SCANNED = "scanned"
    PROCESSING = "processing"
    PROCESSED = "processed"