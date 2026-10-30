"""Add relative shaft-speed observations and persist all native graph ranges."""
from pathlib import Path
import xml.etree.ElementTree as ET
import copy
from pscad_session import get_app
from generator_controls import shaft_observer
from fix_graph_ranges import RANGES,GRIDS,apply
ROOT=Path(__file__).resolve().parents[1]
EXTRA={
 'Generator frequency - Hz':((55,65),2),
 'Shaft speeds - rad/s deviation':((-20,20),5),
 'Shaft torques - pu':((-.2,.8),.2),
 'Gas turbine and excitation':((0,3),.5),
 'Relative shaft speeds - torsional motion':((-.5,.5),.1)}

def prepare(a,name):
    p=a.project(name);c=p.canvas('Main')
    if not c.find_all(name+':ShaftObserver'):
        p.create_definition(shaft_observer());c.create_component(name+':ShaftObserver',76,455)
        ch=[]
        for i,s in enumerate(['Shaft_rel12_rad_s','Shaft_rel23_rad_s']):
            c.create_component('master:datalabel',465,180+7*i,Name=s)
            c.create_wire((465,180+7*i),(480,180+7*i))
            ch.append(c.create_component('master:pgb',480,180+7*i,Name=s,UseSignalName=0,Units='rad/s',Min=-.5,Max=.5,Group='GeneratorTorsion'))
        f=c.create_graph_frame(165,420);f.size=(90,38);f.auto_sizing=True
        title='Relative shaft speeds - torsional motion'
        f.parameters(title=title,xtitle='Time [s]',xmin=0,xmax=30)
        g,_=f.add_overlay_graph(*ch);g.parameters(title=title,manualscale=True,ymin=-.5,ymax=.5,gridvalue=.1)
    p.save()
    for title,(limits,grid) in EXTRA.items():RANGES[title]=limits;GRIDS[title]=grid
    path=apply(p)
    # New frames have no instance Settings until first displayed/run. Create
    # those overrides now, otherwise PSCAD initializes them at -1..1 s.
    tree=ET.parse(path);root=tree.getroot()
    template=next(s for s in root.iter('Settings') if s.get('classid')=='GraphFrameSettings')
    parent=next(e for e in root.iter() if template in list(e))
    links={s.get('link') for s in root.iter('Settings') if s.get('classid')=='GraphFrameSettings'}
    used={int(e.get('id')) for e in root.iter() if e.get('id','').isdigit()};newid=max(used)+1
    for frame in root.iter('Frame'):
        if frame.get('classid')=='GraphFrame' and frame.get('id') not in links:
            setting=copy.deepcopy(template);setting.set('id',str(newid));newid+=1;setting.set('link',frame.get('id'))
            parent.append(setting)
    tree.write(path,encoding='utf-8');a.load(str(path));a.wait_for_idle()
    print('Prepared observations and native axes:',name,flush=True)

if __name__=='__main__':
    a=get_app()
    for n in ['DataCenter_Gerador_Sem_BESS','DataCenter_Gerador_Com_BESS']:prepare(a,n)
