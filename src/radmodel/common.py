import numpy as np

TICK_DURATION = 15
TICKS_PER_DAY = int(24 * (60 / TICK_DURATION))
# midnight in mins
MIDNIGHT = 24 * 60

SUSCEPTIBLE = np.int32(0)
EXPOSED = np.int32(1)
PRESYMPTOMATIC = np.int32(2)
INFECTED_SYMP = np.int32(3)
INFECTED_ASYMP = np.int32(4)
RECOVERED = np.int32(5)
HOSPITALIZED = np.int32(6)
DEAD = np.int32(7)

STATE_MAP = {
    "S": SUSCEPTIBLE,
    "E": EXPOSED,
    "P": PRESYMPTOMATIC,
    "I_A": INFECTED_ASYMP,
    "I_S": INFECTED_SYMP,
    "R": RECOVERED,
    "H": HOSPITALIZED,
    "D": DEAD
}
