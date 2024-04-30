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

    def connectToAwgChannel(self, channel, label, freq, markers = False):
        self.awgChannels.append((channel,label, freq, markers))

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
        relative_time = int(abs(self.sequence.list_of_relative_delays[0]-self.parameters.startup_delay)*awgRate/128)*128+256
        offset = self.awgByteSizeMeasurement-relative_time
        
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

    def loadPulsestoAwg(self, pulses, waittime = 0.1):
        for (awgChannel, channelName, _, _) in self.awgChannels:
            for p in pulses[channelName]:
                offset = self.awgByteSizeMeasurement-p['relative_time']
                self.loadDataToAwg(p['pulse_stream'],awgChannel,offset)
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
        
        # Calculate the total length of the signal
        totalLength = sequence.get_totallength()
    
        # Create the time array
        x = arange(0, totalLength, 1/awgRate)
    
        # Initialize arrays for the excitation pulses, measurement pulse, and markers
        size = len(x)
        pulses = zeros(size, dtype= int8)

        bytes_amplitude = 127

        all_pulses = {}

        for (awgChannel, channelName, if_freq, markers) in self.awgChannels:

            #all_pulses[channelName] = zeros(size, dtype= int8)
            all_pulses[channelName] = []
            
            delay = self.parameters.startup_delay
            for idx,pulseChannel in enumerate(sequence.list_of_channels):
                c = channelName.lower()
                if pulseChannel.lower() == c:
                    p = copy.deepcopy(sequence.list_of_pulses[idx])
                    original_freq = p.frequency
                    #p = sequence.list_of_pulses[idx]
                    p.frequency = if_freq
                    initial_index = int(delay*awgRate)
    
                    p_t, p_wave = p.build(1/awgRate,delay)
    
                    wave = array(bytes_amplitude*p_wave, dtype = int8)

                    # total wave size must be multiples of 128
                    addedZerosLength = len(wave)%128
                    wave = append(zeros(128-addedZerosLength, dtype = int8),wave)

                    if markers:
                        themarkers = 3*ones(len(wave), dtype=int8) 
                        themarkers[-1] = 0
                        wave = array(tuple(zip(wave,themarkers))).flatten()

                    all_pulses[channelName].append({
                        "awgChannel" : awgChannel,
                        "pulse_stream" : wave,
                        "length" : len(wave),
                        "if_freq"   : if_freq,
                        "start_time" : int(initial_index/128)*128, # it must be multiples of 128
                        "relative_time" : int(abs(sequence.list_of_relative_delays[idx])*awgRate/128)*128+256
                    })
                    all_pulses[channelName+'_frequency'] = original_freq-if_freq

                    del p
    
                    #all_pulses[c][initial_index : initial_index + len(wave)] = wave
    
                delay += sequence.list_of_delays[idx] + sequence.list_of_pulses[idx].length


        return all_pulses