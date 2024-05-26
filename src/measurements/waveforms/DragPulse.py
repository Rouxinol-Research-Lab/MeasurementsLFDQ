from measurements.waveforms.Pulse import Pulse
import numpy as np

class DragPulseHolder():
    pass

class DragPulseConstructor():
    def __init__(self,length = 10e-6, alpha = 1, beta = 1, sigma = 1):
        self.length =  length
        self.alpha =  alpha
        self.beta =  beta
        self.sigma =  sigma

    def build(self):
        a = DragPulseHolder()
        a.I = DragPulse(length = self.length, amplitude = 1, alpha = self.alpha, beta = self.beta, sigma = self.sigma, quadrature = 'I' )
        a.Q = DragPulse(length = self.length, amplitude = 1, alpha = self.alpha, beta = self.beta, sigma = self.sigma, quadrature = 'Q')

        return a

    

class DragPulse(Pulse):

    def __init__(self,length, amplitude, alpha = 1, beta = 1, sigma = 1, quadrature = 'I'):
        super().__init__(length)
        self.amplitude = amplitude
        self.alpha =  alpha
        self.beta =  beta
        self.mu =  self.length/2
        self.sigma =  sigma
        self.quadrature = quadrature.upper()

    def build(self, timestep, initial_time = 0):
        t = np.arange(initial_time, initial_time + self.length, timestep)

        
        pulse = self.amplitude*self.alpha*np.exp(-(t-initial_time-self.mu)**2/2/self.sigma**2)
        if self.quadrature.upper() == 'Q':
            pulse = self.beta*(t-self.mu)/self.sigma*pulse

        return t, pulse
