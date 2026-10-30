from pathlib import Path
import json, xml.etree.ElementTree as ET
import mhi.pscad
ROOT=Path(__file__).resolve().parents[1]
app=mhi.pscad.connect(port=62172)
# This is the newly launched task session, with only restored disk projects.
app.new_workspace(str(ROOT/'diagnostics/Inspection.pswx'))
p=app.create_case('InspectDC',folder=str(ROOT/'diagnostics'))
c=p.canvas('Main')
master=ET.parse('C:/Program Files (x86)/PSCAD/5.1.0/master.pslx').getroot()
names=[d.get('name') for d in master.iter('Definition')]
(ROOT/'diagnostics/master_names.json').write_text(json.dumps(names,indent=2))
selected=['source3','source_3','xfmr-3p2w','xfmr-3p2w2','fixed_load','fload','battery','multimeter','multimeter3','ammeter','voltmeter','nodelabel','peswitch','breaker3','var','const','realpole','integral','pll','PLL','abc_dq','abcdq0','dq0','rms3ph','time-sig','sumjct','div','limits','var_impedance']
data={}
for i,n in enumerate(selected):
    if n not in names: continue
    try:
        o=c.create_component('master:'+n,10+(i%5)*30,10+(i//5)*30)
        data[n]={'parameters':o.parameters(),'ports':{k:[v.x,v.y] for k,v in o.ports().items()}}
        d=next(d for d in master.iter('Definition') if d.get('name')==n)
        ET.ElementTree(d).write(ROOT/'diagnostics'/f'def_{n}.xml',encoding='utf-8')
    except Exception as ex: data[n]={'error':str(ex)}
p.save()
(ROOT/'diagnostics/components.json').write_text(json.dumps(data,indent=2))
(ROOT/'diagnostics/session.json').write_text(json.dumps({'port':62172,'pid':36080}))
print(json.dumps(data,indent=2),flush=True)
