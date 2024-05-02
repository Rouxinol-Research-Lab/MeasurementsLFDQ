from measurements.Pulse import Pulse
from measurements.PulseSequence import PulseSequence
from measurements.DataChannelManager import DataChannelManager

import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output


def cavity_measure(instruments, parameters, freqs):

    p1 = Pulse(length = parameters['RFExcitationLength'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)
    
    mp = Pulse(length = parameters['RFMeasurementLength'],
               amplitude = 1,
               phase = 0,
               frequency = parameters['Measurement_IF'])
    
    # create pulse sequence
    s1 = PulseSequence("transmon3D")
    s1.startup_delay = 1e-6
    parameters['RFExcitationState'] = False
    
    s1.clear()
    
    if parameters['RFExcitationState']: # add excitation pulse only if we want it
        s1.add(p1,'q1',parameters['RFExcitationDelay']) # add pulse p1 to channel 'q1', put a delay after pulse p1
    
    s1.add(mp, 'm')
    
    # prepare data to awg
    ms = DataChannelManager('AWG')
    
    instruments['awg'].setRefInClockFrequency(10e6)
    instruments['awg'].setRefInClockExternal()  
    instruments['awg'].set_sampleRate(61440000000)
    
    instruments['awg'].setDualWithMarker() # use two markers, one for alazar, other for instruments
    SCPI_sock_send(instruments['awg']._session, ':TRAC2:MMOD EXT') # use external memory, 16 Gbytes
    SCPI_sock_send(instruments['awg']._session, ':INST:MEM:EXT:RDIV DIV2') # devide memory, one for each channel
    
    # label the awg channels to what one used for the pulses
    ms.clearAwgChannel()
    ms.labelAwgChannel(2,'q1', parameters['Excitation_IF'])
    ms.labelAwgChannel(1,'m', parameters['Measurement_IF'], True) # if set to true, that means it is a measurement channel
    
    channelData = ms.prepareChannelData(instruments['awg'], s1, parameters['measurementLength']) # add total length, pulses and relaxation to alloc the necessary bytes in memory
    
    # clear memory, alloc new memory, put data into awg memory
    instruments['awg'].clearMemory()
    sleep(0.05)
    ms.allocAwgMemory(instruments['awg'],channelData)
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'m')
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
    sleep(0.05)
    
    instruments['awg'].start()
    
    instruments['RFsourceMeasurement'].set_pulse_trigger_external()
    instruments['RFsourceMeasurement'].setPulsePolarityInverted()
    instruments['RFsourceMeasurement'].start_mod()
    
    instruments['RFsourceExcitation'].set_pulse_trigger_external()
    instruments['RFsourceExcitation'].setPulsePolarityNormal()
    instruments['RFsourceExcitation'].start_mod()
    
    instruments['RFsourceMeasurement'].set_amplitude(parameters['RFMeasurementAmplitude'])
    
    instruments['RFsourceExcitation'].set_amplitude(parameters['RFExcitationAmplitude'])
    instruments['RFsourceExcitation'].set_frequency(parameters['ExcitationFrequency']-parameters['Excitation_IF'])
    
    instruments['RFsourceMeasurement'].start_rf()
    if parameters['RFExcitationState']:
        instruments['RFsourceExcitation'].start_rf()
    
    
    
    instruments['att'].set_attenuation(parameters['attenuation'])
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray(len(freqs))
    Qs = np.ndarray(len(freqs))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,freq in enumerate(freqs):
        clear_output(wait=True)
        
        instruments['RFsourceMeasurement'].set_frequency(freq-parameters['Measurement_IF'])
        sleep(0.05)
    
        I,Q = alazar.capture(0,
                             pointsPerRecord,
                             parameters['numberOfBuffers'],
                             parameters['numberOfRecordsPerBuffers'],
                             parameters['amplitudeReferenceAlazar'],
                             save=False,
                             waveformHeadCut=parameters['waveformHeadCut'],
                             decimation_value = parameters['decimationValue'],
                             triggerLevel_volts=0.7, 
                             triggerRange_volts=1,
                             TTL=True)
    
        Is[idx] = I
        Qs[idx] = Q 
        
        mags = 20*np.log10(np.sqrt(Is**2+Qs**2))
    
        
        plt.pause(0.05)
        plt.plot(freqs,mags)
        
    clear_output(wait=True)
    plt.plot(freqs,mags)
    
    instruments['Voltsource'].turn_off()
    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def twotone_measure(instruments, parameters, freqs):
    p1 = Pulse(length = parameters['RFExcitationLength'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)
    
    mp = Pulse(length = parameters['RFMeasurementLength'],
               amplitude = 1,
               phase = 0,
               frequency = parameters['Measurement_IF'])
    
    # create pulse sequence
    s1 = PulseSequence("transmon3D")
    s1.startup_delay = 1e-6
    
    s1.clear()
    
    s1.add(p1,'q1',parameters['RFExcitationDelay']) # add pulse p1 to channel 'q1', put a delay after pulse p1
    s1.add(mp, 'm')
    
    # prepare data to awg
    ms = DataChannelManager('AWG')
    
    instruments['awg'].setRefInClockFrequency(10e6)
    instruments['awg'].setRefInClockExternal()  
    instruments['awg'].set_sampleRate(61440000000)
    
    instruments['awg'].setDualWithMarker() # use two markers, one for alazar, other for instruments
    SCPI_sock_send(instruments['awg']._session, ':TRAC2:MMOD EXT') # use external memory, 16 Gbytes
    SCPI_sock_send(instruments['awg']._session, ':INST:MEM:EXT:RDIV DIV2') # devide memory, one for each channel
    
    # label the awg channels to what one used for the pulses
    ms.clearAwgChannel()
    ms.labelAwgChannel(2,'q1', parameters['Excitation_IF'])
    ms.labelAwgChannel(1,'m', parameters['Measurement_IF'], True) # if set to true, that means it is a measurement channel
    
    channelData = ms.prepareChannelData(instruments['awg'], s1, parameters['measurementLength']) # add total length, pulses and relaxation to alloc the necessary bytes in memory
    
    # clear memory, alloc new memory, put data into awg memory
    instruments['awg'].clearMemory()
    sleep(0.05)
    ms.allocAwgMemory(instruments['awg'],channelData)
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'m')
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
    sleep(0.05)
    
    instruments['awg'].start()
    
    instruments['RFsourceMeasurement'].set_pulse_trigger_external()
    instruments['RFsourceMeasurement'].setPulsePolarityInverted()
    instruments['RFsourceMeasurement'].start_mod()
    
    instruments['RFsourceExcitation'].set_pulse_trigger_external()
    instruments['RFsourceExcitation'].setPulsePolarityNormal()
    instruments['RFsourceExcitation'].start_mod()
    
    instruments['RFsourceMeasurement'].set_amplitude(parameters['RFMeasurementAmplitude'])
    
    instruments['RFsourceExcitation'].set_amplitude(parameters['RFExcitationAmplitude'])
    
    instruments['RFsourceMeasurement'].set_frequency(parameters['MeasurementFrequency']-parameters['Measurement_IF'])
    
    instruments['RFsourceMeasurement'].start_rf()
    instruments['RFsourceExcitation'].start_rf()
    
    
    
    instruments['att'].set_attenuation(parameters['attenuation'])
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray(len(freqs))
    Qs = np.ndarray(len(freqs))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,freq in enumerate(freqs):
        clear_output(wait=True)
        
        instruments['RFsourceExcitation'].set_frequency(freq-parameters['Excitation_IF'])
        sleep(0.05)
    
        I,Q = alazar.capture(0,
                             pointsPerRecord,
                             parameters['numberOfBuffers'],
                             parameters['numberOfRecordsPerBuffers'],
                             parameters['amplitudeReferenceAlazar'],
                             save=False,
                             waveformHeadCut=parameters['waveformHeadCut'],
                             decimation_value = parameters['decimationValue'],
                             triggerLevel_volts=0.7, 
                             triggerRange_volts=1,
                             TTL=True)
    
        Is[idx] = I
        Qs[idx] = Q 
        
        mags = 20*np.log10(np.sqrt(Is**2+Qs**2))
    
        
        plt.pause(0.05)
        plt.plot(freqs,mags)
        
    clear_output(wait=True)
    plt.plot(freqs,mags)
    
    instruments['Voltsource'].turn_off()
    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def rabi_measure(instruments, parameters, pulse_durations):
    p1 = Pulse(length = pulse_durations[0],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)
    
    mp = Pulse(length = parameters['RFMeasurementLength'],
               amplitude = 1,
               phase = 0,
               frequency = parameters['Measurement_IF'])
    
    # create pulse sequence
    s1 = PulseSequence("transmon3D")
    s1.startup_delay = 1e-6
    
    s1.clear()
    
    s1.add(p1,'q1',parameters['RFExcitationDelay']) # add pulse p1 to channel 'q1', put a delay after pulse p1
    s1.add(mp, 'm')
    
    # prepare data to awg
    ms = DataChannelManager('AWG')
    
    instruments['awg'].setRefInClockFrequency(10e6)
    instruments['awg'].setRefInClockExternal()  
    instruments['awg'].set_sampleRate(61440000000)
    
    instruments['awg'].setDualWithMarker() # use two markers, one for alazar, other for instruments
    SCPI_sock_send(instruments['awg']._session, ':TRAC2:MMOD EXT') # use external memory, 16 Gbytes
    SCPI_sock_send(instruments['awg']._session, ':INST:MEM:EXT:RDIV DIV2') # devide memory, one for each channel
    
    # label the awg channels to what one used for the pulses
    ms.clearAwgChannel()
    ms.labelAwgChannel(2,'q1', parameters['Excitation_IF'])
    ms.labelAwgChannel(1,'m', parameters['Measurement_IF'], True) # if set to true, that means it is a measurement channel
    
    channelData = ms.prepareChannelData(instruments['awg'], s1, parameters['measurementLength']) # add total length, pulses and relaxation to alloc the necessary bytes in memory
    
    # clear memory, alloc new memory, put data into awg memory
    instruments['awg'].clearMemory()
    sleep(0.05)
    ms.allocAwgMemory(instruments['awg'],channelData)
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'m')
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
    sleep(0.05)
    
    instruments['awg'].start()
    
    instruments['RFsourceMeasurement'].set_pulse_trigger_external()
    instruments['RFsourceMeasurement'].setPulsePolarityInverted()
    instruments['RFsourceMeasurement'].start_mod()
    
    instruments['RFsourceExcitation'].set_pulse_trigger_external()
    instruments['RFsourceExcitation'].setPulsePolarityNormal()
    instruments['RFsourceExcitation'].start_mod()
    
    instruments['RFsourceMeasurement'].set_amplitude(parameters['RFMeasurementAmplitude'])
    
    instruments['RFsourceExcitation'].set_amplitude(parameters['RFExcitationAmplitude'])
    
    instruments['RFsourceMeasurement'].set_frequency(parameters['MeasurementFrequency']-parameters['Measurement_IF'])
    instruments['RFsourceExcitation'].set_frequency(parameters['ExcitationFrequency']-parameters['Excitation_IF'])
    
    instruments['RFsourceMeasurement'].start_rf()
    instruments['RFsourceExcitation'].start_rf()
    
    
    
    instruments['att'].set_attenuation(parameters['attenuation'])
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray(len(freqs))
    Qs = np.ndarray(len(freqs))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,duration in enumerate(pulse_durations):
        clear_output(wait=True)

        p1.length = duration
        ms.updateChannelData(channelData,s1,'q1')
        ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
        sleep(0.05)
        ms.setInstrumentsMarker(instruments['awg'], channelData)
    
        I,Q = alazar.capture(0,
                             pointsPerRecord,
                             parameters['numberOfBuffers'],
                             parameters['numberOfRecordsPerBuffers'],
                             parameters['amplitudeReferenceAlazar'],
                             save=False,
                             waveformHeadCut=parameters['waveformHeadCut'],
                             decimation_value = parameters['decimationValue'],
                             triggerLevel_volts=0.7, 
                             triggerRange_volts=1,
                             TTL=True)
    
        Is[idx] = I
        Qs[idx] = Q 
        
        mags = 20*np.log10(np.sqrt(Is**2+Qs**2))
    
        
        plt.pause(0.05)
        plt.plot(freqs,mags)
        
    clear_output(wait=True)
    plt.plot(freqs,mags)
    
    instruments['Voltsource'].turn_off()
    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def T1_measure(instruments, parameters, delays):
    p1 = Pulse(length = parameters['PiPulse'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)
    
    mp = Pulse(length = parameters['RFMeasurementLength'],
               amplitude = 1,
               phase = 0,
               frequency = parameters['Measurement_IF'])
    
    # create pulse sequence
    s1 = PulseSequence("transmon3D")
    s1.startup_delay = 1e-6
    
    s1.clear()
    
    s1.add(p1,'q1',delays[0]) # add pulse p1 to channel 'q1', put a delay after pulse p1
    s1.add(mp, 'm')
    
    # prepare data to awg
    ms = DataChannelManager('AWG')
    
    instruments['awg'].setRefInClockFrequency(10e6)
    instruments['awg'].setRefInClockExternal()  
    instruments['awg'].set_sampleRate(61440000000)
    
    instruments['awg'].setDualWithMarker() # use two markers, one for alazar, other for instruments
    SCPI_sock_send(instruments['awg']._session, ':TRAC2:MMOD EXT') # use external memory, 16 Gbytes
    SCPI_sock_send(instruments['awg']._session, ':INST:MEM:EXT:RDIV DIV2') # devide memory, one for each channel
    
    # label the awg channels to what one used for the pulses
    ms.clearAwgChannel()
    ms.labelAwgChannel(2,'q1', parameters['Excitation_IF'])
    ms.labelAwgChannel(1,'m', parameters['Measurement_IF'], True) # if set to true, that means it is a measurement channel
    
    channelData = ms.prepareChannelData(instruments['awg'], s1, parameters['measurementLength']) # add total length, pulses and relaxation to alloc the necessary bytes in memory
    
    # clear memory, alloc new memory, put data into awg memory
    instruments['awg'].clearMemory()
    sleep(0.05)
    ms.allocAwgMemory(instruments['awg'],channelData)
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'m')
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
    sleep(0.05)
    
    instruments['awg'].start()
    
    instruments['RFsourceMeasurement'].set_pulse_trigger_external()
    instruments['RFsourceMeasurement'].setPulsePolarityInverted()
    instruments['RFsourceMeasurement'].start_mod()
    
    instruments['RFsourceExcitation'].set_pulse_trigger_external()
    instruments['RFsourceExcitation'].setPulsePolarityNormal()
    instruments['RFsourceExcitation'].start_mod()
    
    instruments['RFsourceMeasurement'].set_amplitude(parameters['RFMeasurementAmplitude'])
    
    instruments['RFsourceExcitation'].set_amplitude(parameters['RFExcitationAmplitude'])
    
    instruments['RFsourceMeasurement'].set_frequency(parameters['MeasurementFrequency']-parameters['Measurement_IF'])
    instruments['RFsourceExcitation'].set_frequency(parameters['ExcitationFrequency']-parameters['Excitation_IF'])
    
    instruments['RFsourceMeasurement'].start_rf()
    instruments['RFsourceExcitation'].start_rf()
    
    
    
    instruments['att'].set_attenuation(parameters['attenuation'])
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray(len(freqs))
    Qs = np.ndarray(len(freqs))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,delay in enumerate(delays):
        clear_output(wait=True)

        s1.list_of_delays[0] = delay
        ms.updateChannelData(channelData,s1,'q1')
        ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
        sleep(0.05)
        ms.setInstrumentsMarker(instruments['awg'], channelData)
    
        I,Q = alazar.capture(0,
                             pointsPerRecord,
                             parameters['numberOfBuffers'],
                             parameters['numberOfRecordsPerBuffers'],
                             parameters['amplitudeReferenceAlazar'],
                             save=False,
                             waveformHeadCut=parameters['waveformHeadCut'],
                             decimation_value = parameters['decimationValue'],
                             triggerLevel_volts=0.7, 
                             triggerRange_volts=1,
                             TTL=True)
    
        Is[idx] = I
        Qs[idx] = Q 
        
        mags = 20*np.log10(np.sqrt(Is**2+Qs**2))
    
        
        plt.pause(0.05)
        plt.plot(freqs,mags)
        
    clear_output(wait=True)
    plt.plot(freqs,mags)
    
    instruments['Voltsource'].turn_off()
    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def ramsey_measure(instruments, parameters, delays):
    p1 = Pulse(length = parameters['HalfPiPulse'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)

    p2 = Pulse(length = parameters['HalfPiPulse'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)
    
    mp = Pulse(length = parameters['RFMeasurementLength'],
               amplitude = 1,
               phase = 0,
               frequency = parameters['Measurement_IF'])
    
    # create pulse sequence
    s1 = PulseSequence("transmon3D")
    s1.startup_delay = 1e-6
    
    s1.clear()
    
    s1.add(p1,'q1',delays[0]) # add pulse p1 to channel 'q1', put a delay after pulse p1
    s1.add(p2,'q1',parameters['RFExcitationDelay']) # add pulse p1 to channel 'q1', put a delay after pulse p1
    s1.add(mp, 'm')
    
    # prepare data to awg
    ms = DataChannelManager('AWG')
    
    instruments['awg'].setRefInClockFrequency(10e6)
    instruments['awg'].setRefInClockExternal()  
    instruments['awg'].set_sampleRate(61440000000)
    
    instruments['awg'].setDualWithMarker() # use two markers, one for alazar, other for instruments
    SCPI_sock_send(instruments['awg']._session, ':TRAC2:MMOD EXT') # use external memory, 16 Gbytes
    SCPI_sock_send(instruments['awg']._session, ':INST:MEM:EXT:RDIV DIV2') # devide memory, one for each channel
    
    # label the awg channels to what one used for the pulses
    ms.clearAwgChannel()
    ms.labelAwgChannel(2,'q1', parameters['Excitation_IF'])
    ms.labelAwgChannel(1,'m', parameters['Measurement_IF'], True) # if set to true, that means it is a measurement channel
    
    channelData = ms.prepareChannelData(instruments['awg'], s1, parameters['measurementLength']) # add total length, pulses and relaxation to alloc the necessary bytes in memory
    
    # clear memory, alloc new memory, put data into awg memory
    instruments['awg'].clearMemory()
    sleep(0.05)
    ms.allocAwgMemory(instruments['awg'],channelData)
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'m')
    sleep(0.05)
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
    sleep(0.05)
    
    instruments['awg'].start()
    
    instruments['RFsourceMeasurement'].set_pulse_trigger_external()
    instruments['RFsourceMeasurement'].setPulsePolarityInverted()
    instruments['RFsourceMeasurement'].start_mod()
    
    instruments['RFsourceExcitation'].set_pulse_trigger_external()
    instruments['RFsourceExcitation'].setPulsePolarityNormal()
    instruments['RFsourceExcitation'].start_mod()
    
    instruments['RFsourceMeasurement'].set_amplitude(parameters['RFMeasurementAmplitude'])
    
    instruments['RFsourceExcitation'].set_amplitude(parameters['RFExcitationAmplitude'])
    
    instruments['RFsourceMeasurement'].set_frequency(parameters['MeasurementFrequency']-parameters['Measurement_IF'])
    instruments['RFsourceExcitation'].set_frequency(parameters['ExcitationFrequency']-parameters['Excitation_IF'])
    
    instruments['RFsourceMeasurement'].start_rf()
    instruments['RFsourceExcitation'].start_rf()
    
    
    
    instruments['att'].set_attenuation(parameters['attenuation'])
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray(len(freqs))
    Qs = np.ndarray(len(freqs))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,delay in enumerate(delays):
        clear_output(wait=True)

        s1.list_of_delays[0] = delay # update the delay between pulse 1 and pulse 2
        ms.updateChannelData(channelData,s1,'q1')
        ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
        sleep(0.05)
        ms.setInstrumentsMarker(instruments['awg'], channelData)
    
        I,Q = alazar.capture(0,
                             pointsPerRecord,
                             parameters['numberOfBuffers'],
                             parameters['numberOfRecordsPerBuffers'],
                             parameters['amplitudeReferenceAlazar'],
                             save=False,
                             waveformHeadCut=parameters['waveformHeadCut'],
                             decimation_value = parameters['decimationValue'],
                             triggerLevel_volts=0.7, 
                             triggerRange_volts=1,
                             TTL=True)
    
        Is[idx] = I
        Qs[idx] = Q 
        
        mags = 20*np.log10(np.sqrt(Is**2+Qs**2))
    
        
        plt.pause(0.05)
        plt.plot(freqs,mags)
        
    clear_output(wait=True)
    plt.plot(freqs,mags)
    
    instruments['Voltsource'].turn_off()
    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

