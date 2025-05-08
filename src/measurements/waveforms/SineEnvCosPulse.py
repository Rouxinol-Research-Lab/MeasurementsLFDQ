from measurements.waveforms.Pulse import Pulse
import numpy as np


class SenoidCosPulse(Pulse):
    """
    This class defines a sine wave oscillating pulse with a sine wave 0 to pi
    envelope to be sent to the AWG.
    The total area of the envelope of this pulse is given by
    2*amplitude*length/pi
    """

    def __init__(
        self, amplitude, frequency, length, phase=0
    ):
        '''0 to pi sinusoidal enveloped cosine wave

        Args:
            amplitude (float): vp
            frequency (float): cos frequency
            length (float,optional): total length in seconds
            phase (float, optional): cosine phase (rad). Defaults to 0.
        '''
       
        super().__init__(length)

        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase

    def envelope(self, t):
        '''Envelope in relative time

        Args:
            t (np.ndarray): array with relative time values (starting from 0)

        Returns:
            np.ndarray: envelope amplitudes
        '''
        # sinusoidal envelope that goes from 0 to pi over the pulse length
        s = self.amplitude np.sin(np.pi*t/self.length)
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
