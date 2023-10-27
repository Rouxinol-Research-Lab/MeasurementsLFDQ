from instruments.ATS9872_driver import * # alazar
from instruments.DG645_driver import * # delay generator
from instruments.M8195A_driver import * # awg
from instruments.E8257D_driver import * #RF source
from instruments.Agilent11713C_driver import * # attenuator
from instruments.SIM928_driver import * # Voltage source
from IPython.display import clear_output
from time import sleep,strftime,localtime
import numpy as np
import pylab as plt
from toml import load
import sys
from IPython.display import clear_output
from pyvisa.errors import VisaIOError

from instruments.pulse_generator import *
def loadparams(filename):

    parameters = load(filename)

    alazar = ATS9872_driver()
    awg = M8195A_driver(parameters['awg_address'])
    dg = DG645_driver(parameters['delay_generator_address'])
    att = Agilent11713C_driver(parameters['att_address'])
    RFsource = E8257D_driver(parameters['RFsource_address'])

    port = parameters['Voltage_Source_port']
    current_step_time =  parameters['current_step_time']
    Voltsource = SIM928_driver(parameters['Voltage_Source_address'],port,step_time=current_step_time)

    voltageSourceState = parameters['voltage_source_state']

    if_freq = parameters('if_frequency')
    qubitname = parameters['qubitname']

    center_freq = parameters['center_frequency']
    span_freq = parameters['span_frequency']
    step_freq = parameters['step_frequency']

    rf_amp = parameters['RFSource_amplitude']
    attenuator_att = parameters['attenuator_attenuation']

    voltage = parameters['Voltage_Source_voltage']


    return alazar,awg, dg,att,RFsource,Voltsource,voltage,rf_amp,attenuator_att, center_freq,span_freq,step_freq,if_freq, qubitname,voltageSourceState


def measure(alazar,
            awg,
            dg,
            att,
            RFsourceMeasurement,
            RFsourceExcitation,
            Voltsource,
            freqMeasurement,
            rabi_map_qfreq_init,
            rabi_map_qfreq_final,
            rabi_map_qfreq_step,
            voltage,
            rf_excitation_amp,
            rf_measurement_amp,
            attenuator_att,
            pulseExcitationLength_init,
            pulseExcitationLength_final,
            pulseExcitationLength_step,
            if_freq,
            qubitname,
            voltageSourceState,
            nBuffer,
            recordPerBuffers,
            waveformHeadCut,
            pulsesPeriod,
            pulseMeasurementLength,
            delayBetweenPulses,
            ampReference,
            decimation_value,
            excitationPulseIFAmp,
            currentResistance):
    '''
     2 -> A 3 -> B
     4 -> C 5 -> D
    
      pulsesPeriod
     |------------------------------------------------------------------------------|
      _________________         _____                                                _________________         _____ 
     |                 |       |     |                                              |                 |       |     |
     |                 |       |     |                                              |                 |       |     |
     |                 |_______|     |______________________________________________|                 |_______|     |_____ ...
    
     |-----------------|       |-----|
     A                 B       C     D
     excitation                 measurement

     |-------------------------|
     A                         C
      delay
       
    '''
    
    typename = "rabi_map"

    samplingRate = 1e9/decimation_value

    awg.stop()

    awg.setRefInClockFrequency(10e6)
    awg.setRefInClockExternal()
    awg.setDualWithMarker()
    awg.setMemoryDivision(2)
    awg.setChannelMemoryToExtended(2)


    pointsPerRecord = int(pulseMeasurementLength*samplingRate/256)*256

    RFsourceMeasurement.stop_rf()
    RFsourceMeasurement.start_pulse()
    RFsourceMeasurement.start_mod()
    RFsourceMeasurement.set_pulse_trigger_external()

    awg.stop()

    Voltsource.ramp_voltage(0)
    Voltsource.turn_off()

    timeDurationExcitations = np.arange(pulseExcitationLength_init,pulseExcitationLength_final,pulseExcitationLength_step)
    qubit_freqs = np.arange(rabi_map_qfreq_init,rabi_map_qfreq_final, rabi_map_qfreq_step)


    Is = np.ndarray((len(qubit_freqs),len(timeDurationExcitations)))
    Qs = np.ndarray((len(qubit_freqs),len(timeDurationExcitations)))
    Is[:] = 10**(-45/20)
    Qs[:] = 10**(-45/20)


    name = qubitname + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ typename + "_cfreq_"+str(int(freqMeasurement*1e-6))


    howtoplot = "\
    #freqMeasurement: " + str(freqMeasurement)+ "\n\
    #rabi_map_qfreq_init: " + str(rabi_map_qfreq_init)+ "\n\
    #rabi_map_qfreq_final: " + str(rabi_map_qfreq_final)+ "\n\
    #rabi_map_qfreq_step: " + str(rabi_map_qfreq_step)+ "\n\
    #voltage: " + str(voltage)+ "\n\
    #rf_excitation_amp: " + str(rf_excitation_amp)+ "\n\
    #rf_measurement_amp: " + str(rf_measurement_amp)+ "\n\
    #attenuator_att: " + str(attenuator_att)+ "\n\
    #pulseExcitationLength_init: " + str(pulseExcitationLength_init)+ "\n\
    #pulseExcitationLength_final: " + str(pulseExcitationLength_final)+ "\n\
    #pulseExcitationLength_step: " + str(pulseExcitationLength_step)+ "\n\
    #if_freq: " + str(if_freq)+ "\n\
    #qubitname: " + str(qubitname)+ "\n\
    #voltageSourceState,: " + str(voltageSourceState)+ "\n\
    #nBuffer: " + str(nBuffer)+ "\n\
    #recordPerBuffers: " + str(recordPerBuffers)+ "\n\
    #waveformHeadCut: " + str(waveformHeadCut)+ "\n\
    #pulsesPeriod: " + str(pulsesPeriod)+ "\n\
    #pulseMeasurementLength: " + str(pulseMeasurementLength)+ "\n\
    #delayBetweenPulses: " + str(delayBetweenPulses)+ "\n\
    #ampReference: " + str(ampReference)+ "\n\
    #decimation_value: " + str(decimation_value)+ "\n\
    #currentResistance: " + str(currentResistance)+ "\n\
    #HOW TO PLOT\n\
    data = np.load(filename)\n\
    duration = data['duration']\n\
    qfreq = data['qubit_freqs']\n\
    mag = np.abs(data['Z'])\n\
    phase = np.unwrap(np.angle(data['Z']))\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.pcolor(qfreq*1e-6,duration*1e6,20*np.log10(mag.T))\n\
    cbar=plt.colorbar()\n\
    cbar.ax.tick_params(labelsize=20)\n\
    cbar.ax.set_ylabel('S21 (dB)',fontsize=20)\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Frequency (MHz)',fontsize=20)\n\
    ax.set_ylabel('duration (µs)',fontsize=20)\n\
    ax.set_title(filename,fontsize=16)\n\
    plt.show()"

    att.set_attenuation(attenuator_att)
   


    fig = plt.figure()
    ax = fig.gca()

   


    if voltageSourceState:
        Voltsource.turn_on()
        sleep(0.05)
        Voltsource.ramp_voltage(voltage)

    # TODO I have to fix this for 2 channels
    numberOfChannels = 1
    periodPerPacket,awgRate,sampleSizePacket = findAwgRateAndPeriod(if_freq,numberOfChannels)
    awgRate = awgRate/2
    awg.set_sampleRate(awgRate*2)

    sampleSizeMeasurement = int(awgRate*pulsesPeriod/512)*512

    print('Memory allocation')
    SCPI_sock_send(awg._session,":TRAC1:DEL:ALL")
    SCPI_sock_send(awg._session,":TRAC2:DEL:ALL")
    SCPI_sock_send(awg._session,":TRAC1:DEF 1,{},0".format(sampleSizeMeasurement))
    sleep(1)
    awg.getError()



    awg.setVoltage(1,0.6)
    awg.setVoltage(2,excitationPulseIFAmp)
    awg.setVoltage(3,1)
    awg.setVoltage(4,1)

    awg.setVoltageOffset(3,0.5)
    awg.setVoltageOffset(4,0.5)

    awg.openChanneloutput(1)
    awg.openChanneloutput(2)
    awg.openChanneloutput(3)
    awg.openChanneloutput(4)

    RFsourceMeasurement.set_amplitude(rf_measurement_amp)
    RFsourceMeasurement.set_frequency(freqMeasurement-if_freq)
    RFsourceMeasurement.start_rf()
    RFsourceMeasurement.setPulsePolarityInverted()


    # A first long pulse to see if it works
    _,pulseMeasurement,pulsesExcitation,markers = prepareSignalData(pulseMeasurementLength,[1e-6],[delayBetweenPulses],[0],if_freq,qubit_freqs[0],awgRate)
    pulseMeasurement = addPadding(pulseMeasurement)
    pulsesExcitation = addPadding(pulsesExcitation)
    markers = addPadding(markers)

    
    withmarker = np.array(tuple(zip(pulseMeasurement,markers))).flatten()
    awg.downloadDataToAwg(withmarker, 1,0)
    sleep(1)
    awg.downloadDataToAwg(pulsesExcitation, 2,0)
    sleep(1)


    awg.start()
    sleep(0.05)
    I,Q = alazar.capture(0,pointsPerRecord,nBuffer,recordPerBuffers,ampReference,save=False,waveformHeadCut=waveformHeadCut, decimation_value = decimation_value, triggerLevel_volts=0.7, triggerRange_volts=1,TTL=True)



    try:

        for idx_qfreq, qfreq in enumerate(qubit_freqs):
         
            Z = Is+Qs*1j

            np.savez(name,header=howtoplot,qubit_freqs=qubit_freqs,duration=timeDurationExcitations,Z=Z)



            sleep(0.05)
            for idx, duration in enumerate(timeDurationExcitations):
                clear_output(wait=True) 

                awg.stop()

                
                _,pulseMeasurement,pulsesExcitation,markers = prepareSignalData(pulseMeasurementLength,[duration],[delayBetweenPulses],[0],if_freq,qfreq,awgRate)
                pulseMeasurement = addPadding(pulseMeasurement)
                pulsesExcitation = addPadding(pulsesExcitation)
                markers = addPadding(markers)

                
        
                withmarker = np.array(tuple(zip(pulseMeasurement,markers))).flatten()
                awg.downloadDataToAwg(withmarker, 1,0)
                sleep(1)
                awg.downloadDataToAwg(pulsesExcitation, 2,0)
                sleep(1)
    

                awg.start()

                I,Q = alazar.capture(0,pointsPerRecord,nBuffer,recordPerBuffers,ampReference,save=False,waveformHeadCut=waveformHeadCut, decimation_value = decimation_value, triggerLevel_volts=0.7, triggerRange_volts=1,TTL=True)
                Is[idx_qfreq,idx] = I
                Qs[idx_qfreq,idx] = Q 
                
                mags = 20*np.log10(np.sqrt(Is**2+Qs**2))

                
                plt.pause(0.05)
                plt.pcolor(qubit_freqs,timeDurationExcitations,mags.T)

                # line.set_ydata(mags)
                # ax.set_ylim(np.min(mags)-1,np.max(mags)+1)
                
                # fig.canvas.draw()
                # fig.canvas.flush_events()


        awg.closeChanneloutput(1)
        awg.closeChanneloutput(2)
        awg.closeChanneloutput(3)
        awg.closeChanneloutput(4)
        RFsourceMeasurement.stop_rf()
        awg.stop()

        if voltageSourceState:
            Voltsource.ramp_voltage(0)
            Voltsource.turn_off()


        
        clear_output(wait=True)
        plt.pause(0.05)
        plt.show()

    except KeyboardInterrupt:
        pass
    except VisaIOError:
        pass
    except RuntimeError:
        pass

    Z = Is+Qs*1j

    np.savez(name,header=howtoplot,qubit_freqs=qubit_freqs,duration=timeDurationExcitations,Z=Z)

    filename = name+'.npz'
    return filename

# TODO fix ylabel
def plot(filename):
    data = np.load(filename)
    #type = data['type']
    duration = data['duration']
    qfreq = data['qubit_freqs']
    mag = np.abs(data['Z'])
    phase = np.unwrap(np.angle(data['Z']))
    fig = plt.figure(figsize=(10,7))
    ax = fig.gca()
    plt.pcolor(qfreq*1e-6,duration*1e6,20*np.log10(mag.T))
    cbar=plt.colorbar()
    cbar.ax.tick_params(labelsize=20)
    cbar.ax.set_ylabel('S21 (dB)',fontsize=20)
    ax.tick_params(labelsize=20)
    ax.set_xlabel('Frequency (MHz)',fontsize=20)
    ax.set_ylabel('duration (µs)',fontsize=20)
    ax.set_title(filename,fontsize=16)
    plt.show()

def main():
    args = sys.argv

    command = args[1]
    filename = args[2]

    if command == "measure":
        alazar,awg, dg,att,RFsource,Voltsource,voltage,rf_amp,attenuator_att, center_freq,span_freq,step_freq,if_freq, qubitname,voltageSourceState = loadparams(filename)

        name = measure(alazar,awg, dg,att,RFsource,Voltsource,voltage,rf_amp,attenuator_att, center_freq,span_freq,step_freq,if_freq, qubitname,voltageSourceState)
        
        print(name)
    elif command == "plot":
        plot(filename)

if __name__ == "__main__":
    main()

