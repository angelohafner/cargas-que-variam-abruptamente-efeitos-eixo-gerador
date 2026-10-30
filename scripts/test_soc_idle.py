"""Physical regression for low SOC with zero AC command and recovery disabled."""
from pathlib import Path
import sys,json,numpy as np
from pscad_session import get_app
from run_pscad import run
from analysis import read_run,average
ROOT=Path(__file__).resolve().parents[1]
def test_idle(label='soc_idle'):
    a=get_app();name='DataCenter_Com_BESS';source=ROOT/'pscad'/(name+'.pscx')
    if not any(x['name']==name for x in a.projects()):a.load(str(source))
    p=a.project(name)
    if Path(p.filename).resolve()!=source.resolve():raise ValueError('A different BESS case is open in this session')
    ctl=p.canvas('Main').find(name+':DC_Controller')
    old=ctl.parameters();ctl.parameters(TestPower=0,RecoveryGain=0)
    try:
        folder=run('bess',label,5,10,100,soc=20.001,mode=1)
        d=read_run(folder);m=d['time']>1.2
        minimum=float(np.min(d['SOC_pct']));forbidden=float(np.mean(average(d['time'],d['Pbat_MW'])[m]))
        result={'status':'PASS' if minimum>=19.9999 and forbidden<=.005 else 'FAIL',
                'minimum_SOC_percent':minimum,'mean_battery_discharge_MW_at_idle':forbidden,
                'run_folder':folder.relative_to(ROOT).as_posix()}
        (folder/'regression.json').write_text(json.dumps(result,indent=2));print(result,flush=True)
    finally:
        ctl.parameters(TestPower=old['TestPower'],RecoveryGain=old['RecoveryGain']);p.save()
    if result['status']!='PASS':raise AssertionError('Physical SOC idle protection regression failed')
    return folder
if __name__=='__main__':test_idle(sys.argv[1] if len(sys.argv)>1 else 'soc_idle')
