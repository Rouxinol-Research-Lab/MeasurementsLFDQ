from matplotlib.pyplot import plot, show,figure
from numpy import sin, cos, exp, pi, arange, sqrt, array, append, ndarray, invert,zeros
import numpy as np
from scipy.signal import convolve

from measurements.Pulse import Pulse

class PulseSequence:
    def __init__(self, name):
        self.name = name
        self.list_of_pulses = array([])
        self.list_of_delays = array([])
        self.list_of_channels = array([])
        self.list_of_relative_delays = array([])

    def add(self, p, channel, delay = 0.1e-9):
        if isinstance(p, Pulse):
            relative_delay = 0

            self.list_of_pulses = append(self.list_of_pulses,p)
            self.list_of_delays = append(self.list_of_delays,delay)
            self.list_of_channels = append(self.list_of_channels,channel.lower())
            self.create_relative_delays()
            
        else:
            raise TypeError('p should type Pulse.')

    # TODO
    def create_relative_delays(self):
        list_pulse_length = []
        for a_p, a_d in zip(self.list_of_pulses,self.list_of_delays):
            list_pulse_length.append(a_p.length + a_d)

        self.list_of_relative_delays = zeros(len(list_pulse_length))
        for idx,_ in enumerate(self.list_of_pulses):
            self.list_of_relative_delays[idx] = -sum(list_pulse_length[idx:])

    def get_totallength(self):
        totallength = np.sum(self.list_of_delays)
        for p in self.list_of_pulses:
            totallength += p.length

        return totallength
    
    def build(self, timestep):
        
        totallength = self.get_totallength()
        
        t = arange(0,totallength,timestep)
        sequence = ndarray(len(t))

        initial_time = 0
        idx = 0
        for (p,d) in zip(self.list_of_pulses,self.list_of_delays):
            idx = int(initial_time/timestep)
            tp, wavep = p.build(timestep,initial_time)
            
            length_p = len(wavep)

            sequence[idx:idx+length_p] = wavep

            initial_time += p.length + d
            
        return t,sequence

    def set_delay(self,i,delay):
        self.list_of_delays[i] = delay
    
    def clear(self):
        self.list_of_pulses = array([])
        self.list_of_delays = array([])
        self.list_of_channels = array([])
        self.list_of_relative_delays = array([])

    def show(self, timestep = 0.01e-9):

        totallength = self.get_totallength()
        
        t = arange(0,totallength,timestep)
        sequence = ndarray(len(t))

        initial_time = 0
        idx = 0
        zorder = len(self.list_of_pulses)
        fig = figure()
        ax = fig.gca()
        for (p,d) in zip(self.list_of_pulses,self.list_of_delays):
            idx = int(initial_time/timestep)
            tp, wavep = p.build(timestep,initial_time)
            
            length_p = len(wavep)

            sequence[idx:idx+length_p] = wavep

            initial_time += p.length + d
            ax.plot(t,sequence,zorder = zorder)
            zorder -= 1
        

        return fig

            