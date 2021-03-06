import argparse
import logging
import time

import gym
import torch
from loguru import logger
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, CallbackList
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.ppo import MlpPolicy

from callbacks import TensorboardCallback
from environment.command import common_args, parse_args
from environment.controller import AEController
from environment.utility import seed
from environment.wrappers import make_wrappers
from environment.custom_reward import reward2
import random

def load_ae_controller(path=None):
    ae_controller = AEController(path)
    return ae_controller


def main(args: dict):

    logging.basicConfig(level=logging.INFO)
    logging.info('Started')

    vae = load_ae_controller(args["ae_path"])

    train_conf = {"exe_path": "/home/awinlab/Documents/cjr/projects/DonkeySimLinux/donkey_sim.x86_64",
                  "host": "127.0.0.1",
                  "port": 9091,
                  "car_name": "training",
                  "max_cte": 4.0
                  }

    env = gym.make(args["environment_id"], conf=train_conf)
    #env.set_reward_fn(reward2)
    try:
        env = make_wrappers(env, vae)


        env.metadata["video.frames_per_second"] = 10
        env = gym.wrappers.monitor.Monitor(
            env,
            directory=args["monitoring_dir"],
            force=True,
            video_callable=lambda episode: episode % 5,  # Dump every 5 episodes
        )

        test_callback = TensorboardCallback()
        # Save a checkpoint every 1000 steps
        id = int(time.time())
        checkpoint_callback = CheckpointCallback(save_freq=1000, save_path="./logs/ppo-road/",
                                                 name_prefix="donkey_model")
        callback = CallbackList([test_callback])

        seed(42, env)

        policy = dict(activation_fn=torch.nn.ReLU, net_arch=[64, 64], use_sde=True, log_std_init=-2)

        logger.info('create model and start learning')

        model = PPO(MlpPolicy,
                    env=env,
                    batch_size=256,
                    n_steps=64,
                    gamma=0.99,
                    gae_lambda=0.9,
                    ent_coef=0.0,
                    sde_sample_freq=64,
                    max_grad_norm=0.5,
                    vf_coef=0.5,
                    learning_rate=3e-4,
                    verbose=1,
                    tensorboard_log=str(f'{args["tensorboard_dir"]}/ppo')
                    )
        model.learn(total_timesteps=int(50000), callback=callback)

        # model = PPO(policy=MlpPolicy,
        #             env=env,
        #             batch_size=256,
        #             n_steps=512,
        #             gamma=0.99,
        #             gae_lambda=0.9,
        #             ent_coef=0.0,
        #             sde_sample_freq=64,
        #             max_grad_norm=0.5,
        #             vf_coef=0.5,
        #             learning_rate=5e-4,
        #             use_sde=True,
        #             clip_range=0.4,
        #             tensorboard_log=str(f'{args["tensorboard_dir"]}/ppo')
        #             )
        #
        # model.learn(total_timesteps=int(50000), callback=callback)

        logger.info('save the model')
        # save the model
        model.save("ppo_donkeycar")

        for i in range(10000):
            action = random.randint(0, 6)
            # action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            env.render()
            if reward > 0:
                print(i, action, reward, done)
            if done:
                print(f'final reward: {reward}')
    except KeyboardInterrupt as e:
        logging.info('Finished early')
        pass
    except Exception as e:
        logging.info('Finished early')
        pass
    finally:
        # logger.info(f'Trained for {env.get_total_steps()}')
        logger.info(f'Saving model to {args["model_path"]}, don\'t quit!')
        model.save(args["model_path"])
        env.close()
        logging.info('Finished')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train the PPO algorithm on the DonkeyCar environment with a VAE."
    )
    parser = common_args(parser)
    main(parse_args(parser))
