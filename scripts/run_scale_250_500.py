"""Run the scaled four-case study; final runs restore all delivered defaults.

Use this runner instead of legacy runners, whose defaults target 4--10 MW.
Every run keeps a source snapshot and hashes of freshly generated EMTDC files.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, json, re, shutil
from pscad_session import get_app
from run_generator_case import sha
from scale_models_250_500 import NAMES
ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results/scale_250_500'
LABELS=['ideal_base','ideal_bess','generator_base','generator_bess']

def capture(app, project, dest, started, before, duration, step, sample, extra=None):
    path=Path(project.filename);name=path.stem
    messages=project.messages();errors=[str(m) for m in messages if m.status=='error']
    (dest/'messages.txt').write_text('\n'.join(map(str,messages)),encoding='utf-8')
    build=path.with_suffix('.gf81');inf=build/(name+'.inf')
    indices=[int(x) for x in re.findall(r'PGB\((\d+)\)',inf.read_text())] if inf.exists() else []
    outputs=[inf]+[build/f'{name}_{i:02d}.out' for i in range(1,(max(indices)+9)//10+1)] if indices else []
    fresh=bool(outputs) and all(f.exists() and f.stat().st_mtime>=started.timestamp()-2 for f in outputs)
    for f in outputs:
        if f.exists():shutil.copy2(f,dest/f.name)
    for pattern in ['*.log','Main.f','Main.dta','*.map']:
        for f in build.glob(pattern):shutil.copy2(f,dest/f.name)
    shutil.copy2(path,dest/path.name)
    receipt=dict(start_utc=started.isoformat(),finish_utc=datetime.now(timezone.utc).isoformat(),
        pscad_version=app.version,compiler='GFortran 8.1 (64-bit)',duration_s=duration,
        time_step_us=step,sample_step_us=sample,project_sha256=before,
        project_unchanged_during_run=sha(path)==before,fresh_outputs=fresh,errors=errors,
        output_sha256={f.name:sha(dest/f.name) for f in outputs if (dest/f.name).exists()},**(extra or {}))
    (dest/'run_receipt.json').write_text(json.dumps(receipt,indent=2,default=str))
    if errors or not fresh or not receipt['project_unchanged_during_run']:raise RuntimeError('Failed run: '+str(dest))
    return receipt

def run(case,label,duration=30,step=10,sample=100,mode=0,soc=50,test_mode=0,pbase=250,amplitude=25):
    name=NAMES[LABELS.index(case)];path=ROOT/'pscad'/(name+'.pscx')
    app=get_app();app.flags(silence=True)
    if not any(p['name']==name for p in app.projects()):app.load(str(path))
    p=app.project(name)
    if Path(p.filename).resolve()!=path.resolve():raise ValueError('Another source with the same project name is open')
    p.parameters(time_duration=duration,time_step=step,sample_step=sample)
    c=p.canvas('Main');ctl=c.find(name+':DC_Controller')
    ctl.parameters(TestMode=test_mode,Pmin=250 if mode==0 else pbase,TestPower=150)
    for b in c.find_all('master:battery'):b.parameters(SOCint=soc)
    experiment=None
    if 'Gerador' in name:
        ex=c.find(name+':TorsionExperiment')
        ex.parameters(Mode=mode,Pbase=375 if mode==0 else pbase,Amplitude=25 if mode==0 else amplitude,
            Fsine=10.61087357,Start=5,Duration=20,PulseWidth=.025)
        c.find('master:sync_machine').parameters(P0=f'{255 if mode==0 else pbase+5} [MW]',Q0='60 [MVAR]')
        experiment=ex.parameters()
    p.save();before=sha(path)
    dest=RESULTS/(label+'_'+datetime.now().strftime('%Y%m%d_%H%M%S'));dest.mkdir(parents=True)
    started=datetime.now(timezone.utc)
    print('RUN',case,label,dict(duration=duration,step=step,mode=mode,soc=soc),flush=True)
    p.run();capture(app,p,dest,started,before,duration,step,sample,
        dict(initial_soc=soc,test_mode=test_mode,experiment=experiment))
    print('RESULT',dest.relative_to(ROOT).as_posix(),'PASS fresh error-free',flush=True)
    return dest

def suite():
    RESULTS.mkdir(parents=True,exist_ok=True);manifest=RESULTS/'latest_suite.json'
    report=dict(status='RUNNING',created_utc=datetime.now(timezone.utc).isoformat(),cases={})
    def record(label,case,**kw):
        report['cases'][label]=run(case,label,**kw).relative_to(ROOT).as_posix()
        manifest.write_text(json.dumps(report,indent=2))
    manifest.write_text(json.dumps(report,indent=2))
    record('soc_low','ideal_bess',duration=6,soc=20.015,test_mode=1)
    record('soc_high','ideal_bess',duration=6,soc=79.985,test_mode=2)
    for case in ['generator_base','generator_bess']:
        for suffix,step in [('',10),('_fine',5)]:
            record('pulse_'+case+suffix,case,duration=20,step=step,sample=200,mode=2)
    record('profile_generator_bess_fine','generator_bess',duration=6,step=5)
    # Last execution for each canonical file uses exactly the delivered settings.
    from scale_models_250_500 import main as rebuild_defaults
    rebuild_defaults()
    for case in LABELS:record(case,case)
    report['status']='COMPLETE';manifest.write_text(json.dumps(report,indent=2))
    print('SUITE COMPLETE',len(report['cases']),'runs',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--suite',action='store_true')
    ap.add_argument('--case',choices=LABELS,default='ideal_bess');ap.add_argument('--label',default='smoke')
    ap.add_argument('--duration',type=float,default=6);ap.add_argument('--step',type=float,default=10)
    args=vars(ap.parse_args());all_cases=args.pop('suite')
    suite() if all_cases else run(**args)
