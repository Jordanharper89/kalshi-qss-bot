import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_119_persisted_sports_structured_descriptor import descriptor_from_persisted_sports_row

class T(unittest.TestCase):
    def test_mlb_descriptor(self):
        row=SimpleNamespace(
            observation_id="oid-1",
            source_id="source.independent.mlb:game:824638",
            payload=(("subject","Cincinnati Reds at Chicago Cubs"),("independent_evidence",True)),
        )
        d=descriptor_from_persisted_sports_row(row)
        print("[SPORT]",d.sport_family)
        print("[AWAY]",d.away_team)
        print("[HOME]",d.home_team)
        print("[PAIR]",d.team_pair_key)
        self.assertEqual(d.sport_family,"baseball")
        self.assertEqual(d.away_team,"Cincinnati Reds")
        self.assertEqual(d.home_team,"Chicago Cubs")
        self.assertTrue(d.independent_evidence)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-119 persisted sports structured descriptor certified")
