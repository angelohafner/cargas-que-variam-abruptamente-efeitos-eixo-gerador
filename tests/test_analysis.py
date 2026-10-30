from pathlib import Path
import unittest,tempfile,sys,json,hashlib
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
try:
    from analysis import read_run, metrics
except ImportError:
    read_run=metrics=None

class AnalysisContract(unittest.TestCase):
    def fixture(self,root):
        files={'Case.inf':'PGB(1) Output Desc="Pgrid_MW" Units="MW"\n',
               'Case_01.out':'header\n0 2\n0.1 3\n0.2 4\n',
               'Case.pscx':'<project name="Case"/>'}
        for n,s in files.items():(root/n).write_text(s)
        sha=lambda n:hashlib.sha256((root/n).read_bytes()).hexdigest()
        (root/'run_receipt.json').write_text(json.dumps({'fresh_outputs':True,'errors':[],
            'duration_s':.2,'sample_step_us':100000,'project_sha256':sha('Case.pscx'),
            'project_unchanged_during_run':True,'output_sha256':{n:sha(n) for n in ['Case.inf','Case_01.out']}}))
    def test_recorded_mapping_and_modified_data_rejected(self):
        self.assertIsNotNone(read_run,'analysis reader is not implemented')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root)
            data=read_run(root,required=['Pgrid_MW'])
            np.testing.assert_allclose(data['Pgrid_MW'],[2,3,4])
            (root/'Case_01.out').write_text('header\n0 0\n.1 0\n.2 0\n')
            with self.assertRaisesRegex(ValueError,'hash'):read_run(root)
    def test_missing_channel_not_silently_zero_filled(self):
        self.assertIsNotNone(read_run,'analysis reader is not implemented')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root)
            with self.assertRaisesRegex(ValueError,'Missing'):read_run(root,required=['SOC_pct'])
    def test_ramp_and_energy_have_physical_units(self):
        self.assertIsNotNone(metrics,'metrics are not implemented')
        t=np.linspace(0,10,10001);p=2+0.5*t
        m=metrics(t,p,ramp_window=.1)
        self.assertAlmostEqual(m['maximum_ramp_MW_per_s'],.5,places=9)
        self.assertAlmostEqual(m['net_energy_MWh'],45/3600,places=9)

if __name__=='__main__':unittest.main()
