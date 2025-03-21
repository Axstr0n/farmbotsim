import pygame
import numpy as np
from pettingzoo import ParallelEnv
from gymnasium import spaces
import functools

from task_management.task_manager import BaseTaskManager
from scene.scene import Scene
from rendering.gui import GUI
from rendering.camera import Camera
from utilities.configuration import FONT_PATH

from utilities.create import init_agents
from rendering.render import render_agents, render_gui_agents, render_gui_stations, render_gui_crop_field, render_gui_tasks


class ContinuousMARLEnv(ParallelEnv):
    metadata = {'render.modes': ['human', 'rgb_array'], 'render_fps': 60}

    def __init__(self,
                 screen_size: tuple,
                 n_agents: int,
                 config: dict,
                 task_manager: BaseTaskManager):
        
        super().__init__()
        self.scene = Scene(config)

        self.task_manager = task_manager
        self.task_manager.navmesh = self.scene.navmesh
        self.n_agents = n_agents

        # Define agents
        self.possible_agents = [f"agent_{i}" for i in range(n_agents)]
        self.agent_name_mapping = dict(zip(self.possible_agents, list(range(self.n_agents))))

        # Pygame rendering setup
        self.screen = None
        self.static_surface = None
        self.dynamic_surface = None
        self.screen_size = screen_size
        self.clock = None
        self.camera = Camera()

    def reset(self, seed:int=None, options=None):
        # Reset the environment to initial state
        self.step_count = 0
        self.scene.reset()
        self.task_manager.reset()

        # Initialize agents
        # self.agents = self.possible_agents[:]
        # agent_colors = generate_colors(self.n_agents, 0.11)
        # spawning_area = self.scene.config["spawning_area"]
        # self.agent_objects = {
        #     agent_id: Agent(
        #         id=agent_id,
        #         color=agent_colors[i],
        #         position=get_random_point_in_rect(spawning_area),
        #         direction=Vec2f(1, 0).rotate(np.random.uniform(0, 2 * math.pi)),
        #         movement = RombaMovement(),
        #         battery=StandardBattery(initial_soc=50)
        #     )
        #     for i,agent_id in enumerate(self.agents)
        # }

        self.agents, self.agent_objects = init_agents(self.n_agents, self.scene.config["spawning_area"])

        self.rewards = {agent_id: 0 for agent_id in self.agents}
        self.terminations = {agent_id: False for agent_id in self.agents}
        self.truncations = {agent_id: False for agent_id in self.agents}
        self.infos = {agent_id: {} for agent_id in self.agents}

        observations = {agent_id: self.observe(agent_id) for agent_id in self.agents}

        return observations, self.infos

    def step(self, actions:dict[str:list()]):

        if not actions:
            self.agents = []
            return {}, {}, {}, {}, {}
        
        self.step_count += 1

        # Initialize dicts
        rewards = {agent_id: 0 for agent_id in self.agents}
        terminations = {agent_id: False for agent_id in self.agents}
        truncations = {agent_id: False for agent_id in self.agents}
        infos = {agent_id: {} for agent_id in self.agents}

        for agent_id, action in actions.items():
            agent = self.agent_objects[agent_id]
            rot_input, acc_input = action
            
            # Update agent state
            speed_factor = 10
            dt = (1 / self.metadata['render_fps']) * min(10, speed_factor)
            #dt = (1 / self.metadata['render_fps'])
            agent.update(dt, self.scene.navmesh)
        
        # Check if crop field is processed
        self.scene.crop_field.update_field()
        is_processed = self.scene.crop_field.is_processed()
        terminations = {agent_id: is_processed for agent_id in self.agents}


        observations = {agent_id: self.observe(agent_id) for agent_id in self.agents}
        return observations, rewards, terminations, truncations, infos
        
    def observe(self, agent_id):
        # Return the observation for the specified agent
        agent = self.agent_objects[agent_id]
        return np.array([
            agent.position.x,
            agent.position.y,
            agent.velocity_l,
            agent.direction.get_angle("deg")
        ], dtype=np.float32)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Handle window close
                pygame.quit()
                exit()
            self.camera.handle_event(event)
            self.gui.handle_event(event)
            
    def render(self, mode='human'):
        if self.screen is None and mode == 'human':
            pygame.init()
            self.screen = pygame.display.set_mode(self.screen_size)
            self.static_surface = pygame.Surface(self.screen_size)
            self.dynamic_surface = pygame.Surface(self.screen_size, pygame.SRCALPHA)
            pygame.display.set_caption("Environment")
            self.clock = pygame.time.Clock()
            font = pygame.font.Font(FONT_PATH, 12)
            self.gui = GUI(self.screen, font)

        if mode == 'human':
            self.handle_events()

            BG = (40,40,40)
            if self.step_count<2 or self.camera.dragging or self.camera.zoom_level!=self.camera.last_zoom_level:
                self.static_surface.fill(BG)
                self.scene.render_static(self.static_surface, self.camera, draw_navmesh=True)
            self.screen.fill(BG)

            self.dynamic_surface.fill((0, 0, 0, 0))
            self.scene.render_dynamic(self.dynamic_surface, self.camera)
            font = pygame.font.Font(FONT_PATH, 12)
            fps_text = font.render(f'FPS: {self.clock.get_fps():.2f}', True, (255, 255, 255))
            self.dynamic_surface.blit(fps_text, (10, 10))

            render_agents(self.dynamic_surface, self.camera, self.agent_objects)

            self.screen.blit(self.static_surface, (0,0))
            self.screen.blit(self.dynamic_surface, (0,0))

            draw_stats = True
            draw_agent_stats = True
            draw_station_stats = True
            draw_row_stats = True
            draw_tasks = True
            #region Draw stats
            if draw_stats:

                self.gui.begin_window(0,0,0,0,"DEBUG",3,480)

                self.gui.add_text("")
                self.gui.add_text(f"Step: {self.step_count}")

                if draw_agent_stats:
                    render_gui_agents(self.gui, self.agent_objects, draw_task_target=True)

                if draw_station_stats:
                    render_gui_stations(self.gui, self.scene.station_objects)
                        
                if draw_row_stats:
                    render_gui_crop_field(self.gui, self.scene.crop_field)
                        
                if draw_tasks:
                    render_gui_tasks(self.gui, self.task_manager, self.n_agents)

                self.gui.end_window()
                self.gui.windows[0].active = True # Set only window to active
                self.gui.draw()
            #endregion

            pygame.display.flip()
            self.clock.tick(self.metadata['render_fps']*20)

    def close(self):
        if self.screen is not None:
            pygame.quit()
            self.screen = None

    @functools.lru_cache(maxsize=None)
    def observation_space(self, agent_id):
        return spaces.Box(low=-10000, high=10000, shape=(4,), dtype=np.float32)

    @functools.lru_cache(maxsize=None)
    def action_space(self, agent_id):
        return spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32)


