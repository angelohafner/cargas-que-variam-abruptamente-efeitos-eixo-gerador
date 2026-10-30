"""Scale four native PSCAD projects from an immutable archived baseline."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,math,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/scale_250_500'
NAMES=['DataCenter_Sem_BESS','DataCenter_Com_BESS','DataCenter_Gerador_Sem_BESS','DataCenter_Gerador_Com_BESS']
FACTOR=50.;HV=230.;PCC=34.5;GEN=20.;BASE=1000.

def impedance_scale(v0,v1,s0,s1):return (v1/v0)**2/(s1/s0)
def load_level(p):return 250+(p-4)*(250/6)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def number(v):return float(str(v).split()[0])
def params(u):return {x.get('name'):x.get('value') for x in u.findall('paramlist/param')}
def setp(u,**values):
    pl=u.find('paramlist')
    for key,value in values.items():
        nodes=u.findall(f"paramlist/param[@name='{key}']")
        if not nodes:nodes=[ET.SubElement(pl,'param',name=key)]
        for node in nodes:node.set('value',str(value))
def mul(u,key,factor):
    p=params(u);s=p[key];parts=s.split(maxsplit=1);setp(u,**{key:f'{number(s)*factor:.15g}'+(' '+parts[1] if len(parts)>1 else '')})
def baseline():
    OUT.mkdir(parents=True,exist_ok=True);record=OUT/'baseline.json'
    if record.exists():
        r=json.loads(record.read_text());folder=ROOT/r['folder']
        for n,h in r['project_sha256'].items():assert sha(folder/'pscad'/n)==h
        return folder
    folder=ROOT/'history'/('before_250_500MW_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    for sub in ['pscad','scripts','tests']: (folder/sub).mkdir(parents=True)
    for name in NAMES:shutil.copy2(ROOT/'pscad'/(name+'.pscx'),folder/'pscad'/(name+'.pscx'))
    for p in (ROOT/'pscad').glob('*.pswx'):shutil.copy2(p,folder/'pscad'/p.name)
    for sub,pattern in [('scripts','*.py'),('tests','test_*.py')]:
        for p in (ROOT/sub).glob(pattern):shutil.copy2(p,folder/sub/p.name)
    for p in ROOT.glob('README*.md'):shutil.copy2(p,folder/p.name)
    record.write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),folder=folder.relative_to(ROOT).as_posix(),
        project_sha256={n+'.pscx':sha(folder/'pscad'/(n+'.pscx')) for n in NAMES},
        old_validation='validation/generator/validation.json',old_packages='delivery/generator_package_verification.json'),indent=2))
    return folder

def transform(source,dest):
    tree=ET.parse(source);root=tree.getroot();isgen='_Gerador_' in source.stem
    profiles={key:load_level(old) for key,old in [('Pmin',4),('Pmax',10),('Pmid',7),('Pstep1',9),('Pstep2',5)]}
    control={**profiles,'RampMax':25,'PmaxBess':250,'RecoveryGain':1,'RecoveryMax':25,
             'Lf':.00004/FACTOR,'Rf':.0005/FACTOR,'KpI':.04/FACTOR,'KiI':20/FACTOR,'Imax':6.2*FACTOR,'TestPower':150,'TestMode':0}
    for u in root.iter('User'):
        kind=u.get('defn','');p=params(u);name=p.get('Name','')
        if kind.endswith(':DC_Controller'):setp(u,**control)
        elif kind.endswith(':TorsionExperiment'):setp(u,Mode=0,Pbase=375,Amplitude=25,Start=5,Duration=20)
        elif kind=='master:source_3':setp(u,Vm='230 [kV]',Name='Grid230kV')
        elif name in ['Grid_R','Grid_L']:
            mul(u,'R' if name=='Grid_R' else 'L',impedance_scale(69,HV,20,BASE))
        elif name in ['Feeder_R','Feeder_L']:
            mul(u,'R' if name=='Feeder_R' else 'L',impedance_scale(13.8,PCC,20,BASE))
        elif kind=='master:xfmr-3p2w':
            if name=='Grid_20MVA':setp(u,Name='Grid_1000MVA',Tmva='1000 [MVA]',V1='230 [kV]',V2='34.5 [kV]')
            elif name=='GT_StepUp_20MVA':setp(u,Name='GT_StepUp_1000MVA',Tmva='1000 [MVA]',V1='20 [kV]',V2='230 [kV]')
            elif name=='BESS_6p25MVA':setp(u,Name='BESS_Aggregate_312p5MVA',Tmva='312.5 [MVA]',V1='34.5 [kV]')
        elif kind=='master:fixed_load':setp(u,VBO=f'{PCC/math.sqrt(3):.15g} [kV]')
        elif kind=='master:battery':setp(u,Name='BESS_50x2p5MWh',Qrated=f'{125/1.5:.15g} [kA*hr]',SOCint=50)
        elif kind=='master:resistor' and (name.startswith('Rf_') or name in ['Precharge_R','DC_reference_only']):mul(u,'R',1/FACTOR)
        elif kind=='master:inductor' and name.startswith('Lf_'):mul(u,'L',1/FACTOR)
        elif kind=='master:capacitor' and name=='DC_cap':mul(u,'C',FACTOR)
        elif kind in ['master:peswitch','master:breaker1']:
            for k in ['RON','ROFF']:
                if k in p:mul(u,k,1/FACTOR)
        elif kind=='master:sync_machine':setp(u,Name='GT_Equivalent_1000MVA',MVA='1000 [MVA]',VbaseLL='20 [kV]',P0='255 [MW]',Q0='60 [MVAR]')
        elif kind=='master:multimass2':setp(u,MVA=1000)
    # Defaults are consistent with saved controller instances.
    for d in root.iter('Definition'):
        if d.get('name')=='DC_Controller':
            for par in d.findall('.//form/category/parameter'):
                if par.get('name') in control:par.find('value').text=str(control[par.get('name')])
        if d.get('name')=='TorsionExperiment':
            defaults={'Mode':0,'Pbase':375,'Amplitude':25}
            for par in d.findall('.//form/category/parameter'):
                if par.get('name') in defaults:par.find('value').text=str(defaults[par.get('name')])
        if d.get('name')=='EnergyAudit':
            segment=d.find('script/segment');code=segment.text
            replacements={'PFILT=0.0005*I2':'PFILT=0.00001*I2','PTF=0.00038088*I2':'PTF=0.0000076176*I2',
                '0.0045*$IBat':'0.00009*$IBat','0.5*0.02*$VDc*$VDc':'0.5*1.0*$VDc*$VDc','0.5*0.0000521238*I2':'0.5*0.000001042476*I2'}
            for old,new in replacements.items():
                if old not in code:raise ValueError('Unexpected audit source: '+old)
                code=code.replace(old,new)
            segment.text=code
    replacements={'69/13.8 kV':'230/34.5 kV','deterministic 4-10 MW':'intermittent 250-500 MW',
        'Scc 1000 MVA; X/R=10 | 20 MVA':'Equivalent Scc 50000 MVA; X/R=10 | 1000 MVA',
        'Bateria nativa | 1.5 kV x 1.6667 kAh = 2.5 MWh nominal | 6 IGBTs + 6 diodos':'50 parallel equivalent modules | 250 MW / 125 MWh | aggregate currents',
        '6.25 MVA 13.8/0.69 kV Yg-Yg | L=40 uH/phase':'312.5 MVA 34.5/0.69 kV | equivalent L=0.8 uH/phase',
        '13.8 kV GENERATOR TO 69 kV BUS':'20 kV GENERATOR TO 230 kV BUS',
        '20 MVA | real step-up transformer':'1000 MVA equivalent | real step-up transformer',
        'Gas turbine / native 3-mass shaft | BESS 5 MW':'250-500 MW | gas turbine / native 3-mass shaft | BESS 250 MW',
        'Gas turbine / native 3-mass shaft | without BESS':'250-500 MW | gas turbine / native 3-mass shaft | without BESS',
        'Data center 4-10 MW':'Data center 250-500 MW','BESS 5 MW / 2.5 MWh':'BESS equivalent 250 MW / 125 MWh'}
    for e in root.iter():
        if e.tag in ['param','text']:
            if e.text:
                for old,new in replacements.items():e.text=e.text.replace(old,new)
            if 'value' in e.attrib:
                value=e.get('value')
                for old,new in replacements.items():value=value.replace(old,new)
                if isgen:value=value.replace('Equivalent Scc 50000 MVA; X/R=10 | 1000 MVA','Series network impedance, X/R=10 | 1000 MVA')
                e.set('value',value)
    limits={'Potencias - MW':(-300,600,100),'Controle BESS - MW':(-300,300,100),
            'Tensao barramento - kV':(0,38,5)}
    graphids={}
    for g in root.iter('Graph'):
        p=params(g);title=p.get('title')
        if title in limits:
            lo,hi,grid=limits[title];setp(g,ymin=lo,ymax=hi,gridvalue=grid);graphids[g.get('id')]=(lo,hi)
    for s in root.iter('Settings'):
        if s.get('classid')=='OverlayGraphSettings' and s.get('link') in graphids:
            lo,hi=graphids[s.get('link')];setp(s,ymin=lo,ymax=hi)
    tree.write(dest,encoding='utf-8')

def main():
    from pscad_session import get_app
    folder=baseline();a=get_app();a.flags(silence=True)
    for name in NAMES:
        if any(p['name']==name for p in a.projects()):a.project(name).unload()
        dest=ROOT/'pscad'/(name+'.pscx');transform(folder/'pscad'/dest.name,dest)
        a.load(str(dest));p=a.project(name);p.parameters(time_duration=30,time_step=10,sample_step=100);p.save()
        print('SCALED',name,flush=True)
    a.save_workspace(str(ROOT/'pscad/DataCenter_Quatro_Casos.pswx'),save_projects=False)
    wp=ROOT/'pscad/DataCenter_Quatro_Casos.pswx';t=ET.parse(wp)
    for node in t.findall('./projects/project'):node.set('filepath','./'+node.get('name')+'.pscx')
    t.write(wp,encoding='utf-8')
    (OUT/'design.json').write_text(json.dumps(dict(power_base_MVA=BASE,HV_kV=HV,PCC_kV=PCC,generator_kV=GEN,
        BESS_MW=250,BESS_MWh=125,parallel_modules=50,battery_kAh=125/1.5,
        source_Scc_MVA=50000,feeder_R_ohm=.02*impedance_scale(13.8,PCC,20,BASE),
        canonical_names=NAMES,baseline_folder=folder.relative_to(ROOT).as_posix()),indent=2))
if __name__=='__main__':main()
