import pyvisa as visa

rm = visa.ResourceManager()

class VisaInstrument:
    def __init__(self,resource_address):
        self._inst = rm.open_resource(resource_address)
        self._idn = self._inst.query("*IDN?")[:-1]

    def write(self,command):
        return self._inst.write(command)

    def write_raw(self,commad):
        return self._inst.write_raw(commad)

    def query(self,command):
        return self._inst.query(command)

    def read_raw(self):
        return self._inst.read_raw()

    def open(self):
        return self._inst.open()

    def close(self):
        return self._inst.close()