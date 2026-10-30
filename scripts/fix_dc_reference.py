import mhi.pscad
a=mhi.pscad.connect(port=62172);p=a.project('DataCenter_Com_BESS');c=p.canvas('Main')
for g in c.find_all('master:ground'):
    if g.location==(205,105):g.delete()
rg=c.create_component('master:resistor',205,110,Name='DC_reference_only',R='1e6 [ohm]');rg.rotate_right()
ends=sorted([(v.x,v.y) for v in rg.ports().values()],key=lambda x:x[1])
c.create_wire((205,105),ends[0]);c.create_wire(ends[1],(205,115));c.create_component('master:ground',205,115)
p.save()
print('DC negative isolated with 1 Mohm earth reference')
