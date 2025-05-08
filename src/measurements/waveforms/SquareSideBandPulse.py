from measurements.waveforms.Pulse import Pulse
import numpy as np

class SquareSideBandPulse(Pulse):
    '''
        This class defines a sine wave oscillating pulse with a square envelope
        to be sent to the AWG.
        The area of the envelope of this pulse is length*amplitude
    '''

    def __init__(self, length, frequency, amplitude = 1, phase=0):
	'''Cosine wave with square envelope
	
        Args:
            amplitude (float): vp
            frequency (float): cos frequency
            length (float, optional): total length in seconds
            phase (float, optional): cosine phase (rad). Defaults to 0.
    '''
        super().__init__(length)
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase=0
   
   def envelope	(self, t):
	   '''Envelope in relative time

        Args:
            t (np.ndarray): array with relative time values (starting from 0)

        Returns:
            float: envelope amplitude
        '''
	   return self.amplitude
	   
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
