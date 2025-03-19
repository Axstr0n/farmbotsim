
from agent.movement import BaseMovement
from agent.battery import BaseBattery
from utilities.utils import Vec2f
from path_planning.navmesh import NavMesh
from agent.agent_state_machine import AgentStateMachine

from utilities.states import AgentState

from utilities.configuration import TOLERANCE_DISTANCE, TOLERANCE_ANGLE, MAX_FORWARD_VELOCITY
from utilities.configuration import BATTERY_DISCHARGE_STATE_IDLE, BATTERY_DISCHARGE_STATE_TRAVEL, BATTERY_DISCHARGE_STATE_WORK_SCAN, BATTERY_DISCHARGE_STATE_WORK_PROCESS, BATTERY_CHARGE_STATE_CHARGING


state_power_dict = {
    AgentState.IDLE: BATTERY_DISCHARGE_STATE_IDLE ,
    AgentState.TRAVEL_FAST: BATTERY_DISCHARGE_STATE_TRAVEL,
    AgentState.TRAVEL_SLOW: BATTERY_DISCHARGE_STATE_TRAVEL,
    AgentState.WORK_SCAN: BATTERY_DISCHARGE_STATE_WORK_SCAN,
    AgentState.WORK_PROCESS: BATTERY_DISCHARGE_STATE_WORK_PROCESS,
    AgentState.CHARGING: BATTERY_CHARGE_STATE_CHARGING,
    AgentState.DISCHARGED: 0,
}


class Agent:
    """
    A class representing Agent.

    Attributes:
        id (str): String id of agent
        color (tuple): Color of agent
        position (Vec2f): Position of agent
        direction (Vec2f): Direction of agent
        velocity (float): Velocity of agent
        acceleration (float): Acceleration of agent
        movement (BaseMovement): Injected class that represents movement logic
        battery (BaseBattery): Injected class that represents battery
        state (AgentState): State of agent
    """
    def __init__(self,
                 id:str,
                 color:tuple,
                 position:Vec2f,
                 direction:Vec2f,
                 movement:BaseMovement,
                 battery:BaseBattery,
                 velocity_l:float=0,
                 velocity_r:float=0):
        self.id = id

        self.position = position
        self.direction = direction
        self.velocity_l = velocity_l
        self.velocity_r = velocity_r
        
        self.movement = movement
        self.battery = battery
        self.state_machine = AgentStateMachine(self)

        self.color = color
        self.spawn_position = position

        self.path:list = []
        self.task = None

        self.update_count = 0
    

    def update(self, dt:int, navmesh:NavMesh):
        """ Only for step in environment """
        self.state_machine.update_state()
        def update_path():
            # Calculate path to task target
            interval = 50
            if self.task is not None:# and self.update_count%interval==0:
                self.path, _ = navmesh.find_shortest_path(tuple(self.position), tuple(self.task.target.position))
                self.path = [Vec2f(pos) for pos in self.path]

            # Update path
            if self.path:
                while True:
                    if len(self.path)==0: break
                    if self.position.is_close(self.path[0], TOLERANCE_DISTANCE):
                        self.path.pop(0)
                    else: break

        match self.state_machine.state:
            case AgentState.DISCHARGED:
                return
            case AgentState.IDLE:
                #update_path()
                pass
            case AgentState.CHARGING:
                pass
            case AgentState.WORK_SCAN:
                self.task.object.process()
            case AgentState.WORK_PROCESS:
                self.task.object.process()
            case AgentState.TRAVEL_SLOW:
                #update_path()
                pass
            case AgentState.TRAVEL_FAST:
                #update_path()
                pass
        update_path()

        # Decrease battery based on state
        state = self.state_machine.get_state()
        if state == AgentState.CHARGING:
            self.battery.charge(power_w=state_power_dict[state], time_s=dt)
        elif state==AgentState.TRAVEL_SLOW or state==AgentState.TRAVEL_FAST:
            self.battery.discharge(power_w=state_power_dict[state]*self.velocity_l/MAX_FORWARD_VELOCITY, time_s=dt)
        else:
            self.battery.discharge(power_w=state_power_dict[state], time_s=dt)

        if self.task is not None and self._has_reached_target():
            self.path = []
            self.update_count = 0

        # Get new position, direction, velocity, acceleration
        m1, m2 = self._get_actions()
        self.position, self.direction, self.velocity_l, self.velocity_r = self.movement.move(
            dt, m1, m2, self.position, self.direction, self.velocity_l
        )

        if self.task is not None: self.update_count += 1
        self.state_machine.update_state()
    
    def on_task_assigned(self, new_task):
        self.task = new_task
     
    def _has_reached_target(self):
        """Checks if the agent has reached its target."""
        # If target has no direction requirement, just check position
        if len(self.path) == 1 and self.task.target.direction is None:
            return self.position.is_close(self.task.target.position, TOLERANCE_DISTANCE)
        
        # Otherwise, check both position and facing direction
        at_position = self.position.is_close(self.task.target.position, TOLERANCE_DISTANCE)
        if self.task.target.direction is None:
            facing_correctly = True
        else:
            facing_correctly = abs(self.direction.get_angle("deg") - self.task.target.direction.get_angle("deg")) <= TOLERANCE_ANGLE

        return at_position and facing_correctly

    def _get_actions(self):
        """Computes the rotation and acceleration inputs based on target."""
        if self.state_machine.get_state() in {AgentState.DISCHARGED, AgentState.CHARGING}:
            return 0, 0  # No movement when discharged or charging
        
        if not self.task:
            return 0, 0  # No movement if no target
        
        next_direction = None

        if len(self.path) > 0:  # Follow path normally
            next_position = self.path[0]
            if len(self.path) == 1:  # Last waypoint
                next_direction = self.task.target.direction  # Ensure correct final direction
        else:  # Path is empty, but still need to rotate
            next_position = self.position  # Stay in place
            next_direction = self.task.target.direction  # Ensure rotation to correct direction
        
        m1, m2 = self.movement.compute_movement_inputs(
            self.position, self.direction, next_position, next_direction
        )

        return m1, m2

    def has_task_and_at_location(self, obj):
        if self.task is None: return False
        if not self.task.target_id.startswith(obj): return False
        if not self.position.is_close(self.task.object.position, TOLERANCE_DISTANCE): return False
        if self.task.target.direction is None: pass
        elif not self.direction.is_close(self.task.target.direction, TOLERANCE_ANGLE): return False
        
        return True

    def __repr__(self):
        return f'Agent(id="{self.id}", position={self.position}, direction={self.direction}, velocity_l={self.velocity_l}, movement={self.movement}, battery={self.battery}, state={self.state_machine.get_state().value})'

