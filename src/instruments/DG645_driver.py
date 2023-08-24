from instruments.VisaInstrument import *


class DG645_driver(VisaInstrument):

    def __init__(self,address,port):
        super().__init__(address)
        

