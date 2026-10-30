from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analysis import read_run,average,metrics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation';OUT.mkdir(exist_ok=True)
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
checks=[]
def run_folder(label):
    manifest=ROOT/'results/latest_suite.json'
    if manifest.exists():
        data=json.loads(manifest.read_text())
        if data.get('status')!='COMPLETE':raise ValueError('Latest suite is incomplete; validation cannot reuse older results')
        path=(ROOT/data['cases'][label]).resolve()
        if not path.is_relative_to(ROOT.resolve()):raise ValueError('Suite path outside package')
        return path
    return ROOT/'results'/label
def check(name,passed,value=None,limit=None):
    checks.append({'name':name,'status':'PASS' if bool(passed) else 'FAIL','value':value,'limit':limit})
def peak(v):return float(np.max(np.abs(v)))
def rms(v):return float(np.sqrt(np.mean(v*v)))
def battery_power(d):
    # Differentiate EMTDC-integrated energy before display filtering. This uses
    # interval energy, avoiding point-sampling alias of the switching current.
    return average(d['time'],np.gradient(d['Ebat_MJ'],d['time']))
def end_delta(d,key,start=.6):
    i=np.searchsorted(d['time'],start);return float(d[key][-1]-d[key][i])

def validate():
    base=read_run(run_folder('nominal_base'),required=['Pgrid_MW','Pload_MW','Pload_command_MW'])
    bess=read_run(run_folder('nominal_bess'),required=['Pgrid_MW','Pbess_MW','SOC_pct','Charge_kAs','Eloss_MJ'])
    t=base['time'];check('identical_nominal_timestamps',np.array_equal(t,bess['time']))
    check('identical_load_command',np.array_equal(base['Pload_command_MW'],bess['Pload_command_MW']))
    m=t>=.6
    b={k:average(t,v) for k,v in base.items() if k!='time'}
    a={k:average(t,v) for k,v in bess.items() if k!='time'}
    for label,raw,d in [('base',base,b),('bess',bess,a)]:
        err=rms(d['Pload_MW'][m]-d['Pload_command_MW'][m])
        check(label+'_load_tracking_RMS_MW',err<.5,err,.5)
        vr=[float(np.min(d['Vload_kV'][m])/13.8),float(np.max(d['Vload_kV'][m])/13.8)]
        check(label+'_PCC_voltage_pu',vr[0]>.90 and vr[1]<1.10,vr,[.90,1.10])
        balance=d['Pgrid_MW']-d['Pload_MW']+d['Pbess_MW']-3*.02*d['Igrid_kA']**2
        err=rms(balance[m]);check(label+'_network_balance_RMS_MW',err<.03,err,.03)
    mismatch=rms(a['Pload_MW'][m]-b['Pload_MW'][m])
    check('same_served_load_RMS_difference_MW',mismatch<.30,mismatch,.30)
    ein0=float(np.trapezoid(base['Pload_MW'][m],t[m]));ein1=float(np.trapezoid(bess['Pload_MW'][m],t[m]))
    mismatch=abs(ein1-ein0)/ein0
    check('same_served_load_energy_relative',mismatch<.02,mismatch,.02)
    check('nominal_SOC_bounds',np.min(bess['SOC_pct'])>=20 and np.max(bess['SOC_pct'])<=80,[float(np.min(bess['SOC_pct'])),float(np.max(bess['SOC_pct']))],[20,80])
    vd=[float(np.min(a['Vdc_kV'][m])),float(np.max(a['Vdc_kV'][m]))]
    check('nominal_DC_voltage_kV',vd[0]>1.3 and vd[1]<1.7,vd,[1.3,1.7])
    power=peak(a['Pbess_MW'][m]);check('AC_power_limit_including_4percent_transient_allowance',power<=5.2,power,5.2)
    curr=peak(a['Id_kA'][m]);check('dq_current_with_10percent_dynamic_allowance_kA',curr<=6.82,curr,6.82)
    tracking=rms((a['Pbess_MW']-a['Pbess_ref_MW'])[m])
    check('BESS_power_tracking_RMS_MW',tracking<=.25,tracking,.25)
    check('modulation_limit',max(peak(bess['Mod_'+p]) for p in 'ABC')<=.980001)
    soc_expected=50-100*bess['Charge_kAs']/(1.6666666667*3600)
    soc_error=peak(bess['SOC_pct']-soc_expected)
    check('SOC_independent_coulomb_count_percent_points',soc_error<.0001,soc_error,.0001)
    err=end_delta(bess,'Ebat_MJ')-end_delta(bess,'Ebess_MJ')-end_delta(bess,'Eloss_MJ')-end_delta(bess,'Ecap_MJ')-end_delta(bess,'Eind_MJ')
    throughput=end_delta(bess,'Edis_MJ')+end_delta(bess,'Echg_MJ')
    check('BESS_terminal_energy_balance_relative',abs(err)/max(throughput,1)<.02,{'residual_MJ':err,'relative':abs(err)/max(throughput,1)},.02)
    check('positive_measured_converter_losses',end_delta(bess,'Eloss_MJ')>0,end_delta(bess,'Eloss_MJ'),'>0 MJ')
    comparison={}
    for label,start,end in [('full',.6,30),('pulses_6_10',6,10),('pulses_20_25',20,25)]:
        mm=(t>=start)&(t<=end)
        mb=metrics(t[mm],b['Pgrid_MW'][mm]);ma=metrics(t[mm],a['Pgrid_MW'][mm])
        red={key:100*(1-ma[key]/mb[key]) for key in ['std_MW','maximum_ramp_MW_per_s','maximum_MW','peak_to_peak_MW']}
        comparison[label]={'without_BESS':mb,'with_BESS':ma,'reduction_percent':red,'window_s':[start,end]}
        if label!='full':
            check(label+'_std_reduction_at_least_50percent',red['std_MW']>=50,red['std_MW'],50)
            check(label+'_ramp_reduction_at_least_50percent',red['maximum_ramp_MW_per_s']>=50,red['maximum_ramp_MW_per_s'],50)
            sat=(bess['Power_limit'][mm]>.5)|(bess['Current_limit'][mm]>.5)|(abs(bess['SOC_block'][mm])>.5)
            comparison[label]['saturation_fraction']=float(np.mean(sat))
    energy={'SOC_initial_percent':float(bess['SOC_pct'][0]),'SOC_final_percent':float(bess['SOC_pct'][-1]),
        'SOC_excursion_percent_points':float(np.ptp(bess['SOC_pct'])),
        'battery_terminal_net_MWh':end_delta(bess,'Ebat_MJ',0)/3600,
        'battery_chemical_net_MWh':end_delta(bess,'Echem_MJ',0)/3600,
        'discharged_terminal_MWh':end_delta(bess,'Edis_MJ',0)/3600,
        'charged_terminal_MWh':end_delta(bess,'Echg_MJ',0)/3600,
        'converter_path_losses_MWh':end_delta(bess,'Eloss_MJ',0)/3600}
    closure=abs(end_delta(bess,'Edis_MJ',0)-end_delta(bess,'Echg_MJ',0)-end_delta(bess,'Ebat_MJ',0))
    check('EMTDC_gross_minus_net_energy_closure_MJ',closure<1e-6,closure,1e-6)
    idle=read_run(run_folder('soc_idle'));im=idle['time']>1.2
    imin=float(np.min(idle['SOC_pct']));ip=float(np.mean(battery_power(idle)[im]))
    check('SOC_idle_lower_bound_percent',imin>=19.9999,imin,20)
    check('SOC_idle_zero_request_actual_discharge_MW',ip<=.005,ip,.005)
    protection={}
    for label,sign,initial in [('soc_low',1,20.015),('soc_high',-1,79.985)]:
        d=read_run(run_folder(label));tt=d['time'];act=(np.abs(d['SOC_block'])>.5)&(tt<2.95)
        check(label+'_protection_activated',act.any())
        check(label+'_SOC_bounds',np.min(d['SOC_pct'])>=19.9999 and np.max(d['SOC_pct'])<=80.0001,[float(np.min(d['SOC_pct'])),float(np.max(d['SOC_pct']))],[20,80])
        measured=battery_power(d)
        if act.any():
            start=float(tt[np.flatnonzero(act)[0]])
            steady=act&(tt>start+.08)
            violation=float(np.max(sign*measured[steady])) if steady.any() else 1e6
            check(label+'_actual_battery_power_allowed_direction_MW',violation<=.02,violation,.02)
            protection[label]={'activation_s':start,'worst_forbidden_direction_MW':violation}
        recovery=(tt>3.5)&(tt<5.5)
        actual=float(np.mean(sign*measured[recovery]));check(label+'_reverse_recovery_allowed',actual<-.5,actual,'<-0.5 MW')
        expected=initial-100*d['Charge_kAs']/(1.6666666667*3600)
        err=peak(d['SOC_pct']-expected);check(label+'_SOC_coulomb_count',err<.0001,err,.0001)
        plot_soc(d,label)
    coarse=read_run(run_folder('step_coarse'));fine=read_run(run_folder('step_fine'))
    for key in ['Pload_MW','Pgrid_MW','Pbess_MW','Vdc_kV','SOC_pct']:
        tc=coarse['time'];mm=tc>=.6
        aa=average(tc,coarse[key]);ff=np.interp(tc,fine['time'],average(fine['time'],fine[key]))
        scale={'Pload_MW':10,'Pgrid_MW':10,'Pbess_MW':5,'Vdc_kV':1.5,'SOC_pct':100}[key]
        err=rms((aa-ff)[mm])/scale;check('half_step_'+key+'_normalized_RMS',err<.03,err,.03)
    detail=read_run(run_folder('switching_detail'))
    for ph in 'ABC':
        overlap=peak(detail['Gate_'+ph+'H']*detail['Gate_'+ph+'L']);check('switching_no_gate_overlap_'+ph,overlap==0,overlap,0)
    plot_main(t,b,a,bess)
    plot_switching(detail)
    result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','checks':checks,
        'run_folders':{label:run_folder(label).relative_to(ROOT).as_posix() for label in ['nominal_base','nominal_bess','soc_low','soc_high','soc_idle','step_coarse','step_fine','switching_detail']},
        'comparison':comparison,'energy':energy,'protection':protection,
        'method':{'startup_excluded_s':.6,'power_filter_s':1/60,'ramp_window_s':.1,
                  'full_window_s':[.6,30],'energy_note':'SOC differs at finish; grid energy change is not an efficiency or energy-saving claim.'}}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(result['status'],sum(c['status']=='PASS' for c in checks),'/',len(checks),flush=True)
    for c in checks:
        if c['status']=='FAIL':print('FAIL',c,flush=True)
    print(json.dumps(comparison,indent=2),flush=True)
    return result

def style(ax,title,ylabel):
    ax.set_title(title,loc='left',fontsize=11,fontweight='bold');ax.set_ylabel(ylabel);ax.grid(alpha=.22);ax.legend(fontsize=8,loc='best')
def plot_main(t,b,a,raw):
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(4,2,figsize=(15,15),sharex=True)
    ax=axs[0,0];ax.plot(t,b['Pload_MW'],c='#505050',lw=1,label='Carga sem BESS');ax.plot(t,a['Pload_MW'],'--',c='#e09b26',lw=.9,alpha=.8,label='Carga com BESS');style(ax,'Demanda atendida','MW')
    ax=axs[0,1];ax.plot(t,b['Pgrid_MW'],c='#c74a40',lw=1,label='Sem BESS');ax.plot(t,a['Pgrid_MW'],c='#127a9b',lw=1.3,label='Com BESS');ax.plot(t,a['Pgrid_ref_MW'],'--',c='black',lw=.8,label='Referência');style(ax,'Potência importada da rede','MW')
    ax=axs[1,0];ax.plot(t,a['Pbess_MW'],label='Medida',c='#21896b');ax.plot(t,a['Pbess_ref_MW'],'--',lw=.8,label='Referência',c='black');style(ax,'BESS: positivo = descarga','MW')
    ax=axs[1,1];ax.plot(t,raw['SOC_pct'],label='SOC',c='#7954a1');style(ax,'Estado de carga da bateria','%')
    ax=axs[2,0];ax.plot(t,b['Vload_kV'],label='Sem BESS',c='#c74a40');ax.plot(t,a['Vload_kV'],label='Com BESS',c='#127a9b',alpha=.85);style(ax,'Tensão RMS do barramento','kV')
    mm=t>=.6;v=np.concatenate([b['Vload_kV'][mm],a['Vload_kV'][mm]]);ax.set_ylim(float(v.min())-.08,float(v.max())+.08)
    ax=axs[2,1];ax.plot(t,b['Igrid_kA'],label='Sem BESS',c='#c74a40');ax.plot(t,a['Igrid_kA'],label='Com BESS',c='#127a9b');style(ax,'Corrente RMS da rede','kA')
    ax=axs[3,0];ax.plot(t,a['Vdc_kV'],label='Barramento CC',c='#127a9b');ax.plot(t,a['Vbat_kV'],'--',label='Bateria',c='#e09b26',alpha=.8);style(ax,'Tensões CC','kV')
    v=np.concatenate([a['Vdc_kV'][mm],a['Vbat_kV'][mm]]);ax.set_ylim(float(v.min())-.005,float(v.max())+.005)
    ax=axs[3,1];ax.plot(t,b['Qgrid_Mvar'],label='Rede sem BESS',c='#c74a40');ax.plot(t,a['Qgrid_Mvar'],label='Rede com BESS',c='#127a9b');ax.plot(t,a['Qbess_Mvar'],'--',label='BESS',c='#21896b');style(ax,'Potência reativa','Mvar')
    for ax in axs.flat:ax.set_xlim(.6,30)
    for ax in axs[-1]:ax.set_xlabel('Tempo [s]')
    fig.suptitle('Data center intermitente — comparação PSCAD/EMTDC\nBESS 5 MW / 2,5 MWh • potências com média móvel de um ciclo',fontsize=16)
    fig.tight_layout(rect=(0,0,1,.95));fig.savefig(FIG/'comparacao_principal.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(3,1,figsize=(13,10),sharex=True)
    for ax,(lo,hi) in zip(axs,[(1.8,2.4),(6,7),(20,21)]):
        ax.plot(t,b['Pgrid_MW'],label='Rede sem BESS',c='#c74a40');ax.plot(t,a['Pgrid_MW'],label='Rede com BESS',c='#127a9b');ax.plot(t,a['Pbess_MW'],label='BESS',c='#21896b');style(ax,f'Transitório {lo:g}–{hi:g} s','MW');ax.set_xlim(lo,hi)
    # Independent time windows must not share limits.
    plt.close(fig)
    fig,axs=plt.subplots(3,1,figsize=(13,10))
    for ax,(lo,hi) in zip(axs,[(1.8,2.4),(6,7),(20,21)]):
        ax.plot(t,b['Pgrid_MW'],label='Rede sem BESS',c='#c74a40');ax.plot(t,a['Pgrid_MW'],label='Rede com BESS',c='#127a9b');ax.plot(t,a['Pbess_MW'],label='BESS',c='#21896b');style(ax,f'Transitório {lo:g}–{hi:g} s','MW');ax.set_xlim(lo,hi);ax.set_xlabel('Tempo [s]')
    fig.tight_layout();fig.savefig(FIG/'transitorios_comparados.png',dpi=150);plt.close(fig)
    n=round(.1/np.median(np.diff(t)));rrt=t[n:]
    fig,axs=plt.subplots(3,1,figsize=(13,10),sharex=True)
    for d,label,col in [(b,'Sem BESS','#c74a40'),(a,'Com BESS','#127a9b')]:axs[0].plot(rrt,(d['Pgrid_MW'][n:]-d['Pgrid_MW'][:-n])/(t[n:]-t[:-n]),label=label,color=col,lw=.8)
    style(axs[0],'Rampa em janela de 100 ms','MW/s')
    axs[1].plot(t,average(t,np.gradient(raw['Charge_kAs'],t)),label='Corrente da bateria');style(axs[1],'Corrente medida: positivo = descarga','kA')
    for k in ['Power_limit','Current_limit','Modulation_limit','SOC_block']:axs[2].plot(t,raw[k],label=k,lw=.7)
    style(axs[2],'Estados de limitação','Estado');axs[-1].set_xlabel('Tempo [s]')
    for ax in axs:ax.set_xlim(.6,30)
    fig.tight_layout();fig.savefig(FIG/'rampas_corrente_limites.png',dpi=150);plt.close(fig)
def plot_soc(d,label):
    fig,axs=plt.subplots(3,1,figsize=(12,9),sharex=True);t=d['time']
    axs[0].plot(t,d['SOC_pct'],label='SOC');axs[0].axhline(20 if label=='soc_low' else 80,color='red',ls='--',label='Limite');style(axs[0],label,'SOC [%]')
    axs[1].plot(t,battery_power(d),label='Bateria CC');axs[1].plot(t,average(t,d['Pbess_MW']),label='BESS CA');axs[1].plot(t,d['Pbess_ref_MW'],'--',label='Referência CA',alpha=.7);style(axs[1],'Atuação física e recuperação','MW')
    axs[2].plot(t,d['SOC_block'],label='Bloqueio por SOC');style(axs[2],'Estado da proteção','Estado');axs[2].set_xlabel('Tempo [s]')
    fig.tight_layout();fig.savefig(FIG/(label+'.png'),dpi=150);plt.close(fig)
def plot_switching(d):
    t=d['time'];m=(t>=.95)&(t<=.953)
    fig,axs=plt.subplots(3,1,figsize=(12,9),sharex=True)
    for k in ['Carrier','Mod_A']:axs[0].plot(t[m],d[k][m],label=k)
    style(axs[0],'PWM com resolução de 5 µs','pu')
    for k in ['Gate_AH','Gate_AL']:axs[1].step(t[m],d[k][m],where='post',label=k,alpha=.7)
    style(axs[1],'Pulsos complementares — braço A','Estado')
    for ph in 'ABC':axs[2].plot(t[m],d[f'IL{ph}_kA'][m],label=ph)
    style(axs[2],'Correntes CA no ensaio detalhado','kA');axs[2].set_xlabel('Tempo [s]')
    fig.tight_layout();fig.savefig(FIG/'pwm_detalhado.png',dpi=160);plt.close(fig)
if __name__=='__main__':
    raise SystemExit(0 if validate()['status']=='PASS' else 1)
