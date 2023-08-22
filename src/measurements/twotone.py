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
import datetime

#TODO set amplitude of na

def loadparams(filename):

    parameters = load(filename)


    na = E5063A_driver(parameters['na_address'])
    att = Agilent11713C_driver(parameters['att_address'])
    RFsource = E8257D_driver(parameters['RFsource_address'])

    port = parameters['Voltage_Source_port']
    current_step_time =  parameters['current_step_time']
    Voltsource = SIM928_driver(parameters['Voltage_Source_address'],port,step_time=current_step_time)


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

    qfreq_init = parameters['RFSource_frequency_initial']
    qfreq_final = parameters['RFSource_frequency_final']
    qfreq_step = parameters['RFSource_frequency_step']

    return na, att,RFsource,Voltsource,voltage,rf_amp,attenuator_att,na_amp,ave_time, center_freq,span_freq, naverages, npoints, if_freq, qfreq_init, qfreq_final, qfreq_step,qubitname

def measure(na, att,RFsource,Voltsource,voltage,rf_amp,attenuator_att,na_amp,ave_time, center_freq,span_freq, naverages, npoints, if_freq, qfreq_init, qfreq_final, qfreq_step,qubitname):
    typename = "twotone"
    na.average_points = naverages
    na.averaging = 1
    na.power = 0

    na.center_frequency = center_freq
    na.span_frequency = span_freq

    na.sweep_points = npoints
    na.if_bandwidth_frequency = if_freq
    na.data_array_format = 'PLOG'
    na.parameter = 'S21'

    qubitfreqs = np.arange(qfreq_init, qfreq_final, qfreq_step)

    name = qubitname + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ typename + "_from_" + str(int(qfreq_init*1e-6)) + "_to_" + str(int(qfreq_final*1e-6))+"_cfreq_"+str(int(center_freq*1e-6))


    howtoplot = "\
    data = np.load('"+name+".npz')\n\
    qfreqs = data['qubit_freqs']\n\
    mags = np.abs(data['Z'])\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.pcolor(qfreqs*1e-6,20*np.log10(mags))\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_ylabel('S21 (dB)',fontsize=20)\n\
    ax.set_xlabel('Frequency (MHz)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"


    att.set_attenuation(attenuator_att)
    RFsource.set_amplitude(rf_amp)

    mags = np.ndarray(len(qubitfreqs))
    phases = np.ndarray(len(qubitfreqs))

    mags[:] = -50
    phases[:] = 0

    fig = plt.figure()
    ax = fig.gca()

    line, = ax.plot(qubitfreqs,mags)

    Voltsource.ramp_voltage(0)
    sleep(0.05)
    Voltsource.turn_on()
    sleep(0.05)
    RFsource.start_rf()
    sleep(0.05)
    na.power = 1
    sleep(0.05)

    Voltsource.ramp_voltage(voltage)

    try:
        for idx,qfreq in enumerate(qubitfreqs):
            clear_output(wait=True)
            
            RFsource.set_frequency(qfreq)
            na.clear_averaging()
            sleep(ave_time)

            data = np.array(na.data_array().split(',')).astype(float)
            mags[idx] = data[::2][1]
            phases[idx] =  data[1::2][1]


            line.set_ydata(mags)
            ax.set_ylim(np.min(mags)-1,np.max(mags)+1)
        
            plt.pause(0.05)

            fig.canvas.draw()
            fig.canvas.flush_events()
            

        na.power = 0
        sleep(0.05)
        RFsource.stop_rf()
        sleep(0.05)

        Voltsource.ramp_voltage(0)
        Voltsource.turn_off()


        Z = 10**(mags/20)*np.exp(1j*phases*np.pi/180)

        np.savez(name,header=howtoplot,qubit_freqs=qubitfreqs,Z=Z)
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
    qfreqs = data['qubit_freqs']
    mags = np.abs(data['Z'])
    fig = plt.figure(figsize=(10,7))
    ax = fig.gca()
    plt.plot(qfreqs*1e-6,20*np.log10(mags))
    ax.tick_params(labelsize=20)
    ax.set_ylabel('S21 (dB)',fontsize=20)
    ax.set_xlabel('Frequency (MHz)',fontsize=20)
    ax.set_title(filename,fontsize=16)
    plt.show()

def main():
    args = sys.argv

    command = args[1]
    filename = args[2]

    if command == "measure":
        na, att,RFsource,Voltsource,voltage,rf_amp,attenuator_att,na_amp,ave_time, center_freq,span_freq, naverages, npoints, if_freq, qfreq_init, qfreq_final, qfreq_step,qubitname = loadparams(filename)

        name = measure( na, att,RFsource,Voltsource,voltage,rf_amp,attenuator_att,na_amp,ave_time, center_freq,span_freq, naverages, npoints, if_freq, qfreq_init, qfreq_final, qfreq_step,qubitname)
        
        print(name)

    if command == 'time':
        _, _,_,_,_,_,_,_,ave_time, _,_, _, _, _, qfreq_init, qfreq_final, qfreq_step,_ = loadparams(filename)

        time= len(np.arange(qfreq_init,qfreq_final,qfreq_step))*ave_time

        timedelta_obj = datetime.timedelta(seconds=time)
        print("Time of measurement: ",timedelta_obj)
        
        
    elif command == "plot":
        plot(filename)

if __name__ == "__main__":
    main()

