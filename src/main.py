
from utilities.configuration import CONFIG
from env import ContinuousMARLEnv
from task_management.task_manager import TaskManager1


def test_api(env, n):
    """
    Test parallel api
    """
    from pettingzoo.test import parallel_api_test
    env.reset()
    parallel_api_test(env, n)


if __name__ == "__main__":

    env = ContinuousMARLEnv(
        screen_size = (1200,600),
        n_agents=4,
        task_manager=TaskManager1(),
        config=CONFIG
    )
    
    # test_api(env, 1000)
    # env.reset()

    render_env = True
    
    n_episodes = 10
    for episode in range(n_episodes):
        print(f"Episode {episode+1}/{n_episodes}")
        observations, _ = env.reset()
        if render_env: env.render()
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
            #actions = {agent: env.action_space(agent).sample() for agent in env.agents}
            actions = {agent: (1,1) for agent in env.agents}
            
            # Step the environment
            next_observations, rewards, terminations, truncations, infos = env.step(actions)
            if render_env and env.step_count%1==0: env.render() # render every n simulation frames
            #if env.step_count%300==0: input("Enter")
            
            # Accumulate rewards
            total_reward += sum(rewards.values())
            done = all(terminations.values()) or all(truncations.values())
            #done = done or env.step_count>100

            observations = next_observations

        print(f"Finished episode {episode+1}")