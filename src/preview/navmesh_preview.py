import pygame

from utilities.utils import Target, Vec2f 
from task_management.task_manager import Task
from rendering.render import render_gui_agents, render_gui_crop_field
from preview.preview import Preview
from utilities.configuration import CONFIG

class NavmeshPreview(Preview):
    def __init__(self, config, title="Preview", n_agents=0, fps=60):
        super().__init__(config, title, n_agents, fps)
        
    def handle_events(self):
        events = super().handle_events()
        if events is False:  # Quit condition
            return False

        for event in events:  # Use the returned event list
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.target_position = self.camera.screen_to_scene_pos(Vec2f(event.pos))
                    target = Target(self.target_position, Vec2f(0, 1))

                    for agent_id, agent in self.agent_objects.items():
                        task = Task(
                            task_id=0,
                            agent_id=agent_id,
                            target_id="idle",
                            _object=None,
                            target=target
                        )
                        agent.on_task_assigned(task)
        return True
    
    def render(self):
        super().render()

        self.gui.begin_window(0,0,0,0,"DEBUG",3,450)

        render_gui_agents(self.gui, self.agent_objects, draw_path=True, draw_task_target=True)
        render_gui_crop_field(self.gui, self.scene.crop_field)

        self.gui.end_window()
        self.gui.windows[0].active = True # Set only window to active
        self.gui.draw()

        pygame.display.flip()


if __name__ == "__main__":

    editor = NavmeshPreview(CONFIG, "Navmesh Preview", 2, 60)
    editor.run()

