from measurements.waveforms.Pulse import Pulse
import numpy as np

class GaussianPulse(Pulse):
    '''
        This class defines a pulse to be sent to the AWG.
    '''

    def __init__(self, length, amplitude,sigma, tau):
        super().__init__(length)
        self.amplitude = amplitude
        self.sigma = sigma
        self.tau = tau

    def build(self, timestep, initial_time = 0):
        t = np.arange(initial_time, initial_time + self.length, timestep)
        pulse = np.ones(len(t))


        t_ends = np.arange(0,self.tau, timestep)
        pulse = np.ones(len(t))

        head = np.exp(-(t_ends-t_ends[-1])**2/(2*self.sigma)**2)
        tail = np.exp(-(t_ends)**2/(2*self.sigma)**2)

        n = len(t_ends)
        pulse = self.amplitude*np.concatenate((head,pulse[n:-n],tail))

        return t, pulse