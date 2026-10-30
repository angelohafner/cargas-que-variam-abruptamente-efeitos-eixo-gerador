"""Preserve old ZIP; create and fully hash/CRC-verify four-case packages."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,zipfile,xml.etree.ElementTree as ET
from package_delivery import SCRIPTS as ORIGINAL_SCRIPTS,sha_file
ROOT=Path(__file__).resolve().parents[1]
EXTRA=['generator_controls.py','build_generator_cases.py','polish_generator_cases.py','prepare_generator_views.py',
       'torsion_math.py','torsion_identification.py','run_generator_case.py','run_generator_suite.py',
       'validate_generator_results.py','plot_generator_results.py','export_generator_views.py',
       'verify_generator_portability.py','write_generator_report.py','package_generator_delivery.py']
def archive(path,files,manifest_name):
    entries={p.relative_to(ROOT).as_posix():sha_file(p) for p in sorted(files)}
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),algorithm='SHA-256',files=entries)
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for i,p in enumerate(sorted(files)):
            z.write(p,p.relative_to(ROOT).as_posix())
            if i%40==0:print('ZIP',path.name,i+1,'/',len(files),flush=True)
        if manifest_name:z.writestr(manifest_name,json.dumps(manifest,indent=2))
    print('Verifying CRC and all payload hashes:',path.name,flush=True)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for name,h in entries.items():
            actual=hashlib.sha256()
            with z.open(name) as f:
                for b in iter(lambda:f.read(1024*1024),b''):actual.update(b)
            assert actual.hexdigest()==h,name
        assert len(z.namelist())==len(entries)+bool(manifest_name)
        if manifest_name:assert json.loads(z.read(manifest_name))==manifest
    h=sha_file(path);path.with_suffix(path.suffix+'.sha256').write_text(h+'  '+path.name+'\n',encoding='ascii')
    return dict(file=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=h,payload_files=len(entries),zip_crc='PASS',all_payload_sha256='PASS')
def main():
    suite=json.loads((ROOT/'results/generator/latest_suite.json').read_text())
    validation=json.loads((ROOT/'validation/generator/validation.json').read_text())
    portability=json.loads((ROOT/'validation/generator/portability.json').read_text())
    assert suite['status']=='COMPLETE' and validation['status']=='PASS' and portability['status']=='PASS'
    assert validation['run_folders']==suite['cases']
    oldzip=ROOT/'delivery/DataCenter_BESS_PSCAD_5_1.zip'
    oldreport=json.loads((ROOT/'delivery/package_verification.json').read_text());oldhash=sha_file(oldzip)
    assert oldhash==oldreport['sha256'],'Original delivery changed'
    names=['DataCenter_Sem_BESS','DataCenter_Com_BESS','DataCenter_Gerador_Sem_BESS','DataCenter_Gerador_Com_BESS']
    workspace=ROOT/'pscad/DataCenter_Quatro_Casos.pswx';projects=ET.parse(workspace).findall('./projects/project')
    assert sorted(p.get('name') for p in projects)==sorted(names)
    for p in projects:
        ref=Path(p.get('filepath'));assert not ref.is_absolute() and (workspace.parent/ref).is_file()
    for name,label in zip(names,['ideal_base','ideal_bess','chirp_base','chirp_bess']):
        h=sha_file(ROOT/'pscad'/(name+'.pscx'));rec=json.loads((ROOT/suite['cases'][label]/'run_receipt.json').read_text())
        assert h==rec['project_sha256']==portability['source_hashes'][name]
    files={workspace}|{ROOT/'pscad'/(n+'.pscx') for n in names}
    out=ROOT/'delivery';out.mkdir(exist_ok=True)
    small=archive(out/'DataCenter_Quatro_Casos_Modelos.zip',files,None)
    for name in ['README.md','README_GERADOR_TORCIONAL.md','requirements.txt','requirements-lock.txt','results/latest_suite.json','results/generator/latest_suite.json','pscad/DataCenter_BESS.pswx']:
        files.add(ROOT/name)
    for name in set(ORIGINAL_SCRIPTS+EXTRA):files.add(ROOT/'scripts'/name)
    files.update((ROOT/'tests').glob('test_*.py'))
    folders=set(suite['cases'].values())|set(json.loads((ROOT/'results/latest_suite.json').read_text())['cases'].values())
    for folder in folders:files.update(p for p in (ROOT/folder).iterdir() if p.is_file())
    files.update((ROOT/'figures').rglob('*.png'))
    for name in ['validation.json','RELATORIO.md','REVIEW.md','native_exports.json','portability.json','unit_tests.txt','visual_review.json']:
        files.add(ROOT/'validation'/name)
    for name in ['validation.json','RESULTADOS.md','REVIEW.md','native_exports.json','portability.json','unit_tests.txt','visual_review.json','original_hashes.json']:
        files.add(ROOT/'validation/generator'/name)
    for folder in ['validation/portability_runs','validation/generator/portability_runs']:
        files.update(p for p in (ROOT/folder).rglob('*') if p.is_file())
    for p in files:assert p.is_file(),p
    full=archive(out/'DataCenter_Quatro_Casos_PSCAD_5_1.zip',files,'validation/generator/manifest_sha256.json')
    assert sha_file(oldzip)==oldhash
    report=dict(status='PASS',original_zip_preserved=True,workspace_projects=names,model_package=small,full_package=full,
                amplitude_convergence_limitations=validation['spectral_amplitude_step_sensitivity'])
    (out/'generator_package_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
