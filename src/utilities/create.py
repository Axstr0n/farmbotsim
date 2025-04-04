
import numpy as np
import math
import random

from utilities.utils import Vec2f, generate_colors
from agent.agent import Agent
from agent.movement import RombaMovement
from agent.battery import Battery


def init_agents(n_agents, spawning_area, navmesh=None):
    def get_random_point_in_rect(spawning_area):
        left_top = spawning_area["left_top_pos"]
        width = spawning_area["width"]
        height = spawning_area["height"]
        angle = spawning_area["angle"]
        x1, y1 = left_top

        # Generate a random point inside an unrotated rectangle
        random_x = random.uniform(0, width)
        random_y = random.uniform(0, height)

        # Rotate this point around the top-left corner
        angle_rad = math.radians(angle)  # Convert angle to radians
        rotated_x = x1 + (random_x * math.cos(angle_rad)) - (random_y * math.sin(angle_rad))
        rotated_y = y1 + (random_x * math.sin(angle_rad)) + (random_y * math.cos(angle_rad))

        return Vec2f(rotated_x, rotated_y)

    agents = [f'agent_{i}' for i in range(n_agents)]
    agent_colors = generate_colors(n_agents, 0.11)
    agent_objects = {
        agent_id: Agent(
            id=agent_id,
            color=agent_colors[i],
            #position=get_random_point_in_rect(spawning_area),
            position=Vec2f(2,6),
            direction=Vec2f(1, 0).rotate(np.random.uniform(0, 2 * math.pi)),
            movement = RombaMovement(),
            battery=Battery("../batteries/battery1", initial_soc=random.randint(50,70)),
            #battery=Battery("../batteries/battery1", initial_soc=100),
            navmesh=navmesh
        )
        for i,agent_id in enumerate(agents)
    }
    return agents, agent_objects