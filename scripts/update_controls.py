from pathlib import Path
import xml.etree.ElementTree as ET
import shutil,time
import mhi.pscad
from controller import definition,PARAMETERS
ROOT=Path(__file__).resolve().parents[1]
a=mhi.pscad.connect(port=62172)
for name in ['DataCenter_Sem_BESS','DataCenter_Com_BESS']:
    p=a.project(name)
    p.save()
    path=Path(p.filename)
    history=ROOT/'history'/('controls_'+time.strftime('%Y%m%d_%H%M%S'));history.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,history/path.name)
    p.unload()
    tree=ET.parse(path);root=tree.getroot();defs=root.find('definitions')
    old=next(d for d in defs if d.get('name')=='DC_Controller')
    new=definition();new.set('id',old.get('id'));defs.remove(old);defs.append(new)
    for u in root.iter('User'):
        if u.get('defn')!=name+':DC_Controller':continue
        pl=u.find('paramlist');existing={p.get('name') for p in pl}
        for key,(value,desc) in PARAMETERS.items():
            if key not in existing:ET.SubElement(pl,'param',name=key,value=str(value))
    tree.write(path,encoding='utf-8')
    a.load(str(path));a.project(name).save()
    print('UPDATED',name,flush=True)
