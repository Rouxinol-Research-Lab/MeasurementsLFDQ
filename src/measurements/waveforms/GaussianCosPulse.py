from measurements.waveforms.Pulse import Pulse
import numpy as np


class GaussianCosPulse(Pulse):
    '''
    This class defines a senoid oscillating pulse with a gaussian envelope to be sent to the AWG.
    The total area of the envelope of this pulse is given by
    amplitude*sigma*sqrt(2*pi) if length >> sigma
    '''

    def __init__(
        self, amplitude, sigma, frequency, length=None, length_factor=7, phase=0
    ):
    '''Gaussian enveloped cosine wave

        Args:
            amplitude (float): vp
            sigma (float): gaussian std
            frequency (float): cos frequency
            length (float,optional): total length in seconds, if set ignores length_factor
            length_factor (float,optional): length in number of times the std sigma
            phase (float, optional): cosine phase (rad). Defaults to 0.
    '''
        # sigma dependant length
        if length is None:
            self.length_factor = length_factor
            super().__init__(length_factor * sigma)
        # length explicitely set by user, size independant of sigma internally
        else:
            super().__init__(length)

        self.amplitude = amplitude
        self.sigma = sigma
        self.frequency = frequency
        self.phase = phase

    def envelope(self, t):
        '''Envelope in relative time

        Args:
            t (np.ndarray): array with relative time values (starting from 0)

        Returns:
            np.ndarray: envelope amplitudes
        '''
        #middle of the pulse peak centered gaussian
        s = self.amplitude * np.exp(
            -(((t + (-self.length) / 2)) ** 2) / self.sigma**2 / 2
        )
        return s

    def oscillation(self, t):
        '''Oscillation to be used in absolute time to maintain phase coherence

        Args:
            t (np.ndarray): array with absolute time values

        Returns:
            np.ndarray: amplitudes of the oscillation
        '''
        return np.sin(2 * np.pi * self.frequency * t + self.phase)
        
    def build(self, timestep, initial_time=0):
        t = np.arange(initial_time, initial_time + self.length, timestep)
        pulse=self.envelope(t - initial_time) * self.oscillation(t)
        return t, pulse
