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

from measurements.Pulse import Pulse,Envelope
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

        
        self.RFMeasurementLength = RFMeasurementLength
        self.RFMeasurementAmplitude = RFMeasurementAmplitude
        self.RFExcitationLength = RFExcitationLength
        self.RFExcitationAmplitude = RFExcitationAmplitude
        self.RFExcitationDelay = RFExcitationDelay
        self.RFExcitationState = RFExcitationState
        self.fluxValue = fluxValue
        self.fluxResistance = fluxResistance
        self.fluxState = fluxState
        self.numberOfBuffers = numberOfBuffers
        self.numberOfRecordsPerBuffers = numberOfRecordsPerBuffers
        self.waveformHeadCut = waveformHeadCut
        self.amplitudeReferenceAlazar = amplitudeReferenceAlazar
        self.decimationValue = decimationValue
        self.MeasurementFrequency = MeasurementFrequency
        self.ExcitationFrequency = ExcitationFrequency
        self.Measurement_IF = Measurement_IF
        self.Excitation_IF = Excitation_IF
        self.attenuation = attenuation
        self.backgroundPlotValue = backgroundPlotValue

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


        self.inst_awg.set_sampleRate(awgSamplingRate)

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
        SCPI_sock_send(self.inst_awg._session, ':TRAC2:MMOD EXT') # use external memory, 16 Gbytes
        # dividir a memória em 2
        SCPI_sock_send(self.inst_awg._session, ':INST:MEM:EXT:RDIV DIV2') # devide memory, one for each channel

        # markers should have 1 V amplitude and offset 0.5
        self.inst_awg.setVoltage(3,1) 
        self.inst_awg.setVoltage(4,1)

        self.inst_awg.setVoltageOffset(3,0.5) 
        self.inst_awg.setVoltageOffset(4,0.5)

        self.inst_awg.openChanneloutput(1)
        self.inst_awg.openChanneloutput(2)
        self.inst_awg.openChanneloutput(3)
        self.inst_awg.openChanneloutput(4)
    
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

        self.DefaultAlazarSamplingRate = 1e9
        samplingRate = self.DefaultAlazarSamplingRate/self.alazar_params['decimationValue']

        # O número pontos por aquisição depende do sampling rate. Tem que ser múltiplos de 256.
        self.alazar_params['postTriggerSamples'] = int(self.RFMeasurementLength*samplingRate/256)*256    # quantos pontos depois do trigger.
        self.alazar_params['preTriggerSamples'] = 0 # quantos pontos o alazar vai salvar antes do trigger.

        self.ms = DataChannelManager('AWG')


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


    def prepareForCavityMeasure(self, ExperimentName, MeasurementLength, MeasurementPulseLength, AttenuationValue):
        self.inst_awg.stop()
        self.inst_RFsourceMeasurement.stop_rf()
        
        self.RFMeasurementLength = MeasurementPulseLength
        self.attenuation = AttenuationValue
        self.measurementLength = MeasurementLength

        samplingRate = self.DefaultAlazarSamplingRate/self.alazar_params['decimationValue']

        # O número pontos por aquisição depende do sampling rate. Tem que ser múltiplos de 256.
        self.alazar_params['postTriggerSamples'] = int(self.RFMeasurementLength*samplingRate/256)*256    # quantos pontos depois do trigger.

        mp = Pulse(length = self.RFMeasurementLength, # duração
           amplitude = 1, # amplitude. não utilizado para nada
           frequency = 70e6, # frequência, o de medida não utilizado para nada
           phase = 0, # a fase
           envelope='zero') # o seu formanto, gaussiano, quadrado ou quadrado gaussiano
        
        self.sequence = PulseSequence(ExperimentName) # dá um nome da medida
        self.sequence.startup_delay = 1e-6 # um delay para ligar antecipadamente a fonte de excitação. liga a fonte antecipadamente por esse valor antes do primeiro pulso de excitação

        self.sequence.clear()

        self.sequence.add(mp,'m') # Adiciona o pulso ao sequenciador e o conecta a um canal, no caso o canal "m"
        # Esse canal vai ser especificado a um dos canais do awg. Isso ainda não aconteceu

        

        #Aqui conectamos canais usados pelo sequenciado aos canais do AWG
        # o mesmo canal do AWG pode ser usado por muitos canais do sequenciador
        self.ms.clearAwgChannel()
        self.ms.labelAwgChannel(channel = 1, # o canal do awg
                                channelName = 'm',  # o seu nome em relação ao sequenciador
                                freq = 0, # a frequência real a ser utilizada por esse canal. Se 0, significa que o sinal vai ser apenas 0
                                markerValue = 2, # Esse valor indica qual marker vai ser ligado enquanto estiver ocorendo algum pulso nesse canal
                                markers = True) # Afirma que esse canal é usado para configurar markers


        # essa função gera os dados aceitos pelo awg para uma medida total especificada
        # o tempo total deve ser maior que o tempo total da sequência dos pulsis
        channelData = self.ms.prepareChannelData(self.inst_awg, self.sequence, self.measurementLength) # add total length, pulses and relaxation to alloc the necessary bytes in memory


        # deleta toda memória do awg
        self.inst_awg.clearMemory()
        sleep(0.05)

        # Aloca o espaço necessário para a medida
        self.ms.allocAwgMemory(self.inst_awg,channelData)
        sleep(0.05)


        # Carrega os pulsos ao awg
        self.ms.loadChannelDataToAwg(self.inst_awg,channelData,'m')
        sleep(0.05)

        # adiciona o tempo de antecipação da fonte de excitação
        self.ms.setInstrumentsMarker(self.inst_awg,channelData)



            
    def measureCavity(self, freqs):
        self.inst_awg.start()
        self.inst_RFsourceMeasurement.start_rf()

        Is = np.ndarray(len(freqs))
        Qs = np.ndarray(len(freqs))

        Is[:] = 10**(self.backgroundPlotValue/20)
        Qs[:] = 10**(self.backgroundPlotValue/20)

        for idx,freq in enumerate(freqs):
            clear_output(wait=True)
            
            self.inst_RFsourceMeasurement.set_frequency(freq-self.Measurement_IF)
            sleep(0.05)

            I,Q = self.capture()

            Is[idx] = I
            Qs[idx] = Q 
            
            mags = 20*np.log10(np.sqrt(Is**2+Qs**2))

            
            plt.pause(0.05)
            plt.plot(freqs,mags)
            
        clear_output(wait=True)
        plt.plot(freqs,mags)

        self.inst_awg.stop()
        self.inst_RFsourceMeasurement.stop_rf()

        return Is,Qs,mags

