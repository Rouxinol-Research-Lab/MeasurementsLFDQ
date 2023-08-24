from instruments.VisaInstrument import *


class DG645_driver(VisaInstrument):

    def __init__(self,address):
        super().__init__(address)
        
    def startTrigger(self):
        '''Sends pulses. Can be a single pulse or a pulse sequence'''
        self.write('*TRG')

    def setTriggerRate(self,f):
        '''Set the trigger rate for internal triggering'''
        self.write('TRAT {}'.format(f))

    def getTriggerRate(self):
        '''Get the trigger rate for internal triggering'''
        return self.query('TRAT?')
    
    def setTriggerSource(self,i):
        '''
            Set (query) the trigger source {to i}. The parameter i determines the trigger
            source according to the following table:
            i Trigger Source
            0 Internal
            1 External rising edges
            2 External falling edges
            3 Single shot external rising edges
            4 Single shot external falling edges
            5 Single shot
            6 Line
        '''
        self.write('TSRC {}'.format(i))

    def getTriggerSource(self):
        '''
            get (query) the trigger source. trigger
            source according to the following table:
            0 Internal
            1 External rising edges
            2 External falling edges
            3 Single shot external rising edges
            4 Single shot external falling edges
            5 Single shot
            6 Line
        '''
        i = int(self.query('TSRC?')[:-1])

        if i == 0:
            return 'Internal'
        elif i == 1:
            return 'External rising edges'
        elif i == 2:
            return 'External falling edges'
        elif i == 3:
            return 'Single shot external rising edges'
        elif i == 4:
            return 'Single shot external falling edges'
        elif i == 5:
            return 'Single shot'
        
    def setBurstCount(self,i):
        '''
        Set (query) the burst count {to i}. When burst mode is enabled, the DG645
        outputs burst count delay cycles per trigger.
        '''
        self.write('BURC {}'.format(i))

    def getBurstCount(self):
        '''
        Get (query) the burst count {to i}. When burst mode is enabled, the DG645
        outputs burst count delay cycles per trigger.
        '''

        return self.query('BURC?')
    
    def setBurstMode(self,i):
        '''
        Set (query) the burst mode {to i}. If i is 0, burst mode is disabled. If i is 1, burst
        mode is enabled.
        '''

        self.write('BURM {}'.format(i))

    def getBurstMode(self):
        '''
        Get (query) the burst mode {to i}. If i is 0, burst mode is disabled. If i is 1, burst
        mode is enabled.
        '''

        return self.query('BURM?')
    
    def setBurstPeriod(self,t):
        '''
        Set (query) the burst period {to t}. The burst period sets the time between delay
        cycles during a burst. The burst period may range from 100 ns to 2000 , 10 ns in
        10 ns steps.
        '''

        self.write('BURP {}'.format(t))

    def getBurstPeriod(self):
        '''
        Get (query) the burst period {to t}. The burst period sets the time between delay
        cycles during a burst. The burst period may range from 100 ns to 2000 , 10 ns in
        10 ns steps.
        '''

        return self.query('BURP?')
    
    def setLevelAmplitude(self, b, v):
        '''
        Set (query) the amplitude for output b {to v}.
        '''

        self.write('LAMP {},{}'.format(b,v))

    def getLevelAmplitude(self, b):
        '''
        Get (query) the amplitude for output b .
        '''

        self.query('LAMP?{}'.format(b))

    def setDelay(self, c, d, t):
        '''
        Set (query) the delay for channel c {to t relative to channel d}.
        '''

        self.write('DLAY {},{},{}'.format(c,d,t))

    def getDelay(self, c):
        '''
        Get (query) the amplitude for output c .
        '''

        self.query('DLAY?{}'.format(c))