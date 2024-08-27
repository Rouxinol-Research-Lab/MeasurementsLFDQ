#include <SimpleModbusSlave.h>
#include <TimerOne.h>
#include <EEPROM.h>

//////////////// variables /////////////////////////////////
long cont = 0, contVel;
float a1 = 0, a2 = 0, a3 = 0, auxacel1, auxacel2;
int auxvellida, auxEEPROM,controle_liga=0;
float auxvel;
signed long auxvelbits;
signed long auxvelbits2;
long ev1, ev2, et1, et2, et3, et4, et5, evf, eEVG, eLVG, eLMV;
signed long eEVO;
signed long eLVO;

float erroP, erroD1, erroD2, erroI, erroI1, erroI2, erroI3, erroI4, erroI5, erroI6, erroI7, erroI8, erroI9, erroI10, ajusteP, ajusteD, ajusteI, ajuste1, ajuste2;
signed int egP, egD, egI;

int fBT1,statBT1,fBT2,statBT2;

//////////////// registers of your slave ///////////////////
enum {
  // just add or remove registers and your good to go...
  // The first register starts at address
  VELOCIDADE_VAL,  //4x1
  STATUS_VAL,
  v1,
  v2,
  t1,
  t2,
  t3,
  t4,
  t5,
  InicRec,
  vf,
  Liga,
  EscVelG,
  EscVelO,
  LeiVelG,
  LeiVelO,
  LimVelMax,
  VelLidabits,
  VelEscbits,
  gP,
  gD,
  gI,
  teste,
  HOLDING_REGS_SIZE  // leave this one
  // total number of registers for function 3 and 16 share the same register array
  // i.e. the same address space
};

unsigned int holdingRegs[HOLDING_REGS_SIZE];  // function 3 and 16 register array
////////////////////////////////////////////////////////////


////////////////////////////////////
//      Configuração inicial
///////////////////////////////////
void setup() {
  //configura serial modbus
  //Serial.begin(9600);
  modbus_configure(9600, 1, 2, HOLDING_REGS_SIZE, 0);
  //modbus_configure(&Serial, 9600, SERIAL_8N1, 1, 2, HOLDING_REGS_SIZE, holdingRegs);
//  modbus_update_comms(9600, SERIAL_8N1, 1);

  //configura pinagens
  pinMode(11, INPUT);
  pinMode(6, OUTPUT);
  pinMode(9,INPUT);
  pinMode(8,INPUT);
  pinMode(3,INPUT);  
  pinMode(1,OUTPUT);  
  pinMode(0,INPUT);

  //Configura Timer do loop de controle da velocidade
  Timer1.initialize(50000);       // inicializar timer com período de 0,05 segundo
  Timer1.attachInterrupt(timer);  // anexar função a ser excutada a cada período

  //atualiza variaveis com valores da EEPROM
  ev1 = EEPROM.read(0);
  holdingRegs[v1] = ev1;

  ev2 = EEPROM.read(1);
  ev2 = ev2 << 8;
  ev2 = ev2 | EEPROM.read(2);
  holdingRegs[v2] = ev2;

  et1 = EEPROM.read(3) / 1000;
  holdingRegs[t1] = et1;

  et2 = EEPROM.read(4) / 1000;
  holdingRegs[t2] = et2;

  et3 = EEPROM.read(5) / 1000;
  holdingRegs[t3] = et3;

  et4 = EEPROM.read(6) / 1000;
  holdingRegs[t4] = et4;

  et5 = EEPROM.read(7) / 1000;
  holdingRegs[t5] = et5;

  evf = EEPROM.read(8) / 1000;
  holdingRegs[vf] = evf;

  eEVG = EEPROM.read(9);
  holdingRegs[EscVelG] = eEVG;
  
  eEVO = EEPROM.read(10);
  holdingRegs[EscVelO] = eEVO;

  eLVG = EEPROM.read(11);
  holdingRegs[LeiVelG] = eLVG;

  eLVO = -50 + EEPROM.read(12);
  holdingRegs[LeiVelO] = EEPROM.read(12);

  eLMV = EEPROM.read(13);
  holdingRegs[LimVelMax] = eLMV;

  egP = EEPROM.read(14);
  holdingRegs[gP] = egP;

  egD = EEPROM.read(15);
  holdingRegs[gD] = egD;

  egI = EEPROM.read(16);
  holdingRegs[gI] = egI;


  fBT1=0;
  statBT1=0;
  fBT2=0;
  statBT2=0;
}


/////////////////////////////////////
//  Loop Principal
/////////////////////////////////////
void loop() {
  
  //Botoes
  if(digitalRead(9)==0){
    delay(50);
    if(digitalRead(9)==0){
      if(holdingRegs[Liga] == 1){
        holdingRegs[Liga] = 0;
      }
      else holdingRegs[Liga] = 1;

      while(digitalRead(9)==0);
      delay(500);
    }
  }

  if(digitalRead(8)==0){
    delay(50);
    if(digitalRead(8)==0){
      if(holdingRegs[InicRec] == 1){
        holdingRegs[InicRec] = 0;
      }
      else holdingRegs[InicRec] = 1;

      while(digitalRead(8)==0);
      delay(500);
    }
  }
    
  //holdingRegs[STATUS_VAL] = holdingRegs[STATUS_VAL] + 1;
  //holdingRegs[VELOCIDADE_VAL] = holdingRegs[VELOCIDADE_VAL] + 1;
  //delay(500);
  //atualiza modbus
  modbus_update(holdingRegs);

  //faz 500 leituras do sinal de velocidade, equivalente a 50ms
  contVel = 0;
  for (int i = 0; i < 500; i++) {
    contVel = contVel + analogRead(A0);
  }
  auxvellida = contVel / 500;

  //testa se houve alteração de parâmetros e salva na EEPROM
  if (ev1 != holdingRegs[v1]) {
    ev1 = holdingRegs[v1];
    EEPROM.write(0, ev1);
  }

  if (ev2 != holdingRegs[v2]) {
    ev2 = holdingRegs[v2];
    auxEEPROM = ev2;
    auxEEPROM = auxEEPROM >> 8;
    EEPROM.write(1, auxEEPROM);
    auxEEPROM = ev2;
    auxEEPROM = auxEEPROM & 0xff;
    EEPROM.write(2, auxEEPROM);
  }

  if (et1*100 != holdingRegs[t1]) {
    et1 = holdingRegs[t1] / 100;
    EEPROM.write(3, et1);
  }

  if (et2*100 != holdingRegs[t2]) {
    et2 = holdingRegs[t2] / 100;
    EEPROM.write(4, et2);
  }

  if (et3*100 != holdingRegs[t3]) {
    et3 = holdingRegs[t3] / 100;
    EEPROM.write(5, et3);
  }

  if (et4*100 != holdingRegs[t4]) {
    et4 = holdingRegs[t4]/100;
    EEPROM.write(6, et4);
  }

  if (et5*100 != holdingRegs[t5]) {
    et5 = holdingRegs[t5]/100;
    EEPROM.write(7, et5);
  }

  if (evf != holdingRegs[vf]) {
    evf = holdingRegs[vf];
    EEPROM.write(8, evf);
  }

  if (eEVG != holdingRegs[EscVelG]) {
    eEVG = holdingRegs[EscVelG];
    EEPROM.write(9, eEVG);
  }

  if (eEVO != holdingRegs[EscVelO]) {
    eEVO = holdingRegs[EscVelO];
    EEPROM.write(10, eEVO);
  }

  if (eLVG != holdingRegs[LeiVelG]) {
    eLVG = holdingRegs[LeiVelG];
    EEPROM.write(11, eLVG);
  }

  if (eLVO != -50 + holdingRegs[LeiVelO]) {
    eLVO = -50 + holdingRegs[LeiVelO];
    EEPROM.write(12, holdingRegs[LeiVelO]);
  }

  if (eLMV != holdingRegs[LimVelMax]) {
    eLMV = holdingRegs[LimVelMax];
    EEPROM.write(13, eLMV);
  }

  if (egP != holdingRegs[gP]) {
    egP = holdingRegs[gP];
    EEPROM.write(14, egP);
  }

  if (egD != holdingRegs[gD]) {
    egD = holdingRegs[gD];
    EEPROM.write(15, egD);
  }

  if (egI != holdingRegs[gI]) {
    egI = holdingRegs[gI];
    EEPROM.write(16, egI);
  }
}


///////////////////////////////////////////////////////
// Loop Timer controle velocidade - itera a cada 50ms
///////////////////////////////////////////////////////
void timer() {
  //atualiza velocidade lida em bits
  holdingRegs[VelLidabits] = auxvellida;

  // atualiza velocidade em rpm
  auxvelbits = auxvellida * eLVG;
  auxvelbits = auxvelbits / 100;
  auxvelbits2 = eLVO;
  auxvelbits = auxvelbits + auxvelbits2;
  if ((holdingRegs[Liga] == 0 && holdingRegs[InicRec] == 0) || auxvellida < 15)
    holdingRegs[VELOCIDADE_VAL] = 0;
  else holdingRegs[VELOCIDADE_VAL] = auxvelbits;  // atualiza velocidade em rpm

  //PID
  //if (holdingRegs[Liga] != 0 || holdingRegs[InicRec] != 0) {
  //  erroD2 = erroD1;
  //  erroD1 = auxvel - holdingRegs[VELOCIDADE_VAL];
  //  erroD1 = (erroD1 + erroD2) / 2;

  //  erroP = auxvel - holdingRegs[VELOCIDADE_VAL];
    //holdingRegs[teste] = erroP;

  //  erroI10 = erroI9, erroI9 = erroI8, erroI8 = erroI7, erroI7 = erroI6, erroI6 = erroI5;
  //  erroI5 = erroI4, erroI4 = erroI3, erroI3 = erroI2, erroI2 = erroI1, erroI1 = erroP;
  //  erroI = erroI1 + erroI2 + erroI3 + erroI4 + erroI5 + erroI6 + erroI7 + erroI8 + erroI9 + erroI10;

  //  ajusteP = (erroP * egP) / 100;
  //  ajusteD = (((erroD1 + erroD2) / 2) * egD) / 100;
  //  ajusteI = (erroI * egI) / 100;

  //  ajuste1 = ajuste1 + ajusteP + ajusteD + ajusteI;
  //  ajuste2 = ajusteP + ajusteD + ajusteI;
  //  holdingRegs[teste] = erroI;
  //}


  if (holdingRegs[InicRec] == 1)  //Receita
  {
    if (cont == 0) {
      auxvel = 0;
      auxacel1 = holdingRegs[v1];
      auxacel2 = et1 * 20;
      a1 = auxacel1 / auxacel2;

      auxacel1 = holdingRegs[v2] - holdingRegs[v1];
      auxacel2 = (et3 - et2) * 20;
      a2 = auxacel1 / auxacel2;

      auxacel1 = holdingRegs[v2];
      auxacel2 = (et5 - et4) * 20;
      a3 = auxacel1 / auxacel2;

      erroD1 = 0, erroD2 = 0, erroI1 = 0, erroI2 = 0, erroI3 = 0, erroI4 = 0;
      erroI5 = 0, erroI6 = 0, erroI7 = 0, erroI8 = 0, erroI9 = 0, erroI10 = 0;
    }

    if (cont < et1 * 20) {
      cont++;
      auxvel = auxvel + a1;  // + ajuste2;
    } else if (cont < et2 * 20) {
      cont++;
    } else if (cont < et3 * 20) {
      cont++;
      auxvel = auxvel + a2;  // + ajuste2;
    } else if (cont < et4 * 20) {
      cont++;
    } else if (cont < et5 * 20) {
      cont++;
      auxvel = auxvel - a3;  // + ajuste2;
    } else {
      auxvel = 0;
      holdingRegs[Liga] = 0;
      holdingRegs[InicRec] = 0;
      cont = 0;
    }
  }
  
  else if (holdingRegs[Liga] == 1)  //é-SpiPrn
  {
    cont = 0;
    auxvel = holdingRegs[vf];  //+ajuste1;
  }

  else  //Tudo desligado
  {
    cont = 0;
    auxvel = 0;
    ajuste1 = 0;
    ajuste2 = 0;
  }

  //escreve a velocidade em auxvel
  auxvelbits = auxvel * eEVG;
  auxvelbits = auxvelbits / 100;
  auxvelbits2 = eEVO;
  auxvelbits = auxvelbits + auxvelbits2;
  

  if (auxvel == 0) {
    analogWrite(6, 0);
    holdingRegs[VelEscbits] = 0;
  }

  else if (auxvelbits > holdingRegs[LimVelMax]) {
    analogWrite(6, holdingRegs[LimVelMax]);
    holdingRegs[VelEscbits] = holdingRegs[LimVelMax];
  } else {
    analogWrite(6, auxvelbits);
    holdingRegs[VelEscbits] = auxvelbits;
  }
}
