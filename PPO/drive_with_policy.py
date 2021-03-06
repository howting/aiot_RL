import argparse
import time
from pathlib import Path

import gym
import numpy as np
from loguru import logger
from stable_baselines3 import PPO

import gym_donkeycar
from environment.command import common_args, parse_args
from environment.plotting import VAEVideo
from environment.utility import load_ae_controller, seed
from environment.wrappers import make_wrappers
from callbacks import TensorboardCallback
from torch.utils.tensorboard import SummaryWriter
import logging
import os


def main(args: dict):
    vae = load_ae_controller(path='/home/awinlab/Documents/cjr/projects/donkeycar-rl-main/trained-models/vae-64_0108VAE_road_best.pkl')

    conf = {
        "exe_path": "/home/awinlab/Documents/cjr/projects/DonkeySimLinux/donkey_sim.x86_64",
        "host": "127.0.0.1",
        "port": 9091,
        "car_name": "training",
        "max_cte": 4.0
    }
    env = gym.make(args["environment_id"], conf=conf)
    # writer = SummaryWriter(comment="-" + args["environment_id"])

    try:
        env = make_wrappers(env, vae)

        directory = 'logs/0108/'
        files = os.listdir(directory)
        print(files)

        #print(int(''.join(filter(str.isdigit, 'donkey_model_38000_steps.zip'))))

        # my_list.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
        files.sort(key = lambda x: int(''.join(filter(str.isdigit, x))))
        print(files)

        i = 0
        for filename in files:
            i += 1000
            writer = SummaryWriter('./policy-log/track/' + 'track-speed-reward-' + str(i), args["environment_id"])
            model_path = os.path.join(directory, filename)
            print(model_path)
            # checking if it is a file
            if os.path.isfile(model_path):
                print(model_path)

                #model = SAC.load(model_path)
                model = PPO.load("./ppo_donkeycar.zip")

                distance = 0.0
                speed = 0.0
                timestep = 0

                seed(42, env)
                obs = env.reset()
                for idx in range(args["max_time_steps"]):
                    timestep = idx + 1
                    action = model.predict(obs, deterministic=True)[0]
                    obs, _, done, info = env.step(action)
                    distance = info['distance']
                    speed = info['speed']
                    writer.add_scalar("distance", distance, timestep)
                    writer.add_scalar("speed", speed, timestep)
                    if done:
                        logging.info("done!")
                        break
                logging.info(distance)
    finally:
        logging.info(f'timestep: {timestep}')
        logging.info(f'distance: {distance}')
        logging.info(f'speed: {speed}')
        logging.info('Finished')
        env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use policy to drive car")
    parser = common_args(parser)
    parser.add_argument("--max-time-steps", type=int, default=5000, help="Maximum timesteps to run simulation.")
    main(parse_args(parser))
