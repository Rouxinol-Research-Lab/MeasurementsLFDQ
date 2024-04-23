from matplotlib.pyplot import plot,show
from numpy import sin,cos,exp,pi,arange,sqrt
from scipy.signal import convolve

class Pulse:
    '''
        This class defines a pulse to be sent to the AWG.
    '''

    def __init__(self, length, amplitude, frequency, phase, envelope = 'square', tau = 0.2, sigma = 0.20, nsteps = 0.05e-9):
        self.length = length
        self.phase = phase/180*pi
        self.amplitude = amplitude
        self.frequency = frequency
        self.envelope = envelope
        self.tau = tau
        self.sigma = sigma
        self.divisions = nsteps

        t, pulse = self.build()

        self.t = t
        self.pulse = pulse

    def build(self):
        t = arange(0, self.length, self.divisions)
        pulse = self.amplitude*sin(2*pi*self.frequency*t+self.phase)

        if self.envelope.lower() == 'gaussian':
            o = self.sigma * self.length
            s = exp(-(t-self.length/2)** 2/o**2/2)
            pulse = pulse*s

        return t, pulse
    
    def show(self):
        plot(self.t, self.pulse)
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
def prepareSignalData(measurementPulseLength,
                      excitationPulsesLength,
                      excitationPulsesDelay,
                      excitationPulsesPhase,
                      freq,
                      excitation_freq,
                      awgRate,
                      markerValueForExcitation=2,
                      markerValueForMeasurement=3,
                      sigma = 0.25,
                      tau = 0.20, 
                      waveform = "gaussian"):
    """
    Prepare signal data for waveform.Three formats are available: square, gaussian, and gaussiansquare.

    Args:
        measurementPulseLength (float): Length of the measurement pulse.
        excitationPulsesLength (list): List of lengths of the excitation pulses.
        excitationPulsesDelay (list): List of delays between excitation pulses.
        excitationPulsesPhase (list): List of phases for each excitation pulse.
        freq (float): Frequency of the measurement pulse.
        excitation_freq (float): Frequency of the excitation pulses.
        awgRate (float): Rate of the arbitrary waveform generator (AWG).
        markerValueForExcitation (int, optional): Marker value for the excitation pulses. Defaults to 2.
        markerValueForMeasurement (int, optional): Marker value for the measurement pulse. Defaults to 3.
        sigma (float, optional): Standard deviation for the Gaussian waveform. Defaults to 0.25.
        tau (float, optional): Scaling factor for the final length of the pulse measurement. Defaults to 0.20.
        waveform (str, optional): Type of waveform. Can be "square", "gaussian", or "gaussiansquare". Defaults to "square".

    Returns:
        tuple: A tuple containing the following arrays:
            - x (numpy.ndarray): Time array.
            - pulseMeasurement (numpy.ndarray): Array representing the measurement pulse.
            - pulsesExcitation (numpy.ndarray): Array representing the excitation pulses.
            - pulseMarkers (numpy.ndarray): Array representing the marker values.
    """
    # Calculate the total length of the signal
    totalLength = np.sum(excitationPulsesLength) + \
        np.sum(excitationPulsesDelay) + measurementPulseLength

    # Create the time array
    x = np.arange(0, totalLength, 1/awgRate)

    # Initialize arrays for the excitation pulses, measurement pulse, and markers
    size = len(x)
    pulsesExcitation = np.zeros(size, dtype=np.int8)
    pulseMeasurement = np.zeros(size, dtype=np.int8)
    pulseMarkers = markerValueForExcitation*np.ones(size, dtype=np.int8)

    # Initialize position variable
    pos = 0

    # Generate excitation pulses
    for i in range(len(excitationPulsesLength)):
        xExcitation = np.arange(
            0, excitationPulsesLength[i], 1/awgRate)
        awgOscExcitation = np.array(
            (2**7-1)*np.sin(2*np.pi*(excitation_freq)*xExcitation+excitationPulsesPhase[i]), dtype=np.int8)
        
        # Apply waveform modifications if necessary
        if waveform.lower() == "gaussian":
            awgOscExcitation = awgOscExcitation * \
            np.exp(-(xExcitation-excitationPulsesLength[i]/2)
               ** 2/(sigma * excitationPulsesLength[i])**2)
        
        elif waveform.lower() == "gaussiansquare" or "gaussian_square":
            pulse1 = awgOscExcitation[:int(tau*len(awgOscExcitation))] * \
                np.exp(-(xExcitation-excitationPulsesLength[i]*tau)
                    ** 2/(sigma * excitationPulsesLength[i])**2)[:int(tau*len(awgOscExcitation))]
            pulse2 = awgOscExcitation[int(tau*len(awgOscExcitation)):-int(tau*len(awgOscExcitation))]
            pulse3 = awgOscExcitation[-int(tau*len(awgOscExcitation)):] * \
                np.exp(-(xExcitation-excitationPulsesLength[i]*(1-tau))
                    ** 2/(sigma * excitationPulsesLength[i])**2)[-int(tau*len(awgOscExcitation)):]
            
            awgOscExcitation = np.concatenate((pulse1,pulse2,pulse3))

        # Update the arrays with the excitation pulse and marker values
        end = pos+len(awgOscExcitation)
        pulsesExcitation[pos:end] = awgOscExcitation

        # Update the position variable with the delay
        pos = end + int(excitationPulsesDelay[i]*awgRate)

    # Generate the measurement pulse
    xMeasurement = np.arange(0, measurementPulseLength, 1/awgRate)
    awgOscMeasurement = np.array(
        (2**7-1)*np.sin(2*np.pi*(freq)*xMeasurement), dtype=np.int8)
    
    # Apply waveform modifications if necessary
    if waveform.lower() == "gaussian":
        awgOscMeasurement = awgOscMeasurement * \
        np.exp(-(xMeasurement-measurementPulseLength/2)
               ** 2/(sigma * measurementPulseLength)**2)
    
    elif waveform.lower() == "gaussiansquare" or "gaussian_square":
        pulse1 = awgOscMeasurement[:int(tau*len(awgOscMeasurement))] * \
        np.exp(-(xMeasurement-measurementPulseLength*tau)
               ** 2/(sigma * measurementPulseLength)**2)[:int(tau*len(awgOscMeasurement))]
        pulse2 = awgOscMeasurement[int(tau*len(awgOscMeasurement)):-int(tau*len(awgOscMeasurement))]
        pulse3 = awgOscMeasurement[-int(tau*len(awgOscMeasurement)):] * \
            np.exp(-(xMeasurement-measurementPulseLength*(1-tau))
                ** 2/(sigma * measurementPulseLength)**2)[-int(tau*len(awgOscMeasurement)):]
    
        # Join the the three parts
        awgOscMeasurement = np.concatenate((pulse1,pulse2,pulse3))

    # Update the arrays with the measurement pulse and marker values
    pulseMeasurement[-len(awgOscMeasurement):] = awgOscMeasurement
    pulseMarkers[-len(awgOscMeasurement):] = markerValueForMeasurement
    pulseMarkers[-1] = 0
       
    return x, pulseMeasurement, pulsesExcitation, pulseMarkers