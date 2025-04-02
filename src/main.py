import time

from env import ContinuousMARLEnv
from task_management.task_manager import TaskManager1
from utilities.configuration import ENV_PARAMS
ENV_RENDER_INTERVAL = ENV_PARAMS["simulation"]["render_interval"]


def test_api(env, n):
    """
    Test parallel api
    """
    from pettingzoo.test import parallel_api_test
    env.reset()
    parallel_api_test(env, n)

def main():
    env = ContinuousMARLEnv()
    
    # test_api(env, 1000)
    # env.reset()

    render_env = False if ENV_RENDER_INTERVAL==0 else True
    
    n_episodes = 10
    times = []
    start_time = time.time()
    for episode in range(n_episodes):
        print(f"Episode {episode+1}/{n_episodes}")
        observations, _ = env.reset()
        if render_env: env.render()
        done = False
        total_reward = 0

        while not done:
            
            env.task_manager.assign_tasks()
            # Get actions
            #actions = {agent: env.action_space(agent).sample() for agent in env.agents}
            actions = {agent: (1,1) for agent in env.agents}
            
            # Step the environment
            next_observations, rewards, terminations, truncations, infos = env.step(actions)
            if render_env and env.step_count%ENV_RENDER_INTERVAL==0: env.render() # render every n simulation frames
            #if env.step_count%300==0: input("Enter")
            
            # Accumulate rewards
            total_reward += sum(rewards.values())
            done = all(terminations.values()) or all(truncations.values())

            observations = next_observations

        end_time = time.time()
        duration = end_time-start_time
        times.append(duration)
        print(f"Finished episode {episode+1} {duration}")
        start_time = end_time
    
    print(f"Avg time: {sum(times)/len(times)}")


if __name__ == "__main__":
    main()