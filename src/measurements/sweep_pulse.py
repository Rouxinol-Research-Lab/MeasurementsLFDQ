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

def measure(alazar,awg, dg,att,RFsource,Voltsource,voltage,rf_amp,attenuator_att, center_freq,span_freq,step_freq, if_freq, qubitname,voltageSourceState):
    typename = "sweep_pulse"


    dg.setLevelAmplitude(1,3) # Set AB to 3 Volts
    dg.setTriggerSource(5) # Set trigger to be controlled by me
    dg.setBurstCount(5000) # set 5000 shots
    dg.setBurstPeriod(104e-6) # set period between shots
    dg.setBurstMode(1)
    dg.setDelay(3,2,100e-6)

    RFsource.stop_rf()
    RFsource.start_pulse()
    RFsource.start_mod()
    RFsource.set_pulse_trigger_external()

    awg.stop()


    Voltsource.ramp_voltage(0)
    Voltsource.turn_off()

    awg.setCWFrequency(if_freq)


    freqs = np.arange(center_freq-span_freq/2,center_freq+span_freq/2,step_freq)

    Is = np.ndarray(len(freqs))
    Qs = np.ndarray(len(freqs))

    Is[:] = 1
    Qs[:] = 1



    name = qubitname + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ typename + "_cfreq_"+str(int(center_freq*1e-6))


    howtoplot = "\
    data = np.load('"+name+".npz')\n\
    freqs = data['freqs']\n\
    mag = np.abs(data['Z'])\n\
    phase = np.unwrap(np.angle(data['Z']))\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.plot(freqs*1e-6,20*np.log10(mag))\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Frequency (MHz)',fontsize=20)\n\
    ax.set_ylabel('S21 (dB)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"

    att.set_attenuation(attenuator_att)
   


    fig = plt.figure()
    ax = fig.gca()

    line, = ax.plot(freqs,20*np.log10(np.sqrt(Is**2+Qs**2)))


    if voltageSourceState:
        Voltsource.turn_on()
        sleep(0.05)
        Voltsource.ramp_voltage(voltage)

    
    RFsource.set_amplitude(rf_amp)
    RFsource.start_rf()
    awg.start()
    sleep(0.05)


    try:

        for idx, freq in enumerate(freqs):
            clear_output(wait=True)
            RFsource.set_frequency(freq-if_freq)
            sleep(0.05)
            I,Q = alazar.capture(0,5120,200,25,-8.512,save=False)
            Is[idx] = I
            Qs[idx] = Q
            
            mags = 20*np.log10(np.sqrt(Is**2+Qs**2))

            
            
            plt.pause(0.05)
            plt.plot(freqs,mags)

            # line.set_ydata(mags)
            # ax.set_ylim(np.min(mags)-1,np.max(mags)+1)
            
            # fig.canvas.draw()
            # fig.canvas.flush_events()


        RFsource.stop_rf()
        awg.stop()

        if voltageSourceState:
            Voltsource.ramp_voltage(0)
            Voltsource.turn_off()


        Z = Is+Qs*1j

        np.savez(name,header=howtoplot,freqs=freqs,Z=Z)
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
    type = data['type']
    freqs = data['freqs']
    mag = np.abs(data['Z'])
    phase = np.unwrap(np.angle(data['Z']))
    fig = plt.figure(figsize=(10,7))
    ax = fig.gca()
    plt.plot(freqs*1e-6,20*np.log10(mag))
    ax.tick_params(labelsize=20)
    ax.set_xlabel('Frequency (MHz)',fontsize=20)
    #ax.set_ylabel(str(type)+' (dB)',fontsize=20)
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

