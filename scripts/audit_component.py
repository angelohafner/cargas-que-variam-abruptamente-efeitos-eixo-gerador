"""Independent measured energy accounting embedded in the PSCAD case."""
import xml.etree.ElementTree as ET
from controller import definition

def audit_definition():
    d=definition();d.set('name','EnergyAudit');d.set('id','190020001')
    d.find('paramlist/param').set('value','Independent terminal power, losses, coulomb and energy audit')
    f=d.find('form');f.clear();f.attrib.update(name='Measured energy audit',w='600',h='700',splitter='60',commentlines='4')
    ins={'VB':'Vbat_kV','IBat':'Ibat_kA','VDc':'Vdc_kV','PB':'Pbess_MW',
         'ILA':'ILA_kA','ILB':'ILB_kA','ILC':'ILC_kA','VLA':'VLA_kV','VLB':'VLB_kV','VLC':'VLC_kV'}
    for ph in 'ABC':
        for side in ['H','L']:
            for dev in [ph+side,'D'+ph+side]:
                ins['IC'+dev]='I_'+dev;ins['VC'+dev]='V_'+dev
    outs=['Pbat_MW','Ploss_pre_MW','Ploss_switch_MW','Ploss_filter_MW','Ploss_transformer_MW',
          'P_LV_MW','Ecap_MJ','Eind_MJ','Ebat_MJ','Ebess_MJ','Eloss_MJ','Echem_MJ','Charge_kAs','Edis_MJ','Echg_MJ']
    cat=ET.SubElement(f,'category',name='Measured inputs',visible='true');ET.SubElement(cat,'cond')
    for name,value in ins.items():
        p=ET.SubElement(cat,'parameter',type='Real',name=name,desc=name,content_type='Variable',min='-1E+308',max='1E+308',unit='',group='',helpmode='Append',intent='Input',dim='1',animate='false')
        ET.SubElement(p,'value').text=value;ET.SubElement(p,'cond',type='Enable');ET.SubElement(p,'help')
    cat=ET.SubElement(f,'category',name='Named outputs',visible='true');ET.SubElement(cat,'cond')
    for name in outs:
        p=ET.SubElement(cat,'parameter',type='Text',name=name,desc=name,group='',helpmode='Append',allowemptystr='false')
        ET.SubElement(p,'value').text=name;ET.SubElement(p,'cond',type='Enable');ET.SubElement(p,'help');ET.SubElement(p,'regex');ET.SubElement(p,'error_msg')
    sw='+'.join('$IC'+dev+'*$VC'+dev for ph in 'ABC' for side in ['H','L'] for dev in [ph+side,'D'+ph+side])
    code='''#STORAGE REAL:7
#LOCAL INTEGER K
#LOCAL REAL PBAT
#LOCAL REAL PPRE
#LOCAL REAL PSW
#LOCAL REAL I2
#LOCAL REAL PFILT
#LOCAL REAL PTF
      K=NSTORF
      NSTORF=NSTORF+7
      IF(TIME.LT.DELT*0.5) STORF(K:K+6)=0.0
      PBAT=$VB*$IBat
      PPRE=($VB-$VDc)*$IBat
      I2=$ILA*$ILA+$ILB*$ILB+$ILC*$ILC
      PFILT=0.0005*I2
      PTF=0.00038088*I2
      PSW='''+sw+'''
      STORF(K)=STORF(K)+PBAT*DELT
      STORF(K+1)=STORF(K+1)+$PB*DELT
      STORF(K+2)=STORF(K+2)+(PPRE+PSW+PFILT+PTF)*DELT
      STORF(K+3)=STORF(K+3)+($VB+0.0045*$IBat)*$IBat*DELT
      STORF(K+4)=STORF(K+4)+$IBat*DELT
      STORF(K+5)=STORF(K+5)+MAX(PBAT,0.0)*DELT
      STORF(K+6)=STORF(K+6)+MAX(-PBAT,0.0)*DELT
#OUTPUT REAL Pbat_MW {PBAT}
#OUTPUT REAL Ploss_pre_MW {PPRE}
#OUTPUT REAL Ploss_switch_MW {PSW}
#OUTPUT REAL Ploss_filter_MW {PFILT}
#OUTPUT REAL Ploss_transformer_MW {PTF}
#OUTPUT REAL P_LV_MW {$VLA*$ILA+$VLB*$ILB+$VLC*$ILC}
#OUTPUT REAL Ecap_MJ {0.5*0.02*$VDc*$VDc}
#OUTPUT REAL Eind_MJ {0.5*0.0000521238*I2}
#OUTPUT REAL Ebat_MJ {STORF(K)}
#OUTPUT REAL Ebess_MJ {STORF(K+1)}
#OUTPUT REAL Eloss_MJ {STORF(K+2)}
#OUTPUT REAL Echem_MJ {STORF(K+3)}
#OUTPUT REAL Charge_kAs {STORF(K+4)}
#OUTPUT REAL Edis_MJ {STORF(K+5)}
#OUTPUT REAL Echg_MJ {STORF(K+6)}
'''
    # PSCAD '~' continuation avoids long generated Fortran lines.
    code=code.replace('PSW='+sw,'PSW='+sw.replace('+','+~\n~'))
    script=d.find('script');script.clear();ET.SubElement(script,'segment',name='Dsdyn',id='190020002',classid='CoreSegment').text=code
    svg=d.find('svg')
    svg.findall('text')[0].text='MEASURED ENERGY AUDIT'
    svg.findall('text')[1].text='Terminal energy | Losses | Capacitor | SOC'
    return d,outs

def enrich(p):
    c=p.canvas('Main')
    for ph in 'ABC':
        for side in ['H','L']:
            for dev in [ph+side,'D'+ph+side]:
                c.find('master:peswitch',Name=dev).parameters(I='I_'+dev,V='V_'+dev)
    d,outs=audit_definition()
    p.create_definition(d)
    c.create_component(p.name+':EnergyAudit',70,320)
    for i,sn in enumerate(outs):
        x=10+(i//7)*46;y=338+(i%7)*7
        c.create_component('master:datalabel',x,y,Name=sn);c.create_wire((x,y),(x+18,y))
        c.create_component('master:pgb',x+18,y,Name=sn,UseSignalName=0,Units='MJ' if '_MJ' in sn else ('MW' if '_MW' in sn else 'kA.s'),Group='EnergyAudit')
    p.save()

if __name__=='__main__':
    import mhi.pscad
    a=mhi.pscad.connect(port=62172);enrich(a.project('DataCenter_Com_BESS'))
