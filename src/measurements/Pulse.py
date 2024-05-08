from matplotlib.pyplot import plot,show
from numpy import sin,cos,exp,pi,arange,sqrt,ones,where,flip,array,linspace
from scipy.signal import convolve

class Pulse:
    '''
        This class defines a pulse to be sent to the AWG.
    '''

    def __init__(self, length, amplitude, frequency, phase, envelope = 'square', tau = 0.2, sigma = 0.20):
        self.length = length
        self.phase = phase/180*pi
        self.amplitude = amplitude
        self.frequency = frequency
        self.envelope = envelope
        self.tau = tau
        self.sigma = sigma

    def build(self, nsteps, initial_time = 0):
        t = arange(initial_time, initial_time + self.length, nsteps)
        pulse = self.amplitude*sin(2*pi*self.frequency*t+self.phase)

        if self.envelope.lower() == 'gaussian':
            o = self.sigma * self.length
            s = exp(-(t-initial_time-self.length/2)** 2/o**2/2)
            pulse = pulse*s

        return t, pulse
    
    def show(self, timestep = 0.01e-9):
        t, pulse = self.build(timestep)
        plot(t, pulse)
        show()

class Envelope(Pulse):
    def __init__(self, length, envelope = 'square', tau = 0.2, sigma = 0.20):
        super().__init__(length, 1, 0, 0,envelope,tau,sigma)

    def build(self, nsteps, initial_time = 0):
        t = arange(initial_time, initial_time + self.length, nsteps)
        pulse = ones(len(t))

        if self.envelope.lower() == 'gaussian':
            o = self.sigma * self.length
            s = exp(-(t-initial_time-self.length/2)** 2/o**2/2)
            pulse = pulse*s
        else:
            end = linspace(0,1,40000)
            pulse[:40000] = end
            end = flip(end)
            pulse[-40000:] = end

        return t, pulse
    
    def show(self, timestep = 0.01e-9):
        t, pulse = self.build(timestep)
        plot(t, pulse)
        show()

class GaussianEnvelope(Pulse):
    def __init__(self, length, envelope = 'square', length_ends = 0.2, tau = 0.2, sigma = 0.1):
        super().__init__(length, 1, 0, 0,envelope, tau, sigma)
        self.ends = length_ends

    def build(self, nsteps, initial_time = 0):
        t = arange(initial_time, initial_time + self.length, nsteps)
        pulse = ones(len(t))

        t_ends = t[where(t<=self.length*self.ends*2)]
        
        o = self.length*self.sigma * self.ends*2
        s = exp(-(t_ends-initial_time-self.length*self.ends)** 2/o**2/2)

        size_gaussian = len(s)
        if len(s) %2 == 1:
            s = s[:-1]
            size_gaussian = size_gaussian - 1

        where_size = int(size_gaussian/2)

        pulse[:where_size] = s[:where_size]
        pulse[-where_size:] = s[-where_size:]


        return t, pulse
    
    def show(self, timestep = 0.01e-9):
        t, pulse = self.build(timestep)
        plot(t, pulse)
        show()


# Define a function to prepare signal data for a waveform
