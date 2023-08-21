from instruments.VisaInstrument import *
import numpy as np
from time import sleep

class SIM970_driver(VisaInstrument):

    def __init__(self,address,port):
        super().__init__(address)
        self._port = port

    def get_voltage(self, channel, avg = 1, sleeptime = 0.05):
        self.write('SNDT {}, "VOLT?{},{}"'.format(self._port, channel, avg))
        sleep(sleeptime)
        nbytes = int(self.query('NINP? {}'.format(self._port))[:-1])
        response = self.query('GETN? {},{}'.format(self._port,nbytes))
        x = np.array(response[5:5+nbytes].split('\r\n')[:-1]).astype(float)

        return np.mean(x),len(x)
    
    def get_buffer(self):
        return int(self.query('NINP? {}'.format(self._port))[:-1])
    
    def clean_buffer(self):
        nbuffer = self.get_buffer()
        self.query('GETN? {},{}'.format(self._port,nbuffer))
