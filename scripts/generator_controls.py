"""Open, embedded EMTDC controls: simplified GAST, AVR and load experiments."""
import xml.etree.ElementTree as ET
import re
from controller import definition as dc_definition

def component(name,title,subtitle,params,inputs,outputs,code,idbase):
    d=dc_definition();d.set('name',name);d.set('id',str(idbase))
    d.find('./paramlist/param').set('value',subtitle)
    f=d.find('form');f.clear();f.attrib.update(name=title,w='650',h='750',splitter='60',commentlines='4')
    for category,items,kind in [('Adjustable parameters',params,'Constant'),('Measured inputs',inputs,'Variable')]:
        cat=ET.SubElement(f,'category',name=category,visible='true');ET.SubElement(cat,'cond')
        for key,item in items.items():
            value,desc=item if isinstance(item,tuple) else (item,key)
            p=ET.SubElement(cat,'parameter',type='Real',name=key,desc=desc,content_type=kind,min='-1E+308',max='1E+308',unit='',group='',helpmode='Append',intent='Input',dim='1',animate='false')
            ET.SubElement(p,'value').text=str(value);ET.SubElement(p,'cond',type='Enable');ET.SubElement(p,'help')
    cat=ET.SubElement(f,'category',name='Named outputs',visible='true');ET.SubElement(cat,'cond')
    for key,value in outputs.items():
        p=ET.SubElement(cat,'parameter',type='Text',name=key,desc=key,group='',helpmode='Append',allowemptystr='false')
        ET.SubElement(p,'value').text=value;ET.SubElement(p,'cond',type='Enable');ET.SubElement(p,'help');ET.SubElement(p,'regex');ET.SubElement(p,'error_msg')
    script=d.find('script');script.clear()
    code=re.sub(r'^#LOCAL REAL (.+)$',lambda m:'\n'.join('#LOCAL REAL '+v for v in m[1].split()),code,flags=re.M)
    for i,key in enumerate(outputs):code=re.sub(r'\$'+key+r'\b','GX'+str(i),code)
    prefix=''.join(f'#LOCAL REAL GX{i}\n' for i in range(len(outputs)))
    suffix=''.join(f'#OUTPUT REAL {key} {{GX{i}}}\n' for i,key in enumerate(outputs))
    ET.SubElement(script,'segment',name='Dsdyn',id=str(idbase+1),classid='CoreSegment').text=prefix+code+suffix
    texts=d.find('svg').findall('text');texts[0].text=title;texts[1].text=subtitle
    return d

def gast():
    return component('GasTurbineGAST','GAS TURBINE - GAST','Fuel valve | Turbine | Temperature limit | Speed governor',
        {'R':(.05,'Speed droop [pu]'),'T1':(.15,'Fuel valve time constant [s]'),'T2':(.30,'Turbine power time constant [s]'),
         'T3':(3.,'Exhaust-temperature surrogate lag [s]'),'AT':(.8,'Ambient-temperature power limit [pu on machine MVA]'),
         'KT':(2.,'Temperature limiter gain'),'Vmax':(1.,'Maximum fuel valve [pu]'),'Vmin':(.02,'Minimum fuel valve [pu]'),
         'Rate':(1.,'Valve movement rate [pu/s]'),'KiSpeed':(.5,'Secondary frequency integral gain [1/s]'),
         'Dturb':(0.,'Turbine speed damping [pu]'),'Fbase':(60.,'Electrical frequency base [Hz]'),
         'RPM':(3600.,'Mechanical shaft base speed [rpm]'),'Release':(1.2,'Rotor release time [s]')},
        {'Speed':'Shaft_speed_rad_s','Mass1Deviation':'Shaft_dw1_rad_s','Tinit':'MM_Tm0_pu'},
        {'Tm':'Gas_Tm_pu','Pgas':'Gas_power_pu','Fuel':'Fuel_valve_pu','Temp':'Exhaust_surrogate_pu',
         'Limit':'Gas_limit','Freq':'Generator_Hz','Pref':'Gas_reference_pu'},r'''#STORAGE REAL:4
#LOCAL INTEGER K
#LOCAL REAL WPU WMPU ERR REF THL CMD DVAL POW
      K=NSTORF
      NSTORF=NSTORF+4
      WPU=$Speed/(6.283185307179586*$Fbase)
      WMPU=1.0+$Mass1Deviation/(6.283185307179586*$RPM/60.0)
      ERR=1.0-WPU
      IF(TIME.LT.$Release) THEN
        STORF(K)=MAX($Vmin,MIN($Vmax,$Tinit))
        STORF(K+1)=STORF(K)
        STORF(K+2)=STORF(K)
        STORF(K+3)=STORF(K)
      ELSE
        STORF(K+3)=MAX($Vmin,MIN($AT,STORF(K+3)+$KiSpeed*ERR*DELT))
        REF=STORF(K+3)+ERR/MAX($R,0.001)
        THL=$AT+$KT*($AT-STORF(K+2))
        CMD=MAX($Vmin,MIN($Vmax,MIN(REF,THL)))
        DVAL=(CMD-STORF(K))/MAX($T1,DELT)
        STORF(K)=STORF(K)+DELT*MAX(-$Rate,MIN($Rate,DVAL))
        STORF(K+1)=STORF(K+1)+DELT/MAX($T2,DELT)*(STORF(K)-STORF(K+1))
        STORF(K+2)=STORF(K+2)+DELT/MAX($T3,DELT)*(STORF(K+1)-STORF(K+2))
      ENDIF
      POW=STORF(K+1)-$Dturb*(WPU-1.0)
      $Tm=POW/MAX(0.5,WMPU)
      $Pgas=POW
      $Fuel=STORF(K)
      $Temp=STORF(K+2)
      $Pref=STORF(K+3)
      $Limit=0.0
      IF(STORF(K).GE.$Vmax-0.0001) $Limit=1.0
      IF(STORF(K+2).GE.$AT) $Limit=1.0
      $Freq=WPU*$Fbase
''',190030001)

def avr():
    return component('GeneratorAVR','GENERATOR AVR','Voltage PI | Field limits | Initialization tracking',
        {'Vref':(1.,'Generator terminal voltage reference [pu]'),'Kp':(8.,'Voltage proportional gain'),
         'Ki':(12.,'Voltage integral gain [1/s]'),'Te':(.03,'Field response lag [s]'),
         'Emin':(0.,'Minimum field voltage [pu]'),'Emax':(5.,'Maximum field voltage [pu]'),'Start':(.3,'Source to machine transition [s]')},
        {'Vt':'Generator_Vt_pu','Einit':'Generator_Ef0_pu'},
        {'Ef':'Generator_Ef_pu','Limit':'AVR_limit'},r'''#STORAGE REAL:2
#LOCAL INTEGER K
#LOCAL REAL ERR RAW CMD
      K=NSTORF
      NSTORF=NSTORF+2
      ERR=$Vref-$Vt
      IF(TIME.LT.$Start) THEN
        STORF(K)=$Einit-$Kp*ERR
        STORF(K+1)=$Einit
      ELSE
        RAW=STORF(K)+$Kp*ERR
        CMD=MAX($Emin,MIN($Emax,RAW))
        STORF(K)=STORF(K)+DELT*($Ki*ERR+10.0*(CMD-RAW))
        STORF(K+1)=STORF(K+1)+DELT/MAX($Te,DELT)*(CMD-STORF(K+1))
      ENDIF
      $Ef=MAX($Emin,MIN($Emax,STORF(K+1)))
      $Limit=0.0
      IF($Ef.GE.$Emax-0.0001.OR.$Ef.LE.$Emin+0.0001) $Limit=1.0
''',190040001)

def experiment():
    return component('TorsionExperiment','TORSIONAL LOAD EXPERIMENT','0 profile | 1 constant | 2 pulse | 3 chirp | 4 sine',
        {'Mode':(1.,'0 original load profile; 1 constant; 2 pulse-ringdown; 3 chirp; 4 sine'),
         'Pbase':(4.,'Mean load [MW]'),'Amplitude':(.5,'Load perturbation [MW]'),
         'Start':(5.,'Perturbation start [s]'),'Duration':(20.,'Chirp/sine duration [s]'),
         'PulseWidth':(.025,'Load pulse width [s]'),'Fstart':(5.,'Chirp initial frequency [Hz]'),
         'Fend':(30.,'Chirp final frequency [Hz]'),'Fsine':(10.61087357,'Single sine frequency [Hz]'),
         'Tmachine':(.3,'Source to machine switch [s]'),'Trelease':(1.2,'Rotor release [s]')},
        {},{'Demand':'P_experiment_MW','ModeOut':'ExcitationMode','Fexc':'Excitation_Hz','Machine':'Machine_enabled','Release':'Rotor_released'},r'''#LOCAL REAL T D PH E
      T=TIME-$Start
      D=0.0
      $Fexc=0.0
      IF($Mode.GT.1.5.AND.$Mode.LT.2.5) THEN
        IF(T.GE.0.0.AND.T.LT.$PulseWidth) D=$Amplitude
      ENDIF
      IF($Mode.GT.2.5.AND.$Mode.LT.3.5) THEN
        IF(T.GE.0.0.AND.T.LT.$Duration) THEN
          PH=6.283185307179586*($Fstart*T+0.5*($Fend-$Fstart)*T*T/MAX($Duration,0.001))
          E=MIN(1.0,MIN(T,MAX(0.0,$Duration-T))/0.10)
          D=$Amplitude*E*SIN(PH)
          $Fexc=$Fstart+($Fend-$Fstart)*T/MAX($Duration,0.001)
        ENDIF
      ENDIF
      IF($Mode.GT.3.5) THEN
        IF(T.GE.0.0.AND.T.LT.$Duration) THEN
          E=MIN(1.0,MIN(T,MAX(0.0,$Duration-T))/0.10)
          D=$Amplitude*E*SIN(6.283185307179586*$Fsine*T)
          $Fexc=$Fsine
        ENDIF
      ENDIF
      $Demand=MAX(0.1,$Pbase+D)
      $ModeOut=$Mode
      $Machine=0.0
      $Release=0.0
      IF(TIME.GE.$Tmachine) $Machine=1.0
      IF(TIME.GE.$Trelease) $Release=1.0
''',190050001)

def modified_dc():
    d=dc_definition()
    cat=next(c for c in d.find('form').findall('category') if c.get('name')=='Measured inputs')
    for name,value in [('ExperimentModeIn','ExcitationMode'),('ExperimentDemand','P_experiment_MW')]:
        p=ET.SubElement(cat,'parameter',type='Real',name=name,desc=name,content_type='Variable',min='-1E+308',max='1E+308',unit='',group='',helpmode='Append',intent='Input',dim='1',animate='false')
        ET.SubElement(p,'value').text=value;ET.SubElement(p,'cond',type='Enable');ET.SubElement(p,'help')
    segment=d.find('script/segment')
    segment.text=segment.text.replace('      DV=($Pmax-$Pmin)',
        '      IF($ExperimentModeIn.GT.0.5) TARGET=$ExperimentDemand\n      DV=($Pmax-$Pmin)')
    return d

def shaft_observer():
    return component('ShaftObserver','SHAFT RELATIVE SPEEDS','Relative motion separates torsion from common rotor speed',{},
        {'W1':'Shaft_dw1_rad_s','W2':'Shaft_dw2_rad_s','W3':'Shaft_dw3_rad_s'},
        {'R12':'Shaft_rel12_rad_s','R23':'Shaft_rel23_rad_s'},
        '      $R12=$W1-$W2\n      $R23=$W2-$W3\n',190060001)
