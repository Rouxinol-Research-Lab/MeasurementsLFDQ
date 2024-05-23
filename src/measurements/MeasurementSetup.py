# importar os drivers, arquivos que tem os comandos de controle e acesso aos instrumentos
# sempre é chamando instrument.*** alguma coisa, onde isso é o nome do arquivo.

from instruments.ATS9872_driver import * # alazar placa de aquisição
from instruments.DG645_driver import * # delay generator 
from instruments.M8195A_driver import * # awg
from instruments.E8257D_driver import * #RF source
from instruments.Agilent11713C_driver import * # attenuator
from instruments.SIM928_driver import * # Voltage source
from instruments.SIM970_driver import * # Voltage meter
from importlib import reload # comando para reimportar mais facilmente algum arquivo


from measurements.waveforms.SquarePulse import *
from measurements.waveforms.SquareGaussianPulse import *
from measurements.waveforms.DragPulse import *
from measurements.waveforms.ZeroPulse import *
from measurements.waveforms.GaussianPulse import *

from measurements.PulseSequence import PulseSequence
from measurements.DataChannelManager import DataChannelManager

from IPython.display import clear_output

import matplotlib.pyplot as plt



class MeasurementSetup:
    def __init__(self,
                 awg_address='169.254.101.100',
                 att_address='TCPIP0::169.254.101.101::inst0::INSTR',
                 RFsourceMeasurement_address='TCPIP0::169.254.101.103::inst0::INSTR',
                 RFsourceExcitation_address='TCPIP0::169.254.101.104::inst0::INSTR',
                 Voltsource_address='GPIB0::2::INSTR',
                 Voltsource_channel=8,
                 Voltmeter_address='GPIB0::2::INSTR',
                 Voltmeter_channel=5,
                 awgSamplingRate = 64e9, 
                 TotalMeasurementLength = 125e-6,
                 RFMeasurementLength=5e-6,  # in seconds
                 RFMeasurementAmplitude=18,  # in dBm, this is a local oscillator, it feeds two mixers.
                 RFExcitationLength=20e-6,  # in seconds
                 RFExcitationAmplitude=11,  # in dBm, this is a local oscillator, it feeds one mixer.
                 RFExcitationDelay=0.1e-9,  # delay before the next pulse
                 RFExcitationState=False,  # if the excitation should be on while the measurement happens
                 fluxValue=0,  # in volts
                 fluxResistance=8e3,  # in ohms, this is for logging only. it is resistance used for the flux source
                 fluxState=True,  # if the flux should be on while the measurement happens
                 numberOfBuffers=100,  # number of buffers used by alazar board in the acquisition.
                 numberOfRecordsPerBuffers=50,  # number of records per buffer used by alazar board in the acquisition.
                 waveformHeadCut=500,  # number of points to be cut from head of each record in alazar.
                 amplitudeReferenceAlazar=-5.64,  # in dBm, the amplitude of the reference signal arriving at the alazar.
                 decimationValue=1,  # should be 1, 2, 4, or multiples of 10. it divides the alazar board clock which is 1 GHz. The clock should be at least 4 times reference frequency.
                 MeasurementFrequency=7400e6,  # in Hz, the frequency of the measurement pulse
                 ExcitationFrequency=5012e6,  # in Hz, the frequency of the excitation pulses
                 Measurement_IF=70e6,  # in Hz, the frequency of the measurement pulse
                 Excitation_IF=240e6,  # in Hz, the frequency of the measurement pulse
                 attenuation=30,  # in dB, attenuation
                 backgroundPlotValue=-46):  # in dB

        self.params = {
        'TotalMeasurementLength': TotalMeasurementLength, # total length in time units of the memory allocated to awg. Should be bigger then the total length of the pulse sequence.
        'RFMeasurementLength' : RFMeasurementLength, # Length of the measurement pulse
        'RFMeasurementAmplitude' : RFMeasurementAmplitude, # Amplitude of the measurement signal, should be high enough to feed the mixer.
        'RFExcitationLength' : RFExcitationLength, # length of the measurement pulse
        'RFExcitationAmplitude' : RFExcitationAmplitude, # amplitude of the excitation source. should be high enough to feed the mixer.
        'fluxValue' : fluxValue, # Value in volts of flux applied
        "fluxResistance": fluxResistance,
        "fluxState": fluxState,
        "numberOfBuffers": numberOfBuffers,
        "numberOfRecordsPerBuffers": numberOfRecordsPerBuffers,
        "waveformHeadCut": waveformHeadCut,
        "amplitudeReferenceAlazar": amplitudeReferenceAlazar,
        "decimationValue": decimationValue,
        "MeasurementFrequency": MeasurementFrequency,
        "ExcitationFrequency": ExcitationFrequency,
        "Measurement_IF": Measurement_IF,
        "Excitation_IF": Excitation_IF,
        "attenuation": attenuation,
        "backgroundPlotValue": backgroundPlotValue
        }

        self.inst_alazar = ATS9872_driver()
        self.inst_awg = M8195A_driver(awg_address)
        self.inst_att = Agilent11713C_driver(att_address)
        self.inst_RFsourceMeasurement = E8257D_driver(RFsourceMeasurement_address)
        self.inst_RFsourceExcitation = E8257D_driver(RFsourceExcitation_address)
        self.inst_voltsource =  SIM928_driver(Voltsource_address,Voltsource_channel,step_time=0.1,step_voltage=0.001)
        self.inst_voltmeter = SIM970_driver(Voltmeter_address,Voltmeter_channel)

        self.inst_awg.stop()
        self.inst_RFsourceMeasurement.stop_rf()
        self.inst_RFsourceExcitation.stop_rf()


        self.inst_awg.setSampleRate(awgSamplingRate)

        # tem que conectar também o awg a nossa referência de rubídio 10 MHz
        self.inst_awg.setRefInClockExternal()  
        self.inst_awg.setRefInClockFrequency(10e6)

        # configura o awg para usar dois canais (um de excitação, outro de medida) e usar dois markers
        # o canal 1 gerará o sinal de excitação I e o sinal de medida
        # o canal 2 gerará o sinal de excitação Q
        # o canal 3 será o marker 1 - para ligar a fonte 2, fonte de excitação
        # o canal 4 será o marker 2 - para ligar a fonte 1, de medida, e para trigar a placa de aquisição alazar
        self.inst_awg.setDualWithMarker()

        # usar a memória externa para o canal 2
        self.inst_awg.setChannelMemoryToExtended(2)
        # dividir a memória em 2
        self.inst_awg.setMemoryDivision(2)

        # markers should have 1 V amplitude and offset 0.5
        self.inst_awg.setVoltage(3,1) 
        self.inst_awg.setVoltage(4,1)

        self.inst_awg.setVoltageOffset(3,0.5) 
        self.inst_awg.setVoltageOffset(4,0.5)

        self.inst_awg.enableChanneloutput(1)
        self.inst_awg.enableChanneloutput(2)
        self.inst_awg.enableChanneloutput(3)
        self.inst_awg.enableChanneloutput(4)
    
        # configuração das fontes 1 e 2

        # temos que configurar a fonte no modo de pulsos com trigger externo
        # a polaridade escolhida da fonte depende do canal utilizado do awg.
        # todo canal do awg é duplicado. Ele vai ter um canal normal e outro que idêntico ao normal só que invertido.
        # A fonte de medida recebe o invertido enquando a placa alazar recebe o normal. Eu faço isso para
        # manter o nível do trigger igual em ambos.
        self.inst_RFsourceMeasurement.set_pulse_trigger_external()
        self.inst_RFsourceMeasurement.setPulsePolarityInverted()
        self.inst_RFsourceMeasurement.start_mod()


        # A fonte de excitação recebe o canal 3 - marker 1 -  normal
        self.inst_RFsourceExcitation.set_pulse_trigger_external()
        self.inst_RFsourceExcitation.setPulsePolarityNormal()
        self.inst_RFsourceExcitation.start_mod()

        # Configuramos amplitude do sinal da fonte de medida. Ela tem que ser o suficiente para alimentar os mixers que heterodinagem.
        # calculamos que seu valor deve ser 18 dBm.
        self.inst_RFsourceMeasurement.set_amplitude(self.RFMeasurementAmplitude)

        # A fonte de excitação não é necessariamente usada no processo de medida da cavidade (a menos que se queira ver os deslocamento dispersivo de frequência)
        # no caso sua amplitude é por volta de 11 dBm
        self.inst_RFsourceExcitation.set_amplitude(self.RFExcitationAmplitude)

        self.alazar_params = {}
        #
        # Values that work for recordsPerBuffer and BuffersPerAcquisition
        #                           25                    20
        #                           100                   20
        #                           500                   100
        self.alazar_params['recordsPerBuffer'] = numberOfRecordsPerBuffers  # número de capturas por buffer.
        self.alazar_params['buffersPerAcquisition'] = numberOfBuffers # número de buffers por aquisição.
        self.alazar_params['amplitudeReferenceAlazar'] = amplitudeReferenceAlazar # Intensidade do sinal de referência.
        self.alazar_params['inputLoad'] = 50# impedância dos cabos. 
        self.alazar_params['triggerLevel_volts'] = 0.7  # Level do trigger para ativar captura.
        self.alazar_params['triggerRange_volts'] = 1            # Tamanho máximo do sinal do trigger.
        self.alazar_params['waveformHeadCut'] = waveformHeadCut # quanto pontos iniciais por captura vão ser ignorados.
        self.alazar_params['period'] = 14 # o período em pontos do sinal capturado ( 70 MHz -> 14 pontos).
        self.alazar_params['buffer_timeout_ms'] = 5000 # tempo de espera para chegar um buffer; se ultrapassar, ocorre timeout.
        self.alazar_params['decimationValue'] = decimationValue # valor de divisão do sampling rate.
        self.alazar_params['TTL'] = True # Configuração do sinal de trigger. É o que funcionaou quando estava trigando pelo AWG. Quando é pelo delay generator, não usa isso.
        self.alazar_params['save'] = False # Caso queira salvar todos os pontos adquiridos na aquisição em formato binário.

    
        self.params['DefaultAlazarSamplingRate'] = 1e9
        samplingRate =  self.params['DefaultAlazarSamplingRate']/self.alazar_params['decimationValue']

        # O número pontos por aquisição depende do sampling rate. Tem que ser múltiplos de 256.
        self.alazar_params['postTriggerSamples'] = int(self.RFMeasurementLength*samplingRate/256)*256    # quantos pontos depois do trigger.
        self.alazar_params['preTriggerSamples'] = 0 # quantos pontos o alazar vai salvar antes do trigger.

        self.ms = DataChannelManager(self.inst_awg)

        self.ms.clearAwgChannel()
        self.ms.labelAwgChannel(channel = 1,
                                channelName = 'm',
                                markerValue = 2)

        self.ms.labelAwgChannel(channel = 2, # o canal do awg
                                channelName = 'Q',  
                                markerValue = 1)
        
        self.ms.labelAwgChannel(channel = 1, # o canal do awg
                                channelName = 'I',
                                markerValue = 1)

    def capture(self):
        I,Q = self.inst_alazar.capture(preTriggerSamples = self.alazar_params['preTriggerSamples'],                                       
                                       postTriggerSamples = self.alazar_params['postTriggerSamples'],                     
                                       recordsPerBuffer = self.alazar_params['recordsPerBuffer'], 
                                       buffersPerAcquisition = self.alazar_params['buffersPerAcquisition'],       
                                       powerReference_dBm = self.alazar_params['amplitudeReferenceAlazar'],
                                       inputLoad = self.alazar_params['inputLoad'],                                              
                                       triggerLevel_volts = self.alazar_params['triggerLevel_volts'], 
                                       triggerRange_volts = self.alazar_params['triggerRange_volts'],                                      
                                       waveformHeadCut = self.alazar_params['waveformHeadCut'],             
                                       period = self.alazar_params['period'],                                                 
                                       buffer_timeout_ms = self.alazar_params['buffer_timeout_ms'] ,                                    
                                       decimation_value = self.alazar_params['decimationValue'],            
                                       TTL = self.alazar_params['TTL'],  
                                       save = self.alazar_params['save'])  
        
        return I,Q

    def preparePulseSequence(self, s):
        self.inst_awg.stop()
        
        self.sequence = s

        samplingRate = self.params['DefaultAlazarSamplingRate']/self.alazar_params['decimationValue']

        self.RFMeasurementLength = self.sequence.channels['m']['pulses'][0].length
        self.alazar_params['postTriggerSamples'] = int(self.params['RFMeasurementLength']*samplingRate/256)*256    # quantos pontos depois do trigger.

        self.channelData = self.ms.prepareChannelData(self.sequence, self.params['TotalMeasurementLength']) # add total length, pulses and relaxation to alloc the necessary bytes in memory

        # deleta toda memória do awg
        self.inst_awg.freeMemory()
        sleep(0.05)

        # Aloca o espaço necessário para a medida
        self.ms.allocAwgMemory()
        sleep(0.05)

        for channel in self.sequence.channels.keys():
            self.ms.loadChannelDataToAwg(channel)
            sleep(0.05)

        # adiciona o tempo de antecipação da fonte de excitação
        self.ms.setInstrumentsMarker()
