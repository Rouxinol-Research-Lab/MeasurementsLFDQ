import numpy as np

def prepareSignalData(measurementPulseLength,excitationPulsesLength,excitationPulsesDelay,excitationPulsesPhase,freq,awgRate,markerValueForExcitation=2,markerValueForMeasurement=1):


    # This is to guarantee that it is only half a period oscillation
    measurementPulseLength = np.ceil(measurementPulseLength*freq*2)/freq/2
    for i in range(len(excitationPulsesLength)):
        excitationPulsesLength[i] = np.ceil(excitationPulsesLength[i]*freq*2)/freq/2
    for i in range(len(excitationPulsesDelay)):
        excitationPulsesDelay[i] = np.ceil(excitationPulsesDelay[i]*freq*2)/freq/2
    
    totalLength = np.sum(excitationPulsesLength) + np.sum(excitationPulsesDelay)  + measurementPulseLength
    
    x = np.arange(0,totalLength,1/awgRate)
    
    size = len(x)
    pulsesExcitation = np.zeros(size,dtype=np.int8)
    pulseMeasurement = np.zeros(size,dtype=np.int8)
    pulseMarkers = np.zeros(size,dtype=np.int8)
    
    
    pos = 0
    timeDuration = 0
    for i in range(len(excitationPulsesLength)):
        xExcitation = np.arange(0,excitationPulsesLength[i],1/awgRate) + timeDuration
        awgOscExcitation = np.array((2**7-1)*np.sin(2*np.pi*(freq)*xExcitation+excitationPulsesPhase[i]),dtype=np.int8)
    
        end = pos+len(awgOscExcitation)
        pulsesExcitation[pos:end] = awgOscExcitation
        pulseMarkers[pos:end] = markerValueForExcitation
    
        pos = end + int(excitationPulsesDelay[i]*awgRate)
        timeDuration += excitationPulsesDelay[i] + excitationPulsesLength[i]
    
    xMeasurement = np.arange(0,measurementPulseLength,1/awgRate)
    awgOscMeasurement = np.array((2**7-1)*np.sin(2*np.pi*(freq)*xMeasurement),dtype=np.int8)
    
    pulseMeasurement[-len(awgOscMeasurement):] = awgOscMeasurement
    pulseMarkers[-len(awgOscMeasurement):] = markerValueForMeasurement
    pulseMarkers[-1]=0

    return x,pulseMeasurement,pulsesExcitation,pulseMarkers

def prepareMeasurementSignalData(measurementPulseLength,freq,awgRate,markerValueForMeasurement=1):
    # This is to guarantee that it is only half a period oscillation
    measurementPulseLength = np.ceil(measurementPulseLength*freq*2)/freq/2
    
    xMeasurement = np.arange(0,measurementPulseLength,1/awgRate)
    awgOscMeasurement = np.array((2**7-1)*np.sin(2*np.pi*(freq)*xMeasurement),dtype=np.int8)
    pulseMarkers = np.ndarray(len(xMeasurement),dtype=np.int8)
    pulseMarkers.fill(markerValueForMeasurement)
    pulseMarkers[-1]=0

    return xMeasurement,awgOscMeasurement,pulseMarkers

def addPadding(pulses,padding = 512):
    addedZerosLength = len(pulses)%padding
    return np.append(np.zeros(padding-addedZerosLength,dtype=np.int8),pulses)