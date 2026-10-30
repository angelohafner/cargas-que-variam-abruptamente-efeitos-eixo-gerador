"""Set readable saved axes for the nominal 30 s case in both native projects."""
from pscad_session import get_app
from pathlib import Path
import xml.etree.ElementTree as ET
import shutil,time

RANGES={'Potencias - MW':(-6,12),'SOC - percent':(49.5,50.5),
        'Tensao CC - kV':(0,1.7),'Tensao barramento - kV':(0,15),
        'Controle BESS - MW':(-6,6),'Protecoes':(-.2,1.2)}
GRIDS={'Potencias - MW':3,'SOC - percent':.2,'Tensao CC - kV':.2,
       'Tensao barramento - kV':3,'Controle BESS - MW':2,'Protecoes':.2}

def apply(p):
    # PSCAD stores both definition ranges and per-instance view overrides.
    # In 5.1 the graph API updated the former but left the latter at -2..2.
    # Update the observed native XML fields consistently, then reload.
    path=Path(p.filename);root_dir=Path(__file__).resolve().parents[1]
    backup=root_dir/'history'/('graph_ranges_'+time.strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup/path.name)
    p.unload()
    tree=ET.parse(path);root=tree.getroot();ranges={}
    for graph in root.iter('Graph'):
        if graph.get('classid')!='OverlayGraph':continue
        title=graph.find("./paramlist/param[@name='title']").get('value')
        lo,hi=RANGES[title];ranges[graph.get('id')]=(lo,hi)
        for param in graph.findall('./paramlist/param'):
            if param.get('name') in ['ymin','ymax','gridvalue']:
                param.set('value',str({'ymin':lo,'ymax':hi,'gridvalue':GRIDS[title]}[param.get('name')]))
    for frame in root.iter('Frame'):
        if frame.get('classid')=='GraphFrame':
            for param in frame.findall('./paramlist/param'):
                if param.get('name') in ['xmin','xmax']:param.set('value','0' if param.get('name')=='xmin' else '30')
    for setting in root.iter('Settings'):
        if setting.get('classid')=='OverlayGraphSettings' and setting.get('link') in ranges:
            lo,hi=ranges[setting.get('link')]
            for param in setting.findall('./paramlist/param'):
                if param.get('name') in ['ymin','ymax']:param.set('value',str(lo if param.get('name')=='ymin' else hi))
        if setting.get('classid')=='GraphFrameSettings':
            for param in setting.findall('./paramlist/param'):
                if param.get('name') in ['xmin','xmax']:param.set('value','0' if param.get('name')=='xmin' else '30')
    tree.write(path,encoding='utf-8')
    return path

if __name__=='__main__':
    a=get_app()
    for name in ['DataCenter_Sem_BESS','DataCenter_Com_BESS']:
        path=apply(a.project(name));a.load(str(path));a.wait_for_idle()
        print(name,'saved native definition and instance axes',flush=True)
