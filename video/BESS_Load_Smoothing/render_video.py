"""Render Manim chapters, concatenate losslessly and collect review frames."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import time
import shutil
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
SCENES=['Applications','ParallelBuffer','PowerComparison','ShaftMechanism',
        'MeasuredBenefits']
TITLES=['Abrupt loads','Parallel BESS','Power comparison','Shaft twist',
        'Measured benefits']


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))


def render(preview=False,only=None,assemble_only=False):
    mode='preview' if preview else 'final'
    media=HERE/'media'/mode
    logs=HERE/'evidence'/'logs';logs.mkdir(parents=True,exist_ok=True)
    selected=[] if assemble_only else (SCENES if not only else only)
    start=time.time()
    for scene in selected:
        log=logs/(mode+'_'+scene+'.log')
        cmd=[sys.executable,'-m','manim','render','--renderer','cairo','--resolution',
             '854,480' if preview else '1920,1080','--fps','15' if preview else '30',
             '--media_dir',str(media),'--verbosity','WARNING','--progress_bar','none',
             '--disable_caching','scenes.py',scene]
        print('Rendering',mode,scene,flush=True)
        with log.open('w',encoding='utf-8') as f:
            p=subprocess.run(cmd,cwd=HERE,stdout=f,stderr=subprocess.STDOUT)
        if p.returncode:
            print(log.read_text(encoding='utf-8')[-9000:],flush=True)
            raise SystemExit(p.returncode)
        print('Finished',scene,'elapsed',round(time.time()-start,1),'s',flush=True)
    if only:
        return
    folder=media/'videos'/'scenes'/('480p15' if preview else '1080p30')
    clips=[folder/(s+'.mp4') for s in SCENES]
    for p in clips:
        if not p.exists():raise FileNotFoundError(p)
    playlist=media/'concat.txt'
    playlist.write_text(''.join("file '"+str(p).replace('\\','/')+"'\n" for p in clips),encoding='utf-8')
    timeline=[];cursor=0.
    for title,scene,p in zip(TITLES,SCENES,clips):
        duration=float(probe(p)['format']['duration'])
        timeline.append(dict(scene=scene,title=title,start_s=cursor,end_s=cursor+duration))
        cursor+=duration
    meta=media/'chapters.ffmeta'
    text=';FFMETADATA1\ntitle=BESS and Abrupt Loads\ncomment=Existing PSCAD results; Manim and Schemdraw; English; LaTeX mathematics.\n'
    for ch in timeline:
        text+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(ch['start_s']*1000)}\nEND={round(ch['end_s']*1000)}\ntitle={ch['title']}\n"
    meta.write_text(text,encoding='utf-8')
    out=HERE/'output';out.mkdir(exist_ok=True)
    target=out/('BESS_Abrupt_Loads_Preview.mp4' if preview else 'BESS_Abrupt_Loads_1080p.mp4')
    subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(playlist),'-i',str(meta),
                    '-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(target)],check=True)
    if not preview:
        shutil.copy2(folder/'ShaftMechanism.mp4',out/'Shaft_Twist_Comparison_1080p.mp4')
    (HERE/'evidence'/(mode+'_timeline.json')).write_text(json.dumps(timeline,indent=2))
    (HERE/'evidence'/(mode+'_probe.json')).write_text(json.dumps(probe(target),indent=2))
    extract_review(target,timeline,mode)
    print('VIDEO READY',target,'duration',cursor,flush=True)


def extract_review(video,timeline,mode):
    out=HERE/'evidence'/('frames_'+mode);out.mkdir(exist_ok=True)
    samples=[]
    for c in timeline:
        for fraction in [.45,.8]:
            t=c['start_s']+fraction*(c['end_s']-c['start_s'])
            name=c['scene']+('_a' if fraction==.45 else '_b')+'.png'
            subprocess.run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1',str(out/name)],check=True)
            samples.append((out/name,t))
    thumbs=[]
    for p,t in samples:
        im=Image.open(p).convert('RGB');im.thumbnail((640,360))
        canvas=Image.new('RGB',(640,390),'#142035');canvas.paste(im,(0,0))
        ImageDraw.Draw(canvas).text((12,368),f'{t:.1f} s | {p.stem}',fill='white')
        thumbs.append(canvas)
    sheet=Image.new('RGB',(1280,390*((len(thumbs)+1)//2)),'#0B1425')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%2)*640,(i//2)*390))
    sheet.save(HERE/'evidence'/('contact_sheet_'+mode+'.jpg'),quality=94)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--only',nargs='+',choices=SCENES)
    p.add_argument('--assemble-only',action='store_true',help='Assemble already-rendered chapters and refresh review frames')
    a=p.parse_args();render(a.preview,a.only,a.assemble_only)
