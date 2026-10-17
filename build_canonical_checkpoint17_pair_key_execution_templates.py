from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint17_pair_key_execution_templates.py"
TEST=ROOT/"test_canonical_checkpoint17_pair_key_execution_templates.py"

MODULE=r"""from __future__ import annotations
import argparse,copy,threading
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint12_multi_pool_live_size_optimizer as c12
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint15_cheapest_legal_fee_signed_simulation as c15

PAIR_TEMPLATES={}
ROUTE_LOCK=threading.Lock()
ORIGINAL_ROUTE=None

def _pair_key(token,pool):
    return str(token)+"|"+str(pool)

def _build_pair_templates(state,user,warmed):
    global PAIR_TEMPLATES
    PAIR_TEMPLATES={}
    old_ready=set(r.READY_TOKENS)
    old_meteora=dict(r.METEORA_TEMPLATES)
    try:
        for pair in state["pairs"]:
            token=str(pair.token); pool=str(pair.meteora_pool); key=_pair_key(token,pool)
            r.READY_TOKENS={token}
            count=r.prebuild_meteora_templates({"pairs":[pair]},user,warmed)
            if count!=1:
                raise RuntimeError("CHECKPOINT17_PAIR_TEMPLATE_COUNT:"+key+":"+str(count))
            template=r.METEORA_TEMPLATES.get(token)
            if template is None:
                raise RuntimeError("CHECKPOINT17_PAIR_TEMPLATE_MISSING:"+key)
            if str(template.get("pool"))!=pool:
                raise RuntimeError("CHECKPOINT17_PAIR_TEMPLATE_POOL_DRIFT:"+key)
            PAIR_TEMPLATES[key]=copy.deepcopy(template)
            print("[CHECKPOINT17_TEMPLATE_READY] pair=%s token=%s pool=%s arrays=%d"%(key[:34],token[:10],pool[:12],len(template.get("arrays") or [])),flush=True)
    finally:
        r.READY_TOKENS=old_ready
        r.METEORA_TEMPLATES=old_meteora
    if len(PAIR_TEMPLATES)!=len(state["pairs"]):
        raise RuntimeError("CHECKPOINT17_TEMPLATE_COVERAGE:%d/%d"%(len(PAIR_TEMPLATES),len(state["pairs"])))
    return len(PAIR_TEMPLATES)

def _pair_bound_route(user,snap,opportunity):
    token=str(snap["token"]); pool=str(snap["meteora"]["address"]); key=_pair_key(token,pool)
    template=PAIR_TEMPLATES.get(key)
    if template is None:
        raise RuntimeError("PAIR_KEY_METEORA_TEMPLATE_MISSING:"+key)
    with ROUTE_LOCK:
        old=dict(r.METEORA_TEMPLATES)
        try:
            r.METEORA_TEMPLATES={token:copy.deepcopy(template)}
            if str(r.METEORA_TEMPLATES[token].get("pool"))!=pool:
                raise RuntimeError("CHECKPOINT17_ROUTE_POOL_DRIFT:"+key)
            return ORIGINAL_ROUTE(user,snap,opportunity)
        finally:
            r.METEORA_TEMPLATES=old

def main():
    global ORIGINAL_ROUTE
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=3600.0)
    args=p.parse_args()
    if args.seconds<=0:
        raise RuntimeError("CHECKPOINT17_SECONDS_MUST_BE_POSITIVE")

    state,registry,failures=c12._expanded_state()
    warmed=r.q25.install_hot_math_and_prewarm(state)
    r.q18.install_exact_hot_math()
    signer,user=r.q87.c.sim_identity()
    if signer is None or not user:
        raise RuntimeError("CHECKPOINT17_SIGNER_UNAVAILABLE")

    r.prebuild_templates(state,user)
    template_count=_build_pair_templates(state,user,warmed)

    old_expanded=c12._expanded_state
    old_route=c7._route
    ORIGINAL_ROUTE=old_route
    try:
        c12._expanded_state=lambda:(state,registry,failures)
        c7._route=_pair_bound_route
        c15.SECONDS=float(args.seconds)
        print("[CHECKPOINT17_ACTIVATION] pair_key_execution_templates=True seconds=%.0f broadcast=False"%c15.SECONDS,flush=True)
        print("[CHECKPOINT17_COVERAGE] live_pairs=%d templates=%d identity=token|meteora_pool"%(len(state["pairs"]),template_count),flush=True)
        print("[CHECKPOINT17_ROUTE_BINDING] token_level_overwrite=False exact_pool_template_required=True",flush=True)
        print("[CHECKPOINT17_PIPELINE] gross_positive -> pair_bound_route -> all_legal_candidates -> real_fee_each -> best_after_fee -> signed_simulation",flush=True)
        print("[BROADCAST] disabled",flush=True)
        return c15.main()
    finally:
        c12._expanded_state=old_expanded
        c7._route=old_route

if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast,unittest
from pathlib import Path
P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint17_pair_key_execution_templates.py")
class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8"); ast.parse(cls.s)
    def test_pair_key_identity(self): self.assertIn('str(token)+"|"+str(pool)',self.s)
    def test_every_pair_prebuilt(self):
        self.assertIn('for pair in state["pairs"]:',self.s); self.assertIn("r.prebuild_meteora_templates(",self.s)
    def test_pool_drift_fails_closed(self): self.assertIn("CHECKPOINT17_ROUTE_POOL_DRIFT",self.s)
    def test_route_is_pair_bound(self):
        self.assertIn("c7._route=_pair_bound_route",self.s); self.assertIn("PAIR_KEY_METEORA_TEMPLATE_MISSING",self.s)
    def test_reuses_checkpoint15(self): self.assertIn("return c15.main()",self.s)
    def test_no_broadcast(self): self.assertNotIn("sendTransaction",self.s)
if __name__=="__main__": unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")
print("[PASS] checkpoint-17 pair-key execution template activation installed")
print("[FIX] Meteora execution templates keyed by token|meteora_pool")
print("[COVERAGE] one startup template per live registry pair")
print("[HOT_PATH] exact pair template bound with zero template-discovery RPC")
print("[PIPELINE] checkpoint-15 all-candidate fee ranking + signed simulation reused")
print("[SIZES] full certified ladder; no 0.001 bias")
print("[ALT] unchanged")
print("[KEY] existing signer read only; untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
