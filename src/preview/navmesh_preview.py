import pygame

from utilities.utils import Target, Vec2f 
from task_management.task_manager import Task
from preview.preview import Preview
from utilities.configuration import NAVMESH_PREVIEW_PARAMS

class NavmeshPreview(Preview):
    def __init__(self, title="Preview"):
        super().__init__(NAVMESH_PREVIEW_PARAMS, title)
        
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
    

if __name__ == "__main__":

    editor = NavmeshPreview("Navmesh Preview")
    editor.run()

