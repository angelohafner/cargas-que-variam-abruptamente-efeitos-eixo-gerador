"""Capture PSCAD native diagrams and curves for the delivered scaled runs."""
from pathlib import Path
import time,json
from PIL import ImageGrab
from pscad_session import get_app
from scale_models_250_500 import NAMES
ROOT=Path(__file__).resolve().parents[1]
def main():
    app=get_app();out=ROOT/'figures/scale_250_500/native';out.mkdir(parents=True,exist_ok=True);exports=[]
    for name in NAMES:
        p=app.project(name);p.focus();c=p.canvas('Main')
        for f in c.find_all('GraphFrame'):f.zoom_x_extents()
        regions=[('network',(0,0,295 if 'Com_BESS' in name else 145,153)),('electrical_graphs',(160,180,355,313))]
        if 'Gerador' in name:regions += [('generator',(0,330,160,470)),('mechanical_graphs',(160,328,355,460))]
        for kind,box in regions:
            c.select_components(*box)
            if not c.copy():raise RuntimeError('Native bitmap copy failed')
            bitmap=None
            for _ in range(8):
                time.sleep(.4)
                try:bitmap=ImageGrab.grabclipboard()
                except OSError:continue
                if hasattr(bitmap,'save'):break
            if not hasattr(bitmap,'save'):raise RuntimeError('Native bitmap unavailable')
            path=out/(name+'_'+kind+'.png');bitmap.save(path)
            exports.append(dict(project=name,kind=kind,file=path.relative_to(ROOT).as_posix(),size_px=list(bitmap.size),source='PSCAD native rendered clipboard'))
            print(path.name,bitmap.size,flush=True)
        c.clear_selection()
    (ROOT/'validation/scale_250_500/native_exports.json').write_text(json.dumps(exports,indent=2))
if __name__=='__main__':main()
