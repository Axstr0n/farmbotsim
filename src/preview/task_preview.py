from utilities.utils import Vec2f, Target
from task_management.task_manager import Task, TaskManager1
from preview.preview import Preview
from utilities.configuration import TASK_PREVIEW_PARAMS

class TaskPreview(Preview):
    def __init__(self, title="Preview"):
        super().__init__(TASK_PREVIEW_PARAMS, title)
        self.task_manager = TaskManager1()
        self.task_manager.agents = self.agent_objects
        self.task_manager.crop_field = self.scene.crop_field
        self.task_manager.obstacles = self.scene.crop_field.padded_obstacles
        self.task_manager.stations = self.scene.station_objects

    def handle_events(self):
        events = super().handle_events()
        if events is False:  # Quit condition
            return False
        return True

    def render_extra_gui(self):
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
            self.task_manager.assign_task(task, agent)
            

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

