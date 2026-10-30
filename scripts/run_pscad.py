from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,shutil,time,re
import mhi.pscad
from pscad_session import get_app
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(case='bess',label='nominal_bess',duration=30,step=10,sample=100,port=None,soc=None,mode=0):
    name='DataCenter_Com_BESS' if case=='bess' else 'DataCenter_Sem_BESS'
    path=ROOT/'pscad'/f'{name}.pscx'
    app=get_app(port);app.flags(silence=True)
    app.settings(fortran_version='GFortran 8.1 (64-bit)')
    if not any(x['name']==name for x in app.projects()):app.load(str(path))
    p=app.project(name)
    if Path(p.filename).resolve()!=path.resolve():raise ValueError('A different project with the same name is open; use a separate PSCAD session')
    c=p.canvas('Main')
    p.parameters(time_duration=duration,time_step=step,sample_step=sample)
    for o in c.find_all(name+':DC_Controller'):
        o.parameters(TestMode=mode)
    if soc is not None:
        for o in c.find_all('master:battery'):o.parameters(SOCint=soc)
    p.save()
    folder=ROOT/'results'/label
    if folder.exists():folder=ROOT/'results'/(label+'_'+time.strftime('%H%M%S'))
    folder.mkdir(parents=True)
    start=datetime.now(timezone.utc)
    before=sha(path)
    print('RUN',name,label,'duration',duration,'step',step,flush=True)
    p.run()
    messages=p.messages();errors=[str(m) for m in messages if m.status=='error']
    (folder/'messages.txt').write_text('\n'.join(str(m) for m in messages),encoding='utf-8')
    build=path.with_suffix('.gf81')
    inf=build/(name+'.inf')
    indices=[int(x) for x in re.findall(r'PGB\((\d+)\)',inf.read_text())] if inf.exists() else []
    outputs=([build/f'{name}_{i:02d}.out' for i in range(1,(max(indices)+9)//10+1)]+[inf]) if indices else []
    outputs=[f for f in outputs if f.exists()]
    fresh=bool(outputs) and all(f.stat().st_mtime>=start.timestamp()-2 for f in outputs)
    for f in outputs:shutil.copy2(f,folder/f.name)
    for pattern in ['*.log','Main.f','Main.dta','*.map','*.mak']:
        for f in build.glob(pattern):shutil.copy2(f,folder/f.name)
    shutil.copy2(path,folder/path.name)
    receipt=dict(start_utc=start.isoformat(),finish_utc=datetime.now(timezone.utc).isoformat(),
        pscad_version=app.version,compiler='GFortran 8.1 (64-bit)',duration_s=duration,time_step_us=step,
        sample_step_us=sample,initial_soc=soc,test_mode=mode,project_sha256=before,
        project_unchanged_during_run=sha(path)==before,fresh_outputs=fresh,errors=errors,
        output_sha256={f.name:sha(folder/f.name) for f in outputs})
    (folder/'run_receipt.json').write_text(json.dumps(receipt,indent=2))
    print('RESULT',str(folder),'fresh',fresh,'errors',errors,flush=True)
    assert fresh and not errors,'See run receipt/messages'
    return folder
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case',choices=['base','bess'],default='bess');ap.add_argument('--label',default='nominal_bess');ap.add_argument('--duration',type=float,default=30);ap.add_argument('--step',type=float,default=10);ap.add_argument('--sample',type=float,default=100);ap.add_argument('--port',type=int);ap.add_argument('--soc',type=float);ap.add_argument('--mode',type=int,default=0)
    run(**vars(ap.parse_args()))
