from instruments.Pulse import Pulse
from instruments.PulseSequence import PulseSequence

from numpy import array, pi, ndarray, sin, cos, sqrt, exp, zeros, arange, ones, int8

class Parameter:
    def __init__(self):
        super().__init__()
        
class Instrument:
    def __init__(self):
        super().__init__()
        
class MeasurementSystem:

    def __init__(self, name):
        self.name = name
        self.awgChannels = []
        self.parameters = Parameter()
        self.instruments = Instrument()

    def connectToAwgChannel(self, channel, label):
        self.awgChannels.append((channel,label))

    def prepareSignalData(self,
                          sequence,
                          awgRate):
        """
        Prepare signal data for waveform.Three formats are available.
    
        Args:
            sequence (PulseSequence): holds the pulses and its sequence.
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
    
        Returns:
            tuple: A tuple containing the following arrays:
                - x (numpy.ndarray): Time array.
                - pulseMeasurement (numpy.ndarray): Array representing the measurement pulse.
                - pulsesExcitation (numpy.ndarray): Array representing the excitation pulses.
                - pulseMarkers (numpy.ndarray): Array representing the marker values.
        """
        # Calculate the total length of the signal
        totalLength = sequence.get_totallength()
    
        # Create the time array
        x = arange(0, totalLength, 1/awgRate)
    
        # Initialize arrays for the excitation pulses, measurement pulse, and markers
        size = len(x)
        pulses = zeros(size, dtype= int8)

        bytes_amplitude = 127

        all_pulses = {}

        for (awgChannel, channelName) in self.awgChannels:

            all_pulses[channelName] = zeros(size, dtype= int8)
            
            delay = 0
            for idx,pulseChannel in enumerate(sequence.list_of_channels):
                c = channelName.lower()
                if pulseChannel.lower() == c:
                    p = sequence.list_of_pulses[idx]
                    initial_index = int(delay*awgRate)
    
                    p_t, p_wave = p.build(1/awgRate,delay)
    
                    wave = array(bytes_amplitude*p_wave, dtype = int8)
    
                    all_pulses[c][initial_index : initial_index + len(wave)] = wave
    
                delay += sequence.list_of_delays[idx] + sequence.list_of_pulses[idx].length


        return x, all_pulses