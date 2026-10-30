"""Independent shaft modes; native multimass Units=12 (H seconds, K pu/rad)."""
import numpy as np
import xml.etree.ElementTree as ET

def natural_modes(h,k,rpm=3600):
    h=np.asarray(h,dtype=float);k=np.asarray(k,dtype=float)
    if h.ndim!=1 or k.ndim!=1 or len(h)<2 or len(k)!=len(h)-1 or not np.all(np.isfinite(h)) or not np.all(np.isfinite(k)) or np.any(h<=0) or np.any(k<=0) or not np.isfinite(rpm) or rpm<=0:
        raise ValueError('Positive H, adjacent K and rpm required; len(K)=len(H)-1')
    omega=rpm*2*np.pi/60
    mass=2*h/omega
    incidence=np.zeros((len(k),len(h)))
    for i in range(len(k)):incidence[i,i:i+2]=[1,-1]
    stiffness=incidence.T@np.diag(k)@incidence
    lam,u=np.linalg.eigh(stiffness/np.sqrt(mass[:,None]*mass[None,:]))
    lam[np.abs(lam)<max(1,np.max(np.abs(lam)))*1e-12]=0
    modes=u/np.sqrt(mass[:,None])
    modes/=np.max(np.abs(modes),axis=0)
    return np.sqrt(np.maximum(lam,0))/(2*np.pi),modes

def shaft_parameters(project):
    root=ET.parse(project).getroot()
    mm=next(u for u in root.iter('User') if u.get('defn')=='master:multimass2')
    p={x.get('name'):x.get('value') for x in mm.findall('./paramlist/param')}
    def number(key):return float(p[key].split()[0])
    n=int(number('N'))
    if int(number('Units'))!=12:raise ValueError('Modal calculation expects native unit system 12 / 9b')
    if n!=3:raise ValueError('This teaching report expects the delivered three-mass topology')
    return dict(H=[number('H'+str(i)) for i in range(1,n+1)],K=[number('K12'),number('K23')],
                rpm=number('RPM'),MVA=number('MVA'),generator_mass=int(number('GenID')),
                torque_shares=[number('TF'+str(i)) for i in range(1,n+1)],
                mutual_damping=[number('MD12'),number('MD23')])

if __name__=='__main__':
    import argparse,json
    ap=argparse.ArgumentParser(description='Calculate mechanical modes from the actual native shaft parameters')
    ap.add_argument('project',help='Path to a saved generator .pscx');args=ap.parse_args()
    p=shaft_parameters(args.project);f,v=natural_modes(p['H'],p['K'],p['rpm'])
    print(json.dumps(dict(parameters=p,frequencies_Hz=f.tolist(),mode_shapes=v.tolist()),indent=2))
