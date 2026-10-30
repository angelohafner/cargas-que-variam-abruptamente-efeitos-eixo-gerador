"""Read only hash-bound, completed EMTDC runs and compute physical metrics."""
from pathlib import Path
import hashlib,json,re
import numpy as np

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_run(folder,required=()):
    folder=Path(folder);receipt=json.loads((folder/'run_receipt.json').read_text())
    if not receipt.get('fresh_outputs') or receipt.get('errors') or not receipt.get('project_unchanged_during_run'):
        raise ValueError('Run lacks fresh error-free source-bound evidence')
    sources=list(folder.glob('*.pscx'))
    if len(sources)!=1 or digest(sources[0])!=receipt['project_sha256']:raise ValueError('Project hash mismatch')
    for name,expected in receipt['output_sha256'].items():
        if not (folder/name).is_file() or digest(folder/name)!=expected:raise ValueError('Output hash mismatch: '+name)
    infs=list(folder.glob('*.inf'))
    if len(infs)!=1:raise ValueError('Expected one .inf metadata file')
    inf=infs[0]
    mapping=[]
    for line in inf.read_text().splitlines():
        m=re.search(r'PGB\((\d+)\).*?Desc="([^"]+)"',line)
        if m:mapping.append((int(m[1]),m[2]))
    result={};blocks={};ref=None
    for index,name in mapping:
        block=(index-1)//10+1;col=(index-1)%10+1
        if block not in blocks:
            path=folder/f'{inf.stem}_{block:02d}.out'
            if path.name not in receipt['output_sha256']:raise ValueError('Output block absent from receipt')
            a=np.loadtxt(path,skiprows=1,ndmin=2);blocks[block]=a
            if not np.isfinite(a).all():raise ValueError('Nonfinite EMTDC values')
            if ref is None:ref=a[:,0]
            elif not np.array_equal(ref,a[:,0]):raise ValueError('Time axes differ')
        a=blocks[block]
        if col>=a.shape[1]:raise ValueError('Missing channel data: '+name)
        if name in result:raise ValueError('Duplicate channel: '+name)
        result[name]=a[:,col]
    if ref is None or len(ref)<2 or np.any(np.diff(ref)<=0):raise ValueError('Invalid time axis')
    if abs(ref[-1]-receipt['duration_s'])>max(2e-5,receipt['sample_step_us']*1e-6*1.1):raise ValueError('Simulation duration incomplete')
    missing=set(required)-result.keys()
    if missing:raise ValueError('Missing channels: '+','.join(sorted(missing)))
    result['time']=ref
    return result

def average(t,values,window=1/60):
    n=max(1,round(window/np.median(np.diff(t))))
    # Centered common processing, with no zero-padding edges.
    left=n//2;right=n-1-left
    return np.convolve(np.pad(values,(left,right),mode='edge'),np.ones(n)/n,mode='valid')

def metrics(t,p,ramp_window=.1):
    n=max(1,round(ramp_window/np.median(np.diff(t))))
    ramp=(p[n:]-p[:-n])/(t[n:]-t[:-n])
    return {'mean_MW':float(np.mean(p)),'maximum_MW':float(np.max(p)),
        'minimum_MW':float(np.min(p)),'std_MW':float(np.std(p)),
        'peak_to_peak_MW':float(np.ptp(p)),
        'maximum_ramp_MW_per_s':float(np.max(np.abs(ramp))),
        'net_energy_MWh':float(np.trapezoid(p,t)/3600),
        'import_energy_MWh':float(np.trapezoid(np.maximum(p,0),t)/3600)}
