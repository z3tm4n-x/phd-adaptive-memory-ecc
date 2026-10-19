"""Scope/serialization checks for the unified delivery."""
import json
import unittest
from cold_envelope import build,HERE
from replay_burst import canonical


class DeliveryTests(unittest.TestCase):
    def test_cold_keeps_injections_and_payloads(self):
        cfg=json.loads((HERE/'config.json').read_text())
        old=next(s for s in cfg['scenarios'] if s['id']==4)
        new=build()
        self.assertEqual(new['injections'],sorted(old['injections'],key=lambda x:(x['at_ns'],x['parent'])))
        self.assertEqual(new['horizon_ns'],48000000)
        apps=new['applications']
        self.assertEqual(len(apps),48)
        for i,a in enumerate(apps):
            self.assertEqual(a['at_ns'],10000+1000000*i)
            kind=2 if i%2==0 else 1
            mask=old['application']['write_masks_cycle'][(i//2)%5]
            expected=(i<<57)|(mask<<53)|((0x12340000|i)<<21)|((400000+i//2)<<2)|kind
            self.assertEqual(int(a['packet'],16),expected)
        self.assertLess(apps[-1]['at_ns']+3000,new['horizon_ns'])
        self.assertLessEqual(24/(new['horizon_ns']/1e9),1000)

    def test_json_canonicalization_is_not_rounding(self):
        x={'permissions':[(2**63+1,0.123456789012345,False,None)]}
        y=canonical(x)
        self.assertEqual(y,{'permissions':[[2**63+1,0.123456789012345,False,None]]})
        self.assertNotEqual(y,{'permissions':[[2**63,0.123456789012345,False,None]]})
        self.assertNotEqual(y,{'permissions':[[2**63+1,0.123456789012346,False,None]]})

if __name__=='__main__':unittest.main()
