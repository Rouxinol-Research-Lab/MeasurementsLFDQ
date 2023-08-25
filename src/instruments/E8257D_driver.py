from instruments.VisaInstrument import *

class E8257D_driver(VisaInstrument):
    def __init__(self,resource_address):
        super().__init__(resource_address)
        self.stop_rf()
        self.stop_mod()

    def start_rf(self):
        self.write(":OUTPUT ON")

    def stop_rf(self):
        self.write(":OUTPUT OFF")

    def start_mod(self):
        self.write(":OUTPUT:MOD ON")

    def stop_mod(self):
        self.write(":OUTPUT:MOD OFF")

    def start_pulse(self):
        self.write(":PULM:STAT 1")

    def stop_pulse(self):
        self.write(":PULM:STAT 0")

    def set_pulse_trigger_external(self):
        self.write(':PULM:SOUR EXT')

    def is_mod_on(self):
        mod_on = self.query(":OUTPUT:MOD?").strip()
        return int(mod_on) == 1

    def is_on(self):
        on = self.query(":OUTPUT?").strip()
        return int(on) == 1

    def get_frequency(self):
        freq = self.query(':FREQ?').strip()
        return float(freq)


    def set_frequency(self,freq):
        self.write(':FREQ {}'.format(freq))


    def get_amplitude(self):
        amp = self.query(':POWER?').strip()
        return float(amp)


    def set_amplitude(self,amp):
        self.write(':POWER {} dBm'.format(amp))