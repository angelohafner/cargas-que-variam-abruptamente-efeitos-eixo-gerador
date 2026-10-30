from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from torsion_math import natural_modes
from torsion_identification import identify_modes

class ModalIdentification(unittest.TestCase):
    def test_ringdown_modes_reject_common_speed_oscillation(self):
        h=np.array([1.5,1,2.5]);f,v=natural_modes(h,[40,50])
        t=np.arange(0,15,.001)
        w=10*np.sin(2*np.pi*.8*t)[:,None]+np.sin(2*np.pi*f[1]*t)[:,None]*v[:,1]*np.exp(-.1*t)[:,None]
        w+=.4*np.sin(2*np.pi*f[2]*t)[:,None]*v[:,2]*np.exp(-.2*t)[:,None]
        modes=identify_modes(t,w,h,f[1:],v[:,1:])
        for m,expected in zip(modes,f[1:]):
            self.assertLess(abs(m['frequency_Hz']-expected),.03)
            self.assertGreater(m['MAC'],.99)
            self.assertGreater(m['peak_to_median'],20)

    def test_stronger_nearby_nonmodal_peak_is_not_called_a_shaft_mode(self):
        h=np.array([1.5,1,2.5]);f,v=natural_modes(h,[40,50]);t=np.arange(0,15,.001)
        w=np.sin(2*np.pi*f[1]*t)[:,None]*v[:,1]+.2*np.sin(2*np.pi*f[2]*t)[:,None]*v[:,2]
        mixed=v[:,1]+v[:,2]
        w+=2*np.sin(2*np.pi*20.25*t)[:,None]*mixed
        modes=identify_modes(t,w,h,f[1:],v[:,1:])
        self.assertLess(abs(modes[1]['frequency_Hz']-f[2]),.03)
        self.assertGreater(modes[1]['MAC'],.99)
        self.assertLess(modes[1]['strongest_band_peak']['MAC'],.95)

if __name__=='__main__':unittest.main()
