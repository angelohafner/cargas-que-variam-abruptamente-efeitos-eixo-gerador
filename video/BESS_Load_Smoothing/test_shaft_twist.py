import unittest
import numpy as np
from shaft_twist import twist_change, visual_deflection, GAUGE_GAIN


class ShaftTwistTests(unittest.TestCase):
    def example(self):
        t=np.linspace(1.8,2.8,2001)
        delta=np.where(t<2.,0.,.005*np.sin((t-2.)*4))
        common=3*t+np.sin(t)
        return t,common+.012+delta,common+.007,delta

    def test_pre_step_equilibrium_is_removed(self):
        t,a,b,expected=self.example()
        np.testing.assert_allclose(twist_change(t,a,b),expected,atol=2e-15)

    def test_common_rotation_cancels(self):
        t,a,b,_=self.example()
        shift=7*np.cos(t*3)
        np.testing.assert_allclose(twist_change(t,a+shift,b+shift),twist_change(t,a,b),atol=4e-15)

    def test_shared_gain_preserves_amplitude_ratio(self):
        a=np.array([.001,.005]); b=a*.05
        np.testing.assert_allclose(visual_deflection(b)/visual_deflection(a),.05)
        self.assertEqual(GAUGE_GAIN,200.)
        self.assertAlmostEqual(visual_deflection(np.array([.005]))[0],1.)

    def test_empty_reference_window_rejected(self):
        t=np.linspace(2.,3.,100)
        with self.assertRaisesRegex(ValueError,'reference'):
            twist_change(t,np.ones(100),np.zeros(100))

    def test_nonfinite_signal_rejected(self):
        t,a,b,_=self.example();a[400]=np.nan
        with self.assertRaisesRegex(ValueError,'finite'):
            twist_change(t,a,b)

    def test_time_alignment_required(self):
        t,a,b,_=self.example()
        with self.assertRaises(ValueError):
            twist_change(t,a[:-1],b)


if __name__=='__main__':unittest.main()
