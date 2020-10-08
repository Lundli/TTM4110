
import simpy as sim
import numpy as np
import math

from typing import Union
import matplotlib.pyplot as plt

# Global variables
T_GUARD = 60
P_DELAY = 0.1

U_DELAY = 500
U_TURNAROUND = 45*60
SIM_TIME = 1*24*60*60  # simulate for 1 day


inter_arrivals = []
time_inter_arrival = []

landing_queue = []
time_landing_queue = []

takeoff_queue = []
time_takeoff_queue = []


NUM_AIRSTRIPS = 2

LANDING_TIME = 60
TAKEOFF_TIME = 60


def get_hour(time):
    return math.floor(time)


def turn_around():
    return np.random.gamma(7, U_TURNAROUND)


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


class Plane(object):
    number = 0

    def __init__(self, env, scheduled, delay):
        Plane.number += 1
        self.number = Plane.number

        self.env = env
        self.scheduled = scheduled
        self.delay = delay
        self.action = env.process(self.run())

        self.landing_queue_time = None
        self.takeoff_queue_time = None

    def run(self):
        # wait if delay
        if self.delay:
            yield self.env.timeout(self.delay)

        # LANDING: request airstrip
        before = env.now
        with airstrip.request(1) as req:
            yield req

            self.landing_queue_time = env.now - before
            landing_queue.append(self.landing_queue_time)
            time_landing_queue.append(env.now/3600)

            yield self.env.timeout(LANDING_TIME)

        # TURN AROUND TIME
        yield self.env.timeout(turn_around())

        # TAKEOFF: request airstrip
        before = env.now
        with airstrip.request(2) as req:
            yield req

            self.takeoff_queue_time = env.now - before
            takeoff_queue.append(self.takeoff_queue_time)
            time_takeoff_queue.append(env.now/3600)

            yield self.env.timeout(TAKEOFF_TIME)


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

                plane = Plane(env, scheduled=time_now, delay=delay)

                yield self.env.timeout(inter_arrival_time)

            else:
                # time is between 00-05, there are no planes
                inter_arrivals.append(0)
                time_inter_arrival.append(time_now / 3600)
                yield self.env.timeout(60 * 60)  # yield one hour


def total_average(data, time_data):
    total_per_hour = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    amount_at_hour = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(len(data)):
        hour = get_hour(time_data[i] % 86400)
        hour = hour % 24

        total_per_hour[hour] += data[i]
        amount_at_hour[hour] += 1

    for i in range(len(total_per_hour)):
        try:
            total_per_hour[i] = total_per_hour[i] / amount_at_hour[i]
        except ZeroDivisionError:
            pass
    average_per_hour = total_per_hour

    return average_per_hour


if __name__ == '__main__':
    env = sim.Environment()
    gen = Generator(env)
    airstrip = sim.PriorityResource(env, capacity=NUM_AIRSTRIPS)

    env.run(until=SIM_TIME)

    takeoff = total_average(takeoff_queue, time_takeoff_queue)
    landing = total_average(landing_queue, time_landing_queue)
    inter_arrivals = total_average(inter_arrivals, time_inter_arrival)


    # PLOT INTER ARRIVALS
    """
    plt.plot(inter_arrivals, color='green', label="Inter arrival times")
    plt.title("Inter arrival times at airport")
    plt.legend()
    plt.xlabel("Hour of day")
    plt.ylabel("Inter arrival time in seconds")
    plt.show()
    """

    # TAKEOFF & LANDING TIMES
    """
    plt.plot(takeoff, color='blue', label="Take-off queue")
    plt.plot(landing, color='red', label="Landing queue")
    plt.legend()
    title = f"Average queue times for takeoff & landing, P={ P_DELAY }, μdelay={ U_DELAY }"
    plt.title(title)
    plt.xlabel("Hour of day")
    plt.ylabel("Queue time in seconds")
    plt.show()
    #
    """
