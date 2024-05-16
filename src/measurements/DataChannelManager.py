from measurements.waveforms.Pulse import Pulse
from measurements.PulseSequence import PulseSequence
import copy
from time import sleep

from instruments.SCPI_socket import *

from numpy import array, pi, ndarray, sin, cos, sqrt, exp, zeros, arange, ones, int8,append, log10,repeat


class DataChannelManager:
    '''
    An instance of this class does two things. It receives a PulseSequence and create a dict called ChannelData,
    which is a structure with the data of th pulses in the format accepted by the AWG.

    To do that it uses and dict called awgChannel which connects the channels defined in the 
    PulseSequence to a AWG channels.

    Let say that are defined 3 channels 'I', 'Q' and 'm'.

    That could be defined as 

    self.awgChannels
    {
        'i' : {
                            'channel': 1
                        'markerValue': 2
              }
        'q' : {
                            'channel': 2
                        'markerValue': 2
              }
        'm' : {
                            'channel': 1
                        'markerValue': 1
              }
    }

    The key channel is related to the actual number of the AWG channel; there are two options: 1 and 2.
    The key markerValue indicate what marker is related to that channel. The AWG have two markers: 1 and 2.

    Obs: 
    The AWG have physically 4 channels. They are channel 1, 2, 3 and 4. They have colors.
    Channel 1 is yellow, 2 is green, 3 is blue and 4 is red. 

    However, not all of them are used.
    That depends on the mode of operation and the license. Here at the LFDQ, we have license only for
    two channels, and the other could be used as markers.

    The markers output TTL signals as the sampling rate of the AWG. It is used to sync and start the RF sources.
    Marker 1 is output at channel 3.
    Marker 2 is output at channel 4.

    markerValue value should be 0, 1, 2 and 3.
        0 => no marker, 
        1 => only marker 1, 
        2 => only marker 2,
        3 => both marker 1 and marker 2


    the use case of a DataChannelManager instance is
    define awgChannels with labelAwgChannel
    the send a PulseSequence to prepareChannelData, which return channelData
    call allocAwgMemory
    then, call loadChannelDataToAwg



    '''

    def __init__(self, name, awg):
        self.name = name
        self.awg = awg
        self.awgChannels = {}

    def labelAwgChannel(self, channel, channelName, markerValue):
        self.awgChannels[channelName.lower()] = {'channel':channel, 'markerValue': markerValue}

    def setInstrumentsMarker(self, channelData, marker_value = 1, offset = 0):
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
        offset = channelData['totalSizeMeasurement']-channelData['startupInstrumentIndex']
        
        a = repeat(0,128) # awg only accepts multiples of 128
        b = repeat(marker_value,128)
        data = array(array(tuple(zip(a,b))).flatten(),dtype=int8)
        self.awg.loadData(data,1,offset)

    def clearAwgChannel(self):
        self.awgChannels.clear()

    def allocAwgMemory(self, channelData):
        self.awg.allocMemory(channelData['totalSizeMeasurement'])
        


    def loadChannelDataToAwg(self, channelData, channelName):
        p = channelData['channels'][channelName.lower()]
        offset = channelData['totalSizeMeasurement']-p['relative_memory_index']
        self.awg.loadData(p['pulse_stream'],p['awgChannel'],offset)

    def mergePulseData(self, sequence, channelName, awgRate):
        c = channelName.lower()
        channelInfo = self.awgChannels[c]
        bytes_amplitude = 127

        
        delay = 0
        totallength = sum(sequence.channels[c]['delays'])
        for p in sequence.channels[c]['pulses']:
            totallength += p.length

        wave_data_size = int(totallength*awgRate)
        this_channel_wave_data = zeros(wave_data_size,dtype=int8)

        for idx,pulse in enumerate(sequence.channels[c]['pulses']):

            _, p_wave = p.build(1/awgRate,delay)

            data = array(bytes_amplitude*p_wave, dtype = int8)

            i = int(delay*awgRate)

            this_channel_wave_data.flat[i:i+len(data)] = data  

            delay += sequence.channels[c]['delays'][idx] + pulse.length

        relative_memory_index = int(abs(sequence.channels[c]['relative_delays'][0])*awgRate/256)*256+256 # 256 is a buffer to not overflow at end of the memory

        return relative_memory_index, this_channel_wave_data

    def createChannelData(self,awgChannel, markers, markerValue, wave_data, relative_memory_index):
        # total wave size must be multiples of 128
        addedZerosLength = len(wave_data)%128
        wave_data = append(zeros(128-addedZerosLength, dtype = int8),wave_data)

        if markers:
            themarkers = markerValue*ones(len(wave_data), dtype=int8) 
            themarkers[-1] = 0
            wave_data = array(tuple(zip(wave_data,themarkers))).flatten()
        

        aChannelData = {
            "awgChannel" : awgChannel,
            "pulse_stream" : wave_data,
            "length" : len(wave_data),
            "relative_memory_index" : relative_memory_index
        }

        return aChannelData
    
    def updateChannelData(self,channelData, sequence, channelName):
        c = channelName.lower()
        channelInfo = self.awgChannels[c]
        awgChannel = channelInfo['channel']

        areThereMarker = False
        if awgChannel == 1:
            areThereMarker = True
        

        markerValue = channelInfo['markerValue']
        
        relative_memory_index, wave_data = self.mergePulseData(sequence,channelName.lower(),channelData['awgRate'])

        channelData['channels'][c] = self.createChannelData(awgChannel, areThereMarker, markerValue, wave_data, relative_memory_index)

        last_relative_delay = 0
        for c in sequence.channels.keys():
            relative_delay = sequence.channels[c]['relative_delays'][0]
            if last_relative_delay > relative_delay:
                last_relative_delay = relative_delay


        startupInstrumentIndex = int(abs(last_relative_delay-sequence.startup_delay)*channelData['awgRate']/256)*256+256
        channelData['startupInstrumentIndex'] = startupInstrumentIndex
    
    def prepareChannelData(self,
                          sequence,
                          totalExperimentDuration):
        """
        Prepare signal data for waveform.Three formats are available.
    
        """

        awgRate = self.awg.get_sampleRate()/2 # divide by two because there are two channels.

        last_relative_delay = 0
        for c in sequence.channels.keys():
            relative_delay = sequence.channels[c]['relative_delays'][0]
            if last_relative_delay > relative_delay:
                last_relative_delay = relative_delay

        startupInstrumentIndex = int(abs(last_relative_delay-sequence.startup_delay)*awgRate/256)*256+256
        totalSizeMeasurement = int(totalExperimentDuration*awgRate*2/128)*128
        all_pulses = {'channels':{},'startupInstrumentIndex': startupInstrumentIndex, 'totalSizeMeasurement' : totalSizeMeasurement, 'awgRate': awgRate}

        for (channelName, channelInfo) in self.awgChannels.items():
            awgChannel = channelInfo['channel']
            
            areThereMarker = False
            if awgChannel == 1:
                areThereMarker = True
            
            markerValue = channelInfo['markerValue']
            
            if channelName in sequence.channels.keys():
                relative_memory_index, wave_data = self.mergePulseData(sequence,channelName,awgRate)

                all_pulses['channels'][channelName] = self.createChannelData(awgChannel, areThereMarker, markerValue, wave_data, relative_memory_index)
                    
    
                    #all_pulses[c][initial_index : initial_index + len(wave)] = wave
    
                

        return all_pulses