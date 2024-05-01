from instruments.Pulse import Pulse
from instruments.PulseSequence import PulseSequence
import copy
from time import sleep

from instruments.SCPI_socket import *

from numpy import array, pi, ndarray, sin, cos, sqrt, exp, zeros, arange, ones, int8,append, log10,repeat


class DataChannelManager:

    def __init__(self, name):
        self.name = name
        self.awgChannels = {}

    def labelAwgChannel(self, channel, channelName, freq, markers = False):
        self.awgChannels[channelName.lower()] = {'channel':channel, 'if_freq': freq, 'measurementMarker': markers}

    def setInstrumentsMarker(self, awg, channelData, marker_value = 1, offset = 0):
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
        self.loadDataToAwg(awg,data,1,offset)

    def clearAwgChannel(self):
        self.awgChannels.clear()

    def deleteAwgMemory(self,awg):
        SCPI_sock_send(awg._session,":TRAC1:DEL:ALL")
        SCPI_sock_send(awg._session,":TRAC2:DEL:ALL")

    def allocAwgMemory(self, awg, channelData):
        SCPI_sock_send(awg._session,":TRAC1:DEF 1,{},0".format(channelData['totalSizeMeasurement']))
        

    def getDataFromSocketBinary(self,awg):
        dat = b''
        while 1:
            message = awg._session.recv(4096)
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
    
    def loadDataToAwg(self,awg,data,channel,offset):
        tag = self.getIEEEBlockTag(data)
        cmd = ":TRAC{}:DATA 1,{},".format(channel,offset) + tag
        awg._session.sendall(cmd.encode()+bytes(data)+"\n".encode())



    def loadChannelDataToAwg(self, awg, channelData, channelName):
        p = channelData['channels'][channelName]
        offset = channelData['totalSizeMeasurement']-p['relative_memory_index']
        self.loadDataToAwg(awg, p['pulse_stream'],p['awgChannel'],offset)

    def mergePulseData(self, sequence, channelName, awgRate):

        channelInfo = self.awgChannels[channelName.lower()]
        if_freq = channelInfo['if_freq']
        bytes_amplitude = 127


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

        relative_memory_index = int(abs(sequence.list_of_relative_delays[idx_start])*awgRate/128)*128+256 # 256 is a buffer to not overflow at end of the memory

        return relative_memory_index, this_channel_wave_data

    def createChannelData(self,awgChannel, if_freq, markers, wave_data, relative_memory_index):
        # total wave size must be multiples of 128
        addedZerosLength = len(wave_data)%128
        wave_data = append(zeros(128-addedZerosLength, dtype = int8),wave_data)

        if markers:
            themarkers = 3*ones(len(wave_data), dtype=int8) 
            themarkers[-1] = 0
            wave_data = array(tuple(zip(wave_data,themarkers))).flatten()
        

        aChannelData = {
            "awgChannel" : awgChannel,
            "pulse_stream" : wave_data,
            "length" : len(wave_data),
            "if_freq"   : if_freq, 
            "relative_memory_index" : relative_memory_index
        }

        return aChannelData
    
    def updateChannelData(self,channelData, sequence, channelName):
        c = channelName.lower()
        channelInfo = self.awgChannels[c]
        awgChannel = channelInfo['channel']
        if_freq    = channelInfo['if_freq']
        markers    = channelInfo['measurementMarker']
        
        relative_memory_index, wave_data = self.mergePulseData(sequence,channelName,channelData['awgRate'])

        channelData['channels'][c] = self.createChannelData(awgChannel, if_freq, markers, wave_data, relative_memory_index)

        startupInstrumentIndex = int(abs(sequence.list_of_relative_delays[0]-sequence.startup_delay)*channelData['awgRate']/128)*128+256
        channelData['totalSizeMeasurement'] = startupInstrumentIndex
    
    def prepareChannelData(self, 
                          awg,
                          sequence,
                          totalExperimentDuration):
        """
        Prepare signal data for waveform.Three formats are available.
    
        """

        awgRate = awg.get_sampleRate()/2 # divide by two because there are two channels.

        startupInstrumentIndex = int(abs(sequence.list_of_relative_delays[0]-sequence.startup_delay)*awgRate/128)*128+256
        totalSizeMeasurement = int(totalExperimentDuration*awgRate/128)*128
        all_pulses = {'channels':{},'startupInstrumentIndex': startupInstrumentIndex, 'totalSizeMeasurement' : totalSizeMeasurement, 'awgRate': awgRate}

        for (channelName, channelInfo) in self.awgChannels.items():
            awgChannel = channelInfo['channel']
            if_freq    = channelInfo['if_freq']
            markers    = channelInfo['measurementMarker']
            
            relative_memory_index, wave_data = self.mergePulseData(sequence,channelName,awgRate)

            all_pulses['channels'][channelName] = self.createChannelData(awgChannel, if_freq, markers, wave_data, relative_memory_index)
                    
    
                    #all_pulses[c][initial_index : initial_index + len(wave)] = wave
    
                

        return all_pulses