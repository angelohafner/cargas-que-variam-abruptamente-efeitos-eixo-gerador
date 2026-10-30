from pathlib import Path
import time,json
from PIL import ImageGrab
from pscad_session import get_app
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'figures/native';folder.mkdir(parents=True,exist_ok=True)
a=get_app();exports=[]
for name,short in [('DataCenter_Sem_BESS','sem_bess'),('DataCenter_Com_BESS','com_bess')]:
    p=a.project(name);p.focus();c=p.canvas('Main')
    regions=[('circuito',(0,0,295 if short=='com_bess' else 145,152 if short=='com_bess' else 110)),
             ('graficos',(160,180,355,313))]
    for kind,box in regions:
        c.select_components(*box)
        if not c.copy():raise RuntimeError('Native PSCAD copy failed')
        time.sleep(.5);bitmap=ImageGrab.grabclipboard()
        if not hasattr(bitmap,'save'):raise RuntimeError('Native clipboard bitmap unavailable')
        path=folder/(short+'_'+kind+'.png');bitmap.save(path)
        exports.append({'project':name,'kind':kind,'file':path.relative_to(ROOT).as_posix(),'size_px':list(bitmap.size),'source':'PSCAD native rendered clipboard'})
        print(path,bitmap.size,flush=True)
    c.clear_selection()
(ROOT/'validation/native_exports.json').write_text(json.dumps(exports,indent=2))
