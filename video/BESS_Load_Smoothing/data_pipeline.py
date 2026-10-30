"""Prepare a source-bound, portable animation dataset from existing PSCAD runs."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import numpy as np
from source_reader import read_run, average

HERE = Path(__file__).resolve().parent
CHANNELS = ['Pload_command_MW', 'Pload_MW', 'Pgrid_MW', 'Pgen_MW', 'Pbess_MW',
            'Pgrid_ref_MW', 'SOC_pct', 'Generator_Hz', 'Generator_Te_pu', 'Gas_Tm_pu',
            'Shaft_T12_pu', 'Shaft_T23_pu', 'Shaft_rel12_rad_s', 'Shaft_rel23_rad_s',
            'Shaft_theta1_rad', 'Shaft_theta2_rad', 'Shaft_theta3_rad',
            'Shaft_dw1_rad_s', 'Shaft_dw2_rad_s', 'Shaft_dw3_rad_s']
SMOOTH = {'Pload_MW', 'Pgrid_MW', 'Pgen_MW', 'Pbess_MW', 'Generator_Te_pu'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def validate_pair(a, b):
    if not np.array_equal(a['time'], b['time']):
        raise ValueError('Comparison time axes differ')
    if not np.array_equal(a['Pload_command_MW'], b['Pload_command_MW']):
        raise ValueError('Comparison load commands differ')


def power_metrics(t, p, start=1.5, end=30., ramp_interval=.1):
    mask = (t >= start) & (t <= end)
    t, p = t[mask], p[mask]
    if len(t) < 3 or not np.all(np.isfinite(p)):
        raise ValueError('Invalid analysis window')
    n = max(1, round(ramp_interval / np.median(np.diff(t))))
    if len(t) <= n:
        raise ValueError('Analysis window shorter than ramp interval')
    return dict(mean_MW=float(np.mean(p)), std_MW=float(np.std(p)),
                min_MW=float(np.min(p)), max_MW=float(np.max(p)),
                max_ramp_MW_s=float(np.max(np.abs((p[n:]-p[:-n])/(t[n:]-t[:-n])))))


def prepare(root):
    root = Path(root).resolve()
    dest = HERE / 'data'
    dest.mkdir(exist_ok=True)
    evidence = HERE / 'evidence'
    evidence.mkdir(exist_ok=True)
    manifest_path = root/'results/scale_250_500/latest_suite.json'
    suite = json.loads(manifest_path.read_text())
    if suite['status'] != 'COMPLETE':
        raise ValueError('Source suite incomplete')
    audit_path = root/'validation/scale_250_500/validation.json'
    audit = json.loads(audit_path.read_text())
    if audit['status'] != 'PASS':
        raise ValueError('Existing numerical audit is not PASS')
    cases, provenance, raw, display, result = {}, {}, {}, {}, {}
    for suffix, key in [('without', 'generator_base'), ('with', 'generator_bess')]:
        folder = (root/suite['cases'][key]).resolve()
        if not folder.is_relative_to(root):
            raise ValueError('Source path outside project')
        print('Verify and read:', key, flush=True)
        d = read_run(folder, required=CHANNELS)
        cases[suffix] = {k:d[k] for k in ['time']+CHANNELS}
        t = d['time']
        receipt = json.loads((folder/'run_receipt.json').read_text())
        target = evidence/suffix
        target.mkdir(exist_ok=True)
        for p in list(folder.glob('*.pscx'))+list(folder.glob('*.inf'))+[folder/'run_receipt.json']:
            shutil.copy2(p, target/p.name)
        mapping = []
        for line in next(folder.glob('*.inf')).read_text().splitlines():
            m = re.search(r'PGB\((\d+)\).*?Desc="([^"]+)"', line)
            if m and m[2] in CHANNELS:
                i = int(m[1]); mapping.append(dict(channel=m[2], index=i, block=(i-1)//10+1, column=(i-1)%10+1))
        provenance[suffix] = dict(original_folder=str(folder.relative_to(root)).replace('\\','/'),
                                  receipt_sha256=sha(folder/'run_receipt.json'),
                                  source_project_sha256=receipt['project_sha256'],
                                  original_outputs_sha256=receipt['output_sha256'],
                                  time_step_us=receipt['time_step_us'], sample_step_us=receipt['sample_step_us'],
                                  samples=len(t), duration_s=float(t[-1]), channel_mapping=mapping)
        ix = np.arange(0, len(t), 5)  # 0.5 ms traces; raw archive retains every sample.
        if ix[-1] != len(t)-1:
            ix = np.r_[ix, len(t)-1]
        display[suffix+'__time'] = t[ix]
        raw[suffix+'__time'] = t
        result[suffix] = {}
        for ch in CHANNELS:
            raw[suffix+'__'+ch] = d[ch]
            processed = average(t, d[ch]) if ch in SMOOTH else d[ch]
            display[suffix+'__'+ch] = processed[ix]
            if ch in {'Pgrid_MW','Pgen_MW'}:
                result[suffix][ch] = power_metrics(t, processed)
        # Preserve raw Te as a separate trace for the explicitly unfiltered torque scene.
        display[suffix+'__Generator_Te_raw_pu'] = d['Generator_Te_pu'][ix]
        for ch in ['Shaft_T12_pu','Shaft_T23_pu']:
            mask = (t >= 1.8) & (t <= 2.8)
            result[suffix][ch] = {'window_s':[1.8,2.8], 'raw_min_pu':float(d[ch][mask].min()),
                                  'raw_max_pu':float(d[ch][mask].max())}
        result[suffix]['SOC_range_pct'] = [float(d['SOC_pct'].min()),float(d['SOC_pct'].max())]
    validate_pair(cases['without'], cases['with'])
    for field in ['time_step_us','sample_step_us']:
        if provenance['without'][field] != provenance['with'][field]:
            raise ValueError('Mismatched integration/sampling settings')
    result['reductions_percent'] = {
        ch:{metric:100*(1-result['with'][ch][metric]/result['without'][ch][metric])
            for metric in ['std_MW','max_ramp_MW_s']} for ch in ['Pgen_MW','Pgrid_MW']}
    # Independent comparison with the archived audit of the downstream measurement.
    audit_errors = []
    for suffix,key in [('without','generator_base'),('with','generator_bess')]:
        old = audit['four_case_power_metrics'][key]
        for new_key, old_key in [('std_MW','std_MW'),('max_ramp_MW_s','maximum_ramp_MW_per_s')]:
            audit_errors.append(abs(result[suffix]['Pgrid_MW'][new_key]-old[old_key]))
    if max(audit_errors) > 1e-7:
        raise ValueError('Fresh metrics disagree with archived audit')
    result.update(shaft=audit['shaft'], natural_frequencies_Hz=audit['calculated_frequencies_Hz'],
                  modal_step_sensitivity=audit['modal_step_sensitivity'],
                  method={'power_window_s':[1.5,30], 'power_average_s':1/60, 'ramp_interval_s':.1,
                          'shaft_traces':'No time averaging; uniformly sampled at 0.5 ms for display.',
                          'power_measurement':'Pgen_MW is generator-terminal power. Pgrid_MW is measured downstream on the 34.5 kV side.',
                          'initialization':'Events shown only after the 1.2 s rotor release.',
                          'limitation':'BESS torsional amplitudes are not timestep-converged. No physical damping ratio or quantified torsional benefit is claimed.'})
    np.savez_compressed(dest/'raw_selected.npz', **raw)
    np.savez_compressed(dest/'display.npz', **display)
    (dest/'metrics.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    provenance.update(source_suite_sha256=sha(manifest_path), source_audit_sha256=sha(audit_path),
                      status='PASS', checks={'source_receipts_and_outputs':'PASS','same_time_axis':'PASS',
                                             'same_load_command':'PASS','same_integration_settings':'PASS',
                                             'archived_power_metrics':'PASS'},
                      raw_archive_sha256=sha(dest/'raw_selected.npz'), display_archive_sha256=sha(dest/'display.npz'))
    (dest/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    shutil.copy2(audit_path,evidence/'existing_pscad_validation.json')
    shutil.copy2(manifest_path,evidence/'source_suite.json')
    print(json.dumps({'reductions':result['reductions_percent'], 'shaft_ranges':{s:result[s]['Shaft_T23_pu'] for s in ['without','with']},'status':'PASS'},indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--project-root',type=Path,default=HERE.parents[1])
    prepare(p.parse_args().project_root)
