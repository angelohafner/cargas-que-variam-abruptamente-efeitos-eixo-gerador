"""Export real PSCAD-rendered bitmaps while final chirp results are loaded."""
from pathlib import Path
import time,json
from PIL import ImageGrab
from pscad_session import get_app
ROOT=Path(__file__).resolve().parents[1]
def main():
    a=get_app();out=ROOT/'figures/generator/native';out.mkdir(parents=True,exist_ok=True);exports=[]
    for suffix,short in [('Sem_BESS','sem_bess'),('Com_BESS','com_bess')]:
        name='DataCenter_Gerador_'+suffix;p=a.project(name);p.focus();c=p.canvas('Main')
        for frame in c.find_all('GraphFrame'):frame.zoom_x_extents()
        for kind,box in [('gerador',(0,330,160,470)),('graficos',(160,328,355,460)),('rede',(0,0,295,153))]:
            c.select_components(*box)
            if not c.copy():raise RuntimeError('Native PSCAD copy failed')
            bitmap=None
            for attempt in range(8):
                time.sleep(.4)
                try:bitmap=ImageGrab.grabclipboard()
                except OSError:continue
                if hasattr(bitmap,'save'):break
            if not hasattr(bitmap,'save'):raise RuntimeError('Clipboard has no native bitmap')
            path=out/(short+'_'+kind+'.png');bitmap.save(path)
            exports.append(dict(project=name,file=path.relative_to(ROOT).as_posix(),size_px=list(bitmap.size),source='PSCAD native rendered clipboard'))
            print(path,bitmap.size,flush=True)
        c.clear_selection()
    (ROOT/'validation/generator/native_exports.json').write_text(json.dumps(exports,indent=2))
if __name__=='__main__':main()
