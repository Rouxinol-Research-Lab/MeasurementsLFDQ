import serial


class ERASynth_driver():
    def __init__(self,port, baudrate, timeout = 10):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout

        self._serial_conn = serial.Serial()

    def open(self):
        self._serial_conn.open()

    def close(self):
        self._serial_conn.close()

    def start_rf(self):
        self._serial_conn.write(b'>P01\r\n')
    
    def stop_rf(self):
        self._serial_conn.write(b'>P00\r\n')
    
    def set_RF(self, freq_mhz):
        '''set RF frequency integer in MHZ'''
        freq_hz = int(1000000*freq_mhz)
        self._serial_conn.write(b'>F%d\r\n'  % freq_hz)
    
    def set_level(self,level_dbm):
        '''Set the power output in dBm'''
        level_dbm = float(level_dbm)
        self._serial_conn.write(b'>A%d\r\n' % level_dbm)

    def log(self):
        print(self._serial_conn.readlines())


