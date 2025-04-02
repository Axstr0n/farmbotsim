from abc import ABC, abstractmethod
import pygame

from rendering.gui import GUI
from rendering.camera import Camera
from scene.scene import Scene
from utilities.create import init_agents
from utilities.configuration import FONT_PATH
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


class Preview(ABC):
    def __init__(self, PREVIEW_PARAMS, title="Preview"):
        pygame.init()
        self.SIZE = (1000,600)
        self.screen = pygame.display.set_mode(self.SIZE)
        pygame.display.set_caption(title)

        self.static_surface = pygame.Surface(self.SIZE)
        self.dynamic_surface = pygame.Surface(self.SIZE, pygame.SRCALPHA)

        self.font = pygame.font.Font(FONT_PATH, 12)
        self.gui = GUI(self.screen, self.font)

        self.PREVIEW_PARAMS = PREVIEW_PARAMS
        self.SIMULATION_PARAMS = PREVIEW_PARAMS["simulation"]

        self.simulation_step = self.SIMULATION_PARAMS["simulation_step"]
        self.render_interval = self.SIMULATION_PARAMS["render_interval"]

        self.clock = pygame.time.Clock()
        self.fps = self.SIMULATION_PARAMS["fps"]
        self.camera = Camera()

        self.scene = Scene(start_date_time=self.SIMULATION_PARAMS["date_time"])
        self.config = self.scene.config

        self.step_count = 0

        self.n_agents = self.SIMULATION_PARAMS["n_agents"]
        self.agents, self.agent_objects = init_agents(self.n_agents, self.config["spawning_area"], self.scene.navmesh)

    def handle_events(self):
        events = pygame.event.get()  # Get events once
        for event in events:
            if event.type == pygame.QUIT:
                return False
            self.camera.handle_event(event)
            self.gui.handle_event(event)
        return events
    
    def update(self):
        self.scene.update(self.simulation_step)
        for agent_id,agent in self.agent_objects.items():
            agent.update(self.simulation_step, self.scene.date_time_manager)

    def render_extra_gui(self):
        pass

    def render(self, always_draw=False):
        RENDER_PARAMS = self.PREVIEW_PARAMS["render"]
        RENDER_SCENE_PARAMS = RENDER_PARAMS["scene"]
        RENDER_GUI_PARAMS = RENDER_PARAMS["gui"]

        self.screen.fill(BG_COLOR)
        self.dynamic_surface.fill((0, 0, 0, 0))

        if self.step_count<2 or self.camera.dragging or self.camera.zoom_level!=self.camera.last_zoom_level or always_draw:
            self.static_surface.fill(BG_COLOR)
            self.scene.render_static(self.static_surface, self.camera, params=RENDER_SCENE_PARAMS, font=self.font)

        self.scene.render_dynamic(self.dynamic_surface, self.camera, params=RENDER_SCENE_PARAMS)

        if RENDER_SCENE_PARAMS["agents"] and len(self.agents)>0: render_agents(self.dynamic_surface, self.camera, self.agent_objects)
        if RENDER_SCENE_PARAMS["fps"]: render_fps(self.dynamic_surface, self.camera, self.clock, self.font)
        if RENDER_SCENE_PARAMS["mouse_scene_pos"]: render_mouse_scene_pos(self.dynamic_surface, self.camera, self.font)

        self.screen.blit(self.static_surface, (0,0))
        self.screen.blit(self.dynamic_surface, (0,0))

        if RENDER_GUI_PARAMS["draw"]:

            self.gui.begin_window(0,0,0,0,"DEBUG",3,480)

            self.render_extra_gui()

            if RENDER_GUI_PARAMS["step_count"]: render_gui_step_count(self.gui, self.step_count)
            if RENDER_GUI_PARAMS["date_time"]: render_gui_date_time(self.gui, self.scene.date_time_manager)
            if RENDER_GUI_PARAMS["field_params"]: render_gui_field_params(self.gui, self.scene.config["field"])
            if RENDER_GUI_PARAMS["spawning_area_params"]: render_gui_spawning_area_params(self.gui, self.scene.config["spawning_area"])
            if RENDER_GUI_PARAMS["agent_stats"]: render_gui_agents(self.gui, self.agent_objects)
            if RENDER_GUI_PARAMS["station_stats"]: render_gui_stations(self.gui, self.scene.station_objects)
            if RENDER_GUI_PARAMS["crop_field_stats"]: render_gui_crop_field(self.gui, self.scene.crop_field)
            if RENDER_GUI_PARAMS["tasks"]: render_gui_tasks(self.gui, self.task_manager, self.n_agents)

            self.gui.end_window()
            self.gui.windows[0].active = True # Set only window to active
            self.gui.draw()
        
        pygame.display.flip()

    def run(self):
        """Main loop."""
        running = True
        while running:
            self.update()
            if self.step_count%self.render_interval==0: self.render()
            running = self.handle_events()
            if self.fps == None: self.clock.tick()
            else: self.clock.tick(self.fps)
            self.step_count += self.simulation_step

        pygame.quit()

