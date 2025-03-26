import math
from abc import ABC, abstractmethod

from utilities.utils import Vec2f
from utilities.configuration import MAX_FORWARD_VELOCITY, MAX_ANGULAR_VELOCITY, MAX_FORWARD_WORKING_VELOCITY, WHEEL_DISTANCE, WHEEL_RADIUS, TOLERANCE_DISTANCE, TOLERANCE_ANGLE


class BaseMovement(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def move(self, simulation_step: int, m1: float, m2: float, 
             position: Vec2f, direction: Vec2f, velocity: float, acceleration: float):
        """ For given inputs -> moves/updates movement parameters like position, direction, linear / rotation velocity, """
        pass

    @abstractmethod
    def compute_movement_inputs(self, position: Vec2f, direction: Vec2f, target_position: Vec2f, target_direction: Vec2f):
        """ For given target position and direction -> it gives movement inputs """
        pass


class RombaMovement(BaseMovement):
    def __init__(self):
        super().__init__()
        self.max_forward_velocity = MAX_FORWARD_VELOCITY  # m/s
        self.max_angular_velocity = MAX_ANGULAR_VELOCITY  # m/s
        self.max_forward_working_velocity = MAX_FORWARD_WORKING_VELOCITY  # m/s
        self.wheel_distance = WHEEL_DISTANCE  # m (distance between wheels)
        self.wheel_radius = WHEEL_RADIUS  # m (radius of wheels)
        
    def move(self, simulation_step: int, m1: float, m2: float, position: Vec2f, direction: Vec2f, velocity: float):
        """
        Move the robot using differential drive model.
        m1: Left motor input (-1.0 to 1.0)
        m2: Right motor input (-1.0 to 1.0)
        """
        # Clamp motor inputs between -1 and 1
        m1 = max(-1.0, min(1.0, m1))
        m2 = max(-1.0, min(1.0, m2))
        
        # Calculate maximum velocity based on working state
        max_velocity = self.max_forward_velocity
        
        # Calculate wheel velocities
        v_left = m1 * max_velocity
        v_right = m2 * max_velocity
        
        # Calculate linear and angular velocities
        v = (v_right + v_left) / 2.0  # Linear velocity
        omega = (v_right - v_left) / self.wheel_distance * self.max_angular_velocity  # Angular velocity in rad/s
        
        # Calculate new direction
        angle = omega * simulation_step
        new_direction = (direction.rotate(angle)).normalize()
        
        # Calculate new position
        new_position = position + direction * (v * simulation_step)
        
        # Current velocity for return value
        current_velocity = v
        
        return new_position, new_direction, current_velocity, omega
    
    def compute_movement_inputs(self, position: Vec2f, direction: Vec2f, target_position: Vec2f, target_direction: Vec2f = None):
        """
        Compute differential drive inputs (m1, m2) to reach target position and direction.
        """
        
        # Initialize motor inputs
        m1 = 0.0
        m2 = 0.0
        
        distance = position.distance_to(target_position)
        
        # First, check if we need to move towards the target position
        if distance > TOLERANCE_DISTANCE:
            # Compute angle to target
            direction_to_target = (target_position - position).normalize()
            angle_to_target = direction_to_target.get_angle("deg")
            angle_of_agent = direction.get_angle("deg")
            
            # Compute angle difference
            delta_angle = (angle_to_target - angle_of_agent + 180) % 360 - 180  # Ensures shortest turn direction
            
            # Normalize delta_angle to -1...1 range
            normalized_delta = delta_angle / 180.0
            
            # Basic differential drive control for turning and moving forward
            if abs(delta_angle) > TOLERANCE_ANGLE:
                # If we need to turn, adjust motor speeds accordingly
                turn_strength = min(1.0, abs(normalized_delta))  # Scale turn strength

                if normalized_delta < 0:  # Turn right
                    m1 = turn_strength
                    m2 = -turn_strength
                else:  # Turn left
                    m1 = -turn_strength
                    m2 = turn_strength
            else:
                # Move straight towards the target (no turning needed)
                speed = min(distance * 0.05, 1.0)  # Scale speed based on distance, up to a maximum of 1
                m1 = speed
                m2 = speed
        
        # If at the target and a target direction is provided, adjust heading to match target direction
        elif target_direction is not None:
            angle_of_target = target_direction.get_angle("deg")
            angle_of_agent = direction.get_angle("deg")
            delta_angle = (angle_of_target - angle_of_agent + 180) % 360 - 180
            
            # Normalize delta_angle to -1...1 range
            normalized_delta = delta_angle / 180.0
            
            # Only turn in place when adjusting final heading
            turn_strength = min(1.0, abs(normalized_delta) * 0.5)
            
            if normalized_delta < 0:  # Turn right
                m1 = turn_strength
                m2 = -turn_strength
            else:  # Turn left
                m1 = -turn_strength
                m2 = turn_strength

        threshold = 1e-4
        if -threshold < m1 < threshold: m1=0
        if -threshold < m2 < threshold: m2=0
        
        return (m1, m2)

