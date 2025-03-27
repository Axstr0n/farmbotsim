import pygame

from utilities.utils import Vec2f, Target
from task_management.task_manager import Task, TaskManager1
from preview.preview import Preview
from utilities.configuration import TASK_PREVIEW_PARAMS
TASK_PREVIEW_SIMULATION_PARAMS = TASK_PREVIEW_PARAMS["simulation"]
TASK_PREVIEW_RENDER_PARAMS = TASK_PREVIEW_PARAMS["render"]

from rendering.render import render_gui_agents, render_gui_crop_field, render_gui_stations


class TaskPreview(Preview):
    def __init__(self, title="Preview"):
        super().__init__(TASK_PREVIEW_SIMULATION_PARAMS, title)
        self.task_manager = TaskManager1()

    def handle_events(self):
        events = super().handle_events()
        if events is False:  # Quit condition
            return False
        return True
      
    def render(self):

        super().render(TASK_PREVIEW_RENDER_PARAMS)

        self.gui.begin_window(0,0,0,0,"DEBUG",3,450)

        if self.gui.add_button("Go to station 0"):
            self.assign_task("station_0")

        if self.gui.add_button("Go to crop_0_0, agent_0"):
            self.assign_task("crop_0_0", 0)
        if self.gui.add_button("Go to crop_0_1"):
            self.assign_task("crop_0_1")

        if self.gui.add_button("Go to spawn"):
            self.assign_task("spawn")
        if self.gui.add_button("Go to crop_2_1"):
            self.assign_task("crop_2_1")

        render_gui_agents(self.gui, self.agent_objects, draw_path=TASK_PREVIEW_RENDER_PARAMS["draw_path"], draw_task_target=TASK_PREVIEW_RENDER_PARAMS["draw_task_target"])
        render_gui_stations(self.gui, self.scene.station_objects)
        render_gui_crop_field(self.gui, self.scene.crop_field)

        self.gui.end_window()
        self.gui.windows[0].active = True # Set only window to active
        self.gui.draw()

        pygame.display.flip()

    def assign_task(self, target_id, index=-1):
        def task_crop(crop_id):
            crop = self.scene.crop_field.crops_dict[crop_id]
            target = Target(crop.position, None)
            row_id = f'row_{crop_id.split("_")[1]}'
            self.scene.crop_field.rows_assign[row_id] = agent_id
            return Task(
                task_id=self.task_manager.task_id_counter,
                agent_id=agent_id,
                target_id=crop_id,
                _object=crop,
                target=target
            )

        def task_station(station_id):
            station = self.scene.station_objects[station_id]
            pos = station.request_charge(agent)
            if pos == station.position:
                target = Target(pos, Vec2f(0,1))
            else:
                target = Target(pos, Vec2f(0,1))
            return Task(
                task_id=self.task_manager.task_id_counter,
                agent_id=agent_id,
                target_id=station_id,
                _object=station,
                target=target
            )
        
        def task_spawn(agent):
            target = Target(agent.spawn_position, Vec2f(0,1))
            return Task(
                task_id=self.task_manager.task_id_counter,
                agent_id=agent_id,
                target_id="idle",
                _object=None,
                target=target
            )

        def update_agent(agent):
            if target_id.startswith("station"):
                task = task_station(target_id)
            if target_id.startswith("crop"):
                task = task_crop(target_id)
            elif target_id == "spawn":
                task = task_spawn(agent)
            self.task_manager.assign_task(task, agent, self.scene.crop_field, self.scene.station_objects)
            

        if index == -1: # Assign for all agents
            for agent_id,agent in self.agent_objects.items():
                update_agent(agent)
        else: # For single agent
            agent_id = f"agent_{index}"
            agent = self.agent_objects[agent_id]
            update_agent(agent)
                


if __name__ == "__main__":

    editor = TaskPreview("Task Preview")
    editor.run()

