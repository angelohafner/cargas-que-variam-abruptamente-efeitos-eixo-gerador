"""Independent physical checks of fresh 250--500 MW EMTDC results."""
from pathlib import Path
import json, xml.etree.ElementTree as ET
import numpy as np
from analysis import read_run, average, metrics
from torsion_math import shaft_parameters, natural_modes
from torsion_identification import identify_modes
from run_generator_case import sha
from run_scale_250_500 import LABELS, NAMES
from scale_models_250_500 import params, number
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'validation/scale_250_500'
KEYS=['time','Pgrid_MW','Pload_MW','Pload_command_MW','Pbess_MW','Pbess_ref_MW','Vload_kV',
      'Igrid_kA','SOC_pct','Vdc_kV','Charge_kAs','Id_kA','Mod_A','Mod_B','Mod_C','Ebat_MJ',
      'Ebess_MJ','Eloss_MJ','Ecap_MJ','Eind_MJ','Edis_MJ','Echg_MJ','SOC_block',
      'Generator_Hz','Gas_Tm_pu','Gas_power_pu','Generator_Te_pu','Rotor_released','Machine_enabled',
      'Shaft_T12_pu','Shaft_T23_pu','Shaft_rel12_rad_s','Shaft_rel23_rad_s',
      'Shaft_dw1_rad_s','Shaft_dw2_rad_s','Shaft_dw3_rad_s']
def rms(x):return float(np.sqrt(np.mean(np.square(x))))
def peak(x):return float(np.max(np.abs(x)))
def speeds(d):return np.column_stack([d[f'Shaft_dw{i}_rad_s'] for i in (1,2,3)])
def delta(d,key):return float(d[key][-1]-d[key][np.searchsorted(d['time'],1.5)])

def validate():
    manifest=json.loads((ROOT/'results/scale_250_500/latest_suite.json').read_text())
    if manifest['status']!='COMPLETE':raise ValueError('Current suite is incomplete')
    checks=[];data={};modal={};sensitivity={};comparisons={};filtered={};energy={};protection={}
    def check(name,condition,value=None,limit=None):
        checks.append(dict(name=name,status='PASS' if bool(condition) else 'FAIL',value=value,limit=limit))
    for label,path in manifest['cases'].items():
        folder=(ROOT/path).resolve()
        if not folder.is_relative_to(ROOT):raise ValueError('External results path')
        print('READ',label,flush=True)
        raw=read_run(folder,required=['Pgrid_MW','Pload_MW','Pload_command_MW'])
        d={k:raw[k].copy() for k in KEYS if k in raw};del raw;data[label]=d
        check(label+'_fresh_complete_source_bound_run',True)
        users=list(ET.parse(next(folder.glob('*.pscx'))).getroot().iter('User'))
        t=d['time'];m=t>=1.5
        command=d['Pload_command_MW'];check(label+'_load_command_250_500_MW',command.min()>=250-1e-6 and command.max()<=500+1e-6,[float(command.min()),float(command.max())],[250,500])
        v=average(t,d['Vload_kV'])[m]/34.5
        check(label+'_PCC_voltage_pu',v.min()>.9 and v.max()<1.1,[float(v.min()),float(v.max())],[.9,1.1])
        if 'generator' in label:
            machine=params(next(u for u in users if u.get('defn')=='master:sync_machine'))
            sp=shaft_parameters(next(folder.glob('*.pscx')))
            check(label+'_native_multimass_and_1000MVA_bases',machine['MM']=='0' and number(machine['MVA'])==1000 and sp['MVA']==1000 and not any(u.get('defn')=='master:source_3' for u in users))
            check(label+'_machine_and_rotor_released',np.all(d['Machine_enabled'][m]>.5) and np.all(d['Rotor_released'][m]>.5) and np.all(d['Rotor_released'][t<1.19]<.5))
            hz=d['Generator_Hz'][m];check(label+'_frequency_Hz',hz.min()>57 and hz.max()<63,[float(hz.min()),float(hz.max())],[57,63])
            h=np.asarray(sp['H']);omega=sp['rpm']*2*np.pi/60;coi=speeds(d)@h/(h.sum()*omega)
            tm=(d['Gas_Tm_pu']-d['Generator_Te_pu'])[m];tt=t[m]
            impulse=np.r_[0,np.cumsum(.5*(tm[1:]+tm[:-1])*np.diff(tt))]
            error=peak(2*h.sum()*(coi[m]-coi[m][0])-impulse)
            check(label+'_angular_momentum_residual_pu_s',error<.002,error,.002)
            error=peak((d['Gas_power_pu']-d['Gas_Tm_pu']*(1+d['Shaft_dw1_rad_s']/omega))[m])
            check(label+'_power_at_driven_mass_residual_pu',error<5e-5,error,5e-5)
        if label.startswith('pulse_'):
            f,shapes=natural_modes(sp['H'],sp['K'],sp['rpm']);mm=(t>=5.3)&(t<=19.8)
            check(label+'_post_pulse_constant_demand',np.ptp(command[mm])<1e-6)
            modal[label]=identify_modes(t[mm],speeds(d)[mm],sp['H'],f[1:],shapes[:,1:])
            for i,item in enumerate(modal[label],1):
                for suffix,value,limit,ok in [('frequency_error',item['relative_error'],.02,item['relative_error']<.02),
                    ('shape_MAC',item['MAC'],.95,item['MAC']>.95),('peak_to_background',item['peak_to_median'],5,item['peak_to_median']>5)]:
                    check(f'{label}_mode{i}_{suffix}',ok,value,limit)
    t=data[LABELS[0]]['time'];m=t>=1.5
    for label,name in zip(LABELS,NAMES):
        d=data[label];folder=ROOT/manifest['cases'][label]
        receipt=json.loads((folder/'run_receipt.json').read_text())
        check(label+'_delivered_file_matches_executed_file',sha(ROOT/'pscad'/(name+'.pscx'))==receipt['project_sha256'])
        check(label+'_same_time_axis',np.array_equal(t,d['time']))
        check(label+'_same_intermittent_command',np.array_equal(data[LABELS[0]]['Pload_command_MW'],d['Pload_command_MW']))
        check(label+'_both_endpoints_exercised',abs(d['Pload_command_MW'].min()-250)<1e-6 and abs(d['Pload_command_MW'].max()-500)<1e-6)
        a={k:average(t,d[k]) for k in ['Pgrid_MW','Pload_MW','Pload_command_MW','Pbess_MW','Vload_kV','Igrid_kA']};filtered[label]=a
        err=rms((a['Pload_MW']-a['Pload_command_MW'])[m]);check(label+'_load_tracking_RMS_MW',err<25,err,25)
        balance=a['Pgrid_MW']+a['Pbess_MW']-a['Pload_MW']-3*.0025*a['Igrid_kA']**2
        err=rms(balance[m]);check(label+'_PCC_balance_RMS_MW',err<1.5,err,1.5)
        energy[label]=float(np.trapezoid(d['Pload_MW'][m],t[m]))
        err=abs(energy[label]/energy[LABELS[0]]-1);check(label+'_same_served_energy',err<.03,err,.03)
        comparisons[label]=metrics(t[m],a['Pgrid_MW'][m])
        if label.endswith('bess'):
            a.update({k:average(t,d[k]) for k in ['Pbess_ref_MW','Id_kA','Vdc_kV']})
            check(label+'_SOC_limits',d['SOC_pct'].min()>=20 and d['SOC_pct'].max()<=80,[float(d['SOC_pct'].min()),float(d['SOC_pct'].max())],[20,80])
            err=peak(d['SOC_pct']-(50-100*d['Charge_kAs']/((125/1.5)*3600)))
            check(label+'_coulomb_count_percentage_points',err<1e-4,err,1e-4)
            for suffix,value,limit in [('power_MW',peak(a['Pbess_MW'][m]),260),('aggregate_current_kA',peak(a['Id_kA'][m]),341),
                ('modulation',max(peak(d['Mod_'+p]) for p in 'ABC'),.980001),('tracking_RMS_MW',rms((a['Pbess_MW']-a['Pbess_ref_MW'])[m]),12.5)]:
                check(label+'_'+suffix,value<=limit,value,limit)
            v=a['Vdc_kV'][m];check(label+'_DC_voltage_kV',v.min()>1.3 and v.max()<1.7,[float(v.min()),float(v.max())],[1.3,1.7])
            res=delta(d,'Ebat_MJ')-delta(d,'Ebess_MJ')-delta(d,'Eloss_MJ')-delta(d,'Ecap_MJ')-delta(d,'Eind_MJ')
            err=abs(res)/max(delta(d,'Edis_MJ')+delta(d,'Echg_MJ'),1)
            check(label+'_energy_balance_relative',err<.02,dict(residual_MJ=res,relative=err),.02)
    reductions={}
    for prefix in ['ideal','generator']:
        base=prefix+'_base';bess=prefix+'_bess'
        reductions[prefix]={k:100*(1-comparisons[bess][k]/comparisons[base][k]) for k in ['std_MW','maximum_ramp_MW_per_s','peak_to_peak_MW']}
        for start,end in [(6,10),(20,25)]:
            mm=(t>=start)&(t<=end);mb=metrics(t[mm],filtered[base]['Pgrid_MW'][mm]);ma=metrics(t[mm],filtered[bess]['Pgrid_MW'][mm])
            for k in ['std_MW','maximum_ramp_MW_per_s']:
                red=100*(1-ma[k]/mb[k]);check(f'{prefix}_pulses_{start}_{end}_{k}_reduction_percent',red>50,red,50)
    for label,sign,initial in [('soc_low',1,20.015),('soc_high',-1,79.985)]:
        d=data[label];tt=d['time'];active=(abs(d['SOC_block'])>.5)&(tt<2.95)
        check(label+'_protection_activated',active.any())
        check(label+'_SOC_bounds',d['SOC_pct'].min()>=19.9999 and d['SOC_pct'].max()<=80.0001,[float(d['SOC_pct'].min()),float(d['SOC_pct'].max())],[20,80])
        # Integrated terminal energy avoids PWM aliasing in current sampling.
        power=average(tt,np.gradient(d['Ebat_MJ'],tt));violation=1e9;activation=None
        if active.any():
            activation=float(tt[np.flatnonzero(active)[0]]);steady=active&(tt>activation+.08)
            if steady.any():violation=float(np.max(sign*power[steady]))
        check(label+'_actual_forbidden_power_MW',violation<=1,violation,1)
        recovery=(tt>3.5)&(tt<5.5);actual=float(np.mean(sign*power[recovery]))
        check(label+'_reverse_recovery_allowed_MW',actual<-25,actual,-25)
        err=peak(d['SOC_pct']-(initial-100*d['Charge_kAs']/((125/1.5)*3600)))
        check(label+'_coulomb_count_percentage_points',err<1e-4,err,1e-4)
        protection[label]=dict(activation_s=activation,forbidden_power_MW=violation,recovery_MW=actual)
    for case in ['generator_base','generator_bess']:
        coarse=modal['pulse_'+case];fine=modal['pulse_'+case+'_fine']
        change=[100*(b['relative_speed_amplitude']/a['relative_speed_amplitude']-1) for a,b in zip(coarse,fine)]
        sensitivity[case]=dict(amplitude_change_percent=change,amplitudes_within_10percent=bool(max(abs(x) for x in change)<10))
        for i,(a,b) in enumerate(zip(coarse,fine),1):
            err=abs(b['frequency_Hz']/a['frequency_Hz']-1);check(f'{case}_half_step_mode{i}_frequency',err<.02,err,.02)
    d=data['profile_generator_bess_fine'];tf=d['time'];mm=(tf>=1.5)&(tf<=5.95);coarse=data['generator_bess']
    for key,scale in [('Pgrid_MW',500),('Pload_MW',500),('Pbess_MW',250),('Vdc_kV',1.5),('Generator_Hz',60),('SOC_pct',100)]:
        a=np.interp(tf,coarse['time'],average(coarse['time'],coarse[key]));b=average(tf,d[key]);err=rms((a-b)[mm])/scale
        check('profile_half_step_'+key+'_normalized_RMS',err<.03,err,.03)
    params_shaft=shaft_parameters(ROOT/'pscad'/('DataCenter_Gerador_Sem_BESS.pscx'));f,shapes=natural_modes(params_shaft['H'],params_shaft['K'],params_shaft['rpm'])
    result=dict(status='PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL',checks=checks,run_folders=manifest['cases'],
        four_case_power_metrics=comparisons,BESS_reductions_percent=reductions,served_energy_MJ=energy,protection=protection,
        shaft=params_shaft,calculated_frequencies_Hz=f.tolist(),calculated_shapes=shapes.tolist(),modal_identification=modal,
        modal_step_sensitivity=sensitivity,method=dict(power_window_s=[1.5,30],power_average_s=1/60,ramp_interval_s=.1,
        modal_window_s=[5.3,19.8],modal_signal='Raw mechanical speed minus inertia-weighted common speed; Hann spectrum, MAC association.',
        scope='Didactic aggregate model; fresh 250--500 MW runs. No manufacturer calibration. BESS modal amplitude convergence assessed separately; no damping-ratio or energy-saving claim.'))
    (OUT/'validation.json').write_text(json.dumps(result,indent=2))
    from plot_scale_250_500 import make_figures
    make_figures(data,result)
    print(result['status'],sum(c['status']=='PASS' for c in checks),'/',len(checks),flush=True)
    for c in checks:
        if c['status']=='FAIL':print(c,flush=True)
    print('REDUCTIONS',reductions,'STEP SENSITIVITY',sensitivity,flush=True)
    return result
if __name__=='__main__':raise SystemExit(0 if validate()['status']=='PASS' else 1)
