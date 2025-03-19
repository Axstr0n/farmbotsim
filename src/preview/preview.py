from abc import ABC, abstractmethod
import pygame

from rendering.gui import GUI
from rendering.camera import Camera
from scene.scene import Scene
from utilities.create import init_agents
from rendering.render import render_agents
from utilities.configuration import FONT_PATH


class Preview(ABC):
    def __init__(self, config, title="Preview", n_agents=0, fps=60):
        pygame.init()
        self.SIZE = (1000,600)
        self.screen = pygame.display.set_mode(self.SIZE)
        pygame.display.set_caption(title)

        self.static_surface = pygame.Surface(self.SIZE)
        self.dynamic_surface = pygame.Surface(self.SIZE, pygame.SRCALPHA)

        font = pygame.font.Font(FONT_PATH, 12)
        self.gui = GUI(self.screen, font)

        self.clock = pygame.time.Clock()
        self.fps = fps
        self.camera = Camera()

        self.scene = Scene(config)
        self.config = self.scene.config

        self.step_count = 0

        self.agents, self.agent_objects = init_agents(n_agents, self.config["spawning_area"])

    def handle_events(self):
        events = pygame.event.get()  # Get events once
        for event in events:
            if event.type == pygame.QUIT:
                return False
            self.camera.handle_event(event)
            self.gui.handle_event(event)
        return events
    
    def update(self):
        for agent_id,agent in self.agent_objects.items():
            agent.update(0.1, self.scene.navmesh)
            
    def render(self):
        BG = (40,40,40)
        if self.step_count<2 or self.camera.dragging or self.camera.zoom_level!=self.camera.last_zoom_level:
            self.static_surface.fill(BG)
            self.scene.render_static(self.static_surface, self.camera)
        self.screen.fill(BG)

        self.dynamic_surface.fill((0, 0, 0, 0))
        self.scene.render_dynamic(self.dynamic_surface, self.camera)
        font = pygame.font.Font(FONT_PATH, 12)
        fps_text = font.render(f'FPS: {self.clock.get_fps():.2f}', True, (255, 255, 255))
        self.dynamic_surface.blit(fps_text, (10, 10))

        if len(self.agents)>0: render_agents(self.dynamic_surface, self.camera, self.agent_objects)

        self.screen.blit(self.static_surface, (0,0))
        self.screen.blit(self.dynamic_surface, (0,0))

    def run(self):
        """Main loop."""
        running = True
        while running:

            self.update()
            self.render()
            running = self.handle_events()
            if self.fps == None: self.clock.tick()
            else: self.clock.tick(self.fps)
            self.step_count += 1

        pygame.quit()

