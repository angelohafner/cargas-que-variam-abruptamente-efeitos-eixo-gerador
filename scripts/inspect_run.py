import argparse,sys
import numpy as np
from analysis import read_run
ap=argparse.ArgumentParser();ap.add_argument('folder');args=ap.parse_args()
d=read_run(args.folder);t=d['time']
keys=[k for k in ['Pload_command_MW','Pload_MW','Pgrid_MW','Pbess_MW','Pbess_ref_MW','Ibat_kA','Vbat_kV','Vdc_kV','SOC_pct','Id_kA','Iq_kA','Id_ref_kA','Vd_kV','Vq_kV','PLL_Hz','Gate_AH','Gate_AL','Gate_BH','Gate_BL','Gate_CH','Gate_CL'] if k in d]
for start,end in [(0,.1),(.15,.199),(.3,.4),(.8,1),(2.8,3)]:
    m=(t>=start)&(t<=end)
    if not m.any():continue
    print(start,end,{k:round(float(np.mean(d[k][m])),4) for k in keys})
for ph in 'ABC':
    if f'Gate_{ph}H' in d:print('gate_overlap',ph,np.max(d[f'Gate_{ph}H']*d[f'Gate_{ph}L']))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(4,1,figsize=(11,10),sharex=True)
for ax,kk in zip(axs,[['Pload_MW','Pgrid_MW','Pbess_MW','Pbess_ref_MW'],['Vdc_kV','Vbat_kV'],['Ibat_kA'],['Id_kA','Id_ref_kA','Iq_kA']]):
    for k in kk:
        if k in d:ax.plot(t,d[k],label=k,lw=.6)
    ax.legend();ax.grid()
fig.tight_layout();fig.savefig(args.folder+'/inspection.png',dpi=120)
