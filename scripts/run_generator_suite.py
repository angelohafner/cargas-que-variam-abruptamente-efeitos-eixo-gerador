"""Actual EMTDC suite for gas-generator torsional identification and comparison."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,shutil
from run_generator_case import run,sha
from pscad_session import get_app
from analysis import read_run
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reuse-pulse-bess');args=ap.parse_args()
    target=ROOT/'results/generator/latest_suite.json';target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        history=ROOT/'history'/('generator_suite_'+datetime.now().strftime('%Y%m%d_%H%M%S'));history.mkdir(parents=True)
        shutil.copy2(target,history/target.name)
        validation=ROOT/'validation/generator/validation.json'
        if validation.exists():shutil.copy2(validation,history/'validation.json')
    old=json.loads((ROOT/'results/latest_suite.json').read_text())
    protected=json.loads((ROOT/'validation/generator/original_hashes.json').read_text())
    assert old['status']=='COMPLETE'
    for n,h in protected.items():assert sha(ROOT/'pscad'/n)==h
    m={'status':'RUNNING','start_utc':datetime.now(timezone.utc).isoformat(),'cases':{
        'ideal_base':old['cases']['nominal_base'],'ideal_bess':old['cases']['nominal_bess']},
        'original_cases_reused_without_changes':True}
    def save():target.write_text(json.dumps(m,indent=2))
    def execute(label,case,**kw):
        folder=run(case,label,**kw);read_run(folder,required=['Shaft_rel12_rad_s','Shaft_rel23_rad_s','Generator_Hz'])
        m['cases'][label]=folder.relative_to(ROOT).as_posix();save();print('SUITE COMPLETED',label,flush=True)
    save()
    try:
        if args.reuse_pulse_bess:
            f=Path(args.reuse_pulse_bess).resolve();d=read_run(f)
            rec=json.loads((f/'run_receipt.json').read_text())
            assert rec['project_sha256']==sha(ROOT/'pscad/DataCenter_Gerador_Com_BESS.pscx')
            assert rec['duration_s']==20 and float(rec['experiment']['Mode'])==2 and 'Shaft_rel12_rad_s' in d
            m['cases']['pulse_bess']=f.relative_to(ROOT).as_posix();save()
        else:execute('pulse_bess','bess',duration=20,mode=2,sample=200)
        execute('profile_base','base',duration=30,mode=0,sample=100)
        execute('profile_bess','bess',duration=30,mode=0,sample=100)
        execute('pulse_base','base',duration=20,mode=2,sample=200)
        execute('pulse_base_fine','base',duration=20,mode=2,step=5,sample=200)
        execute('pulse_bess_fine','bess',duration=20,mode=2,step=5,sample=200)
        execute('pulse_bess_finer','bess',duration=20,mode=2,step=2.5,sample=200)
        a=get_app();p=a.project('DataCenter_Gerador_Sem_BESS');mm=p.canvas('Main').find('master:multimass2')
        mm.parameters(K12=57.6,K23=72);p.save()
        try:execute('pulse_stiffer','base',duration=20,mode=2,sample=200)
        finally:mm.parameters(K12=40,K23=50);p.save()
        execute('sine_off','base',duration=15,mode=4,freq=8,forcing_duration=8,sample=200)
        execute('sine_mode1','base',duration=15,mode=4,freq=10.6108735692,forcing_duration=8,sample=200)
        # Last runs are the canonical, immediately runnable didactic cases.
        execute('chirp_base','base',duration=30,mode=3,sample=100)
        execute('chirp_bess','bess',duration=30,mode=3,sample=100)
        for n,h in protected.items():assert sha(ROOT/'pscad'/n)==h
        m['status']='COMPLETE';m['finish_utc']=datetime.now(timezone.utc).isoformat();save()
    except BaseException:
        m['status']='FAILED';save();raise

if __name__=='__main__':main()
