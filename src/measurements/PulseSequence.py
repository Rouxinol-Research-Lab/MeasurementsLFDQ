from matplotlib.pyplot import plot, show,figure
from numpy import sin, cos, exp, pi, arange, sqrt, array, append, ndarray, invert,zeros
import numpy as np
from scipy.signal import convolve

from measurements.waveforms.Pulse import Pulse

class PulseSequence:
    '''
    This class allows one to synchronize the any number of pulses for different channels.

    A channel is just a label. It will be used by the DataChannelManager to build the array of bytes
    that will be loaded into AWG. 

    '''
    def __init__(self, name):
        '''
        Init the pulse sequence.
        name: name of this sequence of pulses.

        The self.channels is a dict, where channel will one of its keys.

        self.channels[channel.lower()] is also dict that holds three keys: pulses, delays and relative delays

        self.channels[channel.lower()]['pulses'] is a list of pulses instances in the channel
        self.channels[channel.lower()]['delays'] is a list of delays of each pulse in the channel
        self.channels[channel.lower()]['relative_delays'] is the starting time of pulse in relation to the end of the pulse sequence.
        for example, let the sequence in channel 'I' have two pulses, P1 and P2, with delay of 5 microseconds between them, and 2 microsecond after P2.
        P1 has 1 microsecond of length, P2 has 1 microsecond of length. After that, the sequence repeats. Let the 
        sequence in channel 'Q' be just a P3, with length 3 microsendos and delay 1.5 microseconds.

        Visually this is the sequence in channel 'I' and 'Q'
         _______                                     _______        
        |       |                                   |       |               
        |   P1  |                                   |   P2  |              
        |       |___________________________________|       |_______
            1µs                     5µs                1µs      1µs
        |<----->|<--------------------------------->|<----->|<----->|
                                                            -2 µs
                                                    <----------------
                                     -8 µs
        <------------------------------------------------------------
                                                                        sequences repeat
                                    _____________________               ------->
                                   |                     |          
                                   |          P3         |          
        ___________________________|                     |__________
                                              5 µs           1.5 µs
                                   |<------------------->|<-------->|
                                                -6.5 µs
                                   <---------------------------------

        Here is how its organized by PulseSequence


        self.channels:
        {
            'i': {
                         'pulses' : [   P1,    P2]
                         'delays' : [ 5 µs,  1 µs]
                'relative_delays' : [-8 µs, -2 µs]
                }
            'q': {
                         'pulses' : [     P3]
                         'delays' : [ 1.5 µs]
                'relative_delays' : [-6.5 µs]
                }
        }

        '''
        self.name = name
        self.channels = {} # this dictionary holds the pulses for all channels

    def add(self, p, channel, delay = 0.1e-9):
        '''
        This adds a pulse to a sequence of pulse of a channel. If the channels does not exist, it will be created.
        p is a Pulse.
        delay is an delay put just after the pulse. That is the main way to sync pulses.

        '''
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

    def create_relative_delays(self,c):
        '''
            This calculate the relative delay of a every pulse in a channel.
        '''
        list_pulse_length = []
        for a_p, a_d in zip(self.channels[c]['pulses'],self.channels[c]['delays']):
            list_pulse_length.append(a_p.length + a_d)

        self.channels[c]['relative_delays'] = zeros(len(list_pulse_length))
        for idx,_ in enumerate(self.channels[c]['pulses']):
            self.channels[c]['relative_delays'][idx] = -sum(list_pulse_length[idx:])

    def get_totallength(self,channel):
        '''
        Calculate the total length of a sequence in a channel.
        '''
        c = channel.lower()
        totallength = np.sum(self.channels[c]['delays'])
        for p in self.channels[c]['pulses']:
            totallength += p.length

        return totallength

    
    def clear(self):
        '''
        Clear the sequences.
        '''
        self.channels = {}
    
    def show_all(self, timestep = 0.01e-9, y_offset = 2.05, ignore = []):
        '''
            plots the sequences.

            ignore is a list of channels that one wants to not plot.
            y_offset is the y axis offset between sequences in the plot.
            timestep is the steps used to build the pulses.
        '''
        fig = figure()
        ax = fig.gca()
        yorder = 0

        totallength = 0

        for c in self.channels.keys():
            totallength_aux = self.get_totallength(c)

            if totallength_aux > totallength:
                totallength = totallength_aux

        t = arange(0,totallength,timestep)

        for c in self.channels.keys():
            if not c in ignore:
      
                sequence = zeros(len(t))+yorder

                idx = 0
                zorder = len(self.channels[c]['pulses'])
                

                for idx_p,(p,d) in enumerate(zip(self.channels[c]['pulses'],self.channels[c]['delays'])):
                    initial_time = totallength+self.channels[c]['relative_delays'][idx_p]
                    idx = int(initial_time/timestep)
                    tp, wavep = p.build(timestep,initial_time)

                    length_p = len(wavep)

                    sequence[idx:idx+length_p] += wavep

                    initial_time += p.length + d
                    ax.plot(t,sequence,zorder = zorder)
                    zorder -= 1
                
                yorder += y_offset