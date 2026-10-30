"""Identify free torsional modes using relative rotor speeds and modal assurance."""
import numpy as np

def spectrum(t,y):
    t=np.asarray(t);y=np.asarray(y)
    dt=float(np.median(np.diff(t)))
    if len(t)<100 or not np.allclose(np.diff(t),dt,rtol=1e-5,atol=1e-10):raise ValueError('Uniform, sufficiently long record required')
    window=np.hanning(len(t));axis=(slice(None),)+(None,)*(y.ndim-1)
    z=np.fft.rfft((y-np.mean(y,axis=0))*window[axis],axis=0)*2/window.sum()
    return np.fft.rfftfreq(len(t),dt),z

def relative_speeds(w,h):
    w=np.asarray(w);h=np.asarray(h)
    return w-(w@h/h.sum())[:,None]

def identify_modes(t,w,h,reference_frequencies,reference_shapes):
    w=relative_speeds(w,h);h=np.asarray(h)
    # Normalize inertia weights so the spectrum retains speed units (rad/s).
    f,z=spectrum(t,w);strength=np.sqrt(np.sum(abs(z)**2*h,axis=1)/h.sum());result=[]
    for i,ref in enumerate(reference_frequencies):
        indices=np.flatnonzero((f>=ref*.85)&(f<=ref*1.15))
        if len(indices)<5:raise ValueError('Frequency resolution insufficient')
        expected=np.asarray(reference_shapes)[:,i]
        def shape_mac(j):
            shape=z[j]
            return float(abs(np.sum(h*np.conj(expected)*shape))**2/max(1e-30,np.sum(h*abs(expected)**2)*np.sum(h*abs(shape)**2)))
        strongest=int(indices[np.argmax(strength[indices])])
        # A nearby control/switching line may be stronger than the mechanical
        # resonance. Associate only actual local maxima with compatible shapes.
        candidates=[int(j) for j in indices if 0<j<len(f)-1 and strength[j]>strength[j-1] and strength[j]>=strength[j+1] and shape_mac(j)>=.95]
        if not candidates:raise ValueError(f'No shape-compatible modal peak near {ref:g} Hz')
        j=max(candidates,key=lambda j:strength[j]);offset=0.
        if 0<j<len(f)-1:
            a,b,c=np.log(np.maximum(strength[j-1:j+2],1e-30));den=a-2*b+c
            if abs(den)>1e-15:offset=float(np.clip(.5*(a-c)/den,-.5,.5))
        measured=float(f[j]+offset*(f[1]-f[0]));shape=z[j];mac=shape_mac(j)
        background=indices[abs(indices-j)>3]
        snr=float(strength[j]/max(1e-30,np.median(strength[background])))
        refphase=np.angle(shape[np.argmax(abs(shape))]);aligned=shape*np.exp(-1j*refphase)
        aligned/=max(1e-30,np.max(abs(aligned)))
        result.append(dict(reference_Hz=float(ref),frequency_Hz=measured,
            relative_error=float(abs(measured-ref)/ref),MAC=mac,peak_to_median=snr,
            relative_speed_amplitude=float(strength[j]),observed_shape_real=aligned.real.tolist(),
            observed_shape_imag=aligned.imag.tolist(),frequency_bin_Hz=float(f[1]-f[0]),
            strongest_band_peak=dict(frequency_Hz=float(f[strongest]),MAC=shape_mac(strongest),
                amplitude=float(strength[strongest]),selected_as_mode=bool(strongest==j))))
    return result
