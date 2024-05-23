from measurements.waveforms.Pulse import Pulse
import numpy as np

class SquareSideBandPulse(Pulse):
    '''
        This class defines a pulse to be sent to the AWG.
    '''

    def __init__(self, length, frequency, amplitude = 1):
        super().__init__(length)
        self.amplitude = amplitude
        self.frequency = frequency

    def build(self, timestep, initial_time = 0):
        t = np.arange(initial_time, initial_time + self.length, timestep)
        pulse = self.amplitude*np.sin(2*np.pi*self.frequency*t)
        return t, pulse