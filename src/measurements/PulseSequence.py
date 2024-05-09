from matplotlib.pyplot import plot, show,figure
from numpy import sin, cos, exp, pi, arange, sqrt, array, append, ndarray, invert,zeros
import numpy as np
from scipy.signal import convolve

from measurements.Pulse import Pulse

class PulseSequence:
    def __init__(self, name):
        self.name = name
        self.channels = {}

    def add(self, p, channel, delay = 0.1e-9):
        if isinstance(p, Pulse):
            c = channel.lower ()

            if not c in self.channels:
                self.channels[c] = {}
                self.channels[c]['pulses'] = []
                self.channels[c]['delays'] = []
                self.channels[c]['relative_delays'] = []
            
            self.channels[c]['pulses'] = append(self.channels[c]['pulses'],p)
            self.channels[c]['delays'] = append(self.channels[c]['delays'],delay)
            
            self.create_relative_delays(c)
            
        else:
            raise TypeError('p should type Pulse.')

    # TODO
    def create_relative_delays(self,c):
        list_pulse_length = []
        for a_p, a_d in zip(self.channels[c]['pulses'],self.channels[c]['delays']):
            list_pulse_length.append(a_p.length + a_d)

        self.channels[c]['relative_delays'] = zeros(len(list_pulse_length))
        for idx,_ in enumerate(self.channels[c]['pulses']):
            self.channels[c]['relative_delays'][idx] = -sum(list_pulse_length[idx:])

    def get_totallength(self,channel):
        c = channel.lower()
        totallength = np.sum(self.channels[c]['delays'])
        for p in self.channels[c]['pulses']:
            totallength += p.length

        return totallength
    
    def build(self,channel, timestep):
        c = channel.lower()

        totallength = self.get_totallength(c)
        
        t = arange(0,totallength,timestep)
        sequence = ndarray(len(t))

        initial_time = 0
        idx = 0
        for (p,d) in zip(self.channels[c]['pulses'],self.channels[c]['delays']):
            idx = int(initial_time/timestep)
            tp, wavep = p.build(timestep,initial_time)
            
            length_p = len(wavep)

            sequence[idx:idx+length_p] = wavep

            initial_time += p.length + d
            
        return t,sequence
    
    def clear(self):
        self.channels = {}

    def show(self, channel, timestep = 0.01e-9):
        c = channel.lower()

        totallength = self.get_totallength(c)
        
        t = arange(0,totallength,timestep)
        sequence = ndarray(len(t))

        initial_time = 0
        idx = 0
        zorder = len(self.channels[c]['pulses'])
        fig = figure()
        ax = fig.gca()
        for (p,d) in zip(self.channels[c]['pulses'],self.channels[c]['delays']):
            idx = int(initial_time/timestep)
            tp, wavep = p.build(timestep,initial_time)
            
            length_p = len(wavep)

            sequence[idx:idx+length_p] = wavep

            initial_time += p.length + d
            ax.plot(t,sequence,zorder = zorder)
            zorder -= 1
        

        return fig,ax
    
    def show_all(self, timestep = 0.01e-9, yorder_step = 2.05, ignore = []):
        fig = figure()
        ax = fig.gca()
        yorder = 0

        for c in self.channels.keys():
            if not c in ignore:
                totallength = self.get_totallength(c)
                
                t = arange(0,totallength,timestep)
                sequence = zeros(len(t))+yorder

                initial_time = 0
                idx = 0
                zorder = len(self.channels[c]['pulses'])
                

                for (p,d) in zip(self.channels[c]['pulses'],self.channels[c]['delays']):
                    idx = int(initial_time/timestep)
                    tp, wavep = p.build(timestep,initial_time)

                    length_p = len(wavep)

                    sequence[idx:idx+length_p] += wavep

                    initial_time += p.length + d
                    ax.plot(t,sequence,zorder = zorder)
                    zorder -= 1
                
                yorder += yorder_step