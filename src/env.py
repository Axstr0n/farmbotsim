import pygame
import numpy as np
from pettingzoo import ParallelEnv
from gymnasium import spaces
import functools

from task_management.task_manager import BaseTaskManager
from scene.scene import Scene
from rendering.gui import GUI
from rendering.camera import Camera
from utilities.configuration import FONT_PATH, ENV_PARAMS
ENV_SIMULATION_PARAMS = ENV_PARAMS["simulation"]
ENV_RENDER_PARAMS = ENV_PARAMS["render"]
ENV_RENDER_GUI_PARAMS = ENV_PARAMS["render"]["gui"]

from utilities.create import init_agents
from rendering.render import (
    BG_COLOR,
    render_agents,
    render_fps,
    render_mouse_scene_pos,
    render_gui_step_count,
    render_gui_date_time,
    render_gui_field_params,
    render_gui_spawning_area_params,
    render_gui_agents,
    render_gui_stations,
    render_gui_crop_field,
    render_gui_tasks
)


class ContinuousMARLEnv(ParallelEnv):
    metadata = {'render.modes': ['human', 'rgb_array'], 'render_fps': ENV_SIMULATION_PARAMS["fps"]}

    def __init__(self,
                 screen_size: tuple,
                 task_manager: BaseTaskManager):
        
        super().__init__()
        self.scene = Scene(start_date_time=ENV_SIMULATION_PARAMS["date_time"])

        self.task_manager = task_manager
        self.task_manager.navmesh = self.scene.navmesh
        self.n_agents = ENV_SIMULATION_PARAMS["n_agents"]

        self.simulation_step = ENV_SIMULATION_PARAMS["simulation_step"]

        # Define agents
        self.possible_agents = [f"agent_{i}" for i in range(self.n_agents)]
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

        self.agents, self.agent_objects = init_agents(self.n_agents, self.scene.config["spawning_area"], self.scene.navmesh)

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
        
        self.step_count += self.simulation_step

        # Initialize dicts
        rewards = {agent_id: 0 for agent_id in self.agents}
        terminations = {agent_id: False for agent_id in self.agents}
        truncations = {agent_id: False for agent_id in self.agents}
        infos = {agent_id: {} for agent_id in self.agents}

        self.scene.update(self.simulation_step)
        for agent_id, action in actions.items():
            agent = self.agent_objects[agent_id]
            rot_input, acc_input = action
            
            # Update agent state
            agent.update(self.simulation_step, self.scene.date_time_manager) # simulation step - 1 second
        
        # Check if crop field is processed
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
            self.font = pygame.font.Font(FONT_PATH, 12)
            self.gui = GUI(self.screen, self.font)

        if mode == 'human':
            self.handle_events()

            self.screen.fill(BG_COLOR)
            self.dynamic_surface.fill((0, 0, 0, 0))

            if self.step_count<2 or self.camera.dragging or self.camera.zoom_level!=self.camera.last_zoom_level:
                self.static_surface.fill(BG_COLOR)
                self.scene.render_static(self.static_surface, self.camera, params=ENV_RENDER_PARAMS["scene"], font=self.font)

            self.scene.render_dynamic(self.dynamic_surface, self.camera, params=ENV_RENDER_PARAMS["scene"])
            
            if ENV_RENDER_PARAMS["scene"]["agents"]: render_agents(self.dynamic_surface, self.camera, self.agent_objects)
            if ENV_RENDER_PARAMS["scene"]["fps"]: render_fps(self.dynamic_surface, self.camera, self.clock, self.font)
            if ENV_RENDER_PARAMS["scene"]["mouse_scene_pos"]: render_mouse_scene_pos(self.dynamic_surface, self.camera, self.font)

            self.screen.blit(self.static_surface, (0,0))
            self.screen.blit(self.dynamic_surface, (0,0))

            #region Draw stats
            if ENV_RENDER_GUI_PARAMS["draw"]:

                self.gui.begin_window(0,0,0,0,"DEBUG",3,480)

                if ENV_RENDER_GUI_PARAMS["step_count"]: render_gui_step_count(self.gui, self.step_count)
                if ENV_RENDER_GUI_PARAMS["date_time"]: render_gui_date_time(self.gui, self.scene.date_time_manager)
                if ENV_RENDER_GUI_PARAMS["field_params"]: render_gui_field_params(self.gui, ENV_SIMULATION_PARAMS["scene_config"]["field"])
                if ENV_RENDER_GUI_PARAMS["spawning_area_params"]: render_gui_spawning_area_params(self.gui, ENV_SIMULATION_PARAMS["scene_config"]["spawning_area"])
                if ENV_RENDER_GUI_PARAMS["agent_stats"]: render_gui_agents(self.gui, self.agent_objects)
                if ENV_RENDER_GUI_PARAMS["station_stats"]: render_gui_stations(self.gui, self.scene.station_objects)
                if ENV_RENDER_GUI_PARAMS["crop_field_stats"]: render_gui_crop_field(self.gui, self.scene.crop_field)
                if ENV_RENDER_GUI_PARAMS["tasks"]: render_gui_tasks(self.gui, self.task_manager, self.n_agents)

                self.gui.end_window()
                self.gui.windows[0].active = True # Set only window to active
                self.gui.draw()
            #endregion

            pygame.display.flip()
            #self.clock.tick(self.metadata['render_fps'])
            self.clock.tick() # unlimited

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


