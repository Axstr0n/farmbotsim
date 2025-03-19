from utilities.states import AgentState, CropState
from utilities.configuration import MAX_FORWARD_WORKING_VELOCITY

class AgentStateMachine:
    """
    A class representing AgentStateMachine.

    Attributes:
        agent (Agent): Agent object to which state machine is attached
    """
    def __init__(self, agent):
        self.agent = agent
        self.state = AgentState.IDLE

    def update_state(self):
        """Automatically determine the next state based on agent"""
        threshold_fast = MAX_FORWARD_WORKING_VELOCITY
        match self.state:
            
            case _ if self.agent.battery.get_soc() <= 0:
                self.change_state(AgentState.DISCHARGED, "Discharged")

            case AgentState.IDLE:
                # if self.agent.has_task_and_at_location("station"):
                #     self.change_state(AgentState.CHARGING, "Charging")
                # elif self.agent.has_task_and_at_location("crop") and self.agent.task.object.state == CropState.UNPROCESSED:
                #     self.change_state(AgentState.WORK_SCAN, "Work Scan")
                # elif self.agent.has_task_and_at_location("crop") and self.agent.task.object.state == CropState.SCANNED:
                #     self.change_state(AgentState.WORK_PROCESS, "Work Process")
                if self.agent.velocity_l != 0 or self.agent.velocity_r != 0:
                    self.change_state(AgentState.TRAVEL_SLOW, "Travel Slow")

            case AgentState.CHARGING:
                if self.agent.task is not None and not self.agent.task.target_id.startswith("station"):
                    self.change_state(AgentState.TRAVEL_SLOW, "Travel Slow")

            case AgentState.WORK_SCAN:
                if self.agent.task is not None and not self.agent.task.target_id.startswith("crop"):
                    self.change_state(AgentState.TRAVEL_SLOW, "Travel Slow")
                elif self.agent.has_task_and_at_location("crop") and self.agent.task.object.state == CropState.SCANNED:
                    self.change_state(AgentState.WORK_PROCESS, "Work Process")

            case AgentState.WORK_PROCESS:
                if self.agent.task is not None and not self.agent.task.target_id.startswith("crop"):
                    self.change_state(AgentState.TRAVEL_SLOW, "Travel Slow")
                elif self.agent.task.object.state==CropState.PROCESSED:
                    #self.agent.task = None
                    self.change_state(AgentState.IDLE, "Idle")
            
            case AgentState.TRAVEL_SLOW:
                if self.agent.velocity_l > threshold_fast:
                    self.change_state(AgentState.TRAVEL_FAST, "Travel Fast")
                elif self.agent.velocity_l == 0 and self.agent.velocity_r == 0:
                    self.change_state(AgentState.IDLE, "Idle")
                elif self.agent.has_task_and_at_location("station"):
                    self.change_state(AgentState.CHARGING, "Charging")
                elif self.agent.has_task_and_at_location("crop") and self.agent.task.object.state == CropState.UNPROCESSED:
                    self.change_state(AgentState.WORK_SCAN, "Work Scan")
                elif self.agent.has_task_and_at_location("crop") and self.agent.task.object.state == CropState.SCANNED:
                    self.change_state(AgentState.WORK_PROCESS, "Work Process")

            case AgentState.TRAVEL_FAST:
                if self.agent.velocity_l <= threshold_fast and self.agent.velocity_r == 0:
                    self.change_state(AgentState.TRAVEL_SLOW, "Travel Slow")

    def change_state(self, new_state:AgentState, message):
        """Helper function to change state and print message."""
        if self.state != new_state:
            # print(f"{self.agent.id} {self.state.value} → {new_state.value}")
            self.state = new_state

    def get_state(self):
        return self.state
