"""Add gas-generator cases by copying, never changing the original ideal cases."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,shutil,xml.etree.ElementTree as ET,math
from pscad_session import get_app
from generator_controls import gast,avr,experiment,modified_dc
ROOT=Path(__file__).resolve().parents[1]
NAMES=['DataCenter_Gerador_Sem_BESS','DataCenter_Gerador_Com_BESS']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build(app,bess):
    old='DataCenter_Com_BESS' if bess else 'DataCenter_Sem_BESS'
    name=NAMES[int(bess)];path=ROOT/'pscad'/(name+'.pscx')
    if any(x['name']==name for x in app.projects()):app.project(name).unload()
    if path.exists():
        dest=ROOT/'history'/('generator_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
        dest.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest/path.name)
    source=(ROOT/'pscad'/(old+'.pscx')).read_text(encoding='utf-8')
    root=ET.fromstring(source.replace(old,name))
    if bess:
        # Reserve the lower-left page for the new generation plant. The original
        # audit wires occupy y=338..394 and must move with their labels/PGbs.
        for node in root.iter():
            if node.tag in ['User','Wire'] and 310*18<=float(node.get('y','0'))<=400*18 and float(node.get('x','0'))<150*18:
                node.set('x',str(int(float(node.get('x')))+520*18))
    parent=next(x for x in root.iter() if any(d.tag=='Definition' and d.get('name')=='DC_Controller' for d in x))
    previous=next(d for d in parent if d.tag=='Definition' and d.get('name')=='DC_Controller')
    parent.remove(previous);parent.append(modified_dc())
    for d in [gast(),avr(),experiment()]:parent.append(d)
    ET.ElementTree(root).write(path,encoding='utf-8')
    app.load(str(path));p=app.project(name);c=p.canvas('Main')
    p.parameters(time_duration=30,time_step=10,sample_step=100,
                 output_filename=name+'.out',description='Gas turbine / native 3-mass shaft | '+('BESS 5 MW' if bess else 'without BESS'))
    def comp(n,x,y,**kw):return c.create_component('master:'+n,x,y,**kw)
    def xy(o,key):v=o.ports()[key];return v.x,v.y
    def wire(*pts):return c.create_wire(*pts)
    def sig(o,key,s):comp('datalabel',*xy(o,key),Name=s)
    source=c.find('master:source_3');entry=xy(source,'N');source.delete()
    # A real 13.8 kV machine and its step-up transformer replace the ideal source.
    machine=comp('sync_machine',30,380,Name='GT_Generator_20MVA',MM=0,Nqaxw=2,CfRa=1,
        MVA='20 [MVA]',VolTyp=1,VbaseLL='13.8 [kV]',IorMVA=1,OMO='376.991118430775 [rad/s]',
        Iscl=0,D=0,H=2.5,Ra=.002,Xp=.12,Xd=1.8,Xd_=.30,Xd__=.20,Tdo_=5,Tdo__=.035,
        Xq=1.7,Xq_=.55,Xq__=.22,Tqo_=.7,Tqo__=.05,
        View=1,Term=1,Iexc=1,Igov=1,Ospd=0,Neut=0,RNeut=.01,
        machsw='Machine_enabled',Enab='Rotor_released',InExc='InitEx',InGov='InitGv',
        VT=1.,Pheta=0.,P0='4.05 [MW]',Q0='1.0 [MVAR]',Trmpv=.02,
        POut='Generator_P_pu',QOut='Generator_Q_pu',Tesmt='Generator_Te0_pu',
        Lang='Generator_angle_rad',Theta='Rotor_angle_rad')
    print(name,'machine ports',list(machine.ports()),flush=True)
    meter=comp('multimeter',50,380,MeasP=1,MeasQ=1,RMS=1,IRMS=1,
        P='Pgen_MW',Q='Qgen_Mvar',Vrms='Vgen_kV',Crms='Igen_kA',TS='.001 [s]',BaseV=1,BaseA=1,S=1,Freq=60)
    tr=comp('xfmr-3p2w',75,380,Name='GT_StepUp_20MVA',Tmva='20 [MVA]',V1='13.8 [kV]',V2='69 [kV]',f=60,
            YD1=0,YD2=0,Xl=.06,CuL=.005,NLL=0,Enab=0)
    wire(xy(machine,'NS'),xy(meter,'A'));wire(xy(meter,'B'),xy(tr,'N1'))
    wire(xy(tr,'N2'),(94,380),(94,331),(5,331),(5,22),entry)
    for key in ['G1','G2']:
        pt=xy(tr,key);wire(pt,(pt[0],pt[1]+6));comp('ground',pt[0],pt[1]+6)
    mm=comp('multimass2',70,350,Name='GT_Coupling_Generator',SQC=0,N=3,GenID=3,MVA=20,F=60,RPM=3600,spdini=1,
        Units=12,Enab='Rotor_released',tmi=1,tei=1,H1=1.5,H2=1,H3=2.5,K12=40,K23=50,
        TF1=1,TF2=0,TF3=0,TorP=0,sigma=0,SD1=0,SD2=0,SD3=0,MD12=1,MD23=1,
        T12='Shaft_T12_pu',T23='Shaft_T23_pu',P1='Shaft_theta1_rad',P2='Shaft_theta2_rad',P3='Shaft_theta3_rad',
        W1='Shaft_dw1_rad_s',W2='Shaft_dw2_rad_s',W3='Shaft_dw3_rad_s',Wbas='Shaft_wbase_rad_s')
    for port,signal in [('telect','Generator_Te_pu'),('tmeco','Generator_Tm_out_pu'),('conspd','Shaft_speed_rad_s'),
                        ('efo','Generator_Ef0_pu'),('efldn','Generator_Ef_pu'),('tmech','Gas_Tm_pu'),
                        ('Tmstd','Generator_Tm0_pu'),('mvt','Generator_Vt_pu')]:sig(machine,port,signal)
    for port,signal in [('tmpu','Gas_Tm_pu'),('tepu','Generator_Te_pu'),('spd','Shaft_speed_rad_s'),
                        ('tmpui','MM_Tm0_pu'),('tepui','Generator_Te0_pu')]:sig(mm,port,signal)
    c.create_component(name+':GeneratorAVR',30,414)
    c.create_component(name+':GasTurbineGAST',76,414)
    c.create_component(name+':TorsionExperiment',125,414)
    c.create_annotation(60,337,'GAS TURBINE + THREE-MASS SHAFT','M1: gas turbine + compressor, net torque | M2: coupling equivalent | M3: generator')
    c.create_annotation(58,362,'SHAFT DATA - DIDACTIC','H=[1.5,1.0,2.5] s | K=[40,50] pu/rad | 3600 rpm | mass #3 = generator')
    c.create_annotation(57,395,'13.8 kV GENERATOR TO 69 kV BUS','20 MVA | real step-up transformer x=0.06 pu | no infinite bus after 0.3 s')
    c.create_annotation(76,429,'PARAMETERS','Double-click native shaft for H/K/damping; experiment block for load mode/frequency/amplitude.')
    c.create_annotation(120,438,'GAST IS A SIMPLIFIED NET-POWER MODEL','Compressor power is lumped in net turbine output. M2 is an equivalent coupling inertia, not a separate compressor torque model.')
    channels={g.parameters()['Name']:g for g in c.find_all('master:pgb')}
    additions={'Generator_Hz':'Hz','Pgen_MW':'MW','Qgen_Mvar':'Mvar','Vgen_kV':'kV','Igen_kA':'kA',
        'Generator_Te_pu':'pu','Gas_Tm_pu':'pu','Generator_Ef_pu':'pu','Generator_Vt_pu':'pu',
        'Shaft_T12_pu':'pu','Shaft_T23_pu':'pu','Shaft_dw1_rad_s':'rad/s','Shaft_dw2_rad_s':'rad/s','Shaft_dw3_rad_s':'rad/s',
        'Shaft_theta1_rad':'rad','Shaft_theta2_rad':'rad','Shaft_theta3_rad':'rad','Fuel_valve_pu':'pu',
        'Gas_power_pu':'pu','Exhaust_surrogate_pu':'pu','Gas_limit':'','AVR_limit':'','Rotor_released':'',
        'Machine_enabled':'','P_experiment_MW':'MW','Excitation_Hz':'Hz','ExcitationMode':'',
        'Shaft_speed_rad_s':'rad/s','MM_Tm0_pu':'pu','Generator_Te0_pu':'pu'}
    for i,(signal,unit) in enumerate(additions.items()):
        x=370+(i//15)*45;y=180+(i%15)*7
        comp('datalabel',x,y,Name=signal);wire((x,y),(x+15,y))
        channels[signal]=comp('pgb',x+15,y,Name=signal,UseSignalName=0,Units=unit,Group='GeneratorTorsion',Min=-10,Max=10)
    plots=[('Generator frequency - Hz',['Generator_Hz'],(55,65),2),
        ('Shaft speeds - rad/s deviation',['Shaft_dw1_rad_s','Shaft_dw2_rad_s','Shaft_dw3_rad_s'],(-5,5),2),
        ('Shaft torques - pu',['Shaft_T12_pu','Shaft_T23_pu','Generator_Te_pu'],(-.2,.8),.2),
        ('Gas turbine and excitation',['Gas_Tm_pu','Fuel_valve_pu','Generator_Ef_pu'],(0,3),.5)]
    for i,(title,signals,(lo,hi),grid) in enumerate(plots):
        f=c.create_graph_frame(165+(i%2)*95,330+(i//2)*42);f.size=(90,38)
        f.parameters(title=title,xtitle='Time [s]',xmin=0,xmax=30);f.auto_sizing=True
        g,_=f.add_overlay_graph(*(channels[s] for s in signals))
        g.parameters(title=title,manualscale=True,ymin=lo,ymax=hi,gridvalue=grid)
    p.save();print(name,'created',flush=True)
    return path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',choices=['base','bess','both'],default='both');args=ap.parse_args()
    original={p.name:sha(p) for p in (ROOT/'pscad').glob('DataCenter_*.pscx') if '_Gerador_' not in p.name}
    protected=ROOT/'validation/generator';protected.mkdir(parents=True,exist_ok=True)
    record=protected/'original_hashes.json'
    if record.exists():assert json.loads(record.read_text())==original,'Original cases changed since extension began'
    else:record.write_text(json.dumps(original,indent=2))
    a=get_app();a.flags(silence=True)
    for b in ([False,True] if args.case=='both' else [args.case=='bess']):build(a,b)
    from polish_generator_cases import main as polish
    polish([NAMES[int(b)] for b in ([False,True] if args.case=='both' else [args.case=='bess'])])
    assert original=={n:sha(ROOT/'pscad'/n) for n in original}

if __name__=='__main__':main()
