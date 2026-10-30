import unittest
import numpy as np
from data_pipeline import validate_pair, power_metrics


class ComparisonTests(unittest.TestCase):
    def pair(self):
        t = np.linspace(0, 3, 301)
        return {'time': t, 'Pload_command_MW': np.full(t.size, 250.)}

    def test_different_timestamps_are_rejected(self):
        a, b = self.pair(), self.pair()
        b['time'] = b['time'] + .001
        with self.assertRaisesRegex(ValueError, 'time'):
            validate_pair(a, b)

    def test_different_demands_are_rejected(self):
        a, b = self.pair(), self.pair()
        b['Pload_command_MW'][200] += 10
        with self.assertRaisesRegex(ValueError, 'command'):
            validate_pair(a, b)

    def test_identical_pair_is_accepted(self):
        self.assertIsNone(validate_pair(self.pair(), self.pair()))

    def test_ramp_metric_uses_physical_time(self):
        t = np.linspace(0, 3, 301)
        r = power_metrics(t, 250 + 25*t, start=1.5, end=2.5)
        self.assertAlmostEqual(r['max_ramp_MW_s'], 25, places=8)
        self.assertAlmostEqual(r['mean_MW'], 300, places=8)

    def test_empty_window_rejected(self):
        with self.assertRaises(ValueError):
            power_metrics(np.array([0., 1.]), np.array([250., 500.]), 5., 6.)


if __name__ == '__main__':
    unittest.main()
