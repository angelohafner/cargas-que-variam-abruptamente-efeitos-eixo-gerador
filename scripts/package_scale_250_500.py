"""Publish fresh scaled packages, preserve old ZIPs, verify every payload hash."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,zipfile,xml.etree.ElementTree as ET
from run_scale_250_500 import ROOT,NAMES,LABELS
from run_generator_case import sha
OUT=ROOT/'validation/scale_250_500'
SCRIPTS=['scale_models_250_500.py','run_scale_250_500.py','finalize_scaled_profiles.py',
 'validate_scale_250_500.py','plot_scale_250_500.py','export_scale_views.py','verify_scale_portability.py',
 'write_scale_report.py','package_scale_250_500.py','pscad_session.py','analysis.py','torsion_math.py',
 'torsion_identification.py','run_generator_case.py']
def archive(path,files):
    entries={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),algorithm='SHA-256',files=entries)
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for i,p in enumerate(sorted(files)):
            z.write(p,p.relative_to(ROOT).as_posix())
            if i%40==0:print('ZIP',path.name,i+1,'/',len(files),flush=True)
        z.writestr('manifest_sha256.json',json.dumps(manifest,indent=2))
    print('VERIFY CRC AND SHA256',path.name,flush=True)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(entries)+1
        for name,h in entries.items():
            digest=hashlib.sha256()
            with z.open(name) as f:
                for block in iter(lambda:f.read(1024*1024),b''):digest.update(block)
            assert digest.hexdigest()==h,name
        assert json.loads(z.read('manifest_sha256.json'))==manifest
    h=sha(path);path.with_suffix('.zip.sha256').write_text(h+'  '+path.name+'\n')
    return dict(file=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=h,payload_files=len(entries),CRC='PASS',payload_hashes='PASS')
def main():
    v=json.loads((OUT/'validation.json').read_text());p=json.loads((OUT/'portability.json').read_text())
    suite=json.loads((ROOT/'results/scale_250_500/latest_suite.json').read_text())
    assert v['status']==p['status']=='PASS' and suite['status']=='COMPLETE' and v['run_folders']==suite['cases']
    for name,label in zip(NAMES,LABELS):
        r=json.loads((ROOT/suite['cases'][label]/'run_receipt.json').read_text())
        assert sha(ROOT/'pscad'/(name+'.pscx'))==r['project_sha256']==p['source_hashes'][name]
        assert (r['duration_s'],r['time_step_us'],r['sample_step_us'])==(30,10,100)
    # Historical multi-GB ZIPs stay in the authoring workspace; an extracted
    # current package can be repackaged without carrying those old deliveries.
    preserved={}
    old_record=ROOT/'delivery/generator_package_verification.json'
    if old_record.exists():
        old=json.loads(old_record.read_text())
        preserved.update({item['file']:item['sha256'] for item in [old['model_package'],old['full_package']]})
    old_record=ROOT/'delivery/package_verification.json'
    if old_record.exists():
        old2=json.loads(old_record.read_text());preserved['delivery/DataCenter_BESS_PSCAD_5_1.zip']=old2['sha256']
    for file,h in preserved.items():assert sha(ROOT/file)==h,file
    baseline=json.loads((OUT/'baseline.json').read_text());historical=ROOT/baseline['folder']
    for name,h in baseline['project_sha256'].items():assert sha(historical/'pscad'/name)==h
    workspace=ROOT/'pscad/DataCenter_Quatro_Casos.pswx';refs=ET.parse(workspace).findall('./projects/project')
    assert sorted(n.get('name') for n in refs)==sorted(NAMES)
    for n in refs:
        path=Path(n.get('filepath'));assert not path.is_absolute() and (workspace.parent/path).is_file()
    files={workspace,ROOT/'README_250_500MW.md',OUT/'RESULTADOS.md'}|{ROOT/'pscad'/(n+'.pscx') for n in NAMES}
    (ROOT/'delivery').mkdir(exist_ok=True)
    small=archive(ROOT/'delivery/DataCenter_250_500MW_Modelos.zip',files)
    files.update(ROOT/x for x in ['README.md','README_GERADOR_TORCIONAL.md','requirements.txt','requirements-lock.txt','results/scale_250_500/latest_suite.json'])
    files.update(ROOT/'scripts'/x for x in SCRIPTS)
    files.update((ROOT/'tests').glob('test_*.py'))
    files.update(p for p in historical.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for folder in suite['cases'].values():files.update(p for p in (ROOT/folder).iterdir() if p.is_file())
    for case in p['cases'].values():files.update(f for f in (ROOT/case['run_folder']).iterdir() if f.is_file())
    files.update((ROOT/'figures/scale_250_500').rglob('*.png'))
    for file in ['baseline.json','design.json','validation.json','portability.json','native_exports.json','unit_tests.txt','visual_review.json','REVIEW.md','RESULTADOS.md']:
        files.add(OUT/file)
    for f in files:assert f.is_file(),f
    full=archive(ROOT/'delivery/DataCenter_250_500MW_PSCAD_5_1.zip',files)
    for file,h in preserved.items():assert sha(ROOT/file)==h
    report=dict(status='PASS',model_package=small,full_package=full,previous_archives_preserved=preserved,
        previous_archives_check='PASS' if preserved else 'NOT_INCLUDED_IN_EXTRACTED_PACKAGE',
        historical_sources_preserved=True,validation_checks=len(v['checks']),validated_runs=len(suite['cases']),
        relocated_runs=4,modal_amplitude_sensitivity=v['modal_step_sensitivity'])
    (ROOT/'delivery/scale_250_500_package_verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
