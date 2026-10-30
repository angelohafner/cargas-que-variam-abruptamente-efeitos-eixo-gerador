"""Open all four cases in one relative workspace; run relocated generator cases."""
from pathlib import Path
from datetime import datetime,timezone
import json,shutil,re,xml.etree.ElementTree as ET
import numpy as np
from pscad_session import get_app
from analysis import read_run
from run_generator_case import sha
ROOT=Path(__file__).resolve().parents[1]
NAMES=['DataCenter_Sem_BESS','DataCenter_Com_BESS','DataCenter_Gerador_Sem_BESS','DataCenter_Gerador_Com_BESS']
def main():
    a=get_app();original={n:sha(ROOT/'pscad'/(n+'.pscx')) for n in NAMES}
    workspace=ROOT/'pscad/DataCenter_Quatro_Casos.pswx'
    tree=ET.parse(ROOT/'pscad/DataCenter_BESS.pswx');root=tree.getroot();root.set('name',workspace.stem)
    projects=root.find('projects');projects.clear()
    for n in NAMES:ET.SubElement(projects,'project',type='project',name=n,filepath='./'+n+'.pscx',open='true')
    tree.write(workspace,encoding='utf-8')
    a.load(str(workspace));a.wait_for_idle()
    assert sorted(x['name'] for x in a.projects() if x['type']=='Case')==sorted(NAMES)
    a.save_workspace(str(workspace),save_projects=False)
    # PSCAD may serialize absolute names: enforce package-relative references.
    tree=ET.parse(workspace)
    for node in tree.findall('./projects/project'):node.set('filepath','./'+node.get('name')+'.pscx')
    tree.write(workspace,encoding='utf-8')
    target=ROOT/'validation/generator'/('portable_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S'));target.mkdir()
    for n in NAMES:shutil.copy2(ROOT/'pscad'/(n+'.pscx'),target/(n+'.pscx'))
    shutil.copy2(workspace,target/workspace.name)
    for n in NAMES:a.project(n).unload()
    a.load(str(target/workspace.name));a.wait_for_idle()
    manifest=json.loads((ROOT/'results/generator/latest_suite.json').read_text());assert manifest['status']=='COMPLETE'
    report=dict(status='PASS',workspace_relative=True,all_four_opened=True,clean_build_directory=True,
                test_folder=target.relative_to(ROOT).as_posix(),source_hashes=original,cases={},
                note='New generator cases rerun for 6 s including rotor release and chirp onset. Ideal cases reopened; their original simulation evidence is reused unchanged.')
    for name,label in zip(NAMES[2:],['chirp_base','chirp_bess']):
        p=a.project(name);source=Path(p.filename);assert source.resolve()==(target/(name+'.pscx')).resolve()
        p.parameters(time_duration=6);p.save();h=sha(source);start=datetime.now(timezone.utc)
        print('PORTABILITY RUN',name,flush=True);p.run();messages=p.messages();errors=[str(x) for x in messages if x.status=='error']
        dest=ROOT/'validation/generator/portability_runs'/label;dest.mkdir(parents=True,exist_ok=True)
        (dest/'messages.txt').write_text('\n'.join(map(str,messages)),encoding='utf-8')
        build=source.with_suffix('.gf81');inf=build/(name+'.inf');ids=[int(x) for x in re.findall(r'PGB\((\d+)\)',inf.read_text())]
        files=[inf]+[build/f'{name}_{i:02d}.out' for i in range(1,(max(ids)+9)//10+1)]
        fresh=all(f.stat().st_mtime>=start.timestamp()-2 for f in files)
        for f in files:shutil.copy2(f,dest/f.name)
        shutil.copy2(source,dest/source.name)
        receipt=dict(start_utc=start.isoformat(),finish_utc=datetime.now(timezone.utc).isoformat(),duration_s=6,
            sample_step_us=100,time_step_us=10,project_sha256=h,project_unchanged_during_run=sha(source)==h,
            fresh_outputs=fresh,errors=errors,output_sha256={f.name:sha(dest/f.name) for f in files})
        (dest/'run_receipt.json').write_text(json.dumps(receipt,indent=2))
        d=read_run(dest);ref=read_run(ROOT/manifest['cases'][label]);n=len(d['time'])
        assert np.array_equal(d['time'],ref['time'][:n])
        differences={k:float(np.max(abs(d[k]-ref[k][:n]))) for k in ['Pload_MW','Pgrid_MW','Pbess_MW','SOC_pct','Vdc_kV','Generator_Hz','Shaft_T12_pu','Shaft_T23_pu','Shaft_rel12_rad_s','Shaft_rel23_rad_s']}
        passed=not errors and fresh and max(differences.values())<1e-8
        report['cases'][name]=dict(status='PASS' if passed else 'FAIL',duration_s=6,run_folder=dest.relative_to(ROOT).as_posix(),max_abs_differences=differences)
        if not passed:report['status']='FAIL'
        print('PORTABILITY',name,report['cases'][name],flush=True)
    for n in NAMES:a.project(n).unload()
    a.load(str(workspace));a.wait_for_idle()
    report['canonical_hashes_preserved']=all(sha(ROOT/'pscad'/(n+'.pscx'))==original[n] for n in NAMES)
    report['reopened_projects']=[x['name'] for x in a.projects() if x['type']=='Case']
    if not report['canonical_hashes_preserved'] or sorted(report['reopened_projects'])!=sorted(NAMES):report['status']='FAIL'
    (ROOT/'validation/generator/portability.json').write_text(json.dumps(report,indent=2))
    assert report['status']=='PASS'
if __name__=='__main__':main()
