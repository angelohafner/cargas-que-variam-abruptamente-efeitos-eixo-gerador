import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from torsion_math import natural_modes

class ShaftModes(unittest.TestCase):
    def test_two_mass_closed_form_and_rigid_mode(self):
        f,v=natural_modes([1.5,2.5],[40],3600)
        expected=np.sqrt((2*np.pi*60)*40*.5*(1/1.5+1/2.5))/(2*np.pi)
        self.assertAlmostEqual(f[0],0,places=6)
        self.assertAlmostEqual(f[1],expected,places=10)
        self.assertAlmostEqual(v[0,0],v[1,0],places=10)

    def test_stiffness_scaling_and_relative_modes(self):
        h=np.array([1.5,1.,2.5]);f,v=natural_modes(h,[40,50],3600)
        g,_=natural_modes(h,[160,200],3600)
        np.testing.assert_allclose(g[1:],2*f[1:],rtol=1e-12)
        self.assertTrue(np.all(f[1:]>0))
        np.testing.assert_allclose(h@v[:,1:],0,atol=1e-12)

    def test_reject_nonphysical_or_incompatible_parameters(self):
        for h,k,rpm in [([0,2],[40],3600),([1,2],[-1],3600),([1,2],[1,2],3600),([1,2],[1],0)]:
            with self.assertRaises(ValueError):natural_modes(h,k,rpm)

if __name__=='__main__':unittest.main()
