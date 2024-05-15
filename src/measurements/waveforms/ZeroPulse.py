from measurements.waveforms.Pulse import Pulse
import numpy as np

class ZeroPulse(Pulse):

    def __init__(self, length):
        super().__init__(length)

    def build(self, timestep, initial_time = 0):
        t = np.arange(initial_time, initial_time + self.length, timestep)
        pulse = np.zeros(len(t))

        return t, pulse