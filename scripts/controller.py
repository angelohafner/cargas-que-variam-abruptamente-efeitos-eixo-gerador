"""Editable PSCAD component: deterministic dispatch, protection and dq VSC control.

All electrical devices are native Master Library components. This definition
embeds readable EMTDC Fortran; no external object/library is required.
"""
import xml.etree.ElementTree as ET
import re

PARAMETERS = {
 'BessEnabled':(1,'Enable BESS (0/1)'), 'Pmin':(4,'Low load [MW]'),
 'Pmax':(10,'High load [MW]'), 'Pmid':(7,'Final load [MW]'),
 'Pstep1':(9,'First step load [MW]'), 'Pstep2':(5,'Second step load [MW]'),
 'T1':(2,'First step time [s]'), 'T2':(4,'Second step time [s]'),
 'T3':(6,'First pulse train start [s]'), 'T4':(10,'High plateau start [s]'),
 'T5':(15,'Low plateau start [s]'), 'T6':(20,'Second pulse train start [s]'),
 'T7':(25,'Final plateau start [s]'),
 'Period1':(.4,'First pulse train period [s]'), 'Period2':(.5,'Second pulse train period [s]'),
 'Duty1':(.5,'First pulse duty fraction'), 'Duty2':(.5,'Second pulse duty fraction'),
 'Transition':(.02,'Load transition [s]'), 'TauSmooth':(2,'Smoothing time [s]'),
 'RampMax':(.5,'Grid reference ramp [MW/s]'), 'PmaxBess':(5,'BESS power limit [MW]'),
 'SOCmin':(20,'Minimum SOC [%]'), 'SOCmax':(80,'Maximum SOC [%]'),
 'SOCref':(50,'SOC target [%]'), 'SOChyst':(.05,'SOC hysteresis [% points]'),
 'RecoveryGain':(.02,'SOC recovery gain [MW/percent]'),
 'RecoveryMax':(.5,'SOC recovery maximum [MW]'),
 'RecoveryTau':(20,'SOC recovery time [s]'), 'RecoveryDead':(1,'SOC deadband [% points]'),
 'Fgrid':(60,'Network frequency [Hz]'), 'Fsw':(2000,'PWM frequency [Hz]'),
 'Lf':(.00004,'Coupling inductance [H]'), 'Rf':(.0005,'Coupling resistance [ohm]'),
 'KpI':(.04,'Current PI proportional gain [ohm]'), 'KiI':(20,'Current PI integral gain [ohm/s]'),
 'Imax':(6.2,'dq peak current limit [kA]'), 'Mmax':(.98,'Maximum modulation'),
 'KpPLL':(50,'PLL proportional [1/s]'), 'KiPLL':(900,'PLL integral [1/s2]'),
 'TestMode':(0,'0 nominal; 1 SOC low; 2 SOC high; 3 power reversal'),
 'TestPower':(3,'Protection test power [MW]'),
}
INPUTS={'LoadMeasured':'Pload_MW','SOCMeasured':'SOC_pct',
        'VdcMeasured':'Vdc_kV','Va':'VLA_kV','Vb':'VLB_kV','Vc':'VLC_kV',
        'Ia':'ILA_kA','Ib':'ILB_kA','Ic':'ILC_kA'}
OUTPUTS={'Pcommand':'Pload_command_MW','LoadScale':'Load_scale','GridRef':'Pgrid_ref_MW',
         'BessRaw':'Pbess_raw_MW','BessRef':'Pbess_ref_MW','Recovery':'Precovery_MW',
         'SOCblock':'SOC_block','PowerLimit':'Power_limit','CurrentLimit':'Current_limit',
         'ModLimit':'Modulation_limit','ModA':'Mod_A','ModB':'Mod_B','ModC':'Mod_C',
         'GAH':'Gate_AH','GAL':'Gate_AL','GBH':'Gate_BH','GBL':'Gate_BL','GCH':'Gate_CH','GCL':'Gate_CL',
         'Precharge':'Precharge_open','Theta':'PLL_theta','Frequency':'PLL_Hz',
         'IdMeas':'Id_kA','IqMeas':'Iq_kA','IdRef':'Id_ref_kA',
         'Vd':'Vd_kV','Vq':'Vq_kV','Carrier':'Carrier','Enable':'BESS_ramp'}

CODE = r'''#STORAGE REAL:20
#LOCAL INTEGER K
#LOCAL REAL PI W TARGET DV REC REF RAW PCMD AL BE VM TH VD VQ
#LOCAL REAL IA IB ID IQ IDR IQR ED EQ UD UQ UA UB UC MODMAX FAC CAR EN
#LOCAL REAL XP XQ EP EQP UDL UQL ANG
      K=NSTORF
      NSTORF=NSTORF+20
      PI=3.141592653589793
      W=2.0*PI*$Fgrid
      IF (TIME.LT.DELT*0.5) THEN
        STORF(K:K+19)=0.0
        STORF(K)=$Pmin
        STORF(K+1)=$Pmin
        STORF(K+2)=$Pmin
      ENDIF
! Physical load demand, same in both cases. States: load, LPF, ramp.
      TARGET=$Pmin
      IF(TIME.GE.$T1.AND.TIME.LT.$T2) TARGET=$Pstep1
      IF(TIME.GE.$T2.AND.TIME.LT.$T3) TARGET=$Pstep2
      IF(TIME.GE.$T3.AND.TIME.LT.$T4) THEN
        IF(MODULO(TIME-$T3,$Period1).LT.$Period1*$Duty1) TARGET=$Pmax
      ENDIF
      IF(TIME.GE.$T4.AND.TIME.LT.$T5) TARGET=$Pmax
      IF(TIME.GE.$T6.AND.TIME.LT.$T7) THEN
        IF(MODULO(TIME-$T6,$Period2).LT.$Period2*$Duty2) TARGET=$Pmax
      ENDIF
      IF(TIME.GE.$T7) TARGET=$Pmid
      DV=($Pmax-$Pmin)*DELT/MAX($Transition,DELT)
      STORF(K)=STORF(K)+MAX(-DV,MIN(DV,TARGET-STORF(K)))
      $Pcommand=STORF(K)
      $LoadScale=STORF(K)/3.0
      STORF(K+1)=STORF(K+1)+DELT/MAX($TauSmooth,DELT)*($LoadMeasured-STORF(K+1))
      REC=0.0
      IF(ABS($SOCref-$SOCMeasured).GT.$RecoveryDead) THEN
        REC=MAX(-$RecoveryMax,MIN($RecoveryMax,$RecoveryGain*($SOCref-$SOCMeasured)))
      ENDIF
      STORF(K+3)=STORF(K+3)+DELT/MAX($RecoveryTau,DELT)*(REC-STORF(K+3))
      REF=STORF(K+1)+STORF(K+3)
      DV=$RampMax*DELT
      STORF(K+2)=STORF(K+2)+MAX(-DV,MIN(DV,REF-STORF(K+2)))
      IF(TIME.LT.0.5) THEN
        STORF(K+1)=$Pmin
        STORF(K+2)=$Pmin
      ENDIF
      $GridRef=STORF(K+2)
      $Recovery=STORF(K+3)
      RAW=$LoadMeasured-$GridRef
      IF($TestMode.GT.0.5.AND.TIME.GT.0.8) THEN
        IF($TestMode.LT.1.5) RAW=$TestPower
        IF($TestMode.GE.1.5.AND.$TestMode.LT.2.5) RAW=-$TestPower
        IF($TestMode.GE.2.5) RAW=$TestPower
        IF(TIME.GT.3.0) RAW=-RAW
      ENDIF
      $BessRaw=RAW
      PCMD=MAX(-$PmaxBess,MIN($PmaxBess,RAW))
      $PowerLimit=0.0
      IF(ABS(RAW-PCMD).GT.0.0001) $PowerLimit=1.0
! Predictive guard band .002 percentage points covers controller current decay.
      IF($SOCMeasured.LE.$SOCmin+0.002) STORF(K+4)=1.0
      IF($SOCMeasured.GE.$SOCmin+$SOChyst) STORF(K+4)=0.0
      IF($SOCMeasured.GE.$SOCmax-0.002) STORF(K+5)=1.0
      IF($SOCMeasured.LE.$SOCmax-$SOChyst) STORF(K+5)=0.0
      $SOCblock=0.0
      IF(STORF(K+4).GT.0.5.AND.PCMD.GT.-0.02*$PmaxBess) THEN
! Small permitted charging bias supplies VSC idle losses at the lower limit.
        PCMD=-0.02*$PmaxBess
        $SOCblock=1.0
      ENDIF
      IF(STORF(K+5).GT.0.5.AND.PCMD.LT.0.02*$PmaxBess) THEN
        PCMD=0.02*$PmaxBess
        $SOCblock=-1.0
      ENDIF
      EN=MAX(0.0,MIN(1.0,(TIME-0.5)/0.1))*$BessEnabled
      $BessRef=PCMD*EN
      $Enable=EN
      $Precharge=1.0
      IF(TIME.GT.0.15) $Precharge=0.0
! SRF PLL, amplitude invariant Clarke/Park. Voltage kV, current kA.
      AL=(2.0*$Va-$Vb-$Vc)/3.0
      BE=($Vb-$Vc)/SQRT(3.0)
      VM=MAX(0.1,SQRT(AL*AL+BE*BE))
      TH=STORF(K+6)
      IF(TIME.LT.0.2) TH=ATAN2(BE,AL)
      VD=AL*COS(TH)+BE*SIN(TH)
      VQ=-AL*SIN(TH)+BE*COS(TH)
      EP=MAX(-1.0,MIN(1.0,VQ/VM))
      STORF(K+7)=MAX(-20.0,MIN(20.0,STORF(K+7)+$KiPLL*EP*DELT))
      ANG=W+$KpPLL*EP+STORF(K+7)
      STORF(K+6)=MODULO(TH+ANG*DELT,2.0*PI)
      $Theta=TH
      $Frequency=ANG/(2.0*PI)
      $Vd=VD
      $Vq=VQ
      IA=(2.0*$Ia-$Ib-$Ic)/3.0
      IB=($Ib-$Ic)/SQRT(3.0)
      ID=IA*COS(TH)+IB*SIN(TH)
      IQ=-IA*SIN(TH)+IB*COS(TH)
      STORF(K+8)=STORF(K+8)+DELT/(0.0001+DELT)*(ID-STORF(K+8))
      STORF(K+9)=STORF(K+9)+DELT/(0.0001+DELT)*(IQ-STORF(K+9))
      ID=STORF(K+8)
      IQ=STORF(K+9)
      IDR=$BessRef/(1.5*MAX(0.35,VD))
      $CurrentLimit=0.0
      IF(ABS(IDR).GT.$Imax) $CurrentLimit=1.0
      IDR=MAX(-$Imax,MIN($Imax,IDR))
      IQR=0.0
      $IdMeas=ID
      $IqMeas=IQ
      $IdRef=IDR
      ED=IDR-ID
      EQ=IQR-IQ
      XP=STORF(K+10)
      XQ=STORF(K+11)
      UD=VD+$Rf*ID-W*$Lf*IQ+$KpI*ED+XP
      UQ=VQ+$Rf*IQ+W*$Lf*ID+$KpI*EQ+XQ
      UA=2.0*(UD*COS(TH)-UQ*SIN(TH))/MAX(0.3,$VdcMeasured)
      UB=2.0*(UD*COS(TH-2.0*PI/3.0)-UQ*SIN(TH-2.0*PI/3.0))/MAX(0.3,$VdcMeasured)
      UC=2.0*(UD*COS(TH+2.0*PI/3.0)-UQ*SIN(TH+2.0*PI/3.0))/MAX(0.3,$VdcMeasured)
      MODMAX=MAX(ABS(UA),ABS(UB),ABS(UC))
      FAC=MIN(1.0,$Mmax/MAX(0.0001,MODMAX))
      $ModLimit=0.0
      IF(FAC.LT.0.9999) $ModLimit=1.0
! Back-calculation anti-windup on voltage-vector saturation.
      STORF(K+10)=MAX(-0.4,MIN(0.4,XP+DELT*($KiI*ED+100.0*(FAC-1.0)*UD)))
      STORF(K+11)=MAX(-0.4,MIN(0.4,XQ+DELT*($KiI*EQ+100.0*(FAC-1.0)*UQ)))
      IF(TIME.LT.0.2) THEN
        STORF(K+10)=0.0
        STORF(K+11)=0.0
      ENDIF
      $ModA=UA*FAC
      $ModB=UB*FAC
      $ModC=UC*FAC
      CAR=1.0-4.0*ABS(MODULO(TIME*$Fsw,1.0)-0.5)
      $Carrier=CAR
      $GAH=0.0
      $GAL=0.0
      $GBH=0.0
      $GBL=0.0
      $GCH=0.0
      $GCL=0.0
      IF(TIME.GT.0.2.AND.$BessEnabled.GT.0.5) THEN
        IF($ModA.GE.CAR) $GAH=1.0
        IF($ModA.LT.CAR) $GAL=1.0
        IF($ModB.GE.CAR) $GBH=1.0
        IF($ModB.LT.CAR) $GBL=1.0
        IF($ModC.GE.CAR) $GCH=1.0
        IF($ModC.LT.CAR) $GCL=1.0
      ENDIF
'''

def definition():
    d=ET.Element('Definition',{'classid':'UserCmpDefn','name':'DC_Controller','url':'','view':'false','instances':'0','date':'0','crc':'0','id':'190010001'})
    pl=ET.SubElement(d,'paramlist'); ET.SubElement(pl,'param',name='Description',value='Data center dispatch, SOC protection, SRF PLL and dq current control')
    f=ET.SubElement(d,'form',name='Data center controls',w='600',h='700',splitter='60',commentlines='4')
    cat=ET.SubElement(f,'category',name='Adjustable controls',visible='true'); ET.SubElement(cat,'cond')
    for name,(value,desc) in PARAMETERS.items():
        strictly_positive=name in {'Transition','TauSmooth','RampMax','PmaxBess','RecoveryTau','Fgrid','Fsw','Lf','Imax','Period1','Period2'}
        maximum='100' if name in {'SOCmin','SOCmax','SOCref','SOChyst','RecoveryDead'} else ('1' if name in {'BessEnabled','Mmax','Duty1','Duty2'} else ('3' if name=='TestMode' else '1E+308'))
        p=ET.SubElement(cat,'parameter',type='Real',name=name,desc=desc,content_type='Constant',min='1E-9' if strictly_positive else '0',max=maximum,unit='',group='',helpmode='Append',intent='Input',dim='1',animate='false')
        ET.SubElement(p,'value').text=str(value); ET.SubElement(p,'cond',type='Enable'); ET.SubElement(p,'help')
    cat=ET.SubElement(f,'category',name='Measured inputs',visible='true'); ET.SubElement(cat,'cond')
    for name,value in INPUTS.items():
        p=ET.SubElement(cat,'parameter',type='Real',name=name,desc=name,content_type='Variable',min='-1E+308',max='1E+308',unit='',group='',helpmode='Append',intent='Input',dim='1',animate='false')
        ET.SubElement(p,'value').text=value; ET.SubElement(p,'cond',type='Enable'); ET.SubElement(p,'help')
    cat=ET.SubElement(f,'category',name='Named outputs',visible='true'); ET.SubElement(cat,'cond')
    for name,value in OUTPUTS.items():
        p=ET.SubElement(cat,'parameter',type='Text',name=name,desc=name,group='',helpmode='Append',allowemptystr='false')
        ET.SubElement(p,'value').text=value; ET.SubElement(p,'cond',type='Enable'); ET.SubElement(p,'help'); ET.SubElement(p,'regex'); ET.SubElement(p,'error_msg')
    svg=ET.SubElement(d,'svg',viewBox='-200 -100 200 100')
    ET.SubElement(svg,'rect',x='-180',y='-54',width='360',height='108',stroke='Black',**{'stroke-width':'1','fill-style':'Solid','fill-fg':'#e1f0f4'})
    ET.SubElement(svg,'text',x='0',y='-12',**{'font-size':'14','text-anchor':'middle','fill':'Black'}).text='DATA CENTER CONTROL'
    ET.SubElement(svg,'text',x='0',y='15',**{'font-size':'11','text-anchor':'middle','fill':'Black'}).text='Load | Smoothing | SOC | PLL | dq | PWM'
    script=ET.SubElement(d,'script')
    # Outputs through Text parameters use explicit #OUTPUT macros and local values.
    code=re.sub(r'^#LOCAL REAL (.+)$',lambda m:'\n'.join('#LOCAL REAL '+v for v in m[1].split()),CODE,flags=re.M)
    for i,name in enumerate(OUTPUTS):
        code=re.sub(r'\$'+name+r'\b', 'OUTX'+str(i), code)
    declarations=''.join(f'#LOCAL REAL OUTX{i}\n' for i in range(len(OUTPUTS)))
    outputs=''.join(f'#OUTPUT REAL {name} {{OUTX{i}}}\n' for i,name in enumerate(OUTPUTS))
    ET.SubElement(script,'segment',name='Dsdyn',id='190010002',classid='CoreSegment').text=declarations+code+outputs
    return d
