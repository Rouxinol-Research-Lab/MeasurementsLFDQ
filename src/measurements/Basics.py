from measurements.Pulse import Pulse, Envelope
from measurements.PulseSequence import PulseSequence
from measurements.DataChannelManager import DataChannelManager

import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output

from instruments.SCPI_socket import *
from time import sleep,strftime,localtime


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

    if parameters['fluxState']:
        instruments['Voltsource'].turn_on()
        sleep(0.05)
        instruments['Voltsource'].ramp_voltage(parameters['fluxValue'])
    
    
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
    
        I,Q = instruments['alazar'].capture(0,
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

    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def powersweep_measure(instruments, parameters, freqs, attenuations):
    p1 = Pulse(length = parameters['RFExcitationLength'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)
    
    mp = Pulse(length = parameters['RFMeasurementLength'],
               amplitude = 1,
               phase = 0,
               frequency = parameters['Measurement_IF'])
    
    # create pulse sequence
    s1 = PulseSequence("powersweep")
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

    if parameters['fluxState']:
        instruments['Voltsource'].turn_on()
        sleep(0.05)
        instruments['Voltsource'].ramp_voltage(parameters['fluxValue'])
    
    
    
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray((len(attenuations),len(freqs)))
    Qs = np.ndarray((len(attenuations),len(freqs)))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)

    name = parameters['ExperimentName'] + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ s1.name

    howtoplot = "\
    data = np.load('"+name+".npz')\n\
    freqs = data['freqs']\n\
    mags = np.abs(data['Z'])\n\
    attenuations =data['attenuations']\n\
    phase = np.unwrap(np.angle(data['Z']))\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.pcolor(attenuations,freqs*1e-6,20*np.log10(mags.T))\n\
    cbar=plt.colorbar(label='S21 (dB)')\n\
    cbar.ax.tick_params(labelsize=20)\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Attenuation (dB)',fontsize=20)\n\
    ax.set_ylabel('S21 (dB)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"
    
    for idx_att,attenuator_att in enumerate(attenuations):
        instruments['att'].set_attenuation(attenuator_att)
        for idx,freq in enumerate(freqs):
            clear_output(wait=True)
            
            instruments['RFsourceMeasurement'].set_frequency(freq-parameters['Measurement_IF'])
            sleep(0.05)
        
            I,Q = instruments['alazar'].capture(0,
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
            
            Is[idx_att,idx] = I
            Qs[idx_att,idx] = Q 

            
            mags = 20*np.log10(np.sqrt(Is**2+Qs**2))
        
            
            plt.pause(0.05)
            plt.pcolor(attenuations,freqs*1e-6,mags.T)

    Z = Is+Qs*1j

    np.savez(name,header=howtoplot,params = parameters,freqs=freqs,Z=Z,attenuations=attenuations)
        
    clear_output(wait=True)
    plt.pcolor(attenuations,freqs*1e-6,mags.T)

    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def fluxsweep_measure(instruments, parameters, freqs, volts):
    p1 = Pulse(length = parameters['RFExcitationLength'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)
    
    mp = Pulse(length = parameters['RFMeasurementLength'],
               amplitude = 1,
               phase = 0,
               frequency = parameters['Measurement_IF'])
    
    # create pulse sequence
    s1 = PulseSequence("fluxsweep")
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

    instruments['Voltsource'].turn_on()
    sleep(0.05)
    instruments['Voltsource'].ramp_voltage(volts[0])
    
    
    instruments['att'].set_attenuation(parameters['attenuation'])
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray((len(volts),len(freqs)))
    Qs = np.ndarray((len(volts),len(freqs)))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)

    name = parameters['ExperimentName'] + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ s1.name
    
    howtoplot = "\
        data = np.load('"+name+".npz')\n\
        freqs = data['freqs']\n\
        mags = np.abs(data['Z'])\n\
        voltages =data['voltages']\n\
        phase = np.unwrap(np.angle(data['Z']))\n\
        fig = plt.figure(figsize=(10,7))\n\
        ax = fig.gca()\n\
        plt.pcolor(voltages,freqs*1e-6,20*np.log10(mags.T))\n\
        cbar=plt.colorbar(label='S21 (dB)')\n\
        cbar.ax.tick_params(labelsize=20)\n\
        ax.tick_params(labelsize=20)\n\
        ax.set_xlabel('Flux (V)',fontsize=20)\n\
        ax.set_ylabel('S21 (dB)',fontsize=20)\n\
        ax.set_title('"+name+"',fontsize=16)\n\
        plt.show()"
    
    for idx_volt,volt in enumerate(volts):
        instruments['Voltsource'].set_voltage(volt)
        for idx,freq in enumerate(freqs):
            clear_output(wait=True)
            
            instruments['RFsourceMeasurement'].set_frequency(freq-parameters['Measurement_IF'])
            sleep(0.05)
        
            I,Q = instruments['alazar'].capture(0,
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
            
            Is[idx_volt,idx] = I
            Qs[idx_volt,idx] = Q 

            
            mags = 20*np.log10(np.sqrt(Is**2+Qs**2))
        
            
            plt.pause(0.05)
            plt.pcolor(volts,freqs*1e-6,mags.T)
    
    Z = Is+Qs*1j
    np.savez(name,header=howtoplot,params = parameters, freqs=freqs,voltages=volts, Z=Z)

    clear_output(wait=True)
    plt.pcolor(volts,freqs*1e-6,mags.T)

    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def twotone_measure(instruments, parameters, freqs):
    #p1 = Envelope(length = parameters['RFExcitationLength'])
    p1 = Pulse(length = parameters['RFExcitationLength'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)
    
    mp = Pulse(length = parameters['RFMeasurementLength'],
               amplitude = 1,
               phase = 0,
               frequency = parameters['Measurement_IF'])
    
    # create pulse sequence
    s1 = PulseSequence("twotone")
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
    instruments['awg'].getError()
    ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
    sleep(0.05)
    ms.setInstrumentsMarker(instruments['awg'], channelData)
    
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
    

    if parameters['fluxState']:
        instruments['Voltsource'].turn_on()
        sleep(0.05)
        instruments['Voltsource'].ramp_voltage(parameters['fluxValue'])
    
    instruments['att'].set_attenuation(parameters['attenuation'])
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray(len(freqs))
    Qs = np.ndarray(len(freqs))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)

    name = parameters['ExperimentName'] + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ s1.name 
    
    howtoplot = "\
    #HOW TO PLOT\n\
    data = np.load('"+name+".npz')\n\
    freqs = data['freqs']\n\
    mag = np.abs(data['Z'])\n\
    phase = np.unwrap(np.angle(data['Z']))\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.plot(freqs*1e-6,20*np.log10(mag))\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Excitation Frequency (MHz)',fontsize=20)\n\
    ax.set_ylabel('S21 (dB)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"
    
    
    for idx,freq in enumerate(freqs):
        clear_output(wait=True)
        
        #instruments['RFsourceExcitation'].set_frequency(freq-parameters['Excitation_IF'])
        instruments['RFsourceExcitation'].set_frequency(freq)
        sleep(0.1)
    
        I,Q = instruments['alazar'].capture(0,
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

    Z = Is+Qs*1j

    np.savez(name,header=howtoplot,params=parameters,freqs=freqs,Z=Z)

    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def rabi_measure(instruments, parameters, pulse_durations):
    #p1 = Pulse(length = pulse_durations[0],
    #           amplitude = 1,
    #           frequency = parameters['ExcitationFrequency'],
    #           phase = 0)#,
    #           #envelope='gaussian'
    p1 = Envelope(length = pulse_durations[0])
    
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
    #instruments['RFsourceExcitation'].set_frequency(parameters['ExcitationFrequency']-parameters['Excitation_IF'])
    instruments['RFsourceExcitation'].set_frequency(parameters['ExcitationFrequency'])
    
    instruments['RFsourceMeasurement'].start_rf()
    instruments['RFsourceExcitation'].start_rf()
    
    
    
    instruments['att'].set_attenuation(parameters['attenuation'])
    
    samplingRate = 1e9/parameters['decimationValue']
    pointsPerRecord = int(parameters['RFMeasurementLength']*samplingRate/256)*256
    
    Is = np.ndarray(len(pulse_durations))
    Qs = np.ndarray(len(pulse_durations))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,duration in enumerate(pulse_durations):
        clear_output(wait=True)

        p1.length = duration
        ms.updateChannelData(channelData,s1,'q1')
        ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
        sleep(0.1)
        ms.setInstrumentsMarker(instruments['awg'], channelData)
        sleep(0.1)
    
        I,Q = instruments['alazar'].capture(0,
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
        plt.plot(pulse_durations,mags)
        
    clear_output(wait=True)
    plt.plot(pulse_durations,mags)
    
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
    
    Is = np.ndarray(len(delays))
    Qs = np.ndarray(len(delays))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,delay in enumerate(delays):
        clear_output(wait=True)

        s1.list_of_delays[0] = delay
        ms.updateChannelData(channelData,s1,'q1')
        ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
        sleep(0.05)
        ms.setInstrumentsMarker(instruments['awg'], channelData)
    
        I,Q = instruments['alazar'].capture(0,
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
        plt.plot(delays,mags)
        
    clear_output(wait=True)
    plt.plot(delays,mags)
    
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
    
    Is = np.ndarray(len(delays))
    Qs = np.ndarray(len(delays))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,delay in enumerate(delays):
        clear_output(wait=True)

        s1.list_of_delays[0] = delay # update the delay between pulse 1 and pulse 2
        ms.updateChannelData(channelData,s1,'q1')
        ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
        sleep(0.05)
        ms.setInstrumentsMarker(instruments['awg'], channelData)
    
        I,Q = instruments['alazar'].capture(0,
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
        plt.plot(delays,mags)
        
    clear_output(wait=True)
    plt.plot(delays,mags)
    
    instruments['Voltsource'].turn_off()
    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()

def echo_measure(instruments, parameters, delays):
    p1 = Pulse(length = parameters['HalfPiPulse'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)

    p2 = Pulse(length = parameters['PiPulse'],
               amplitude = 1,
               frequency = parameters['ExcitationFrequency'],
               phase = 0)

    p3 = Pulse(length = parameters['HalfPiPulse'],
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
    s1.add(p2,'q1',delays[0]) # add pulse p1 to channel 'q1', put a delay after pulse p1
    s1.add(p3,'q1',parameters['RFExcitationDelay']) # add pulse p1 to channel 'q1', put a delay after pulse p1
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
    
    Is = np.ndarray(len(delays))
    Qs = np.ndarray(len(delays))
    
    Is[:] = 10**(parameters['backgroundPlotValue']/20)
    Qs[:] = 10**(parameters['backgroundPlotValue']/20)
    
    
    for idx,delay in enumerate(delays):
        clear_output(wait=True)

        s1.list_of_delays[0] = delay # update the delay between pulse 1 and pulse 2
        s1.list_of_delays[1] = delay # update the delay between pulse 2 and pulse 3
        ms.updateChannelData(channelData,s1,'q1')
        ms.loadChannelDataToAwg(instruments['awg'],channelData,'q1')
        sleep(0.05)
        ms.setInstrumentsMarker(instruments['awg'], channelData)
    
        I,Q = instruments['alazar'].capture(0,
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
        plt.plot(delays,mags)
        
    clear_output(wait=True)
    plt.plot(delays,mags)
    
    instruments['Voltsource'].turn_off()
    instruments['awg'].stop()
    instruments['RFsourceMeasurement'].stop_rf()
    instruments['RFsourceExcitation'].stop_rf()
