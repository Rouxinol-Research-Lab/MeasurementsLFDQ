from instruments.SIM928_driver import *
from instruments.E5063A_driver import *
from instruments.Agilent11713C_driver import *
from time import sleep,strftime,localtime
import numpy as np
import pylab as plt
from toml import load
import sys
from IPython.display import clear_output
from pyvisa.errors import VisaIOError
import datetime

def loadparams(filename):

    parameters = load(filename)


    na = E5063A_driver(parameters['na_address'])
    att = Agilent11713C_driver(parameters['att_address'])

    port = parameters['source_port']

    current_step_time = parameters['current_step_time']

    source = SIM928_driver(parameters['source_address'],port, step_time=current_step_time)

    attenuation = parameters['attenuation'] 
    ave_points = parameters['average_points']
    qubitname = parameters['qubitname']

    center_frequency = parameters['center_frequency']
    span_frequency = parameters['span_frequency']
    npoints = parameters['npoints']
    if_freq = parameters['if_freq']
    average_time = parameters['average_time']

    

    volt_initial = parameters['volt_initial']
    volt_final = parameters['volt_final']
    volt_step = parameters['volt_step']

    return na,att,source,qubitname,center_frequency,span_frequency,npoints,if_freq,average_time,volt_initial,volt_final,volt_step,ave_points,attenuation


def plot(filename):
    data = np.load(filename)
    volts = data['volts']
    freqs = data['freqs']
    mags = np.abs(data['Z'])
    fig = plt.figure(figsize=(10,7))
    ax = fig.gca()
    plt.pcolor(volts*1e3,freqs*1e-6,20*np.log10(mags.T))
    cbar=plt.colorbar(label='S21 (dB)')
    cbar.ax.tick_params(labelsize=20)
    ax.tick_params(labelsize=20)
    ax.set_xlabel('Flux (mV)',fontsize=20)
    ax.set_ylabel('Frequency (MHz)',fontsize=20)
    ax.set_title(filename,fontsize=16)
    plt.show()

def measure(qubitname,
                na,
                att,
                source,
                center_freq,
                span_freq,
                if_freq,
                npoints,
                naverages,
                volt_init,
                volt_final,
                volt_step,
                ave_time,
                attenuation_val):

    typename = "fluxsweep"
    na.average_points = naverages
    na.averaging = 1
    na.power = 0
    source.ramp_voltage(0)
    source.turn_off()

    na.center_frequency = center_freq
    na.span_frequency = span_freq

    na.sweep_points = npoints
    na.if_bandwidth_frequency = if_freq
    na.data_array_format = 'PLOG'

    volts = np.arange(volt_init, volt_final, volt_step)

    name = qubitname+ "_"  + str(strftime("%Y%m%d_%H%M",localtime()))  + "_" + typename + "_from_" + str(volt_init) + "_to_" + str(volt_final)+"_cfreq_"+str(int(center_freq*1e-6))


    howtoplot = "\
    data = np.load('"+name+".npz')\n\
    volts = data['volts']\n\
    freqs = data['freqs']\n\
    mags = np.abs(data['Z'])\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.pcolor(volts*1e3,freqs*1e-6,20*np.log10(mags.T))\n\
    cbar=plt.colorbar(label='S21 (dB)')\n\
    cbar.ax.tick_params(labelsize=20)\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Flux (mV)',fontsize=20)\n\
    ax.set_ylabel('Frequency (MHz)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"


    freqs = np.array(na.frequency_array().split(',')).astype(float)


    mags = np.ndarray((len(volts),npoints))
    phases = np.ndarray((len(volts),npoints))


    mags[:] = -100
    phases[:] = 0
    
    att.set_attenuation(attenuation_val)

    
    source.turn_on()
    sleep(0.05)
    na.power = 1
    sleep(0.05)
    source.ramp_voltage(volts[0])

    try:
        for idx,volt_val in enumerate(volts):
            clear_output(wait=True)
            source.set_voltage(volt_val)
            na.clear_averaging()
            sleep(ave_time)
            
            data = np.array(na.data_array().split(',')).astype(float)
            mags[idx] = data[::2]
            phases[idx] =  data[1::2]
            
            plt.pause(0.05)
            plt.pcolor(volts*1e3,freqs*1e-6,mags.T)    
    except KeyboardInterrupt:
        pass
    except VisaIOError:
        pass

    source.ramp_voltage(0)
    na.power = 0
    source.turn_off()
    Z = 10**(mags/20)*np.exp(1j*phases*np.pi/180)

    np.savez(name,header=howtoplot,volts=volts,freqs=freqs,Z=Z)
    clear_output(wait=True)
    plt.pause(0.05)
    plt.show()

    return name+'.npz'

def main():
    args = sys.argv

    command = args[1]
    filename = args[2]

    if command == "measure":
        na,att,source,qubitname,center_freq,span_freq,npoints,if_freq,ave_time,volt_init,volt_final,volt_step,naverages,attenuation = loadparams(filename)

        name = measure(qubitname,
                na,
                att,
                source,
                center_freq,
                span_freq,
                if_freq,
                npoints,
                naverages,
                volt_init,
                volt_final,
                volt_step,
                ave_time,
                attenuation)
        
        print(name)

    if command == 'time':
        _,_,_,_,_,_,_,_,ave_time,volt_init,volt_final,volt_step,_,_ = loadparams(filename)

        time= len(np.arange(volt_init,volt_final,volt_step))*ave_time

        timedelta_obj = datetime.timedelta(seconds=time)
        print("Time of measurement: ",timedelta_obj)
        
        
    elif command == "plot":
        plot(filename)




if __name__ == "__main__":
    main()