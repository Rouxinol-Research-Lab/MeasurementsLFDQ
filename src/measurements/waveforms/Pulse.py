from abc import ABC # this defines the Abstract Base Class


class Pulse(ABC):
    '''
        This class defines an absctract class that is the bases for all waveforms sent do AWG.
    '''

    def __init__(self, length):
        self.length = length

    def build(self, timestep, initial_time = 0):
        '''
        The build method receives the timestep used to discretize pulse.
        initial_time is used to define the initial time of the pulse, to correct the phase.
        '''
        pass
    