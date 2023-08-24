from instruments.E8257D_driver import *
from instruments.Agilent11713C_driver import *
from instruments.E5063A_driver import *
from instruments.SIM928_driver import *

from time import sleep,strftime,localtime
import numpy as np
import pylab as plt
from toml import load
import sys
from IPython.display import clear_output
from pyvisa.errors import VisaIOError


def loadparams(filename):

    parameters = load(filename)


    na = E5063A_driver(parameters['na_address'])
    att = Agilent11713C_driver(parameters['att_address'])
    RFsource = E8257D_driver(parameters['RFsource_address'])

    port = parameters['Voltage_Source_port']
    current_step_time =  parameters['current_step_time']
    Voltsource = SIM928_driver(parameters['Voltage_Source_address'],port,step_time=current_step_time)

    voltageSourceState = parameters['voltage_source_state']
    RFSourceState = parameters['RFsource_state']
    na_measurement = parameters['vna_measurement']
    naverages = parameters['average_points']
    qubitname = parameters['qubitname']

    center_freq = parameters['center_frequency']
    span_freq = parameters['span_frequency']
    npoints = parameters['npoints']
    if_freq = parameters['if_freq']
    ave_time = parameters['average_time']

    rf_amp = parameters['RFSource_amplitude']
    attenuator_att = parameters['attenuator_attenuation']
    na_amp = parameters['na_amplitude']

    voltage = parameters['Voltage_Source_voltage']

    RFfrequency = parameters['RFSource_frequency']

    return na, att,RFsource,Voltsource,voltage,rf_amp,attenuator_att,na_amp,ave_time, center_freq,span_freq, naverages, npoints, if_freq, RFfrequency,qubitname,na_measurement,voltageSourceState,RFSourceState

def measure(na, att,RFsource,Voltsource,voltage,rf_amp,attenuator_att,na_amp,ave_time, center_freq,span_freq, naverages, npoints, if_freq, RFfrequency,qubitname,na_measurement,voltageSourceState,RFSourceState):
    typename = "vna"
    na.average_points = naverages
    na.averaging = 1
    na.power = 0
    Voltsource.ramp_voltage(0)
    Voltsource.turn_off()

    na.center_frequency = center_freq
    na.span_frequency = span_freq

    na.sweep_points = npoints
    na.if_bandwidth_frequency = if_freq
    na.data_array_format = 'PLOG'
    na.parameter = na_measurement


    name = qubitname + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ typename + "_cfreq_"+str(int(center_freq*1e-6))


    howtoplot = "\
    data = np.load('"+name+".npz')\n\
    freqs = data['freqs']\n\
    mag = np.abs(data['Z'])\n\
    phase = np.unwrap(np.angle(data['Z']))\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.plot(freqs*1e-6,20*np.log10(mag))\n\
    cbar=plt.colorbar(label='S21 (dB)')\n\
    cbar.ax.tick_params(labelsize=20)\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Frequency (MHz)',fontsize=20)\n\
    ax.set_ylabel('"+na_measurement+" (dB)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"

    att.set_attenuation(attenuator_att)
   


    fig = plt.figure()
    ax = fig.gca()


    
    na.amplitude = na_amp
    if voltageSourceState:
        Voltsource.turn_on()
        sleep(0.05)
        Voltsource.ramp_voltage(voltage)
    if RFSourceState:
        RFsource.set_amplitude(rf_amp)
        RFsource.start_rf()
        RFsource.frequency = RFfrequency
        sleep(0.05)
    
    na.power = 1
    sleep(0.05)

    freqs = np.array(na.frequency_array().split(',')).astype(float)

    try:
        na.clear_averaging()
        sleep(0.05)
        na.scale(1,5)
        na.autoscale(2)

        sleep(ave_time)
        data = np.array(na.data_array().split(',')).astype(float)
        mag = data[::2]
        phase=  data[1::2]

        plt.plot(freqs,mag)
            

        na.power = 0
        sleep(0.05)
        
        if RFSourceState:
            RFsource.stop_rf()
            sleep(0.05)

        if voltageSourceState:
            Voltsource.ramp_voltage(0)
            Voltsource.turn_off()


        Z = 10**(mag/20)*np.exp(1j*phase*np.pi/180)

        np.savez(name,header=howtoplot,freqs=freqs,Z=Z,type=na_measurement)
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
        na, att,RFsource,Voltsource,voltage,rf_amp,attenuator_att,na_amp,ave_time, center_freq,span_freq, naverages, npoints, if_freq, RFfrequency,qubitname,na_measurement,voltageSourceState,RFSourceState = loadparams(filename)

        name = measure(na, att,RFsource,Voltsource,voltage,rf_amp,attenuator_att,na_amp,ave_time, center_freq,span_freq, naverages, npoints, if_freq, RFfrequency,qubitname,na_measurement,voltageSourceState,RFSourceState)
        
        print(name)
    elif command == "plot":
        plot(filename)

if __name__ == "__main__":
    main()

