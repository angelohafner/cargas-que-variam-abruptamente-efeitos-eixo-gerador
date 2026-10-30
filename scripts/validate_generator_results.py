"""Audit actual EMTDC generator runs and identify free torsional modes.

Power comparisons use the same 1.5--30 s window, one-cycle average and
100 ms ramp. Modal analysis uses RAW mechanical speeds, never cycle averaged.
"""
from pathlib import Path
import json, hashlib
import xml.etree.ElementTree as ET
import numpy as np
from analysis import read_run, average, metrics
from torsion_math import natural_modes, shaft_parameters
from torsion_identification import identify_modes, spectrum, relative_speeds

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/generator'
KEYS=['time','Pgrid_MW','Pload_MW','Pload_command_MW','Pbess_MW','Pbess_ref_MW',
      'Vload_kV','Igrid_kA','SOC_pct','Vdc_kV','Generator_Hz','Generator_Vt_pu',
      'Gas_Tm_pu','Gas_power_pu','Generator_Te_pu','Generator_Ef_pu','Rotor_released','Machine_enabled',
      'Shaft_T12_pu','Shaft_T23_pu','Shaft_rel12_rad_s','Shaft_rel23_rad_s',
      'Shaft_dw1_rad_s','Shaft_dw2_rad_s','Shaft_dw3_rad_s','Excitation_Hz',
      'Charge_kAs','Id_kA','Mod_A','Mod_B','Mod_C','Ebat_MJ','Ebess_MJ','Eloss_MJ',
      'Ecap_MJ','Eind_MJ','Edis_MJ','Echg_MJ','Power_limit','Current_limit','SOC_block']
checks=[]
def check(name,passed,value=None,limit=None):
    checks.append(dict(name=name,status='PASS' if bool(passed) else 'FAIL',value=value,limit=limit))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rms(v):return float(np.sqrt(np.mean(np.square(v))))
def peak(v):return float(np.max(np.abs(v)))
def load(folder):
    raw=read_run(folder,required=['Pload_MW','Pgrid_MW'])
    return {k:raw[k].copy() for k in KEYS if k in raw}
def speeds(d):return np.column_stack([d[f'Shaft_dw{i}_rad_s'] for i in (1,2,3)])
def free_modes(d,params):
    f,s=natural_modes(params['H'],params['K'],params['rpm'])
    t=d['time'];m=(t>=5.3)&(t<=19.8)
    return identify_modes(t[m],speeds(d)[m],params['H'],f[1:],s[:,1:])
def delta(d,k,start=1.5):return float(d[k][-1]-d[k][np.searchsorted(d['time'],start)])

def main():
    manifest=json.loads((ROOT/'results/generator/latest_suite.json').read_text())
    if manifest['status']!='COMPLETE':raise ValueError('Generator suite is incomplete')
    cases=manifest['cases'];data={};parameters={}
    for label,path in cases.items():
        folder=(ROOT/path).resolve()
        if not folder.is_relative_to(ROOT):raise ValueError('Path outside delivery')
        print('Reading and hash-verifying',label,flush=True)
        data[label]=load(folder)
        check(label+'_fresh_hash_bound_complete_run',True)
        if label.startswith('ideal'):continue
        project=next(folder.glob('*.pscx'));parameters[label]=shaft_parameters(project)
        tree=ET.parse(project);users=list(tree.iter('User'))
        machine=next(u for u in users if u.get('defn')=='master:sync_machine')
        p={x.get('name'):x.get('value') for x in machine.findall('./paramlist/param')}
        check(label+'_native_multimass_enabled_no_ideal_source',p['MM']=='0' and not any(u.get('defn')=='master:source_3' for u in users))
        d=data[label];t=d['time'];m=t>=1.5
        check(label+'_rotor_released_after_initialization',np.all(d['Rotor_released'][m]>.5) and np.all(d['Rotor_released'][t<1.19]<.5))
        check(label+'_machine_enabled_after_initialization',np.all(d['Machine_enabled'][m]>.5))
        hz=[float(d['Generator_Hz'][m].min()),float(d['Generator_Hz'][m].max())]
        check(label+'_frequency_Hz',hz[0]>57 and hz[1]<63,hz,[57,63])
        vv=average(t,d['Vload_kV'])/13.8;lim=[float(vv[m].min()),float(vv[m].max())]
        check(label+'_PCC_voltage_pu',lim[0]>.9 and lim[1]<1.1,lim,[.9,1.1])
        # Mutual damping cancels from total angular momentum; SD=0 in these cases.
        h=np.asarray(parameters[label]['H']);omega=parameters[label]['rpm']*2*np.pi/60
        coi=speeds(d)@h/(h.sum()*omega)
        tm=d['Gas_Tm_pu'][m]-d['Generator_Te_pu'][m];tt=t[m]
        integrated=np.concatenate([[0],np.cumsum(.5*(tm[1:]+tm[:-1])*np.diff(tt))])
        inertial=2*h.sum()*(coi[m]-coi[m][0])
        error=peak(inertial-integrated)
        check(label+'_angular_momentum_residual_pu_s',error<.002,error,.002)
        local_speed=1+d['Shaft_dw1_rad_s']/omega
        power_error=peak((d['Gas_power_pu']-d['Gas_Tm_pu']*local_speed)[m])
        check(label+'_gas_power_at_driven_mass_residual_pu',power_error<5e-5,power_error,5e-5)
    t=data['ideal_base']['time'];m=t>=1.5;profiles=['ideal_base','ideal_bess','profile_base','profile_bess']
    comparison={};energy={};filtered={}
    for label in profiles:
        d=data[label]
        check(label+'_same_profile_time_axis',np.array_equal(t,d['time']))
        check(label+'_same_load_command',np.array_equal(data['ideal_base']['Pload_command_MW'],d['Pload_command_MW']))
        a={k:average(t,d[k]) for k in ['Pgrid_MW','Pload_MW','Pbess_MW','Vload_kV','Igrid_kA']};filtered[label]=a
        comparison[label]=metrics(t[m],a['Pgrid_MW'][m])
        energy[label]=float(np.trapezoid(d['Pload_MW'][m],t[m]))
        balance=a['Pgrid_MW']+a['Pbess_MW']-a['Pload_MW']-3*.02*a['Igrid_kA']**2
        check(label+'_PCC_balance_RMS_MW',rms(balance[m])<.03,rms(balance[m]),.03)
        e=abs(energy[label]/energy['ideal_base']-1)
        check(label+'_served_energy_relative_to_ideal_base',e<.03,e,.03)
    reductions={}
    for prefix,base,bess in [('ideal','ideal_base','ideal_bess'),('generator','profile_base','profile_bess')]:
        reductions[prefix]={k:100*(1-comparison[bess][k]/comparison[base][k]) for k in ['std_MW','maximum_ramp_MW_per_s','peak_to_peak_MW']}
    d=data['profile_bess'];a={k:average(t,d[k]) for k in ['Pbess_MW','Pbess_ref_MW','Id_kA','Vdc_kV']}
    check('generator_BESS_SOC_limits',d['SOC_pct'].min()>=20 and d['SOC_pct'].max()<=80,[float(d['SOC_pct'].min()),float(d['SOC_pct'].max())],[20,80])
    check('generator_BESS_coulomb_count_percentage_points',peak(d['SOC_pct']-(50-100*d['Charge_kAs']/(1.6666666667*3600)))<1e-4)
    check('generator_BESS_power_limit_MW',peak(a['Pbess_MW'][m])<=5.2,peak(a['Pbess_MW'][m]),5.2)
    check('generator_BESS_current_dynamic_limit_kA',peak(a['Id_kA'][m])<=6.82,peak(a['Id_kA'][m]),6.82)
    check('generator_BESS_modulation_limit',max(peak(d['Mod_'+p]) for p in 'ABC')<=.980001)
    check('generator_BESS_power_tracking_RMS_MW',rms((a['Pbess_MW']-a['Pbess_ref_MW'])[m])<.25,rms((a['Pbess_MW']-a['Pbess_ref_MW'])[m]),.25)
    check('generator_BESS_DC_voltage_kV',a['Vdc_kV'][m].min()>1.3 and a['Vdc_kV'][m].max()<1.7,[float(a['Vdc_kV'][m].min()),float(a['Vdc_kV'][m].max())],[1.3,1.7])
    residual=delta(d,'Ebat_MJ')-delta(d,'Ebess_MJ')-delta(d,'Eloss_MJ')-delta(d,'Ecap_MJ')-delta(d,'Eind_MJ')
    throughput=delta(d,'Edis_MJ')+delta(d,'Echg_MJ');err=abs(residual)/max(throughput,1)
    check('generator_BESS_energy_balance_relative',err<.02,{'residual_MJ':residual,'relative':err},.02)
    modal={}
    for label in ['pulse_base','pulse_base_fine','pulse_bess','pulse_bess_fine','pulse_bess_finer','pulse_stiffer']:
        d=data[label];modal[label]=free_modes(d,parameters[label]);mfree=(d['time']>=5.3)&(d['time']<=19.8)
        check(label+'_free_response_command_constant',np.ptp(d['Pload_command_MW'][mfree])<1e-7)
        for i,item in enumerate(modal[label],1):
            check(f'{label}_mode{i}_frequency_error',item['relative_error']<.02,item['relative_error'],.02)
            check(f'{label}_mode{i}_shape_MAC',item['MAC']>.95,item['MAC'],.95)
            check(f'{label}_mode{i}_peak_to_local_median',item['peak_to_median']>5,item['peak_to_median'],5)
    for i in range(2):
        ratio=modal['pulse_stiffer'][i]['frequency_Hz']/modal['pulse_base'][i]['frequency_Hz']
        check(f'stiffness_mode{i+1}_frequency_ratio',abs(ratio/1.2-1)<.02,ratio,1.2)
        err=abs(modal['pulse_bess_fine'][i]['frequency_Hz']/modal['pulse_bess'][i]['frequency_Hz']-1)
        check(f'half_step_mode{i+1}_frequency_relative_difference',err<.02,err,.02)
        err=abs(modal['pulse_base_fine'][i]['frequency_Hz']/modal['pulse_base'][i]['frequency_Hz']-1)
        check(f'base_half_step_mode{i+1}_frequency_relative_difference',err<.02,err,.02)
        err=abs(modal['pulse_bess_finer'][i]['frequency_Hz']/modal['pulse_bess_fine'][i]['frequency_Hz']-1)
        check(f'quarter_step_mode{i+1}_frequency_relative_difference',err<.02,err,.02)
    coarse=data['pulse_bess'];fine=data['pulse_bess_fine'];tc=coarse['time'];mm=tc>=1.5
    for key,scale in [('Pgrid_MW',10),('Pbess_MW',5),('Vdc_kV',1.5),('Generator_Hz',60),('Shaft_T12_pu',1),('Shaft_T23_pu',1)]:
        aa=average(tc,coarse[key]);bb=np.interp(tc,fine['time'],average(fine['time'],fine[key]))
        error=rms((aa-bb)[mm])/scale
        check('half_step_'+key+'_normalized_RMS',error<.03,error,.03)
    forced={}
    for label in ['sine_off','sine_mode1']:
        d=data[label];tt=d['time'];mm=(tt>=9)&(tt<=12.8)
        f=8 if label=='sine_off' else 10.6108735692
        # Least-squares harmonic fit separates forcing component from offset/drift.
        design=np.column_stack([np.ones(mm.sum()),tt[mm]-tt[mm].mean(),np.cos(2*np.pi*f*tt[mm]),np.sin(2*np.pi*f*tt[mm])])
        def amp(key):
            c=np.linalg.lstsq(design,d[key][mm],rcond=None)[0];return float(np.hypot(c[-2],c[-1]))
        pl=amp('Pload_MW');r=amp('Shaft_rel12_rad_s')
        forced[label]={'frequency_Hz':f,'actual_load_harmonic_MW':pl,'relative_speed_harmonic_rad_s':r,'gain_rad_s_per_MW':r/pl}
    resonance=forced['sine_mode1']['gain_rad_s_per_MW']/forced['sine_off']['gain_rad_s_per_MW']
    check('resonance_gain_relative_to_8_Hz',resonance>2,resonance,'>2')
    original=json.loads((OUT/'original_hashes.json').read_text())
    check('original_ideal_projects_unchanged',all(sha(ROOT/'pscad'/n)==h for n,h in original.items()))
    for label,name in [('chirp_base','DataCenter_Gerador_Sem_BESS'),('chirp_bess','DataCenter_Gerador_Com_BESS')]:
        rec=json.loads((ROOT/cases[label]/'run_receipt.json').read_text())
        check(label+'_canonical_file_matches_validated_source',sha(ROOT/'pscad'/(name+'.pscx'))==rec['project_sha256'])
    frequencies,shapes=natural_modes(parameters['pulse_base']['H'],parameters['pulse_base']['K'],parameters['pulse_base']['rpm'])
    sensitivity={}
    for name,lo,hi in [('base_10_to_5_us','pulse_base','pulse_base_fine'),('bess_10_to_5_us','pulse_bess','pulse_bess_fine'),('bess_5_to_2p5_us','pulse_bess_fine','pulse_bess_finer')]:
        changes=[100*(modal[hi][i]['relative_speed_amplitude']/modal[lo][i]['relative_speed_amplitude']-1) for i in range(2)]
        sensitivity[name]={'modal_amplitude_change_percent':changes,'amplitude_convergence_within_10percent':bool(max(abs(x) for x in changes)<10)}
    result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','checks':checks,'run_folders':cases,
        'shaft':parameters['pulse_base'],'calculated_frequencies_Hz':frequencies.tolist(),'calculated_shapes':shapes.tolist(),
        'modal_identification':modal,'forced_response':forced,'resonance_gain':resonance,
        'BESS_modal_amplitude_ratio':[modal['pulse_bess'][i]['relative_speed_amplitude']/modal['pulse_base'][i]['relative_speed_amplitude'] for i in range(2)],
        'spectral_amplitude_step_sensitivity':sensitivity,
        'four_case_power_metrics':comparison,'BESS_reductions_percent':reductions,'served_load_energy_MJ':energy,
        'method':{'power_window_s':[1.5,30],'power_average_s':1/60,'ramp_interval_s':.1,'free_mode_window_s':[5.3,19.8],
                  'modal_signal':'raw mechanical speed deviations after inertia-weighted common-speed removal',
                  'modal_amplitude_formula':'sqrt(sum(H_i * abs(speed_spectrum_i)^2) / sum(H_i)), rad/s',
                  'modal_spectrum':'Hann amplitude spectrum; local maxima with H-weighted MAC >= 0.95; log-parabolic frequency interpolation; rejected stronger peaks retained.',
                  'modal_amplitude_note':'Post-pulse finite-window spectral amplitude; active electrical/control forcing remains with BESS. Not a damping-ratio estimate. Amplitude convergence reported separately from frequency/electrical checks.',
                  'scope':'Didactic parameters, native EMT model, no manufacturer validation. Ideal references reused unchanged.'}}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    from plot_generator_results import make_figures
    make_figures(data,result)
    print(result['status'],sum(c['status']=='PASS' for c in checks),'/',len(checks),flush=True)
    for c in checks:
        if c['status']=='FAIL':print('FAIL',c,flush=True)
    print('Modal results',json.dumps(modal,indent=2),flush=True)
    print('Power reductions',reductions,'Resonance gain',resonance,flush=True)
    return result
if __name__=='__main__':raise SystemExit(0 if main()['status']=='PASS' else 1)
