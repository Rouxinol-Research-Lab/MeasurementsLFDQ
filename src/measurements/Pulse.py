from matplotlib.pyplot import plot,show
from numpy import sin,cos,exp,pi,arange,sqrt,ones,where,flip,array,linspace,concatenate,zeros
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
        elif self.envelope.lower() == 'squaregaussian':
            t_ends = arange(0,self.tau,nsteps)
            s = ones(len(t))

            o = self.sigma*t_ends[-1]
            head = exp(-(t_ends-t_ends[-1])**2/(2*o)**2)
            tail = exp(-(t_ends)**2/(2*o)**2)

            n = len(t_ends)
            s = self.amplitude*concatenate((head,s[n:-n],tail))
            pulse = pulse*s
        elif self.envelope.lower() == 'zero':
            pulse = zeros(len(t))

        return t, pulse
    
    def show(self, timestep = 0.01e-9):
        t, pulse = self.build(timestep)
        plot(t, pulse)
        show()

class Envelope(Pulse):
    def __init__(self, length, amplitude, envelope = 'square',tau = 30e-9, sigma = 0.20):
        super().__init__(length, amplitude, 0, 0, envelope,tau,sigma)

    def build(self, nsteps, initial_time = 0):
        t = arange(initial_time, initial_time + self.length, nsteps)
        pulse = self.amplitude*ones(len(t))

        if self.envelope.lower() == 'gaussian':
            o = self.sigma * self.length
            s = exp(-(t-initial_time-self.length/2)** 2/o**2/2)
            pulse = pulse*s
        elif self.envelope.lower() == 'squaregaussian':
            t_ends = arange(0,self.tau,nsteps)
            pulse = ones(len(t))

            
            o = self.sigma*t_ends[-1]
            head = exp(-(t_ends-t_ends[-1])**2/(2*o)**2)
            tail = exp(-(t_ends)**2/(2*o)**2)

            n = len(t_ends)
            pulse = self.amplitude*concatenate((head,pulse[n:-n],tail))


        return t, pulse
    
    def show(self, timestep = 0.01e-9):
        t, pulse = self.build(timestep)
        plot(t, pulse)
        show()



# Define a function to prepare signal data for a waveform
