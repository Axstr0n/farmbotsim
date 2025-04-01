import time
import pygame

from env import ContinuousMARLEnv
from task_management.task_manager import TaskManager1
from utilities.configuration import ENV_PARAMS
ENV_RENDER_INTERVAL = ENV_PARAMS["simulation"]["render_interval"]

OUTPUT_FILE = "performance_matrix.txt"

if __name__ == "__main__":

    env = ContinuousMARLEnv(
        screen_size = (1200,600),
        task_manager=TaskManager1()
    )

    def run_episode(env):
        observations, _ = env.reset()
        done = False
        total_reward = 0

        while not done:
            
            env.task_manager.assign_tasks(
                agents=env.agent_objects,
                crop_field=env.scene.crop_field,
                obstacles=env.scene.crop_field.padded_obstacles,
                stations=env.scene.station_objects
            )
            # Get actions
            actions = {agent: (1,1) for agent in env.agents}
            
            # Step the environment
            next_observations, rewards, terminations, truncations, infos = env.step(actions)

            # for debuging
            # if env.step_count%600==0:
            #     print(env.step_count)
            #     env.render()
            #     # screenshot = pygame.display.get_surface()  # Get the current screen surface
            #     # pygame.image.save(screenshot, f"../dev/{env.n_agents}_{env.task_manager.strategy}/{env.step_count}.png")  # Save it as a PNG file
            
            # Accumulate rewards
            total_reward += sum(rewards.values())
            done = all(terminations.values()) or all(truncations.values())

            observations = next_observations
        
        return {"steps": env.step_count}


    options_n_agents = list(reversed([1,2,3,4]))
    options_strategies = [0, 1]
    
    n_episodes = 10

    header_names = ['n_agents', 'strategy', 'time_avg', 'time_min', 'time_max']
    col_widths = [10, 10, 10, 10, 10]  # Adjust based on expected content
    with open(OUTPUT_FILE, "w") as f:
        header = "|"
        for i,header_name in enumerate(header_names):
            header += f" {header_name.ljust(col_widths[i])} |"
        f.write(header + "\n")
        f.write("-" * len(header) + "\n")
    
    def seconds_to_dhms(seconds):
        days = round(seconds // 86400)
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        # Format each unit with leading zeros
        hours = str(round(hours)).zfill(2)
        minutes = str(round(minutes)).zfill(2)
        seconds = str(round(seconds)).zfill(2)

        return f"{days}:{hours}:{minutes}:{seconds}"
    
    for n_agents in options_n_agents:
        env.n_agents = n_agents
        for strategy in options_strategies:
            env.task_manager.strategy = strategy

            steps = []
            for episode in range(n_episodes):
                print(f"Episode {episode}/{n_episodes}")
                res = run_episode(env)
                steps.append(res["steps"])
            
            with open(OUTPUT_FILE, "a") as f:
                step_avg = sum(steps)/len(steps)
                step_min = min(steps)
                step_max = max(steps)
                time_avg = seconds_to_dhms(step_avg)
                time_min = seconds_to_dhms(step_min)
                time_max = seconds_to_dhms(step_max)

                body_data = [n_agents, strategy, time_avg, time_min, time_max]
                body = "|"
                for i,body_name in enumerate(body_data):
                    body += f" {str(body_name).ljust(col_widths[i])} |"
                f.write(body + "\n")

        