from matplotlib.pyplot import plot,show
from numpy import sin,cos,exp,pi,arange,sqrt
from scipy.signal import convolve

class Pulse:
    '''
        This class defines a pulse to be sent to the AWG.
    '''

    def __init__(self, length, amplitude, frequency, phase, envelope = 'square', tau = 0.2, sigma = 0.20):
        self.length = length
        self.phase = phase/180*pi
        self.amplitude = amplitude
        self.frequency = frequency
        self.envelope = envelope
        self.tau = tau
        self.sigma = sigma

    def build(self, nsteps, initial_time = 0):
        t = arange(initial_time, initial_time + self.length, nsteps)
        pulse = self.amplitude*sin(2*pi*self.frequency*t+self.phase)

        if self.envelope.lower() == 'gaussian':
            o = self.sigma * self.length
            s = exp(-(t-initial_time-self.length/2)** 2/o**2/2)
            pulse = pulse*s

        return t, pulse
    
    def show(self, timestep = 0.01e-9):
        t, pulse = self.build(timestep)
        plot(t, pulse)
        show()
    


def getDataFromSocketBinary(session):
    dat = b''
    while 1:
        message = session.recv(4096)
        last=len(message)
        if chr(message[-1]) == "\n":
            dat=dat+message[:-1]
            return dat
        else:
            dat=dat+message

def getIEEEBlockTag(data):
    dataSize = len(data)
    numberLength =  int(np.log10(dataSize)+1)
    return "#{}{}".format(numberLength,dataSize)

def downloadDataToAwg(data,channel,offset):
    tag = getIEEEBlockTag(data)
    cmd = ":TRAC{}:DATA 1,{},".format(channel,offset) + tag
    awg._session.sendall(cmd.encode()+bytes(data)+"\n".encode())    


# Define a function to prepare signal data for a waveform
