"""Reopen copied cases in another directory, run both, compare actual waveforms."""
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,hashlib,re
import numpy as np
import xml.etree.ElementTree as ET
from pscad_session import get_app
from analysis import read_run
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    a=get_app();names=['DataCenter_Sem_BESS','DataCenter_Com_BESS']
    original={n:sha(ROOT/'pscad'/(n+'.pscx')) for n in names}
    manifest=json.loads((ROOT/'results/latest_suite.json').read_text())
    assert manifest['status']=='COMPLETE'
    workspace=ROOT/'pscad/DataCenter_BESS.pswx'
    # Exactly the two requested projects, with relative references.
    tree=ET.parse(workspace);r=tree.getroot();r.set('name','DataCenter_BESS')
    projects=r.find('projects')
    for child in list(projects):
        if child.get('name') not in names:projects.remove(child)
        else:child.set('filepath','./'+child.get('name')+'.pscx');child.set('open','true')
    tree.write(workspace,encoding='utf-8')
    target=ROOT/'validation'/('portable_pscad_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'))
    target.mkdir(parents=True,exist_ok=False)
    for n in names:shutil.copy2(ROOT/'pscad'/(n+'.pscx'),target/(n+'.pscx'))
    shutil.copy2(workspace,target/workspace.name)
    for n in names:a.project(n).unload()
    a.load(str(target/workspace.name));a.wait_for_idle()
    report={'status':'PASS','workspace_relative':True,'copied_source_hashes':original,
            'clean_build_directory':True,'test_folder':target.relative_to(ROOT).as_posix(),'cases':{}}
    for name,label in zip(names,['nominal_base','nominal_bess']):
        p=a.project(name);assert Path(p.filename).resolve()==(target/(name+'.pscx')).resolve()
        p.parameters(time_duration=2.5,time_step=10,sample_step=100);p.save()
        start=datetime.now(timezone.utc);source=Path(p.filename);source_hash=sha(source)
        p.run();messages=p.messages();errors=[str(m) for m in messages if m.status=='error']
        dest=ROOT/'validation/portability_runs'/label;dest.mkdir(parents=True,exist_ok=True)
        (dest/'messages.txt').write_text('\n'.join(map(str,messages)),encoding='utf-8')
        build=source.with_suffix('.gf81');inf=build/(name+'.inf')
        ids=[int(x) for x in re.findall(r'PGB\((\d+)\)',inf.read_text())]
        files=[inf]+[build/f'{name}_{i:02d}.out' for i in range(1,(max(ids)+9)//10+1)]
        fresh=all(f.stat().st_mtime>=start.timestamp()-2 for f in files)
        for f in files:shutil.copy2(f,dest/f.name)
        shutil.copy2(source,dest/source.name)
        receipt=dict(start_utc=start.isoformat(),finish_utc=datetime.now(timezone.utc).isoformat(),duration_s=2.5,
            sample_step_us=100,time_step_us=10,project_sha256=source_hash,project_unchanged_during_run=sha(source)==source_hash,
            fresh_outputs=fresh,errors=errors,output_sha256={f.name:sha(dest/f.name) for f in files})
        (dest/'run_receipt.json').write_text(json.dumps(receipt,indent=2))
        d=read_run(dest);ref=read_run(ROOT/manifest['cases'][label])
        n=len(d['time']);assert np.array_equal(d['time'],ref['time'][:n])
        differences={k:float(np.max(np.abs(d[k]-ref[k][:n]))) for k in ['Pload_MW','Pgrid_MW','Pbess_MW','SOC_pct','Vdc_kV']}
        okay=not errors and fresh and max(differences.values())<1e-8
        report['cases'][name]={'status':'PASS' if okay else 'FAIL','duration_s':2.5,'max_abs_differences':differences}
        if not okay:report['status']='FAIL'
        print('PORTABILITY',name,report['cases'][name],flush=True)
    for n in names:a.project(n).unload()
    a.load(str(workspace));a.wait_for_idle()
    report['canonical_hashes_preserved']=all(sha(ROOT/'pscad'/(n+'.pscx'))==original[n] for n in names)
    report['reopened_projects']=[x['name'] for x in a.projects() if x['type']=='Case']
    if not report['canonical_hashes_preserved'] or sorted(report['reopened_projects'])!=sorted(names):report['status']='FAIL'
    (ROOT/'validation/portability.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
    assert report['status']=='PASS'
if __name__=='__main__':main()
