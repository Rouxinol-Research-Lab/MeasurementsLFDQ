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
from instruments.SCPI_socket import *


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



    
def convertToSamples(awgRate,length):
    return  int(awgRate*length/512)*512

def measure(alazar,
            awg,att,
            RFsourceMeasurement,
            RFsourceExcitation,
            Voltsource,
            freqMeasurement,
            freqExcitation,
            durationExcitation,
            voltage,
            rf_excitation_amp,
            rf_measurement_amp,
            attenuator_att,
            if_freq,
            qubitname,
            voltageSourceState,
            nBuffer,
            recordPerBuffers,
            waveformHeadCut,
            pulsesPeriod,
            pulseMeasurementLength,
            delayBetweenPulses_init,
            delayBetweenPulses_final,
            delayBetweenPulses_step,
            ampReference,
            decimation_value,
            currentResistance,
            roundDelayArray = 6,
            timeToWaitForAWGUpload = 5,
            saveData = True):
    
    typename = "ramsey"

    samplingRate = 1e9/decimation_value
    

    pointsPerRecord = int(pulseMeasurementLength*samplingRate/256)*256

    RFsourceMeasurement.stop_rf()
    RFsourceMeasurement.start_pulse()
    RFsourceMeasurement.start_mod()
    RFsourceMeasurement.set_pulse_trigger_external()

    RFsourceExcitation.stop_rf()
    RFsourceExcitation.start_pulse()
    RFsourceExcitation.start_mod()
    RFsourceExcitation.set_pulse_trigger_external()

    awg.stop()

    awg.setRefInClockFrequency(10e6)
    awg.setRefInClockExternal()  

    awg.setSingleWithMarker()
    #awg.setDualWithMarker()
    SCPI_sock_send(awg._session, ':INST:MEM:EXT:RDIV DIV1')
    SCPI_sock_send(awg._session, ':TRAC2:MMOD EXT')
    


    Voltsource.ramp_voltage(0)
    Voltsource.turn_off()

    delays = np.round(np.arange(delayBetweenPulses_init, delayBetweenPulses_final, delayBetweenPulses_step,),roundDelayArray)

    Is = np.ndarray(len(delays))
    Qs = np.ndarray(len(delays))

    Is[:] = 10**(-45/20)
    Qs[:] = 10**(-45/20)



    name = qubitname + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ typename + "_cfreq_"+str(int(freqMeasurement*1e-6))


    howtoplot = "\
    #freqMeasurement: " + str(freqMeasurement) + "\n\
    #freqExcitation: " + str(freqExcitation) + "\n\
    #durationExcitation: " + str(durationExcitation) + "\n\
    #voltage: " + str(voltage) + "\n\
    #rf_excitation_amp: " + str(rf_excitation_amp) + "\n\
    #rf_measurement_amp: " + str(rf_measurement_amp) + "\n\
    #attenuator_att: " + str(attenuator_att) + "\n\
    #if_freq: " + str(if_freq) + "\n\
    #qubitname: " + str(qubitname) + "\n\
    #voltageSourceState: " + str(voltageSourceState) + "\n\
    #nBuffer: " + str(nBuffer) + "\n\
    #recordPerBuffers: " + str(recordPerBuffers) + "\n\
    #waveformHeadCut: " + str(waveformHeadCut) + "\n\
    #pulsesPeriod: " + str(pulsesPeriod) + "\n\
    #pulseMeasurementLength: " + str(pulseMeasurementLength) + "\n\
    #delayBetweenPulses_init: " + str(delayBetweenPulses_init) + "\n\
    #delayBetweenPulses_final: " + str(delayBetweenPulses_final) + "\n\
    #delayBetweenPulses_step: " + str(delayBetweenPulses_step) + "\n\
    #ampReference: " + str(ampReference) + "\n\
    #decimation_value: " + str(decimation_value) + "\n\
    #roundDelayArray: " + str(roundDelayArray) + "\n\
    #timeToWaitForAWGUpload : " + str(timeToWaitForAWGUpload) + "\n\
    #currentResistance: " + str(currentResistance)+ "\n\
    #HOW TO PLOT\n\
    data = np.load('"+name+".npz')\n\
    delays = data['delays']\n\
    mag = np.abs(data['Z'])\n\
    phase = np.unwrap(np.angle(data['Z']))\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.plot(delays*1e6,20*np.log10(mag))\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Delay (us)',fontsize=20)\n\
    ax.set_ylabel('S21 (dB)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"

    att.set_attenuation(attenuator_att)
   


    fig = plt.figure()
    ax = fig.gca()

    line, = ax.plot(delays,20*np.log10(np.sqrt(Is**2+Qs**2)))


    if voltageSourceState:
        Voltsource.turn_on()
        sleep(0.05)
        Voltsource.ramp_voltage(voltage)

    freq = 70e6
    periodPerPacket,awgRate,sampleSizePacket = findAwgRateAndPeriod(freq)
    awg.set_sampleRate(awgRate)

    nPackets = pulseMeasurementLength/periodPerPacket*freq
    sampleSizeMeasurementPulse = int(sampleSizePacket*nPackets/512)*512

    sampleSizeExcitation = convertToSamples(awgRate,durationExcitation)

    RFsourceMeasurement.set_amplitude(rf_measurement_amp)
    RFsourceMeasurement.set_frequency(freqMeasurement-if_freq)
    RFsourceMeasurement.start_rf()
    RFsourceMeasurement.setPulsePolarityInverted()
    

    RFsourceExcitation.set_amplitude(rf_excitation_amp)
    RFsourceExcitation.set_frequency(freqExcitation)
    RFsourceExcitation.start_rf()
    #RFsourceExcitation.setPulsePolarityInverted()
    RFsourceExcitation.setPulsePolarityNormal()



    awg.setVoltage(1,0.6)
    awg.setVoltage(3,1)
    awg.setVoltage(4,1)
    awg.setVoltageOffset(3,0.5)
    awg.setVoltageOffset(4,0.5)

    awg.openChanneloutput(1)
    awg.openChanneloutput(3)
    awg.openChanneloutput(4)

    for idx, delayBetweenPulses in enumerate(delays):
        clear_output(wait=True)

        awg.stop()
        sleep(0.05)

        sampleSizeMeasurement = convertToSamples(awgRate,pulsesPeriod+delayBetweenPulses+2*durationExcitation)
        sampleSizeDelay = convertToSamples(awgRate,delayBetweenPulses)


        awg.clearMemory()
        awg.defineSegment(sampleSizeMeasurement)

        sleep(0.05)

        awg.start()

        sleep(0.05)

        awg.setWave(freq,1, sampleSizeDelay+2*sampleSizeExcitation, sampleSizeMeasurementPulse,awgRate)
        sleep(timeToWaitForAWGUpload)

        awg.setMarker(0,2)
        awg.setMarker(sampleSizeExcitation,0)
        awg.setMarker(sampleSizeDelay+sampleSizeExcitation,2)
        awg.setMarker(sampleSizeDelay+2*sampleSizeExcitation+sampleSizeMeasurementPulse,0)

        sleep(0.05)

        I,Q = alazar.capture(0,pointsPerRecord,nBuffer,recordPerBuffers,ampReference,save=False,waveformHeadCut=waveformHeadCut, decimation_value = decimation_value, triggerLevel_volts=0.7, triggerRange_volts=1,TTL=True)

        Is[idx] = I
        Qs[idx] = Q 
        
        mags = 20*np.log10(np.sqrt(Is**2+Qs**2))

        
        plt.pause(0.05)
        plt.plot(delays*1e6,mags)


    try:

        for idx, delayBetweenPulses in enumerate(delays):
            clear_output(wait=True)

            awg.stop()
            sleep(0.05)

            sampleSizeMeasurement = convertToSamples(awgRate,pulsesPeriod+delayBetweenPulses+2*durationExcitation)
            sampleSizeDelay = convertToSamples(awgRate,delayBetweenPulses)


            awg.clearMemory()
            awg.defineSegment(sampleSizeMeasurement)

            sleep(0.05)

            awg.start()

            sleep(0.05)

            awg.setWave(freq,1, sampleSizeDelay+2*sampleSizeExcitation, sampleSizeMeasurementPulse,awgRate)
            sleep(timeToWaitForAWGUpload)

            awg.setMarker(0,2)
            awg.setMarker(sampleSizeExcitation,0)
            awg.setMarker(sampleSizeDelay+sampleSizeExcitation,2)
            awg.setMarker(sampleSizeDelay+2*sampleSizeExcitation+sampleSizeMeasurementPulse,0)

            sleep(0.05)

            I,Q = alazar.capture(0,pointsPerRecord,nBuffer,recordPerBuffers,ampReference,save=False,waveformHeadCut=waveformHeadCut, decimation_value = decimation_value, triggerLevel_volts=0.7, triggerRange_volts=1,TTL=True)

            Is[idx] = I
            Qs[idx] = Q 
            
            mags = 20*np.log10(np.sqrt(Is**2+Qs**2))

            
            plt.pause(0.05)
            plt.plot(delays*1e6,mags)

            if saveData:
                Z = Is+Qs*1j

                np.savez(name,header=howtoplot,delays=delays,Z=Z)

            # line.set_ydata(mags)
            # ax.set_ylim(np.min(mags)-1,np.max(mags)+1)
            
            # fig.canvas.draw()
            # fig.canvas.flush_events()

        awg.closeChanneloutput(1)
        awg.closeChanneloutput(3)
        awg.closeChanneloutput(4)
        
        RFsourceExcitation.stop_rf()        
        RFsourceMeasurement.stop_rf()
        RFsourceMeasurement.setPulsePolarityNormal()
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

    filename = name+'.npz'
    return filename



# TODO fix ylabel
def plot(filename):
    data = np.load(filename)
    delays = data['delays']
    mag = np.abs(data['Z'])
    phase = np.unwrap(np.angle(data['Z']))
    fig = plt.figure(figsize=(10,7))
    ax = fig.gca()
    plt.plot(delays*1e6,20*np.log10(mag))
    ax.tick_params(labelsize=20)
    ax.set_xlabel('Delay (µs)',fontsize=20)
    ax.set_ylabel('S21 (dB)',fontsize=20)
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

