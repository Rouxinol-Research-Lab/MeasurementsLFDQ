from matplotlib.pyplot import plot, show
from numpy import sin, cos, exp, pi, arange, sqrt, array, append, ndarray
import numpy as np
from scipy.signal import convolve

from instruments.Pulse import Pulse

class PulseSequence:
    def __init__(self, name):
        self.name = name
        self.list_of_pulses = array([])
        self.list_of_delays = array([])
        self.list_of_channels = array([])

    def add(self, p, channel, delay = 0.0):
        if isinstance(p, Pulse):
            self.list_of_pulses = append(self.list_of_pulses,p)
            self.list_of_delays = append(self.list_of_delays,delay)
            self.list_of_channels = append(self.list_of_channels,channel.lower())
        else:
            raise TypeError('p should type Pulse.')

    def build(self, timestep):
        
        totallength = np.sum(self.list_of_delays)
        for p in self.list_of_pulses:
            totallength += p.length
        
        t = arange(0,totallength,timestep)
        sequence = ndarray(len(t))

        idx = 0
        for (p,d) in zip(self.list_of_pulses,self.list_of_delays):
            tp, wavep = p.build(timestep)
            
            length_p = len(wavep)
            sequence[idx:idx+length_p] = wavep
            idx += length_p + int(d/timestep) # the length of the pulse plus the total delay steps

        return t,sequence

    def set_delay(self,i,delay):
        self.list_of_delays[i] = delay
    
    def clear(self):
        self.list_of_pulses = array([])
        self.list_of_delays = array([])

    def show(self, timestep = 0.01e-9):
        t,sequence = self.build(timestep)
        plot(t,sequence)
        show()

            