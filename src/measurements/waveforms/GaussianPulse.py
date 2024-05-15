from measurements.waveforms.Pulse import Pulse
import numpy as np

class GaussianPulse(Pulse):
    '''
        This class defines a pulse to be sent to the AWG.
    '''

    def __init__(self, length, amplitude,sigma):
        super().__init__(length)
        self.amplitude = amplitude
        self.sigma = sigma

    def build(self, timestep, initial_time = 0):
        t = np.arange(initial_time, initial_time + self.length, timestep)

        s = self.amplitude*np.exp(-(t-initial_time-self.length/2)** 2/self.sigma**2/2)

        return t, s