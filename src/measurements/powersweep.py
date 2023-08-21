import numpy as np
import pylab as plt
from instruments.E5063A_driver import *
from instruments.Agilent11713C_driver import *
from time import sleep,strftime,localtime
from toml import load
import sys
from IPython.display import clear_output
from pyvisa.errors import VisaIOError


def loadparams(filename):

    parameters = load(filename)


    na = E5063A_driver(parameters['na_address'])
    att = Agilent11713C_driver(parameters['att_address'])


    ave_points = parameters['average_points']
    qubitname = parameters['qubitname']

    center_frequency = parameters['center_frequency']
    span_frequency = parameters['span_frequency']
    npoints = parameters['npoints']
    if_freq = parameters['if_freq']
    average_time = parameters['average_time']

    attenuation_initial = parameters['attenuation_initial']
    attenuation_final = parameters['attenuation_final']
    attenuation_step = parameters['attenuation_step']

    return na,att,qubitname,center_frequency,span_frequency,npoints,if_freq,average_time,attenuation_initial,attenuation_final,attenuation_step,ave_points



def measure(qubitname,
                na,
                att,
                center_freq,
                span_freq,
                if_freq,
                npoints,
                naverages,
                att_init,
                att_final,
                att_step,
                ave_time):

    typename = "powersweep"
    na.average_points = naverages
    na.averaging = 1
    na.power = 0

    na.center_frequency = center_freq
    na.span_frequency = span_freq

    na.sweep_points = npoints
    na.if_bandwidth_frequency = if_freq
    na.data_array_format = 'PLOG'

    attenuations = np.arange(att_init, att_final, att_step)

    name = qubitname + "_"  + str(strftime("%Y%m%d_%H%M",localtime())) + "_"+ typename + "_from_" + str(att_init) + "_to_" + str(att_final)+"_cfreq_"+str(int(center_freq*1e-6))


    howtoplot = "\
    data = np.load('"+name+".npz')\n\
    attenuations = data['atts']\n\
    freqs = data['freqs']\n\
    mags = np.abs(data['Z'])\n\
    fig = plt.figure(figsize=(10,7))\n\
    ax = fig.gca()\n\
    plt.pcolor(attenuations,freqs*1e-6,20*np.log10(mags.T))\n\
    cbar=plt.colorbar(label='S21 (dB)')\n\
    cbar.ax.tick_params(labelsize=20)\n\
    ax.tick_params(labelsize=20)\n\
    ax.set_xlabel('Attenuation (dB)',fontsize=20)\n\
    ax.set_ylabel('Frequency (MHz)',fontsize=20)\n\
    ax.set_title('"+name+"',fontsize=16)\n\
    plt.show()"


    freqs = np.array(na.frequency_array().split(',')).astype(float)


    mags = np.ndarray((len(attenuations),npoints))
    phases = np.ndarray((len(attenuations),npoints))


    mags[:] = 0
    phases[:] = 0

    na.power = 1
    sleep(0.1)

    try:
        for idx,att_val in enumerate(attenuations):
            clear_output(wait=True)
            att.set_attenuation(att_val)
            na.clear_averaging()
            sleep(ave_time)
            
            data = np.array(na.data_array().split(',')).astype(float)
            mags[idx] = data[::2]
            phases[idx] =  data[1::2]
            
            plt.pause(0.05)
            plt.pcolor(attenuations,freqs*1e-6,mags.T)

        na.power = 0
        Z = 10**(mags/20)*np.exp(1j*phases*np.pi/180)

        np.savez(name,header=howtoplot,atts=attenuations,freqs=freqs,Z=Z)
        clear_output(wait=True)
        plt.pause(0.05)
        plt.show()
        
    except KeyboardInterrupt:
        pass
    except VisaIOError:
        pass

    return name+'.npz'

def plot(filename):
    data = np.load(filename)
    attenuations = data['atts']
    freqs = data['freqs']
    mags = np.abs(data['Z'])
    fig = plt.figure(figsize=(10,7))
    ax = fig.gca()
    plt.pcolor(attenuations,freqs*1e-6,20*np.log10(mags.T))
    cbar=plt.colorbar(label='S21 (dB)')
    cbar.ax.tick_params(labelsize=20)
    ax.tick_params(labelsize=20)
    ax.set_xlabel('Attenuation (dB)',fontsize=20)
    ax.set_ylabel('Frequency (MHz)',fontsize=20)
    ax.set_title(filename,fontsize=16)
    plt.show()


def main():
    args = sys.argv

    command = args[1]
    filename = args[2]

    if command == "measure":
        na,att,qubitname,center_freq,span_freq,npoints,if_freq,ave_time,att_init,att_final,att_step,naverages = loadparams(filename)

        name = measure(qubitname,
                na,
                att,
                center_freq,
                span_freq,
                if_freq,
                npoints,
                naverages,
                att_init,
                att_final,
                att_step,
                ave_time)
        
        print(name)
        
    elif command == "plot":
        plot(filename)




if __name__ == "__main__":
    main()