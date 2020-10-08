import simpy as sim
import numpy as np

from typing import Union
import matplotlib.pyplot as plt
import math

# Global variables
T_GUARD = 60
P_DELAY = 0.5

U_DELAY = 400
SIM_TIME = 24 * 60 * 60  # simulate for 24hr

# Lists to keep track of data
inter_arrivals = []
time_inter_arrival = []


def get_hour(time):
    return math.floor(time)


def arrival_intensity(time) -> Union[float, None]:
    """
    Arrival intensity dependent on Table 1.
    """
    mod_time = time % 86400

    # 00-05
    if 0 <= mod_time < 18000:
        tmp = None
    # 05-08
    elif 18000 <= mod_time < 28800:
        tmp = 120
    # 08-11
    elif 28800 <= mod_time < 39600:
        tmp = 30
    # 11-15
    elif 39600 <= mod_time < 54000:
        tmp = 150
    # 15-20
    elif 54000 <= mod_time < 72000:
        tmp = 30
    # 20-00
    elif 72000 <= mod_time < 86400:
        tmp = 120
    # Else: simulation time too long, return None
    else:
        tmp = None

    if tmp is not None:
        return np.random.exponential(tmp)
    else:
        return None


def is_plane_delayed() -> bool:
    """
        P_DELAY: probability of delay (e.g 0.2 -> 20% chance of delay)
    """
    result = np.random.binomial(1, P_DELAY)
    if result == 1:
        return True
    else:
        return False


def calculate_delay() -> float:
    # delay ~ Erlang(3, U_DELAY)
    return np.random.gamma(3, U_DELAY)


class Generator(object):
    def __init__(self, env):
        self.env = env
        self.action = env.process(self.run())

    def run(self):
        while True:
            delay = 0
            time_now = self.env.now

            inter_arrival_time = arrival_intensity(time_now)

            if inter_arrival_time:
                # will only happen if time is NOT 00-05

                if T_GUARD > inter_arrival_time:
                    inter_arrival_time = T_GUARD

                if is_plane_delayed():
                    # update delay from 0 to delayed time
                    delay = calculate_delay()

                inter_arrivals.append(inter_arrival_time)
                time_inter_arrival.append(time_now / 3600)

                # [!] Schedule plane (for part b)
                # plane = Plane(env, scheduled=time_now, delay=delay)

                yield self.env.timeout(inter_arrival_time)
            else:
                # time is between 00-05, there are no planes
                inter_arrivals.append(0)
                time_inter_arrival.append(time_now / 3600)
                yield self.env.timeout(60*60)     # yield until time is 05


if __name__ == '__main__':
    env = sim.Environment()
    gen = Generator(env)
    env.run(until=SIM_TIME)
