
from agent.movement import BaseMovement
from agent.battery import Battery
from utilities.utils import Vec2f
from path_planning.navmesh import NavMesh
from agent.agent_state_machine import State, IdleState, DischargedState

from utilities.configuration import TOLERANCE_DISTANCE, TOLERANCE_ANGLE, MAX_FORWARD_VELOCITY


class Agent:
    """
    A class representing Agent.

    Attributes:
        id (str): String id of agent
        color (tuple): Color of agent
        position (Vec2f): Position of agent
        direction (Vec2f): Direction of agent
        movement (BaseMovement): Injected class that represents movement logic
        battery (BaseBattery): Injected class that represents battery
        navmesh (NavMesh): Class for pathfinding
        velocity_l (float): Linear velocity
        velocity_r (float): Rotational (angular) velocity
    """
    def __init__(self,
                 id:str,
                 color:tuple,
                 position:Vec2f,
                 direction:Vec2f,
                 movement:BaseMovement,
                 battery:Battery,
                 navmesh:NavMesh,
                 velocity_l:float=0,
                 velocity_r:float=0):
        self.id = id

        self.position = position
        self.direction = direction
        self.velocity_l = velocity_l
        self.velocity_r = velocity_r
        
        self.movement = movement
        self.battery = battery

        self.color = color
        self.spawn_position = position

        self.navmesh = navmesh
        self.path:list = []
        self.task = None

        self.state = IdleState(self)  # Initial state
        self.state.on_enter()
        self.state.update()

        self.update_count = 0
    
    def change_state(self, new_state:State):
        self.state.on_exit()
        self.state = new_state
        self.state.on_enter()

    def update(self, simulation_step:int, date_time_manager):
        """ Only for step in environment """
        self.update_count += simulation_step
        self.state.manage_battery(simulation_step, date_time_manager)
        self.state.update()
        if isinstance(self.state, DischargedState): return

        # Get new position, direction, velocity
        m1, m2 = self._get_actions()
        self.position, self.direction, self.velocity_l, self.velocity_r = self.movement.move(
            simulation_step, m1, m2, self.position, self.direction, self.velocity_l
        )

    
    def on_task_assigned(self, new_task):
        self.task = new_task
        self.set_path()
    
    def set_path(self):
        if self.task is not None:
            self.path, _ = self.navmesh.find_shortest_path(tuple(self.position), tuple(self.task.target.position))
            self.path = [Vec2f(pos) for pos in self.path]

    def update_path(self):
        if self.path:
            while True:
                if len(self.path)==0: break
                if self.position.is_close(self.path[0], TOLERANCE_DISTANCE):
                    self.path.pop(0)
                else: break
     
    def has_reached_target(self):
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

