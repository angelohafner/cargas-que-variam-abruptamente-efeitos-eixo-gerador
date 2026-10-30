from pathlib import Path
import unittest,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]

class GeneratorArtifacts(unittest.TestCase):
    def test_two_native_generator_multimass_cases(self):
        for suffix in ['Sem_BESS','Com_BESS']:
            p=ROOT/'pscad'/('DataCenter_Gerador_'+suffix+'.pscx')
            self.assertTrue(p.exists(),p.name)
            users=list(ET.parse(p).getroot().iter('User'))
            self.assertEqual(sum(u.get('defn')=='master:sync_machine' for u in users),1)
            self.assertEqual(sum(u.get('defn')=='master:multimass2' for u in users),1)
            self.assertEqual(sum(u.get('defn')=='master:source_3' for u in users),0)
            machine=next(u for u in users if u.get('defn')=='master:sync_machine')
            pars={p.get('name'):p.get('value') for p in machine.findall('./paramlist/param')}
            self.assertEqual(pars['MM'],'0','Native MM=0 ENABLES the interface')
            self.assertEqual(pars['Enab'],'Rotor_released')

if __name__=='__main__':unittest.main()
