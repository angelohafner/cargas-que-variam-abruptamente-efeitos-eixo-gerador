import mhi.pscad
a=mhi.pscad.connect(port=62172);p=a.project('DataCenter_Com_BESS');c=p.canvas('Main')
for i,name in enumerate(['AH','AL','DAH','DAL']):
    o=c.find('master:peswitch',Name=name);o.parameters(I='I_'+name,V='V_'+name,Ton='Ton_'+name,Toff='Toff_'+name)
    for j,prefix in enumerate(['I_','V_','Ton_','Toff_']):
        sn=prefix+name;x=150+i*35;y=335+j*8
        c.create_component('master:datalabel',x,y,Name=sn)
        c.create_wire((x,y),(x+12,y))
        c.create_component('master:pgb',x+12,y,Name=sn,UseSignalName=0)
p.save()
