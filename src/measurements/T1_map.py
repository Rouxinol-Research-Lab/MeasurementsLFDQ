from site import addusersitepackages
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
from scipy.optimize import curve_fit

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
            freqExcitation,
            durationExcitation_init,
            durationExcitation_final,
            durationExcitation_step,
            voltage,
            rf_excitation_amp,
            rf_measurement_amp,
            attenuator_att,
            if_freq,
            qubitname,
            voltageSourceState,
            excitationState,
            nBuffer,
            recordPerBuffers,
            waveformHeadCut,
            pulsesPeriod,
            pulseMeasurementLength,
            delayBetweenPulses_init,
            delayBetweenPulses_final,
            delayBetweenPulses_step,
            ampReference,
            decimation_value):
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
    
    typename = "T1_map"

    samplingRate = 1e9/decimation_value

    dg.setLevelAmplitude(1,3) # Set AB to 3 Volts
    dg.setLevelAmplitude(2,3) # Set CD to 3 Volts
    dg.setTriggerSource(5) # Set trigger to be controlled by me
    dg.setBurstCount(int(nBuffer*recordPerBuffers)) # set number of shots
    
    dg.setBurstMode(1)  


    
    dg.setDelay(5,4,pulseMeasurementLength) # D in relation to C
    
    

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


    Voltsource.ramp_voltage(0)
    Voltsource.turn_off()

    awg.setCWFrequency(if_freq)


    delays = np.arange(delayBetweenPulses_init, delayBetweenPulses_final, delayBetweenPulses_step,)
    durationExcitations = np.arange(durationExcitation_init, durationExcitation_final, durationExcitation_step)
    
    Is = np.ndarray((len(durationExcitations),len(delays)))
    Qs = np.ndarray((len(durationExcitations),len(delays)))

    Is[:] = 10**(-51/20)
    Qs[:] = 10**(-51/20)



    name = qubitname + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ typename + "_cfreq_"+str(int(freqMeasurement*1e-6))


    howtoplot = "\
    #freqMeasurement:" + str(freqMeasurement)+ "\n\
    #freqExcitation:" + str(freqExcitation)+ "\n\
    #durationExcitation_init:" + str(durationExcitation_init)+ "\n\
    #durationExcitation_final:" + str(durationExcitation_final)+ "\n\
    #durationExcitation_step:" + str(durationExcitation_step)+ "\n\
    #voltage:" + str(voltage)+ "\n\
    #rf_excitation_amp:" + str(rf_excitation_amp)+ "\n\
    #rf_measurement_amp:" + str(rf_measurement_amp)+ "\n\
    #attenuator_att:" + str(attenuator_att)+ "\n\
    #if_freq:" + str(if_freq)+ "\n\
    #qubitname:" + str(qubitname)+ "\n\
    #voltageSourceState:" + str(voltageSourceState)+ "\n\
    #excitationState:" + str(excitationState)+ "\n\
    #nBuffer:" + str(nBuffer)+ "\n\
    #recordPerBuffers:" + str(recordPerBuffers)+ "\n\
    #waveformHeadCut:" + str(waveformHeadCut)+ "\n\
    #pulsesPeriod:" + str(pulsesPeriod)+ "\n\
    #pulseMeasurementLength:" + str(pulseMeasurementLength)+ "\n\
    #delayBetweenPulses_init:" + str(delayBetweenPulses_init)+ "\n\
    #delayBetweenPulses_final:" + str(delayBetweenPulses_final)+ "\n\
    #delayBetweenPulses_step:" + str(delayBetweenPulses_step)+ "\n\
    #ampReference:" + str(ampReference)+ "\n\
    #decimation_value:" + str(decimation_value)+ "\n\
    #HOW TO PLOT\n\
    data = np.load('"+name+".npz')\n\
    delays = data['delays']\n\
    durationExcitations = data['durationExcitations']\n\
    mag = np.abs(data['Z'])\n\
    phase = np.unwrap(np.angle(data['Z']))\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.pcolor(durationExcitations*1e6,delays*1e6,20*np.log10(mags.T))\n\
    cbar=plt.colorbar()\n\
    cbar.ax.tick_params(labelsize=20)\n\
    cbar.ax.set_ylabel('S21 (dB)',fontsize=20)\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Excitation Length (µs)',fontsize=20)\n\
    ax.set_ylabel('Delay (µs)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"

    att.set_attenuation(attenuator_att)
   


    fig = plt.figure()
    ax = fig.gca()



    if voltageSourceState:
        Voltsource.turn_on()
        sleep(0.05)
        Voltsource.ramp_voltage(voltage)

    RFsourceMeasurement.set_amplitude(rf_measurement_amp)
    RFsourceMeasurement.set_frequency(freqMeasurement-if_freq)
    RFsourceMeasurement.start_rf()

    RFsourceExcitation.set_amplitude(rf_excitation_amp)
    RFsourceExcitation.set_frequency(freqExcitation)
    if excitationState:
        RFsourceExcitation.start_rf()

    awg.start()
    sleep(0.05)

    dg.setBurstPeriod(pulsesPeriod+delays[0]) # set period between shots
    dg.setDelay(4,3,delays[0]) # C in relation to B
    I,Q = alazar.capture(0,pointsPerRecord,nBuffer,recordPerBuffers,ampReference,save=False,waveformHeadCut=waveformHeadCut, decimation_value = decimation_value)

    try:
        
        for idx_ext, durExcitation in enumerate(durationExcitations):
            dg.setDelay(3,2,durExcitation) # B in relation to A
            sleep(0.05)
            
            Z = Is+Qs*1j

            np.savez(name,header=howtoplot,durationExcitations=durationExcitations,delays=delays,Z=Z)
            
            for idx, delayBetweenPulses in enumerate(delays):
                clear_output(wait=True)

                dg.setBurstPeriod(pulsesPeriod+delayBetweenPulses) # set period between shots
                dg.setDelay(4,3,delayBetweenPulses) # C in relation to B

                sleep(0.05)
                I,Q = alazar.capture(0,pointsPerRecord,nBuffer,recordPerBuffers,ampReference,save=False,waveformHeadCut=waveformHeadCut, decimation_value = decimation_value)
                Is[idx_ext,idx] = I
                Qs[idx_ext,idx] = Q 
            
                mags = 20*np.log10(np.sqrt(Is**2+Qs**2))

            
                plt.pause(0.05)
                plt.pcolor(durationExcitations*1e6,delays*1e6,mags.T)

                # line.set_ydata(mags)
                # ax.set_ylim(np.min(mags)-1,np.max(mags)+1)
            
                # fig.canvas.draw()
                # fig.canvas.flush_events()


        RFsourceExcitation.stop_rf()
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

    filename = name+'.npz'
    return filename

def plot(filename):
    data = np.load(filename)
    delays = data['delays']
    durationExcitations = data['durationExcitations']
    mag = np.abs(data['Z'])
    phase = np.unwrap(np.angle(data['Z']))
    fig = plt.figure(figsize=(10,7))
    ax = fig.gca()
    plt.pcolor(durationExcitations*1e6,delays*1e6,20*np.log10(mag.T))
    cbar=plt.colorbar()
    cbar.ax.tick_params(labelsize=20)
    cbar.ax.set_ylabel('S21 (dB)',fontsize=20)
    ax.tick_params(labelsize=20)
    ax.set_xlabel('Excitation Length (µs)',fontsize=20)
    ax.set_ylabel('Delay (µs)',fontsize=20)
    ax.set_title(filename,fontsize=16)
    plt.show()

def T1_func(time, Const, Slope, T):   
    """
    Rabi curve using exponential decay: Const + Slope*exp(-time/Tr)*cos(2*pi*time/Period+Phase)

    """
    return (Const + Slope*np.exp(-time/T))



def calculate_T1(filename, expectedT1 =10e-6):
    
    data = np.load(filename)
    delays = data['delays']
    durationExcitations = data['durationExcitations']
    mag = np.abs(data['Z'])
    


    const = (mag[0][1]-mag[0][0])/2
    slope = mag[0][1] - mag[0][0]
    
    
    T1s = np.zeros(len(durationExcitations))
    T1s_error = np.zeros(len(durationExcitations))
    
    for idx,_ in enumerate(durationExcitations):

        
        args = [const,slope,expectedT1]
        popt, pcov  = curve_fit(T1_func, delays, mag[idx], p0=args)
        
        T1s[idx] = popt
        T1s_error[idx] = np.sqrt(np.diag(pcov))


    return durationExcitations,T1s,T1s_error


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

