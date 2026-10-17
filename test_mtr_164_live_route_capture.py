import tempfile,time,json,unittest
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_164_live_route_capture as m
def ix(pid):return {"programId":pid,"accounts":[],"data":"AQ=="}
def row():
    p=ix(m.core.PUMP)
    return {"direction":"PUMP_TO_METEORA","token":"PUBLIC_TOKEN","pump_ixs":[p],
        "pump_ix":p,"pump_index":0,"meteora_ix":ix(m.core.DLMM),
        "start_lamports":10000000,"pump_snapshot_base_out":1,
        "pump_snapshot_net_out":1,"pump_snapshot_max_quote":1,
        "pre_sim_net_lamports":1}
class Tests(unittest.TestCase):
    def test_accepts_canonical_structure_only(self):
        self.assertFalse(m.verify(row())["protected_bounds_certified"])
    def test_rejects_nonpositive(self):
        r=row();r["pre_sim_net_lamports"]=0
        with self.assertRaises(m.HandoffHold):m.verify(r)
    def test_rejects_wrong_size(self):
        r=row();r["start_lamports"]=5000000
        with self.assertRaises(m.HandoffHold):m.verify(r)
    def test_capture_existing_route(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"state.json";p.write_text(json.dumps({"route":row()}))
            report,path=m.capture(t,Path(t)/"captured.json",max_age=120)
            self.assertEqual(report["status"],"ROUTE_CAPTURED_UNVERIFIED")
            self.assertTrue(path.exists())
    def test_missing_and_stale_hold(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"state.json";p.write_text(json.dumps({"route":row()}))
            result,_=m.capture(t,Path(t)/"out.json",max_age=10,now=time.time()+1000)
            self.assertEqual(result["status"],"HOLD_NO_RECENT_CANONICAL_ROUTE")
    def test_no_signer_or_runtime_activation(self):
        import inspect
        code=inspect.getsource(m.capture)
        for forbidden in ("runpy.","signed_tx(","send(","keypair("):
            self.assertNotIn(forbidden,code)
if __name__=="__main__":unittest.main(verbosity=2)
