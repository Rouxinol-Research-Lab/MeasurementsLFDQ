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

    def capture(self,preTriggerSamples, postTriggerSamples, recordsPerBuffer, buffersPerAcquisition, powerReference_dBm, inputLoad = 50, triggerLevel_volts = 0.5, triggerRange_volts = 3.0, waveformHeadCut = 100, period = 14, buffer_timeout_ms = 5000, decimation_value = 1, TTL = False, save = False):
        
        
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