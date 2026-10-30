"""Baseline-relative shaft twist; common physical-to-visual mapping for both cases."""
from pathlib import Path
import json
import numpy as np

GAUGE_GAIN = 200.
REFERENCE_WINDOW = (1.8, 1.95)
EVENT_WINDOW = (1.8, 2.8)


def twist_change(t, theta_left, theta_right, reference_window=REFERENCE_WINDOW):
    t=np.asarray(t,dtype=float)
    left=np.asarray(theta_left,dtype=float); right=np.asarray(theta_right,dtype=float)
    if t.ndim!=1 or left.shape!=t.shape or right.shape!=t.shape or len(t)<2:
        raise ValueError('Time and angle arrays must have identical one-dimensional shapes')
    if not (np.isfinite(t).all() and np.isfinite(left).all() and np.isfinite(right).all()):
        raise ValueError('Time and angle arrays must be finite')
    if np.any(np.diff(t)<=0):
        raise ValueError('Time must increase strictly')
    ref=(t>=reference_window[0])&(t<reference_window[1])
    if ref.sum()<2:
        raise ValueError('Insufficient pre-step reference samples')
    relative=left-right
    return relative-float(np.mean(relative[ref]))


def visual_deflection(delta_twist):
    """Return amplified deflection in radians; no case-dependent normalization."""
    return GAUGE_GAIN*np.asarray(delta_twist)


def load_twist_data(path):
    result={}
    with np.load(path) as d:
        for case in ['without','with']:
            t=d[case+'__time']
            result[case]={
                'time':t,
                'delta':twist_change(t,d[case+'__Shaft_theta2_rad'],d[case+'__Shaft_theta3_rad']),
                'torque':d[case+'__Shaft_T23_pu'],
            }
    return result


def summary(data):
    report={'reference_window_s':list(REFERENCE_WINDOW),'reference_interval':'left-inclusive, right-exclusive',
            'event_window_s':list(EVENT_WINDOW),'visual_gain_for_both_cases':GAUGE_GAIN,
            'units':'Physical readouts in mrad; amplified pointer deflections in radians.',
            'method':'(theta2-theta3) minus the pre-step mean, with no filtering or independent normalization.',
            'limitation':'Observed event only; BESS torsional amplitudes remain timestep sensitive. No damping benefit is quantified.',
            'cases':{}}
    for case,d in data.items():
        t=d['time'];v=d['delta'];m=(t>=EVENT_WINDOW[0])&(t<=EVENT_WINDOW[1])
        ref=(t>=REFERENCE_WINDOW[0])&(t<REFERENCE_WINDOW[1])
        report['cases'][case]={'baseline_mean_change_rad':float(np.mean(v[ref])),
            'minimum_change_mrad':float(v[m].min()*1000),'maximum_change_mrad':float(v[m].max()*1000),
            'peak_absolute_change_mrad':float(np.max(np.abs(v[m]))*1000),
            'peak_visual_deflection_deg':float(np.rad2deg(np.max(np.abs(visual_deflection(v[m])))))}
    return report


if __name__=='__main__':
    root=Path(__file__).resolve().parent
    r=summary(load_twist_data(root/'data/display.npz'))
    (root/'evidence/shaft_twist_revision.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps(r,indent=2))
