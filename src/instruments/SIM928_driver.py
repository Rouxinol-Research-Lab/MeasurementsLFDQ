from instruments.VisaInstrument import *
from time import sleep
import numpy as np

class SIM928_driver(VisaInstrument):

    def __init__(self,address,port, step_voltage = 0.1, step_time = 0.05):
        super().__init__(address)
        self._port = port
        self._step = step_voltage
        self._step_time = step_time

    def turn_on(self):
        self.write('SNDT{}, "OPON"'.format(self._port))

    def turn_off(self):
        self.write('SNDT{}, "OPOF"'.format(self._port))

    def ramp_voltage(self,voltage_final):
        volt_init = self.get_voltage()

        if volt_init > voltage_final:
            step = -self._step
        else:
            step = self._step
            
        step_time = self._step_time

        volts = np.arange(volt_init,voltage_final+step,step)

        for volt in volts:
            self.set_voltage(volt)
            sleep(step_time)




    def reset_voltage(self):
        self.write('SNDT {},"VOLT {}"'.format(self._port,0))

    def set_voltage(self,voltage):
        self.write('SNDT {},"VOLT {}"'.format(self._port,round(voltage,3)))

    def get_voltage(self):
        self.write('SNDT {}, "VOLT?"'.format(self._port))
        sleep(0.05)
        response = self.query('GETN? {},80'.format(self._port))
        numberofbytes = int(response[2:5])-2

        return float(response[5:5+numberofbytes])
    
    def get_buffer(self):
        return int(self.query('NINP? {}'.format(self._port))[:-1])
    
    def clean_buffer(self):
        nbuffer = self.get_buffer()
        self.query('GETN? {},{}'.format(self._port,nbuffer))