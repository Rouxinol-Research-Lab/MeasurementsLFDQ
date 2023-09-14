import ctypes as ct
import numpy as np

                            ########################################################
                            ###      AlazarMeasurer.dll Functions setup          ###
                            ########################################################

class ATS9872_driver():
    def __init__(self):
        self.AlazarMeasurerdll = ct.CDLL('C:\\Users\\Franscisco Rouxinol\Developer\\MeasurementLFDQ\\src\\instruments\\AlazarMeasurer.dll')            

    # retCode = alazarCapture(preTriggerSamples,
    #     postTriggerSamples,
    #     recordsPerBuffer,
    #     buffersPerAcquisition,
    #     triggerLevel_volts,
    #     triggerRange_volts,
    #     waveformHeadCut,
    #     period,
    #     timeout_ms, //time to wait for acquiring all records in buffer
    #     decimation_value, // divides the clock 1 GHz/ decimation_value. It is 1,2 or 4, or multiples of 10
    #     true,
    #     errorMessage,
    #     &returnI, &returnQ);

        self.AlazarMeasurerdll.alazarCapture.argtypes = ct.c_int, ct.c_int, ct.c_int, ct.c_int, ct.c_double,ct.c_double, ct.c_int, ct.c_int,ct.c_int,ct.c_int, ct.c_bool, ct.POINTER(ct.c_char), ct.c_bool, ct.POINTER(ct.c_double), ct.POINTER(ct.c_double)

        self.AlazarMeasurerdll.alazarCapture.restype  = ct.c_int

    def capture(self,
                preTriggerSamples, 
                postTriggerSamples, 
                recordsPerBuffer, 
                buffersPerAcquisition, 
                powerReference_dBm, 
                inputLoad = 50, 
                triggerLevel_volts = 0.5, 
                triggerRange_volts = 3.0, 
                waveformHeadCut = 100, 
                period = 14, 
                buffer_timeout_ms = 5000, 
                decimation_value = 1, 
                TTL = False, 
                save = False):
        
        '''
            This function captures buffersPerAcquisition*recordsPerBuffer shots of measurements and return I and Q corrected with the powerReference given.

           preTriggerSamples: Number of samples to be acquired before the trigger. The Alazar board is always capture the data. It chooses to save it when there is a trigger. So it is able to capture some of the data before the trigger.

           postTriggerSamples: Number of samples to be acquired before the trigger. This number can be calculated using the length of the pulse times Alazar Sampling Rate.

           buffersPerAcquisition: Number of buffers. Alazar requires a number of buffer to be able to acquire all the data without losing any. The idea is that while alazar is capturing the data and saving it to a buffer
                                  it is also transfering data from a full buffer to the memory. It is important that there is enough buffers for that. 20 should be good enough. For more information
                                  look in the docs at C:\Users\Franscisco Rouxinol\Documents\AlazarDocs.

           recordsPerBuffer: Number of records per buffer. Each captured data defined by the trigger is a record.

           powerReference_dBm: There power in dBm of the reference arrinving at the Board. It is used to correct I and Q.

           inputLoad: The input load of the system. It is 50 Ohm. Used in the correction of I and Q.

           triggerLevel_volts: The level in volts to trigger the signal.

           triggerRange_volts: The maximum value of the trigger signal.

           waveformHeadCut: The number of samples to be ignored from the beginning of each record. As there is a delay until the signal from the DUT arrives the first samples of each record are useless. Therefore, it is useful
                            to remove them.
        
           period: The number of samples that define a period of the signal. It is used for the calculation of I and Q. For a signal of 70 MHz and 1 GHz aquisition, it is around 14 points. It can be calculated
                   with this formula: SamplesPerPeriod = AlazarBoardSamplingRate/SignalFrequency.

           buffer_timeout_ms: The time limit to wait for a new buffer to be processed. If  recordsPerBuffer is large, one may want to increase this waiting time.

           decimation_value: The sampling rate of the Alazar board is at maximum 1 GHz. For lesser values, use the decimation value to divide it by 1, 2, 4 or multiples of 10.

           TTL: If the trigger signal is below 3 V, set this value to True, and 
                triggerLevel_volts to  0.7, 
                triggerRange_volts to 1.

            save: You can save all the buffers for debugging. It saves to a filed called data.bin. To read the saved data use the following python command:
            f = open('data.bin','rb')
            data = f.read()
            f.close()

            a = np.frombuffer(data, dtype=np.uint8)

            plt.plot(a[:3840*10]) # this is for a record of size 3840
            plt.ylim(0,256)
        '''
        
        
        preTrigS = ct.c_int(preTriggerSamples)
        postTrigS = ct.c_int(postTriggerSamples)
        
        nRecords =  ct.c_int(recordsPerBuffer)
        nBuffers =  ct.c_int(buffersPerAcquisition)
        trigLevel = ct.c_double(triggerLevel_volts)
        trigRange = ct.c_double(triggerRange_volts)
        headCut = ct.c_int(waveformHeadCut)
        per = ct.c_int(period)
        timeout_ms = ct.c_int(buffer_timeout_ms)
        decimation_value =  ct.c_int(decimation_value)
        setTTL = ct.c_bool(TTL)
        saveData = ct.c_bool(save)
        errorMessage = ct.create_string_buffer(80)

        I = ct.c_double()
        Q = ct.c_double()
        
        # Reference Amplitude
        powerReference = 10**(powerReference_dBm/10)*1e-3 # Watts
        Ar = np.sqrt(2*powerReference*inputLoad)

        
        result = self.AlazarMeasurerdll.alazarCapture(preTrigS,
                                        postTrigS,
                                        nRecords,
                                        nBuffers,
                                        trigLevel,
                                        trigRange,
                                        headCut,
                                        per,
                                        timeout_ms,
                                        decimation_value,
                                        saveData,
                                        errorMessage,
                                        setTTL,
                                        ct.byref(I),
                                        ct.byref(Q))
        
        if result != 0:
            raise RuntimeError("Error Code "+str(result)+". "+errorMessage.value.decode())
        
        return I.value/Ar,Q.value/Ar