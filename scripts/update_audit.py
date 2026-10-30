from pathlib import Path
import xml.etree.ElementTree as ET
from audit_component import audit_definition
from pscad_session import get_app
ROOT=Path(__file__).resolve().parents[1]
a=get_app();p=a.project('DataCenter_Com_BESS');p.save();path=Path(p.filename);p.unload()
tree=ET.parse(path);root=tree.getroot();defs=root.find('definitions')
old=next(d for d in defs if d.get('name')=='EnergyAudit');new,outs=audit_definition();new.set('id',old.get('id'));defs.remove(old);defs.append(new)
for u in root.iter('User'):
    if not u.get('defn','').endswith(':EnergyAudit'):continue
    pl=u.find('paramlist');existing={p.get('name') for p in pl}
    for key in outs:
        if key not in existing:ET.SubElement(pl,'param',name=key,value=key)
tree.write(path,encoding='utf-8');a.load(str(path));p=a.project('DataCenter_Com_BESS');c=p.canvas('Main')
for i,sn in enumerate(['Edis_MJ','Echg_MJ']):
    if c.find_all('master:pgb',Name=sn):continue
    x,y=56,387+i*7
    c.create_component('master:datalabel',x,y,Name=sn);c.create_wire((x,y),(x+18,y));c.create_component('master:pgb',x+18,y,Name=sn,UseSignalName=0,Units='MJ',Group='EnergyAudit')
p.save()
