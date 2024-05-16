from struct import unpack
import numpy as np
from instruments.SCPI_socket import *

class M8195A_driver():
    def __init__(self, address):
        self._session = SCPI_sock_connect(address)

    
    def loadData(self,data,channel,offset):
        '''Load data into the AWG in byte format.'''

        # Make the IEEEBlock
        dataSize = len(data)
        numberLength =  int(np.log10(dataSize)+1)
        tag =  "#{}{}".format(numberLength,dataSize)

        cmd = ":TRAC{}:DATA 1,{},".format(channel,offset) + tag
        self._session.sendall(cmd.encode()+bytes(data)+"\n".encode())


    def enableChanneloutput(self,channel):
        '''Enable a channel'''

        SCPI_sock_send(self._session,":OUTP{} 1".format(channel))

    def disableChanneloutput(self,channel):
        '''disable a channel'''

        SCPI_sock_send(self._session,":OUTP{} 0".format(channel))


    def setRefInClockFrequency(self,frequency):
        '''Set or query the expected reference clock frequency, if the external reference clock source is selected. <frequency (Hz)>|MINimum|MAXimum. 10 MHz to 300 MHz'''
        SCPI_sock_send(self._session,":ROSC:FREQ {}".format(str(frequency)))

    
    def setRefInClockExternal(self):
        '''
        Set or query the reference clock source.
        • EXTernal: reference is taken from REF CLK IN.
        • AXI: reference is taken from AXI backplane.
        • INTernal: reference is taken from module internal reference oscillator. May not be available with every hardware.
        '''
        SCPI_sock_send(self._session,":ROSC:SOUR EXT")

    def getError(self):
        try:
            get_error(self._session,'')
        except ValueError:
            pass

    def start(self):
        SCPI_sock_send(self._session,":INIT:IMM")    
        
    def stop(self):
        SCPI_sock_send(self._session,":ABOR")

    def close(self):
        SCPI_sock_close(self._session)

    def clearMemory(self):
        SCPI_sock_send(self._session,":TRAC1:DEL:ALL")

    def allocMemory(self,nbytes):
        '''
        Alloc memory in AWG
        '''
        SCPI_sock_send(self._session,":TRAC1:DEF 1,{},0".format(nbytes))
        


    def getMemoryDivision(self):
        '''DIV1|DIV2|DIV4
            • DIV1  Memory sample rate is the DAC Sample Rate.
            • DIV2  Memory sample rate is the DAC Sample Rate divided by 2.
            • DIV4  Memory sample rate is the DAC Sample Rate divided by 4.
            Use this command or query to set or get the Sample Rate Divider of the Extended Memory. This value determines also the amount of available Extended Memory for each channel (see section 1.5.5).
        '''
        return SCPI_sock_query(self._session,":INST:MEM:EXT:RDIV?")

    def setMemoryDivision(self, div_n):
        '''DIV1|DIV2|DIV4
            • DIV1  Memory sample rate is the DAC Sample Rate.
            • DIV2  Memory sample rate is the DAC Sample Rate divided by 2.
            • DIV4  Memory sample rate is the DAC Sample Rate divided by 4.
            Use this command or query to set or get the Sample Rate Divider of the Extended Memory. This value determines also the amount of available Extended Memory for each channel (see section 1.5.5).
        '''
        if not isinstance(div_n, int):
            raise TypeError('div_n must be integer.')

        if div_n != 1 and div_n != 2 and div_n != 4:
            raise ValueError('div_n must be 1, 2 or 4.')

        SCPI_sock_send(self._session,":INST:MEM:EXT:RDIV DIV{}".format(div_n))

    def setChannelMemoryToExtended(self,channel):
        '''EXTended
            • INTernal  the channel uses Internal Memory
            • EXTended  the channel uses Extended Memory
        '''
        SCPI_sock_send(self._session,":TRAC{}:MMOD EXT".format(channel))
        
    def setChannelMemoryToInternal(self,channel):
        '''INTernal
            • INTernal  the channel uses Internal Memory
            • EXTended  the channel uses Extended Memory
        '''
        SCPI_sock_send(self._session,":TRAC{}:MMOD INT".format(channel))

    def getChannelMemorySetting(self,channel):
        '''
            • INTernal  the channel uses Internal Memory
            • EXTended  the channel uses Extended Memory
        '''
        return SCPI_sock_query(self._session,":TRAC{}:MMOD?".format(channel))



    def getTriggerMode(self):
        '''
            Query the trigger mode.
        '''
        contState = int(self.query(":INIT:CONT?")[:-1])
        gateState = int(self.query(":INIT:GATE?")[:-1])

        if contState == 0 and gateState == 0:
            return 'TRIGGERED'
        elif contState == 1:
            return 'CONTINUOUS'
        else:
            return 'GATED'

    def setTriggerModeToContinuous(self):
        '''
            Set the continuous mode.
        '''
        SCPI_sock_send(self._session,":INIT:CONT ON")
        SCPI_sock_send(self._session,":INIT:GATE OFF")


    def setTriggerModeToGated(self):
        '''
            Set the gated mode.
        '''
        SCPI_sock_send(self._session,":INIT:GATE ON")
        SCPI_sock_send(self._session,":INIT:CONT OFF")


    def setTriggerModeToTriggered(self):
        '''
            Set the triggered mode.
        '''
        SCPI_sock_send(self._session,":INIT:GATE OFF")
        SCPI_sock_send(self._session,":INIT:CONT OFF")


    def forceTrigger(self):
        SCPI_sock_send(self._session,":TRIG:BEG")


    def getSampleRate(self):
        '''
            Set or query the sample frequency of the output DAC.
        '''

        return float(SCPI_sock_query(self._session,":FREQ:RAST?"))


    def setSampleRate(self,freq):
        '''
            Set or query the sample frequency of the output DAC.
        '''
        

        if type(freq) == str:
            if freq.lower() == 'min' or freq.lower() == 'max':
                freq = freq.lower()
            else:
                raise ValueError("Invalid value. Function accepts only 'min', 'max', float or int.")
        elif type(freq) == float:
            if not (freq >= 53.76e9 and freq <= 65e9):
                raise ValueError("Invalid value. Value not within correct range: between 53.76 GSa/s and 65 GSa/s")
        elif type(freq) == int:
            if not (freq >= int(53.76e9) and freq <= int(65e9)):
                raise ValueError("Invalid value. Value not within correct range: between 53.76 GSa/s and 65 GSa/s")
        else:
            raise TypeError("Invalid type. Function accepts only str, float or int.")

        SCPI_sock_send(self._session,":FREQ:RAST {}".format(freq))

    def downloadWaveform(self):
        '''
        Download the data from AWG.
        '''
        size = int(SCPI_sock_query(self._session,':TRAC1:CAT?').split(',')[1])
        data = SCPI_sock_query(self._session,':TRAC1:DATA? 1, 0,{}'.format(size))
        return np.array(data.split(',')).astype(int)


    def setVoltage(self, channel, volt):
        '''
        Set the voltage output of a channel
        '''
        SCPI_sock_send(self._session, ':VOLT{} {}'.format(channel, volt))
        
    

    def getVoltage(self, channel):
        '''
        Get the voltage output of a channel
        '''
        result = SCPI_sock_query(self._session, ':VOLT{}?'.format(channel))
        print(result)


    def setVoltageOffset(self, channel, volt):
        '''
        Set the voltage offset output of a channel
        '''
        SCPI_sock_send(self._session, ':VOLT{}:OFFS {}'.format(channel, volt))
        

    def getVoltageOffset(self, channel):
        '''
        Get the voltage offset output of a channel
        '''
        result = SCPI_sock_query(self._session, ':VOLT{}:OFFS?'.format(channel))
        print(result)

    def setSecondChannelToExt(self):
        '''
        Sets the second channel to use the external memory (16 GBytes)
        '''
        SCPI_sock_send(self.inst_awg._session, ':TRAC2:MMOD EXT') # use external memory, 16 Gbytes

    def getChannelSetting(self):
        '''
        • SINGle  Channel 1 can generate a signal
        • DUAL  Channels 1 and 4 can generate a signal, channels 2 and 3 are unused
        • FOUR  Channels 1, 2, 3, and 4 can generate a signal
        • MARKer  Channel 1 with two markers output on channel 3 and 4
        • DCDuplicate  dual channel duplicate: Channels 1, 2, 3, and 4 can generate a signal. Channel 3 generates the same signal as channel 1. Channel 4 generates the same signal as channel 2.
        • DCMarker  dual channel with marker: Channels 1 and 2 can generate a signal. Channel 1 has two markers output on channel 3 and 4. Channel 2 can generate signals without markers.
        '''
        return SCPI_sock_query(self._session, ':INST:DACM?')

    def setSingleWithMarker(self):
        '''
        MARKer
        • SINGle  Channel 1 can generate a signal
        • DUAL  Channels 1 and 4 can generate a signal, channels 2 and 3 are unused
        • FOUR  Channels 1, 2, 3, and 4 can generate a signal
        • MARKer  Channel 1 with two markers output on channel 3 and 4
        • DCDuplicate  dual channel duplicate: Channels 1, 2, 3, and 4 can generate a signal. Channel 3 generates the same signal as channel 1. Channel 4 generates the same signal as channel 2.
        • DCMarker  dual channel with marker: Channels 1 and 2 can generate a signal. Channel 1 has two markers output on channel 3 and 4. Channel 2 can generate signals without markers.
        '''
        SCPI_sock_send(self._session, ':INST:DACM MARK')

    def setDual(self):
        '''
        DUAL
        • SINGle  Channel 1 can generate a signal
        • DUAL  Channels 1 and 4 can generate a signal, channels 2 and 3 are unused
        • FOUR  Channels 1, 2, 3, and 4 can generate a signal
        • MARKer  Channel 1 with two markers output on channel 3 and 4
        • DCDuplicate  dual channel duplicate: Channels 1, 2, 3, and 4 can generate a signal. Channel 3 generates the same signal as channel 1. Channel 4 generates the same signal as channel 2.
        • DCMarker  dual channel with marker: Channels 1 and 2 can generate a signal. Channel 1 has two markers output on channel 3 and 4. Channel 2 can generate signals without markers.
        '''
        SCPI_sock_send(self._session, ':INST:DACM DUAL')

    def setDualWithMarker(self):
        '''
        DCMarker
        • SINGle  Channel 1 can generate a signal
        • DUAL  Channels 1 and 4 can generate a signal, channels 2 and 3 are unused
        • FOUR  Channels 1, 2, 3, and 4 can generate a signal
        • MARKer  Channel 1 with two markers output on channel 3 and 4
        • DCDuplicate  dual channel duplicate: Channels 1, 2, 3, and 4 can generate a signal. Channel 3 generates the same signal as channel 1. Channel 4 generates the same signal as channel 2.
        • DCMarker  dual channel with marker: Channels 1 and 2 can generate a signal. Channel 1 has two markers output on channel 3 and 4. Channel 2 can generate signals without markers.
        '''
        SCPI_sock_send(self._session, ':INST:DACM DCMarker')

    def setSingle(self):
        '''
        SINGle
        • SINGle  Channel 1 can generate a signal
        • DUAL  Channels 1 and 4 can generate a signal, channels 2 and 3 are unused
        • FOUR  Channels 1, 2, 3, and 4 can generate a signal
        • MARKer  Channel 1 with two markers output on channel 3 and 4
        • DCDuplicate  dual channel duplicate: Channels 1, 2, 3, and 4 can generate a signal. Channel 3 generates the same signal as channel 1. Channel 4 generates the same signal as channel 2.
        • DCMarker  dual channel with marker: Channels 1 and 2 can generate a signal. Channel 1 has two markers output on channel 3 and 4. Channel 2 can generate signals without markers.
        '''
        SCPI_sock_send(self._session, ':INST:DACM SING')