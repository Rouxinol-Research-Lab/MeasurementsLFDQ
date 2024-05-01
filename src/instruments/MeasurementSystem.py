from instruments.Pulse import Pulse
from instruments.PulseSequence import PulseSequence
import copy
from time import sleep

from instruments.SCPI_socket import *

from numpy import array, pi, ndarray, sin, cos, sqrt, exp, zeros, arange, ones, int8,append, log10,repeat

class Parameters:
    def __init__(self):
        super().__init__()
        
class Instruments:
    def __init__(self):
        super().__init__()
        
class MeasurementSystem:

    def __init__(self, name):
        self.name = name
        self.awgChannels = []
        self.parameters = Parameters()
        self.instruments = Instruments()
        self.awgByteSizeMeasurement = 0
        self.awgChannels = []

    def connectToAwgChannel(self, channel, channelName, freq, markers = False):
        self.awgChannels.append((channel,channelName.lower(), freq, markers))

    def set_instruments_marker(self,awgRate, marker_value = 1, offset = 0):
        '''
        Set a position to trigger a marker
    
        Args:
            marker_value (int): 0 => no marker, 
                                1 => only marker 1, 
                                2 => only marker 2,
                                3 => both marker 1 and marker 2
            offset (int): The position where to set the marker. 
        '''

        # get relative time of the first element
        relative_memory_index = int(abs(self.sequence.list_of_relative_delays[0]-self.parameters.startup_delay)*awgRate/128)*128+256
        offset = self.awgByteSizeMeasurement-relative_memory_index
        
        a = repeat(0,128) # awg only accepts multiples of 128
        b = repeat(marker_value,128)
        data = array(array(tuple(zip(a,b))).flatten(),dtype=int8)
        self.loadDataToAwg(data,1,offset)

    def clearAwgChannel(self):
        self.awgChannels = []

    def clearAwgMemory(self):
        SCPI_sock_send(self.instruments.awg._session,":TRAC1:DEL:ALL")
        SCPI_sock_send(self.instruments.awg._session,":TRAC2:DEL:ALL")

    def allocAwgMemory(self,awgRate):
        totalExperimentLength = self.parameters.relaxation_delay + self.sequence.get_totallength() + self.parameters.startup_delay
        self.awgByteSizeMeasurement = int(totalExperimentLength*awgRate/128)*128
        SCPI_sock_send(self.instruments.awg._session,":TRAC1:DEF 1,{},0".format(self.awgByteSizeMeasurement))
        

    def getDataFromSocketBinary(self):
        dat = b''
        while 1:
            message = self.instruments.awg._session.recv(4096)
            last=len(message)
            if chr(message[-1]) == "\n":
                dat=dat+message[:-1]
                return dat
            else:
                dat=dat+message
    
    def getIEEEBlockTag(self,data):
        dataSize = len(data)
        numberLength =  int(log10(dataSize)+1)
        return "#{}{}".format(numberLength,dataSize)
    
    def loadDataToAwg(self,data,channel,offset):
        tag = self.getIEEEBlockTag(data)
        cmd = ":TRAC{}:DATA 1,{},".format(channel,offset) + tag
        self.instruments.awg._session.sendall(cmd.encode()+bytes(data)+"\n".encode())    

    def loadChannelDataToAwg(self, channelData, channelName, waittime = 0.1):
        p = channelData[channelName]
        offset = self.awgByteSizeMeasurement-p['relative_memory_index']
        self.loadDataToAwg(p['pulse_stream'],p['awgChannel'],offset)
        sleep(waittime)
    
    def prepareSignalData(self,
                          sequence,
                          awgRate):
        """
        Prepare signal data for waveform.Three formats are available.
    
        Args:
            sequence (PulseSequence): holds the pulses and its sequence.
            measurementPulseLength (float): Length of the measurement pulse.
            excitationPulsesLength (list): List of lengths of the excitation pulses.
            excitationPulsesDelay (list): List of delays between excitation pulses.
            excitationPulsesPhase (list): List of phases for each excitation pulse.
            freq (float): Frequency of the measurement pulse.
            excitation_freq (float): Frequency of the excitation pulses.
            awgRate (float): Rate of the arbitrary waveform generator (AWG).
            markerValueForExcitation (int, optional): Marker value for the excitation pulses. Defaults to 2.
            markerValueForMeasurement (int, optional): Marker value for the measurement pulse. Defaults to 3.
            sigma (float, optional): Standard deviation for the Gaussian waveform. Defaults to 0.25.
            tau (float, optional): Scaling factor for the final length of the pulse measurement. Defaults to 0.20.
    
        Returns:
            tuple: A tuple containing the following arrays:
                - x (numpy.ndarray): Time array.
                - pulseMeasurement (numpy.ndarray): Array representing the measurement pulse.
                - pulsesExcitation (numpy.ndarray): Array representing the excitation pulses.
                - pulseMarkers (numpy.ndarray): Array representing the marker values.
        """

        self.sequence = sequence

        bytes_amplitude = 127

        all_pulses = {}

        for (awgChannel, channelName, if_freq, markers) in self.awgChannels:

            #all_pulses[channelName] = zeros(size, dtype= int8)
            all_pulses[channelName] = []
            
            # check where to start and where to end
            idx_start = 0
            idx_end = 0

            for idx,c in enumerate(sequence.list_of_channels):
                if c == channelName:
                    idx_start = idx
                    break

            # in reverse order
            for idx,c in enumerate(reversed(sequence.list_of_channels)):
                if c == channelName:
                    idx_end = len(sequence.list_of_channels)-idx
                    break

            
            delay = 0
            totallength = sum(sequence.list_of_delays[idx_start:idx_end])
            for p in sequence.list_of_pulses[idx_start:idx_end]:
                totallength += p.length


            wave_data_size = int(totallength*awgRate)
            this_channel_wave_data = zeros(wave_data_size,dtype=int8)

            for idx in range(idx_start,idx_end):
                pulse = sequence.list_of_pulses[idx]

                if channelName == sequence.list_of_channels[idx]:
                    p = copy.deepcopy(pulse)
                    p.frequency = if_freq
                    _, p_wave = p.build(1/awgRate,delay)

                    data = array(bytes_amplitude*p_wave, dtype = int8)

                    i = int(delay*awgRate)

                    this_channel_wave_data.flat[i:i+len(data)] = data  

                delay += sequence.list_of_delays[idx] + pulse.length

            # total wave size must be multiples of 128
            addedZerosLength = len(this_channel_wave_data)%128
            this_channel_wave_data = append(zeros(128-addedZerosLength, dtype = int8),this_channel_wave_data)

            if markers:
                themarkers = 3*ones(len(this_channel_wave_data), dtype=int8) 
                themarkers[-1] = 0
                this_channel_wave_data = array(tuple(zip(this_channel_wave_data,themarkers))).flatten()
            
            relative_memory_index = int(abs(sequence.list_of_relative_delays[idx_start])*awgRate/128)*128+256 # 256 is a buffer to not overflow at end of the memory

            all_pulses[channelName]={
                "awgChannel" : awgChannel,
                "pulse_stream" : this_channel_wave_data,
                "length" : len(this_channel_wave_data),
                "if_freq"   : if_freq, 
                "relative_memory_index" : relative_memory_index
            }

                    
    
                    #all_pulses[c][initial_index : initial_index + len(wave)] = wave
    
                

        return all_pulses