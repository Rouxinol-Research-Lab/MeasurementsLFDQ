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
        awgRate = npoints/period*freq
        
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

    def start(self):
        SCPI_sock_send(self._session,":INIT:IMM")    
        print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
        
    def stop(self):
        SCPI_sock_send(self._session,":ABOR")
        print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))

    def close(self):
        SCPI_sock_close(self._session)

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


    def setNumberOfChannels(self,numberOfChannels):
        if numberOfChannels > 2:
            raise ValueError("numberOfChannels cannot be higher than 2 for this instrument! Check for more licenses.")
            
        if numberOfChannels == 1:
            print("Setting system to singular.")
            SCPI_sock_send(self._session,":INST:DACM SING")
            print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
            
            print("Setting memory division to 1.")
            SCPI_sock_send(self._session,":INST:MEM:EXT:RDIV DIV1")
            print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
            
            print("Setting channel 1 memory to extended.")
            SCPI_sock_send(self._session,":TRAC1:MMOD EXT")
            print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
            
            
        else:  # numberOfChannel is 2
            print("Setting system to dual.")
            SCPI_sock_send(self._session,":INST:DACM DUAL")
            print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
            
            print("Setting memory division to 2.")
            SCPI_sock_send(self._session,":INST:MEM:EXT:RDIV DIV2")
            print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
            
            print("Setting channel 1 memory to extended.")
            SCPI_sock_send(self._session,":TRAC1:MMOD EXT")
            print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
            
            print("Setting channel 4 memory to extended.")
            SCPI_sock_send(self._session,":TRAC4:MMOD EXT")
            print("AWG Response: " + SCPI_sock_query(self._session,"SYST:ERR?"))
            

        

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


    def get_sampleRate(self):
        '''
            Set or query the sample frequency of the output DAC.
        '''

        return float(SCPI_sock_query(self._session,":FREQ:RAST?"))
    



    def set_sampleRate(self,freq):
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
