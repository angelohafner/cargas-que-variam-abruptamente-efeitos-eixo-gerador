"""Fresh generator-case execution and source/output-bound evidence."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,shutil,re
from pscad_session import get_app
ROOT=Path(__file__).resolve().parents[1]

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def run(case='base',label='constant',duration=5,step=10,sample=100,mode=1,amplitude=.5,freq=10.61087357,
        start=5,forcing_duration=20,pbase=4,pulse_width=.025):
    name='DataCenter_Gerador_'+('Com_BESS' if case=='bess' else 'Sem_BESS')
    path=ROOT/'pscad'/(name+'.pscx');a=get_app();a.flags(silence=True)
    if not any(x['name']==name for x in a.projects()):a.load(str(path))
    p=a.project(name)
    if Path(p.filename).resolve()!=path.resolve():raise ValueError('Different project with the same name is open')
    p.parameters(time_duration=duration,time_step=step,sample_step=sample)
    c=p.canvas('Main');ex=c.find(name+':TorsionExperiment')
    ex.parameters(Mode=mode,Amplitude=amplitude,Fsine=freq,Start=start,Duration=forcing_duration,Pbase=pbase,PulseWidth=pulse_width)
    c.find(name+':DC_Controller').parameters(TestMode=0)
    p.save();source_hash=sha(path)
    dest=ROOT/'results/generator'/(label+'_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    dest.mkdir(parents=True,exist_ok=False)
    stamp=datetime.now(timezone.utc)
    print('RUN',name,dict(label=label,duration=duration,step=step,mode=mode),flush=True)
    p.run();messages=p.messages();errors=[str(m) for m in messages if m.status=='error']
    (dest/'messages.txt').write_text('\n'.join(map(str,messages)),encoding='utf-8')
    build=path.with_suffix('.gf81');inf=build/(name+'.inf')
    ids=[int(x) for x in re.findall(r'PGB\((\d+)\)',inf.read_text())] if inf.exists() else []
    outputs=([inf]+[build/f'{name}_{i:02d}.out' for i in range(1,(max(ids)+9)//10+1)]) if ids else []
    fresh=bool(outputs) and all(f.exists() and f.stat().st_mtime>=stamp.timestamp()-2 for f in outputs)
    for f in outputs:
        if f.exists():shutil.copy2(f,dest/f.name)
    for pattern in ['*.log','Main.f','Main.dta','*.map']:
        for f in build.glob(pattern):shutil.copy2(f,dest/f.name)
    shutil.copy2(path,dest/path.name)
    receipt=dict(start_utc=stamp.isoformat(),finish_utc=datetime.now(timezone.utc).isoformat(),pscad_version=a.version,
        compiler='GFortran 8.1 (64-bit)',duration_s=duration,time_step_us=step,sample_step_us=sample,
        project_sha256=source_hash,project_unchanged_during_run=sha(path)==source_hash,fresh_outputs=fresh,errors=errors,
        experiment=ex.parameters(),output_sha256={f.name:sha(dest/f.name) for f in outputs if (dest/f.name).exists()})
    (dest/'run_receipt.json').write_text(json.dumps(receipt,indent=2,default=str))
    print('RESULT',dest,'fresh',fresh,'errors',errors,flush=True)
    if errors or not fresh:raise RuntimeError('PSCAD run failed; see '+str(dest/'messages.txt'))
    return dest

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--case',choices=['base','bess'],default='base');ap.add_argument('--label',default='constant')
    for name,default in [('duration',5),('step',10),('sample',100),('mode',1),('amplitude',.5),('freq',10.61087357),
                         ('start',5),('forcing-duration',20),('pbase',4),('pulse-width',.025)]:
        ap.add_argument('--'+name,type=float,default=default)
    run(**vars(ap.parse_args()))
