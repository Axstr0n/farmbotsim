from abc import ABC, abstractmethod

from agent.agent import Agent
from agent.agent_state_machine import IdleState, ChargingState, DischargedState
from scene.scene import Crop, ChargingStation, CropField
from utilities.utils import Vec2f, Target
from utilities.states import CropRowState, CropState
from utilities.configuration import TOLERANCE_DISTANCE


class Task:
    """
    A class representing a Task.

    Attributes:
        task_id (str): Unique id for task
        agent_id (str): Id of agent that has this task assigned
        target_id (str): Id of target
        _object : class Crop or ChargingStation
        target (Target): Target
        info (str): Random info if needed
    """
    def __init__(self, task_id: str, agent_id: str, target_id: str, _object, target: Target, info: str = ""):
        self.id = task_id # counter
        self.agent_id = agent_id
        self.target_id = target_id # crop id / charging station id / idle
        self.object = _object
        self.target = target
        self.info = info
    
    def __repr__(self):
        return f'Task(id={self.id}, agent_id={self.agent_id}, target_id={self.target_id}, target={self.target})'


class BaseTaskManager(ABC):
    def __init__(self, strategy=0):
        self.task_id_counter = 0
        self.history = []
        self.strategy = strategy

    
    def reset(self, env):
        self.task_id_counter = 0
        self.history = []
        self.agents = env.agent_objects
        self.crop_field = env.scene.crop_field
        self.obstacles = env.scene.crop_field.padded_obstacles
        self.stations = env.scene.station_objects
    
    def assign_task(self, new_task: Task, agent: Agent):
        if new_task is None: return False

        # Unassign from previous task
        if agent.task is not None:
            if agent.task.target_id.startswith("station"):
                agent.task.object.release_agent(agent)
            elif agent.task.target_id.startswith("crop"):
                row_id = f'row_{agent.task.target_id.split("_")[1]}'
                self.crop_field.rows_assign[row_id] = False
                agent.task.object.quit_work()
                self.crop_field.update_row_processing_status()

        # Assigns task
        self.history.append(new_task)
        agent.on_task_assigned(new_task)
        self.task_id_counter += 1

        # Assign to current task
        if agent.task.target_id.startswith("crop"):
            crop_id = new_task.target_id
            row_id = f'row_{crop_id.split("_")[1]}'
            self.crop_field.rows_assign[row_id] = agent.id

        return True

    def assign_tasks(self):
        """Called in every iteration - task manager must assign tasks to agents"""

        agent_ids_to_remove = set()
        for agent_id, agent in self.agents.items():

            # Discharged agent
            if isinstance(agent.state, DischargedState):
                agent_ids_to_remove.add(agent_id)
                if agent.task is None: continue
                target_id = agent.task.target_id
                if "station" in target_id:
                    self.stations[target_id].release_agent(agent)
                if "crop" in target_id:
                    row_id = f'row_{agent.task.target_id.split("_")[1]}'
                    self.crop_field.rows_assign[row_id] = False
                    agent.task.object.quit_work()
                    self.crop_field.update_row_processing_status()
                agent.task = None

            # Agent with full battery that are charging
            elif isinstance(agent.state, ChargingState) and agent.battery.get_soc() >= 100:
                station = self.stations[agent.task.target_id]
                station.release_agent(agent)
                task = self.get_crop_task(agent)
                self.assign_task(task, agent)
                agent_ids_to_remove.add(agent.id)

            # Agent travelling to station / waiting in queue
            elif agent.task is not None and "station" in agent.task.target_id:
                agent_ids_to_remove.add(agent_id)
        
        unassigned_agent_ids = [agent_id for agent_id in self.agents.keys() if agent_id not in agent_ids_to_remove]

        unassigned_agent_ids = self.charging_strategy(unassigned_agent_ids)

        # If more agents are idle first assign task to agents with greater battery level
        sorted_agent_ids = sorted(unassigned_agent_ids, key=lambda agent_id: self.agents[agent_id].battery.get_soc(), reverse=True)
        for agent_id in sorted_agent_ids:
            agent = self.agents[agent_id]
            if isinstance(agent.state, IdleState):
                task = self.get_crop_task(agent)
                self.assign_task(task, agent)
                agent_ids_to_remove.add(agent_id)
        unassigned_agent_ids = [agent_id for agent_id in unassigned_agent_ids if agent_id not in agent_ids_to_remove]
    
    @abstractmethod
    def charging_strategy(self, unassigned_agent_ids, agents, crop_field, obstacles, stations):
        pass

    def get_crop_task(self, agent:Agent):
        available_crops = self.crop_field.get_available_crops(agent.id)
        if len(available_crops) == 0: return self.get_idle_task(agent, self.obstacles)
        distances = {crop.id: crop.position.distance_to(agent.position) for crop in available_crops}
        crop_id = min(distances, key=distances.get)
        crop = self.crop_field.crops_dict[crop_id]

        target = Target(crop.position, None)
        task = Task(
            task_id=self.task_id_counter,
            agent_id=agent.id,
            target_id=crop.id,
            _object=crop,
            target=target
        )
        return task
    
    def get_station_task(self, agent: Agent):
        """Creates a task for charging station. If it is occupied, the agent gets task for queue."""

        station_id = self.choose_station(agent)

        best_station = self.stations[station_id]
        if not best_station:
            return self.get_idle_task(agent)
        target_position = best_station.request_charge(agent)
        target_direction = best_station.agent_direction

        target = Target(
            position=target_position,
            direction=target_direction
        )

        return Task(
            task_id=str(self.task_id_counter),
            agent_id=agent.id,
            target_id=best_station.id,
            _object=best_station,
            target=target
        )

    def get_idle_task(self, agent: Agent):
        """Gets task for idle -> agent get send to it's spawn position"""
        if agent.position.is_close(agent.spawn_position, TOLERANCE_DISTANCE): return None
        task_target = Target(
            position=agent.spawn_position,
            direction=None
        )

        task = Task(
            task_id=self.task_id_counter,
            agent_id=agent.id,
            target_id="idle",
            _object=None,
            target=task_target
        )
        return task

    @abstractmethod
    def choose_station(self, agent:Agent):
        # Implement strategy on which station to send agent to
        pass


class TaskManager1(BaseTaskManager):
    def __init__(self):
        super().__init__()

    def charging_strategy(self, unassigned_agent_ids):

        def option1(unassigned_agent_ids):
            """ If agent has less than critical battery level -> send him to station """
            critical_battery_level = 60
            agent_ids_to_remove = set()
            for agent_id in unassigned_agent_ids:
                agent = self.agents[agent_id]
                # If below critical battery go to charging
                if agent.battery.get_soc() < critical_battery_level:
                    task = self.get_station_task(agent)
                    self.assign_task(task, agent)
                    agent_ids_to_remove.add(agent_id)
            unassigned_agent_ids = [agent_id for agent_id in unassigned_agent_ids if agent_id not in agent_ids_to_remove]
            return unassigned_agent_ids

        def option2(unassigned_agent_ids):
            """ 
            If agent has less than threshold battery level and maximum number of charging agents is not reached -> go charging
            If agent has less than critical battery level -> send him to station
            """
            critical_battery_level = 45
            low_battery_threshold = 60

            n_of_all_charging_agents = 0
            for station_id,station in self.stations.items():
                n_of_all_charging_agents += len(station.queue)
            # If not maximum number of charging agents and battery below threshold go charging
            max_agents_charging = len(self.stations)
            agent_ids_to_remove = []
            for agent_id in unassigned_agent_ids:
                agent = self.agents[agent_id]
                if agent.battery.get_soc() < low_battery_threshold:
                    if n_of_all_charging_agents < max_agents_charging:
                        task = self.get_station_task(agent)
                        self.assign_task(task, agent)
                        agent_ids_to_remove.append(agent_id)
                        n_of_all_charging_agents += 1
            unassigned_agent_ids = list(filter(lambda item: item not in agent_ids_to_remove, unassigned_agent_ids))
            # If below critical battery go to charging
            for agent_id in unassigned_agent_ids:
                agent = self.agents[agent_id]
                if agent.battery.get_soc() < critical_battery_level:
                    task = self.get_station_task(agent)
                    self.assign_task(task, agent)
                    agent_ids_to_remove.append(agent_id)
            unassigned_agent_ids = list(filter(lambda item: item not in agent_ids_to_remove, unassigned_agent_ids))
            return unassigned_agent_ids
        
        if self.strategy == 0: return option1(unassigned_agent_ids)
        if self.strategy == 1: return option2(unassigned_agent_ids)

    def choose_station(self, agent):
        def option1(agent):
            """ Always choose first station """
            return list(self.stations.keys())[0]
    
        def option2(agent):
            """ Choose closest station """
            distances = {}
            for station_id,station in self.stations.items():
                distances[station_id] = agent.position.distance_to(station.position)
            return min(distances, key=distances.get)

        def option3(agent):
            """ Choose closest station with min queue """
            distances = {}
            for station_id,station in self.stations.items():
                queue_length = len(station.queue)
                distances[station_id] = agent.position.distance_to(station.position) + 4*queue_length
            return min(distances, key=distances.get)
        
        return option3(agent)

