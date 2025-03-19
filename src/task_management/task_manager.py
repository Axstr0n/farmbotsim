from abc import ABC, abstractmethod

from agent.agent import Agent
from scene.scene import Crop, ChargingStation, CropField
from utilities.utils import Vec2f, Target
from utilities.states import AgentState, CropRowState, CropState
from utilities.configuration import TOLERANCE_DISTANCE


class Task:
    """
    A class representing a Task.

    Attributes:
        task_id (str): Unique id for task
        agent_id (str): Id of agent that has this task assigned
        task_type (str): Type of task
        target_id (str): Id of target
        _object : class Crop or ChargingStation
        target (Target): Target
        task_target (Target): Task target
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
    def __init__(self):
        self.task_id_counter = 0
        self.history = []

        self.navmesh = None
    
    def reset(self):
        self.task_id_counter = 0
        self.history = []
    
    def assign_task(self, new_task: Task, agent: Agent, crop_field: CropField, stations:dict[str,ChargingStation]):
        if new_task is None: return False

        if agent.task is not None:
            if agent.task.target_id.startswith("station"):
                agent.task.object.release_agent(agent)
            elif agent.task.target_id.startswith("crop"):
                row_id = f'row_{agent.task.target_id.split("_")[1]}'
                crop_field.rows_assign[row_id] = False
                agent.task.object.quit_work()
                crop_field.update_field()
        #     # Mark previous target as not assigned
        #     self.mark_as(agent.task.target_id, False, crop_rows, stations)

        # Assigns task
        self.history.append(new_task)
        agent.on_task_assigned(new_task)
        self.task_id_counter += 1

        if agent.task.target_id.startswith("crop"):
            crop_id = new_task.target_id
            row_id = f'row_{crop_id.split("_")[1]}'
            crop_field.rows_assign[row_id] = agent.id
        # # Mark current target as assigned
        # self.mark_as(task.target_id, True, crop_rows, stations)

        return True

    def assign_tasks(self,
                     agents: dict[str,Agent],
                     crop_field: CropField,
                     obstacles:list,
                     stations:dict[str,ChargingStation]
                     ):
        """Called in every iteration - task manager must assign tasks to agents"""
        unassigned_agent_ids = [agent_id for agent_id in agents.keys()]

        agent_ids_to_remove = []
        for agent_id in unassigned_agent_ids:
            agent = agents[agent_id]

            # Discharged agent
            if agent.state_machine.get_state() == AgentState.DISCHARGED:
                agent_ids_to_remove.append(agent_id)
                if agent.task is None: continue
                # # If agent has task - unassign target and task TO DO
                target_id = agent.task.target_id
                if "station" in target_id:
                    stations[target_id].release_agent(agent)
                if "crop" in target_id:
                    # crop_rows[target_id].is_assigned = False
                    row_id = f'row_{agent.task.target_id.split("_")[1]}'
                    crop_field.rows_assign[row_id] = False
                    agent.task.object.quit_work()
                    crop_field.update_field()
                agent.task = None

            # Agent with full battery
            elif agent.battery.get_soc() >= 100 and agent.state_machine.get_state() == AgentState.CHARGING:
                station = stations[agent.task.target_id]
                station.release_agent(agent)
                task = self.get_crop_task(agent, crop_field, obstacles)
                self.assign_task(task, agent, crop_field, stations)
                agent_ids_to_remove.append(agent.id)

            # Agent travelling to station / waiting in queue
            elif agent.task is not None and "station" in agent.task.target_id:
                agent_ids_to_remove.append(agent_id)

            # Agent that are IDLE
            # elif agent.state_machine.get_state() == AgentState.IDLE:
            #     task = self.get_crop_task(agent, crop_field, obstacles)
            #     self.assign_task(task, agent, crop_field, stations)
            #     agent_ids_to_remove.append(agent_id)
        unassigned_agent_ids = list(filter(lambda item: item not in agent_ids_to_remove, unassigned_agent_ids))

        return unassigned_agent_ids
       
    def get_crop_task(self, agent:Agent, crop_field: CropField, obstacles:list):
        available_crops = crop_field.get_available_crops(agent.id)
        if len(available_crops) == 0: return self.get_idle_task(agent, obstacles)
        distances = {crop.id: crop.position.distance_to(agent.position) for crop in available_crops}
        crop_id = min(distances, key=distances.get)
        crop = crop_field.crops_dict[crop_id]

        target = Target(crop.position, None)
        task = Task(
            task_id=self.task_id_counter,
            agent_id=agent.id,
            target_id=crop.id,
            _object=crop,
            target=target
        )
        return task
    
    def get_station_task(self, agent: Agent, stations:dict[str,ChargingStation], obstacles):
        """Creates a task for charging station. If it is occupied, the agent gets task for queue."""

        station_id = self.choose_station(agent, stations, obstacles)

        best_station = stations[station_id]
        if not best_station:
            return self.get_idle_task(agent, obstacles)
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

    def get_idle_task(self, agent: Agent, obstacles):
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
    def choose_station(self, agent:Agent, stations:dict[str,ChargingStation], obstacles):
        pass


class TaskManager1(BaseTaskManager):
    def __init__(self):
        super().__init__()
    
    def assign_tasks(self, agents, crop_field, obstacles, stations):
        unassigned_agent_ids = super().assign_tasks(agents, crop_field, obstacles, stations)

        def option1(unassigned_agent_ids, agents, crop_field, obstacles, stations):
            """ If agent has less than critical battery level -> send him to station """
            critical_battery_level = 60
            agent_ids_to_remove = []
            for agent_id in unassigned_agent_ids:
                agent = agents[agent_id]
                # If below critical battery go to charging
                if agent.battery.get_soc() < critical_battery_level:
                    task = self.get_station_task(agent, stations, obstacles)
                    self.assign_task(task, agent, crop_field, stations)
                    agent_ids_to_remove.append(agent_id)
            unassigned_agent_ids = list(filter(lambda item: item not in agent_ids_to_remove, unassigned_agent_ids))
        
            sorted_agent_ids = sorted(unassigned_agent_ids, key=lambda agent_id: agents[agent_id].battery.get_soc(), reverse=True)
            for agent_id in sorted_agent_ids:
                agent = agents[agent_id]
                # if agent.task is not None and agent.task.target_id.startswith("crop"):
                #     if crop_field.crops_dict[agent.task.target_id].state != CropState.PROCESSED: continue
                if agent.state_machine.get_state() == AgentState.IDLE:
                    task = self.get_crop_task(agent, crop_field, obstacles)
                    #if agent.task is not None and agent.task.target_id == task.target_id: continue
                    self.assign_task(task, agent, crop_field, stations)
                    agent_ids_to_remove.append(agent_id)


        def option2(unassigned_agent_ids, agents, crop_field, obstacles, stations):
            """ 
            If agent has less than threshold battery level and maximum number of charging agents is not reached -> go charging
            If agent has less than critical battery level -> send him to station
            """
            critical_battery_level = 45
            low_battery_threshold = 60

            n_of_all_charging_agents = 0
            for station_id,station in stations.items():
                if station.charging_agent != None: n_of_all_charging_agents += 1
                n_of_all_charging_agents += len(station.queue)
            # If not maximum number of charging agents and battery below threshold go charging
            max_agents_charging = len(stations)
            agent_ids_to_remove = []
            for agent_id in unassigned_agent_ids:
                agent = agents[agent_id]
                if agent.battery.get_soc() < low_battery_threshold:
                    if n_of_all_charging_agents < max_agents_charging:
                        task = self.get_station_task(agent, stations, obstacles)
                        self.assign_task(task, agent, crop_field, stations)
                        agent_ids_to_remove.append(agent_id)
                        n_of_all_charging_agents += 1
            unassigned_agent_ids = list(filter(lambda item: item not in agent_ids_to_remove, unassigned_agent_ids))
            # If below critical battery go to charging
            for agent_id in unassigned_agent_ids:
                agent = agents[agent_id]
                if agent.battery.get_soc() < critical_battery_level:
                    task = self.get_station_task(agent, stations, obstacles)
                    self.assign_task(task, agent, crop_field, stations)
                    agent_ids_to_remove.append(agent_id)
            unassigned_agent_ids = list(filter(lambda item: item not in agent_ids_to_remove, unassigned_agent_ids))

        
        option1(unassigned_agent_ids, agents, crop_field, obstacles, stations)

    def choose_station(self, agent, stations, obstacles):
        def option1(agent, stations, obstacles):
            """ Always choose first station """
            return list(stations.keys())[0]
    
        def option2(agent, stations, obstacles):
            """ Choose closest station """
            distances = {}
            for station_id,station in stations.items():
                distances[station_id] = agent.position.distance_to(station.position)
            return min(distances, key=distances.get)

        def option3(agent, stations, obstacles):
            """ Choose closest station with min queue """
            distances = {}
            for station_id,station in stations.items():
                queue_length = len(station.queue)
                distances[station_id] = agent.position.distance_to(station.position) + 4*queue_length
            return min(distances, key=distances.get)
        
        return option3(agent, stations, obstacles)

