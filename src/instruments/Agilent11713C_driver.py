from instruments.VisaInstrument import *


class Agilent11713C_driver(VisaInstrument):
    def __init__(self,address):
        super().__init__(address)

    def get_attenuation(self):
        '''Gets the attenuation level. '''

        d = int(self.query("ATTenuator:BANK1:Y?").split("\n")[0])
        u = int(self.query("ATTenuator:BANK1:X?").split("\n")[0])
        return d+u


    def set_attenuation(self,att):
        '''Sets the attenuation level. '''

        if att < 0:
            raise ValueError("Negative value for attenuation is not allowed.")

        d = int(att/10)
        u = int(att%10)
        self.write('ATT:BANK1:X {}'.format(u))
        self.write('ATT:BANK1:Y {}'.format(d*10))