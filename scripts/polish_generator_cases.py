"""Refresh embedded gas model and make native signal labels legible."""
from pathlib import Path
from datetime import datetime
import shutil,xml.etree.ElementTree as ET
from pscad_session import get_app
from generator_controls import gast
from prepare_generator_views import prepare
ROOT=Path(__file__).resolve().parents[1]
def main(names=None):
    a=get_app();history=ROOT/'history'/('generator_review_'+datetime.now().strftime('%Y%m%d_%H%M%S'));history.mkdir(parents=True)
    for name in names or ['DataCenter_Gerador_Sem_BESS','DataCenter_Gerador_Com_BESS']:
        path=ROOT/'pscad'/(name+'.pscx');p=a.project(name);p.unload();shutil.copy2(path,history/path.name)
        tree=ET.parse(path);root=tree.getroot()
        old=next(d for d in root.iter('Definition') if d.get('name')=='GasTurbineGAST')
        parent=next(e for e in root.iter() if old in list(e));parent.remove(old);new=gast();parent.append(new)
        inst=next(u for u in root.iter('User') if u.get('defn')==name+':GasTurbineGAST')
        params=inst.find('paramlist')
        for key,value in [('RPM','3600'),('Mass1Deviation','Shaft_dw1_rad_s')]:
            node=params.find(f"param[@name='{key}']")
            if node is None:ET.SubElement(params,'param',name=key,value=value)
            else:node.set('value',value)
        tree.write(path,encoding='utf-8');a.load(str(path));p=a.project(name);c=p.canvas('Main')
        # Only relocate labels still directly on native ports (idempotent).
        specs=[('master:multimass2',{'tmpui':[(66,355),(50,355)],'tmpu':[(68,358),(50,358)],
               'tepu':[(70,361),(90,361)],'spd':[(72,358),(90,358)],'tepui':[(74,355),(90,355)]}),
               ('master:sync_machine',{'efo':[(26,374),(10,374)],'efldn':[(28,370),(10,370)],
               'mvt':[(32,366),(45,366)],'conspd':[(10,378)],'telect':[(10,380)],
               'tmeco':[(24,382),(24,384),(10,384)],'tmech':[(30,390),(45,390)],'Tmstd':[(32,387),(45,387)]})]
        labels={tuple(l.location):l for l in c.find_all('master:datalabel')}
        for component,ports in specs:
            obj=c.find(component)
            for key,route in ports.items():
                port=obj.ports()[key];start=(port.x,port.y)
                if start in labels:
                    label=labels[start];label.location=route[-1];c.create_wire(start,*route)
        p.save();prepare(a,name)
        print('Updated physical torque conversion, labels and views',name,flush=True)
if __name__=='__main__':main()
