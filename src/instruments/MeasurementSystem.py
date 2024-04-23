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