"""Rebuild and run all four relocated native cases, preserving canonical hashes."""
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,xml.etree.ElementTree as ET
import numpy as np
from pscad_session import get_app
from analysis import read_run
from run_scale_250_500 import ROOT,NAMES,LABELS,capture
from run_generator_case import sha
OUT=ROOT/'validation/scale_250_500'
def main():
    app=get_app();workspace=ROOT/'pscad/DataCenter_Quatro_Casos.pswx'
    refs=ET.parse(workspace).findall('./projects/project')
    assert sorted(p.get('name') for p in refs)==sorted(NAMES)
    assert all(not Path(p.get('filepath')).is_absolute() for p in refs)
    hashes={name:sha(ROOT/'pscad'/(name+'.pscx')) for name in NAMES}
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    target=OUT/('portable_'+stamp);target.mkdir()
    for name in NAMES:shutil.copy2(ROOT/'pscad'/(name+'.pscx'),target/(name+'.pscx'))
    shutil.copy2(workspace,target/workspace.name)
    for name in NAMES:app.project(name).unload()
    app.load(str(target/workspace.name));app.wait_for_idle()
    report=dict(status='PASS',source_hashes=hashes,relative_workspace=True,clean_build_folder=True,cases={})
    manifest=json.loads((ROOT/'results/scale_250_500/latest_suite.json').read_text());assert manifest['status']=='COMPLETE'
    try:
        for name,label in zip(NAMES,LABELS):
            p=app.project(name);source=Path(p.filename);assert source.resolve()==(target/(name+'.pscx')).resolve()
            p.parameters(time_duration=6);p.save();h=sha(source)
            dest=OUT/'portability_runs'/stamp/label;dest.mkdir(parents=True,exist_ok=False)
            start=datetime.now(timezone.utc);print('PORTABILITY RUN',name,flush=True)
            p.run();capture(app,p,dest,start,h,6,10,100)
            d=read_run(dest);ref=read_run(ROOT/manifest['cases'][label]);n=len(d['time'])
            assert np.array_equal(d['time'],ref['time'][:n])
            keys=['Pload_MW','Pgrid_MW','Pbess_MW','SOC_pct','Vdc_kV','Vload_kV']
            if 'Gerador' in name:keys+=['Generator_Hz','Shaft_T12_pu','Shaft_T23_pu','Shaft_rel12_rad_s','Shaft_rel23_rad_s']
            diffs={k:float(np.max(abs(d[k]-ref[k][:n]))) for k in keys};del d,ref
            passed=max(diffs.values())<1e-8
            report['cases'][name]=dict(status='PASS' if passed else 'FAIL',duration_s=6,run_folder=dest.relative_to(ROOT).as_posix(),max_abs_differences=diffs)
            if not passed:report['status']='FAIL'
            print('PORTABILITY RESULT',name,report['cases'][name]['status'],diffs,flush=True)
    finally:
        for name in NAMES:
            if any(p['name']==name for p in app.projects()):app.project(name).unload()
        app.load(str(workspace));app.wait_for_idle()
        report['canonical_hashes_preserved']=all(sha(ROOT/'pscad'/(name+'.pscx'))==hashes[name] for name in NAMES)
        report['canonical_reopened']={name:str(app.project(name).filename) for name in NAMES}
        if not report['canonical_hashes_preserved'] or len(report['cases'])!=4:report['status']='FAIL'
        (OUT/'portability.json').write_text(json.dumps(report,indent=2))
    assert report['status']=='PASS'
if __name__=='__main__':main()
