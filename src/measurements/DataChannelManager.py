from measurements.waveforms.Pulse import Pulse
from measurements.PulseSequence import PulseSequence
import copy
from time import sleep

from instruments.SCPI_socket import *

from numpy import array, pi, ndarray, sin, cos, sqrt, exp, zeros, arange, ones, int8,append, log10,repeat


class DataChannelManager:
    '''
    The Problem that this class is trying to solve is the following: Given an instance of PulseSequence, how to produce
    the data that hold the sequence of pulses in a format that is accepted by the awg and load into it.

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
                        'markerValue': 1
              }
        'q' : {
                            'channel': 2
                        'markerValue': 1
              }
        'm' : {
                            'channel': 1
                        'markerValue': 2
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

    if one wants to update something, there is only need to call updateChannelData instead of prepareChannelData.

    An example of self._channelData
    {
        'channels':
        {
            'm':
            { 
                "awgChannel" : 1,
                "pulse_stream" : array([0,2,0,2 ...], dtype=np.int8),
                "length" : 320256,
                "relative_memory_index" : 160256
            },
            'q':
            { 
                "awgChannel" : 2,
                "pulse_stream" : array([0,2,1,5 ...], dtype=np.int8),
                "length" : 169344,
                "relative_memory_index" : 239872
            }
        },
        'startupInstrumentIndex': 271872, 
        'totalSizeMeasurement' : 32000000, 
        'awgRate': 32000000000
    }

    startupInstrumentIndex is the index position in memory where the excitation instruments starts.
    totalSizeMeasurement is the total size of the memory allocated. Multiply it by 1/awgRate and one gets the length in time units.
    awgRate is the sampling rate for each channel.


    Let focus in one of the channel:

    awgChannel is the number of the channel to where the data will be sent
    pulse_stream is array of bytes that will be loaded into awg to channel awgChannel
    length is the length of the pulse_stream
    relative_memory_index is the position where the pulse_stream start in the AWG memory.


    '''

    def __init__(self, awg):
        self.awg = awg
        self.awgChannels = {}
        self._channelData = {}

    def labelAwgChannel(self, channel, channelName, markerValue):
        self.awgChannels[channelName.lower()] = {'channel':channel, 'markerValue': markerValue}

    def setInstrumentsMarker(self, marker_value = 1, offset = 0):
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
        offset = self._channelData['totalSizeMeasurement']-self._channelData['startupInstrumentIndex']
        
        a = repeat(0,128) # awg only accepts multiples of 128
        b = repeat(marker_value,128)
        data = array(array(tuple(zip(a,b))).flatten(),dtype=int8)
        self.awg.loadData(data,1,offset)

    def clearAwgChannel(self):
        self.awgChannels.clear()

    def allocAwgMemory(self):
        self.awg.allocMemory(self._channelData['totalSizeMeasurement'])
        


    def loadChannelDataToAwg(self, channelName):
        p = self._channelData['channels'][channelName.lower()]
        offset = self._channelData['totalSizeMeasurement']-p['relative_memory_index']
        self.awg.loadData(p['pulse_stream'],p['awgChannel'],offset)

    def mergePulseData(self, sequence, channelName, awgRate):
        '''
        This function creates a array with the pulse stream data from PulseSequence of a given channelName. The time
        step used is 1/awgRate
        '''

        c = channelName.lower()
        bytes_amplitude = 127

        
        delay = 0
        totallength = sum(sequence.channels[c]['delays'])
        for p in sequence.channels[c]['pulses']:
            totallength += p.length

        wave_data_size = int(totallength*awgRate)
        this_channel_wave_data = zeros(wave_data_size,dtype=int8)

        for idx,pulse in enumerate(sequence.channels[c]['pulses']):
            

            _, p_wave = pulse.build(1/awgRate,delay)

            data = array(bytes_amplitude*p_wave, dtype = int8)

            i = int(delay*awgRate)

            this_channel_wave_data.flat[i:i+len(data)] = data  

            delay += sequence.channels[c]['delays'][idx] + pulse.length

        relative_memory_index = int(abs(sequence.channels[c]['relative_delays'][0])*awgRate/256)*256+256 # 256 is a buffer to not overflow at end of the memory

        return relative_memory_index, this_channel_wave_data

    def createChannelData(self,awgChannel, markers, markerValue, wave_data, relative_memory_index):
        '''
        this creates the channel data of a given channel.

        If markers is True, it will interleaves the markervalue with the wave_data.
        For example, if the 
        wave_data = array([1,2,3,4,5,6])
        and marker_value is  1

        then the data will be

        array([1, 1, 2, 1, 3, 1, 4, 1, 5, 1, 6, 1])

        That is only is if the AWG channel is 1.

        To understand markers, see pages 163, 253, 256 of the M8195 manual.
        '''
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
    
    def updateChannelData(self, sequence, channelName):
        '''
        Updates a given channel with a new sequence.
        '''
        c = channelName.lower()
        channelInfo = self.awgChannels[c]
        awgChannel = channelInfo['channel']

        areThereMarker = False
        if awgChannel == 1:
            areThereMarker = True
        

        markerValue = channelInfo['markerValue']
        
        relative_memory_index, wave_data = self.mergePulseData(sequence,channelName.lower(),self._channelData['awgRate'])

        self._channelData['channels'][c] = self.createChannelData(awgChannel, areThereMarker, markerValue, wave_data, relative_memory_index)

        last_relative_delay = 0
        for c in sequence.channels.keys():
            relative_delay = sequence.channels[c]['relative_delays'][0]
            if last_relative_delay > relative_delay:
                last_relative_delay = relative_delay


        startupInstrumentIndex = int(abs(last_relative_delay-sequence.startup_delay)*self._channelData['awgRate']/256)*256+256
        self._channelData['startupInstrumentIndex'] = startupInstrumentIndex
    
    def prepareChannelData(self,
                          sequence,
                          totalExperimentDuration):
        """
        Prepare signal data for waveform.
    
        """

        awgRate = self.awg.getSampleRate()/2 # divide by two because there are two channels.

        last_relative_delay = 0
        for c in sequence.channels.keys():
            relative_delay = sequence.channels[c]['relative_delays'][0]
            if last_relative_delay > relative_delay:
                last_relative_delay = relative_delay

        startupInstrumentIndex = int(abs(last_relative_delay-sequence.startup_delay)*awgRate/256)*256+256
        totalSizeMeasurement = int(totalExperimentDuration*awgRate*2/128)*128
        channelData = {'channels':{},'startupInstrumentIndex': startupInstrumentIndex, 'totalSizeMeasurement' : totalSizeMeasurement, 'awgRate': awgRate}

        for (channelName, channelInfo) in self.awgChannels.items():
            awgChannel = channelInfo['channel']
            
            areThereMarker = False
            if awgChannel == 1:
                areThereMarker = True
            
            markerValue = channelInfo['markerValue']
            
            if channelName in sequence.channels.keys():
                relative_memory_index, wave_data = self.mergePulseData(sequence,channelName,awgRate)

                channelData['channels'][channelName] = self.createChannelData(awgChannel, areThereMarker, markerValue, wave_data, relative_memory_index)
                    
    
                    #all_pulses[c][initial_index : initial_index + len(wave)] = wave
    
        self._channelData = channelData

