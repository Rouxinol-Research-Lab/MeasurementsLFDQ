from struct import unpack
import numpy as np
from instruments.SCPI_socket import *

def generateData(numberOfChannels, freq, tFcav, tPulse):
    awgRate = 65e9/numberOfChannels
    pulsePeriod = 1.0/freq
    numberOfPointsPerPeriod = int(round(pulsePeriod*awgRate))
    datatype = np.int8
    
    numberOfPeriods = int(round(tFcav/pulsePeriod))

    x = np.arange(0,pulsePeriod*numberOfPeriods,1/awgRate)

    pulseOsc = np.array(2**7*np.sin(2*np.pi*freq*x),dtype=datatype)
    
    missingPoints = int(np.ceil(pulseOsc.nbytes/256)*256) - int(pulseOsc.nbytes)
    if missingPoints != 0:
        missingPointsArray = np.zeros(missingPoints,dtype=datatype)
        pulseOsc = np.append(pulseOsc,missingPointsArray)
        
    totalNumberOfBytes = int(np.ceil((awgRate*tPulse)/256)*256)
    
    return totalNumberOfBytes,pulseOsc

def convertToStr(data):
    #generate an array with strings
    data_arrstr = np.char.mod('%f', data)
    #combine to a string
    data_str = ",".join(data_arrstr)
    
    return data_str



def findAwgRateAndPeriod(freq,numberOfChannels=1):
    multiple = 256
    n = 0

    foundit = False
    
    while(not foundit):
        npoints = (5+n)*multiple
        nperiod = int(65e9/freq/numberOfChannels)
        period = np.ceil(npoints/nperiod)
        awgRate = int(npoints/period*freq)
        
        if awgRate < 53.76e9/numberOfChannels:
            n += 1
        else:
            foundit = True
    
    
    return period,awgRate,npoints

class M8195A_driver():
    def __init__(self, address):
        self._session = SCPI_sock_connect(address)

    def toggleChannelOuput(self,channel):
        print("Checking output state from channel {}.".format(channel))
        result = int(SCPI_sock_query(self._session,":OUTP{}?".format(channel)))
        print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
        
        print("Changing output state.")
        if result == 0:
            SCPI_sock_send(self._session,":OUTP{} 1".format(channel))
        else:
            SCPI_sock_send(self._session,":OUTP{} 0".format(channel))
        print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))

    def openChanneloutput(self,channel):
        SCPI_sock_send(self._session,":OUTP{} 1".format(channel))

    def closeChanneloutput(self,channel):
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

    def defineSegment(self, nbytes):
        SCPI_sock_send(self._session,":TRAC1:DEF 1,"+ str(nbytes) +",0")

    def allocMemory(self,nbytes):
        if not isinstance(nbytes,int):
            raise TypeError("Parameter nbytes must be an integer!")
            
        if nbytes%256 != 0:
            raise ValueError("Parameter nbytes must be a multiple of 256!")
        
        print('Deleting previously defined segment.')
        SCPI_sock_send(self._session,":TRAC1:DEL:ALL")
        print("AWG response: "+ SCPI_sock_query(self._session,"SYST:ERR?"))

        print('Defining segment size and setting all values to 0.')
        SCPI_sock_send(self._session,":TRAC1:DEF 1,"+ str(nbytes) +",0")
        print("AWG response: "+ SCPI_sock_query(self._session,"SYST:ERR?"))

        print('Checking segment defined:')
        print("id,size")
        print(SCPI_sock_query(self._session,":TRAC1:CAT?"))
        print("AWG response: "+ SCPI_sock_query(self._session,"SYST:ERR?"))

    def setMarker(self,index,marker_value):
        '''
            marker_value:
            0 -> Both markers to low
            1 -> Marker 1 to high
            2 -> Marker 2 to high
            3 -> Both marker to high

            index:
            the starting index to set the marker
        '''
        a = np.zeros(256)
        
        
        # converte para os dados especificados
        marker1 = np.zeros(len(a),dtype=int)
        marker1[:] = marker_value
        
        withmarker = np.array(tuple(zip(a,marker1))).flatten()

        data_arrstr = np.char.mod('%d', withmarker)
        #combine to a string
        data_str = ",".join(data_arrstr)
        
        SCPI_sock_send(self._session, ':TRAC1:DATA 1,{},{}'.format(index,data_str))

    def setWave(self,freq,marker_value, index, size,awgRate):

        x = np.arange(0,size*1/awgRate,1/awgRate)
        awgOsc = np.array((2**7-1)*np.sin(2*np.pi*(freq)*x),dtype=np.int8)

        # converte para os dados especificados
        marker1 = np.zeros(len(awgOsc),dtype=int)
        marker1[:] = marker_value

        withmarker = np.array(tuple(zip(awgOsc,marker1))).flatten()

        data_arrstr = np.char.mod('%d', withmarker)
        #combine to a string
        data_str = ",".join(data_arrstr)

        SCPI_sock_send(self._session, ':TRAC1:DATA 1,{},{}'.format(index,data_str))


    def setCWFrequency(self,freq,channel=1):

        self.stop()
        self.setSingle()

        _,awgRate,npoints = findAwgRateAndPeriod(freq)

        SCPI_sock_send(self._session,":TRAC:DEL {}".format(channel))
        SCPI_sock_send(self._session,":TRAC{}:DEF 1,".format(channel)+ str(npoints) +",0")

        self.set_sampleRate(awgRate)

        x = np.arange(0,npoints*1/awgRate,1/awgRate)
        awgOsc = np.array((2**7-1)*np.sin(2*np.pi*(freq)*x),dtype=np.int8)

        # converte para os dados especificados
        data_arrstr = np.char.mod('%d', awgOsc)
        #combine to a string
        data_str = ",".join(data_arrstr)
        # envia os dados para awg
        SCPI_sock_send(self._session, ':TRAC{}:DATA 1,0,{}'.format(channel,data_str))


    def sendData(self,channel, x_str,delay, numberOfChannels):
            
        awgRate = 65e9/numberOfChannels
        
        delayInBytes = int(np.ceil(delay*awgRate/256)*256)
        
        print("Sendind waveform to channel {}".format(channel))
        SCPI_sock_send(self._session, ':TRAC{}:DATA 1,{},{}'.format(channel, delayInBytes, x_str))
        print("AWG response:" + SCPI_sock_query(self._session,"SYST:ERR?"))

    def disableChannel(self,channel):
        SCPI_sock_send(self._session,":OUTP{} 0".format(channel))
        print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
        
    def enableChannel(self,channel):
        SCPI_sock_send(self._session,":OUTP{} 1".format(channel))
        print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))


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

    def _convertToByte(self,data, A):

        np.clip(data, -A, A, data)

        size = 256 * (1 + divmod(len(data) - 1, 256)[0])

        y = np.zeros(size, dtype=np.int8)
        y[:len(data)] = np.array(127 * data / A, dtype=np.int8)
        return y

    def loadWaveform(self,data):
        self.convertedData = self._convertToByte(data,self.Vamp)

    def clearWaveform(self,ch,seq):
        self.write(":TRAC{}:DEL {}".format(ch,seq));

    def sendWaveform(self,ch,seq):
        data = self.convertedData
        n_elem = len(data)

        self.write(':TRAC{}:DEF {},{},0'.format(ch,seq, n_elem))
        # create binary data as bytes with header
        start, length = 0, len(data)
        sLen = b'%d' % length
        sHead = b'#%d%s' % (len(sLen), sLen)
        # send to AWG
        sCmd = b':TRAC%d:DATA %d,%d,' % (ch, seq, start)
        self.write_raw(sCmd + sHead + data[start:start+length].tobytes())


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
        size = int(SCPI_sock_query(self._session,':TRAC1:CAT?').split(',')[1])
        data = SCPI_sock_query(self._session,':TRAC1:DATA? 1, 0,{}'.format(size))
        return np.array(data.split(',')).astype(int)


    def setVoltage(self, channel, volt):
        SCPI_sock_send(self._session, ':VOLT{} {}'.format(channel, volt))
        print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
    

    def getVoltage(self, channel):
        result = SCPI_sock_query(self._session, ':VOLT{}?'.format(channel))
        print(result)


    def setVoltageOffset(self, channel, volt):
        SCPI_sock_send(self._session, ':VOLT{}:OFFS {}'.format(channel, volt))
        print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))

    def getVoltageOffset(self, channel):
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