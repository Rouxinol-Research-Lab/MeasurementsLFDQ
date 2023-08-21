import pyvisa


rm = pyvisa.ResourceManager()

import numpy as np

class SGS100A_driver():
    def __init__(self, address):
        self._address = address

    def open(self):
        '''Open conenction to instrument using address given in the constructor'''
        self._inst = rm.open_resource(self._address)
        self.idn = self._inst.query("*IDN?")
        self.stop_rf()


    def close(self):
        self.stop_rf()
        self._inst.close()

    def start_rf(self):
        self._inst.write(':OUTPut 1')
    
    def stop_rf(self):
        self._inst.write(':OUTPut 0')
    
    def set_RF(self, freq_mhz):
        self._inst.write(':FREQuency:CW {} MHz'.format(freq_mhz))
    
    def set_level(self,level_dbm):
        '''Set the power output in dBm'''
        self._inst.write(':POWer:POWer {}'.format(level_dbm))
