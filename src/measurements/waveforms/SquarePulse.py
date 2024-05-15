from measurements.waveforms.Pulse import Pulse
import numpy as np

class SquarePulse(Pulse):

    def __init__(self, length, amplitude = 1):
        super().__init__(length)

        self.amplitude = amplitude

    def build(self, timestep, initial_time = 0):
        t = np.arange(initial_time, initial_time + self.length, timestep)
        pulse = self.amplitude*np.ones(len(t))

        return t, pulse
