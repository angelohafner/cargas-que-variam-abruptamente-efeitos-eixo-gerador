"""Sequential actual PSCAD runs; fail closed on compile/runtime/output errors."""
from run_pscad import run
from analysis import read_run
import numpy as np
from pathlib import Path
import json
from datetime import datetime,timezone
from test_soc_idle import test_idle
from pscad_session import get_app
ROOT=Path(__file__).resolve().parents[1]

CASES=[
 ('bess','soc_low',6,10,100,20.015,1),
 ('bess','soc_high',6,10,100,79.985,2),
 ('bess','step_coarse',5,10,100,50,0),
 ('bess','step_fine',5,5,100,50,0),
 ('bess','switching_detail',1,5,5,50,0),
 ('base','nominal_base',30,10,100,None,0),
 ('bess','nominal_bess',30,10,100,50,0),
]
if __name__=='__main__':
    manifest={'status':'RUNNING','start_utc':datetime.now(timezone.utc).isoformat(),'cases':{}}
    manifest_path=ROOT/'results/latest_suite.json';manifest_path.parent.mkdir(exist_ok=True)
    manifest_path.write_text(json.dumps(manifest,indent=2))
    try:
        folder=test_idle()
        manifest['cases']['soc_idle']=folder.relative_to(ROOT).as_posix()
        for case,label,dur,step,sample,soc,mode in CASES:
            folder=run(case,label,dur,step,sample,soc=soc,mode=mode)
            d=read_run(folder);mask=d['time']>=max(.6,dur-.2)
            summary={k:float(np.mean(d[k][mask])) for k in ['Pload_MW','Pgrid_MW','Pbess_MW','SOC_pct','Vdc_kV']}
            print('METRICS',label,summary,flush=True)
            manifest['cases'][label]=folder.relative_to(ROOT).as_posix()
            manifest_path.write_text(json.dumps(manifest,indent=2))
    except BaseException:
        # Even an interrupted suite leaves the two user entry points nominal.
        a=get_app()
        for name in ['DataCenter_Sem_BESS','DataCenter_Com_BESS']:
            p=a.project(name);p.parameters(time_duration=30,time_step=10,sample_step=100)
            c=p.canvas('Main');c.find(name+':DC_Controller').parameters(TestMode=0)
            for bat in c.find_all('master:battery'):bat.parameters(SOCint=50)
            p.save()
        manifest['status']='FAILED';manifest_path.write_text(json.dumps(manifest,indent=2))
        raise
    manifest['status']='COMPLETE';manifest['finish_utc']=datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest,indent=2))
