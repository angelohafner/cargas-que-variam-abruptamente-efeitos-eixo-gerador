from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
class NativeModelContract(unittest.TestCase):
    def test_both_editable_models_exist(self):
        for name in ('DataCenter_Sem_BESS','DataCenter_Com_BESS'):
            self.assertTrue((ROOT/'pscad'/f'{name}.pscx').is_file(),name)

    def test_bess_contains_actual_battery_and_six_igbts(self):
        path=ROOT/'pscad/DataCenter_Com_BESS.pscx'
        self.assertTrue(path.exists(),'BESS model has not been built')
        root=ET.parse(path).getroot()
        users=list(root.iter('User'))
        self.assertEqual(sum(x.get('defn')=='master:battery' for x in users),1)
        switches=[x for x in users if x.get('defn')=='master:peswitch']
        types=[x.find("./paramlist/param[@name='Type']").get('value') for x in switches]
        self.assertEqual(types.count('3'),6)
        self.assertEqual(types.count('0'),6)

if __name__=='__main__': unittest.main()
