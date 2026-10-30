"""Package only the current validated suite; verify ZIP CRC and every SHA-256."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,zipfile,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=['controller.py','audit_component.py','build_model.py','pscad_session.py',
    'run_pscad.py','run_suite.py','test_soc_idle.py','analysis.py','validate_results.py',
    'check_gross_energy.py','export_native_views.py','verify_portability.py','fix_graph_ranges.py',
    'write_report.py','package_delivery.py']

def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    suite=json.loads((ROOT/'results/latest_suite.json').read_text())
    validation=json.loads((ROOT/'validation/validation.json').read_text())
    portability=json.loads((ROOT/'validation/portability.json').read_text())
    assert suite['status']=='COMPLETE' and validation['status']=='PASS' and portability['status']=='PASS'
    assert all(x['status']=='PASS' for x in validation['checks'])
    assert validation['run_folders']==suite['cases'],'Validation must reference the current suite'
    names=['DataCenter_Sem_BESS','DataCenter_Com_BESS']
    workspace=ROOT/'pscad/DataCenter_BESS.pswx'
    ps=ET.parse(workspace).getroot().findall('./projects/project')
    assert sorted(x.get('name') for x in ps)==sorted(names)
    for x in ps:
        ref=Path(x.get('filepath'));assert not ref.is_absolute()
        assert (workspace.parent/ref).is_file()
    for name,label in zip(names,['nominal_base','nominal_bess']):
        receipt=json.loads((ROOT/suite['cases'][label]/'run_receipt.json').read_text())
        current=sha_file(ROOT/'pscad'/(name+'.pscx'))
        assert current==receipt['project_sha256']==portability['copied_source_hashes'][name]
        assert receipt['duration_s']==30 and receipt['time_step_us']==10 and receipt['sample_step_us']==100
    files=set()
    def add(p):
        assert p.is_file(),str(p)
        files.add(p)
    for name in ['README.md','requirements.txt','requirements-lock.txt','results/latest_suite.json']:
        add(ROOT/name)
    for name in names:add(ROOT/'pscad'/(name+'.pscx'))
    add(workspace)
    for name in SCRIPTS:add(ROOT/'scripts'/name)
    for p in (ROOT/'tests').glob('test_*.py'):add(p)
    for folder in suite['cases'].values():
        for p in (ROOT/folder).iterdir():
            if p.is_file():add(p)
    for p in (ROOT/'figures').rglob('*.png'):add(p)
    for name in ['validation.json','RELATORIO.md','REVIEW.md','native_exports.json',
                 'portability.json','unit_tests.txt','visual_review.json']:
        add(ROOT/'validation'/name)
    for p in (ROOT/'validation/portability_runs').rglob('*'):
        if p.is_file():add(p)
    files=sorted(files)
    entries={p.relative_to(ROOT).as_posix():sha_file(p) for p in files}
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'algorithm':'SHA-256','files':entries}
    manifest_path=ROOT/'validation/manifest_sha256.json'
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8');files.append(manifest_path)
    output=ROOT/'delivery';output.mkdir(exist_ok=True)
    zip_path=output/'DataCenter_BESS_PSCAD_5_1.zip'
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for i,p in enumerate(files):
            z.write(p,p.relative_to(ROOT).as_posix())
            if i%25==0:print('ZIP',i+1,'/',len(files),flush=True)
    print('Verifying ZIP CRC and payload hashes...',flush=True)
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None,'ZIP CRC failure'
        stored=json.loads(z.read('validation/manifest_sha256.json'))
        assert stored==manifest
        for name,expected in entries.items():
            h=hashlib.sha256()
            with z.open(name) as f:
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
            assert h.hexdigest()==expected,name
        assert len(z.namelist())==len(entries)+1
    zip_hash=sha_file(zip_path)
    report={'status':'PASS','file':zip_path.relative_to(ROOT).as_posix(),'bytes':zip_path.stat().st_size,
        'sha256':zip_hash,'payload_files':len(entries),'zip_crc':'PASS','all_payload_sha256':'PASS',
        'canonical_sources_match_nominal_runs':True,'workspace_projects':names}
    (output/'package_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (output/(zip_path.name+'.sha256')).write_text(zip_hash+'  '+zip_path.name+'\n',encoding='ascii')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
