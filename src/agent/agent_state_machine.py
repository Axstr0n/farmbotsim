from abc import ABC, abstractmethod

from utilities.states import CropState
from utilities.configuration import MAX_FORWARD_VELOCITY
from utilities.configuration import BATTERY_DISCHARGE_STATE_IDLE, BATTERY_DISCHARGE_STATE_TRAVEL, BATTERY_DISCHARGE_STATE_WORK_SCAN, BATTERY_DISCHARGE_STATE_WORK_PROCESS, BATTERY_CHARGE_STATE_CHARGING

DEBUG_PRINT_STATE_CHANGE = False

class State(ABC):
    def __init__(self, agent):
        self.agent = agent
    def on_enter(self):
        pass
    def update(self):
        if self.agent.battery.get_soc() <= 0:
            self.agent.change_state(DischargedState(self.agent))
    def on_exit(self):
        pass
    def manage_battery(self, dt):
        raise NotImplementedError("This method should be overridden.")

class IdleState(State):
    def on_enter(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Entering Idle State.")
    
    def update(self):
        super().update()
        if self.agent.task is not None and not self.agent.has_reached_target():
            self.agent.change_state(TravelState(self.agent))

    def on_exit(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Exiting Idle State")
    
    def manage_battery(self, dt):
        self.agent.battery.discharge(power_w=BATTERY_DISCHARGE_STATE_IDLE, time_s=dt)

class DischargedState(State):
    def on_enter(self):
        print(f"{self.agent.id} Entering Discharged State.")
        self.agent.task = None
    
    def update(self):
        pass

    def on_exit(self):
        raise ValueError("Shouldn't go out of DischargedState")

    def manage_battery(self, dt):
        pass

class TravelState(State):
    def on_enter(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Entering Travel State")
        self.agent.set_path()
        
    def update(self):
        super().update()
        self.agent.update_path()
        if self.agent.has_task_and_at_location("station"):
            self.agent.change_state(ChargingState(self.agent))
        elif self.agent.has_task_and_at_location("crop") and self.agent.task.object.state == CropState.UNPROCESSED:
            self.agent.change_state(WorkScanState(self.agent))
        elif self.agent.has_task_and_at_location("crop") and self.agent.task.object.state == CropState.SCANNED:
            self.agent.change_state(WorkProcessState(self.agent))
        elif self.agent.has_task_and_at_location("crop") and self.agent.task.object.state == CropState.PROCESSED:
            self.agent.change_state(IdleState(self.agent))
            self.agent.task = None
        elif self.agent.task is not None and self.agent.has_reached_target():
            self.agent.change_state(IdleState(self.agent))
            #self.agent.task = None

    def on_exit(self):
        self.agent.path = []
        self.agent.update_count = 0
        #if self.agent.task.target_id == "idle": self.agent.task = None
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Exiting Travel State")

    def manage_battery(self, dt):
        self.agent.battery.discharge(power_w=BATTERY_DISCHARGE_STATE_TRAVEL*self.agent.velocity_l/MAX_FORWARD_VELOCITY, time_s=dt)

class ChargingState(State):
    def on_enter(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Entering Charging State")
    
    def update(self):
        super().update()
        if self.agent.task is not None and not self.agent.task.target_id.startswith("station"):
            self.agent.change_state(TravelState(self.agent))
    
    def on_exit(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Exiting Charging State")
    
    def manage_battery(self, dt):
        self.agent.battery.charge(power_w=BATTERY_CHARGE_STATE_CHARGING, time_s=dt)

class WorkScanState(State):
    def on_enter(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Entering WorkScan State")
    
    def update(self):
        super().update()
        if self.agent.task is not None and not self.agent.task.target_id.startswith("crop"):
            self.agent.change_state(TravelState(self.agent))
        elif self.agent.task.object.state == CropState.SCANNED:
            self.agent.change_state(WorkProcessState(self.agent))
        
        else: self.agent.task.object.process()
    
    def on_exit(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Exiting WorkScan State")
    
    def manage_battery(self, dt):
        self.agent.battery.discharge(power_w=BATTERY_DISCHARGE_STATE_WORK_SCAN, time_s=dt)

class WorkProcessState(State):
    def on_enter(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Entering WorkProcess State")

    def update(self):
        super().update()
        if self.agent.task is not None and not self.agent.task.target_id.startswith("crop"):
            self.agent.change_state(TravelState(self.agent))
        elif self.agent.task.object.state == CropState.PROCESSED:
            self.agent.task = None
            self.agent.change_state(IdleState(self.agent))
        
        else: self.agent.task.object.process()
    
    def on_exit(self):
        if DEBUG_PRINT_STATE_CHANGE: print(f"{self.agent.id} Exiting WorkProcess State")

    def manage_battery(self, dt):
        self.agent.battery.discharge(power_w=BATTERY_DISCHARGE_STATE_WORK_PROCESS, time_s=dt)

