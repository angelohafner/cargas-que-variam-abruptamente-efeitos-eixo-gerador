"""Build a deterministic source/data/video ZIP and verify CRC and every payload hash."""
from pathlib import Path
import hashlib
import json
import zipfile
from data_pipeline import sha
from render_video import SCENES

HERE=Path(__file__).resolve().parent


def selected():
    files=list(HERE.glob('*.py'))+[HERE/'README.md',HERE/'requirements-lock.txt']
    for folder in ['data','assets','vendor']:
        files.extend(p for p in (HERE/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    files.append(HERE/'output/BESS_Abrupt_Loads_1080p.mp4')
    files.append(HERE/'output/Shaft_Twist_Comparison_1080p.mp4')
    for folder in ['with','without']:
        files.extend(p for p in (HERE/'evidence'/folder).rglob('*') if p.is_file())
    for scene in SCENES:
        files.append(HERE/'evidence/inventories'/(scene+'.json'))
        files.append(HERE/'evidence/scene_posters'/(scene+'.png'))
        files.extend((HERE/'evidence/frames_final').glob(scene+'_*.png'))
        files.append(HERE/'evidence/logs'/('final_'+scene+'.log'))
    for name in ['existing_pscad_validation.json','source_suite.json','independent_review.txt',
                 'delivery_verification.json','visual_review.json','final_timeline.json',
                 'final_probe.json','contact_sheet_final.jpg','shaft_twist_revision.json',
                 'revision_baseline.json','independent_twist_review.txt','edit_baseline.json',
                 'independent_edit_review.txt','converter_baseline.json']:
        files.append(HERE/'evidence'/name)
    files.extend((HERE/'evidence').glob('twist_final_*.png'))
    return sorted(set(files),key=lambda x:x.relative_to(HERE).as_posix())


def package():
    report=json.loads((HERE/'evidence/delivery_verification.json').read_text())
    if report['status']!='PASS':raise ValueError('Delivery verification must pass before packaging')
    files=selected()
    manifest={p.relative_to(HERE).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}
    payload=json.dumps({'format':1,'files':manifest},indent=2).encode()
    target=HERE/'output/BESS_Abrupt_Loads_Complete.zip'
    def write_entry(z,name,data):
        zi=zipfile.ZipInfo(name,(2026,10,30,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED
        zi.external_attr=0o100644<<16
        z.writestr(zi,data,compresslevel=6)
    with zipfile.ZipFile(target,'w') as z:
        for p in files:write_entry(z,p.relative_to(HERE).as_posix(),p.read_bytes())
        write_entry(z,'MANIFEST.json',payload)
    errors=[]
    with zipfile.ZipFile(target) as z:
        corrupt=z.testzip()
        if corrupt:errors.append('CRC: '+corrupt)
        for name,entry in manifest.items():
            data=z.read(name)
            if hashlib.sha256(data).hexdigest()!=entry['sha256'] or len(data)!=entry['bytes']:errors.append(name)
    result={'status':'PASS' if not errors else 'FAIL','zip':target.name,'files':len(manifest)+1,
            'bytes':target.stat().st_size,'sha256':sha(target),'CRC':'PASS' if not corrupt else 'FAIL',
            'all_payload_hashes':'PASS' if not errors else 'FAIL','errors':errors}
    (HERE/'evidence/package_verification.json').write_text(json.dumps(result,indent=2))
    (HERE/'output/MANIFEST.json').write_bytes(payload)
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)


if __name__=='__main__':package()
