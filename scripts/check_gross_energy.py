"""Regression: gross discharge minus charge must equal integrated net energy."""
from pathlib import Path
import sys,json,numpy as np
from analysis import read_run,average
folder=Path(sys.argv[1]);d=read_run(folder);t=d['time']
if 'Edis_MJ' in d:
    discharge=d['Edis_MJ'][-1]-d['Edis_MJ'][0]
    charge=d['Echg_MJ'][-1]-d['Echg_MJ'][0]
    method='EMTDC integration step'
else:
    p=average(t,d['Pbat_MW'])
    discharge=np.trapezoid(np.maximum(p,0),t);charge=np.trapezoid(np.maximum(-p,0),t)
    method='sampled output (former report method)'
net=d['Ebat_MJ'][-1]-d['Ebat_MJ'][0]
error=float(abs(discharge-charge-net))
result={'status':'PASS' if error<1e-6 else 'FAIL','method':method,'discharge_MJ':float(discharge),'charge_MJ':float(charge),'net_MJ':float(net),'closure_error_MJ':error}
print(json.dumps(result,indent=2))
(folder/'gross_energy_regression.json').write_text(json.dumps(result,indent=2))
sys.exit(0 if result['status']=='PASS' else 1)
