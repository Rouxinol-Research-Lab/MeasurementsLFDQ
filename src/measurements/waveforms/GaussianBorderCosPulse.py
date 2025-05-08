from measurements.waveforms.Pulse import Pulse
import numpy as np


class GaussianBorderCosPulse(Pulse):
    '''
    This class defines a sine wave oscillating pulse with a square envelope
     and gaussian curves as edges to be sent to the AWG.
    The total area of the envelope of this pulse is given by
    amplitude*(sigma*sqrt(2*pi)+(length-2 * border_lenght * sigma)) if border_length >> sigma

    '''

    def __init__(
        self,
        length,
        amplitude,
        frequency,
        sigma_factor=0.003,
        phase=0,
        border_lenght=3.5,
    ):
        '''Gaussian edged square envelope with cosine wave oscillation

        Args:
            length: Total lenght (s)
            amplitude: total max amplitude
            frequency: cos freq (s)
            sigma_factor: gaussian border std in factor of the total lenght
            phase (float, optional): cosine phase (rad). Defaults to 0.
            border_lenght (float, optional): border length in factor of gaussian stds.
                Defaults to 3.
        '''
        super().__init__(length)
        self.amplitude = amplitude
        self.sigma_factor = sigma_factor
        self.frequency = frequency
        self.phase = phase
        self.border_length = border_lenght

        if length < 2 * border_lenght * sigma_factor * length:
            raise ValueError("Length smaller than total border length.")

    def envelope(self, t):
        '''Envelope in relative time

        Args:
            t (np.ndarray): array with relative time values (starting from 0)

        Returns:
            np.ndarray: envelope amplitudes
        '''
        sigma = self.sigma_factor * self.length
        border_time = self.border_length * sigma
        if self.length == 0:
            return 0

        return self.amplitude * (
            np.where(t < border_time, 1, 0)  # left  heaviside
            * np.exp(-(((t - border_time) / 2) ** 2) / sigma**2 / 2)  # left gaussian
            + np.where(
                (t < self.length - border_time) & (t > border_time), 1, 0
            )  # heaviside rectangular middle
            + np.where(t > self.length - border_time, 1, 0)  # right heaviside
            * np.exp(-(((t - self.length + border_time) / 2) ** 2) / sigma**2 / 2)
        )
        
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
