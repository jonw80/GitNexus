import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).parents[1]/"ym_v174_final/v199_c10_pinned_inventory.py"
spec=importlib.util.spec_from_file_location("gate",p)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class GateRegression(unittest.TestCase):
    def test_matching_both_directions(self):
        self.assertEqual(gate.assess_crossing(gate.EXPECTED_G10,gate.EXPECTED_G10)["status"],"PASS")
    def test_historical_failure_cannot_pass_on_reverse_reference(self):
        r=gate.assess_crossing(204.7027765713414,204.7027392787817)
        self.assertEqual(r["status"],"FAIL_CLOSED")
        self.assertFalse(r["external_norm_authorized"])
        self.assertLess(r["reverse_reference_abs_diff"],1e-8)
    def test_equal_but_wrong_reference(self):
        self.assertEqual(gate.assess_crossing(200.,200.)["status"],"FAIL_CLOSED")
    def test_crossing_tolerance(self):
        self.assertEqual(gate.assess_crossing(gate.EXPECTED_G10,gate.EXPECTED_G10+2e-8)["status"],"FAIL_CLOSED")
    def test_invalid_norms(self):
        for r,w in [(float("nan"),gate.EXPECTED_G10),(gate.EXPECTED_G10,float("inf")),(-1.,-1.)]:
            self.assertEqual(gate.assess_crossing(r,w)["status"],"FAIL_CLOSED")
    def test_complete_coverage(self):
        gate.check_coverage([{"shard":i,"nshards":8,"lo":947*i,"hi":947*(i+1),"sources":947} for i in range(8)],8)
    def test_duplicate_shard(self):
        with self.assertRaises(ValueError):
            gate.check_coverage([{"shard":0,"nshards":2,"lo":0,"hi":3788,"sources":3788}]*2,2)
    def test_source_gap(self):
        with self.assertRaises(ValueError):
            gate.check_coverage([{"shard":0,"nshards":2,"lo":0,"hi":3788,"sources":3788},
                                 {"shard":1,"nshards":2,"lo":3789,"hi":7576,"sources":3787}],2)

if __name__=="__main__":
    unittest.main(verbosity=2)
