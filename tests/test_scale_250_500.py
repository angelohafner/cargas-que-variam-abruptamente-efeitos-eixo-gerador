from pathlib import Path
import sys,unittest,math,xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from scale_models_250_500 import impedance_scale,load_level
ROOT=Path(__file__).resolve().parents[1]

class RatingScaling(unittest.TestCase):
    def test_network_voltage_drop_and_losses_preserve_pu(self):
        s0,v0,r0=20.,13.8,.02;s1,v1=1000.,34.5
        r1=r0*impedance_scale(v0,v1,s0,s1)
        i0=s0/(math.sqrt(3)*v0);i1=s1/(math.sqrt(3)*v1)
        self.assertAlmostEqual(i0*r0/v0,i1*r1/v1)
        self.assertAlmostEqual(3*i0*i0*r0/s0,3*i1*i1*r1/s1)
    def test_load_profile_endpoints_and_intermediate_positions(self):
        self.assertEqual(load_level(4),250);self.assertEqual(load_level(10),500)
        self.assertEqual(load_level(7),375);self.assertAlmostEqual(load_level(9),458.3333333333333)
    def test_all_four_saved_cases_use_new_intermitent_profile(self):
        files=list((ROOT/'pscad').glob('DataCenter_*.pscx'));self.assertEqual(len(files),4)
        for f in files:
            tree=ET.parse(f)
            ctl=next(u for u in tree.iter('User') if u.get('defn','').endswith(':DC_Controller'))
            p={x.get('name'):x.get('value') for x in ctl.findall('paramlist/param')}
            self.assertEqual(float(p['Pmin']),250,f.name);self.assertEqual(float(p['Pmax']),500,f.name)
            ex=[u for u in tree.iter('User') if u.get('defn','').endswith(':TorsionExperiment')]
            if ex:self.assertEqual(float(ex[0].find("paramlist/param[@name='Mode']").get('value')),0)
if __name__=='__main__':unittest.main()
