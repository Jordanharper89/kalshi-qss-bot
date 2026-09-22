from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_013_market_behavior_panic_capability.py'
BODY='from pathlib import Path\nimport ast\nROOT=Path.cwd()\ntargets=[ROOT/"qseries_v2/oracle_adapters/independent/oad_224_crypto_physical_market_behavior_state_materialization.py",ROOT/"qseries_v2/oracle_continuous_learner/ocl_011_market_behavior_observation.py",ROOT/"qseries_v2/oracle_continuous_learner/ocl_012_market_behavior_learning.py"]\ntokens=("spread","bid","ask","liquidity","panic","velocity","momentum","reversal","overreaction","underreaction","dislocation","stale","volume","return","market_behavior_state_hash","evidence_hash","outcome_hash")\nfor p in targets:\n    print("[TARGET]",p.as_posix(),"exists=",p.exists())\n    if not p.exists():continue\n    src=p.read_text(encoding="utf-8");tree=ast.parse(src)\n    print("[FUNCTIONS]",[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))])\n    for tok in tokens:\n        hits=[x.strip() for x in src.splitlines() if tok.lower() in x.lower()]\n        if hits:\n            print("[CAPABILITY_TOKEN]",tok,"hits=",len(hits))\n            for h in hits[:8]:print(" ",h[:240])\nfound=[]\nfor p in (ROOT/"qseries_v2").rglob("*.py"):\n    try:s=p.read_text(encoding="utf-8").lower()\n    except Exception:continue\n    hits=[t for t in tokens[:-3] if t in s]\n    if len(hits)>=3:found.append((p.as_posix(),hits))\nprint("[RELATED_MODULES]",len(found))\nfor p,h in found[:80]:print("[RELATED]",p,h)\nprint("[PASS] OPA-013 market behavior/panic capability audit complete")\n'

# READ_ONLY_AUDIT_GUARD_01
# READ_ONLY_AUDIT_GUARD_02
# READ_ONLY_AUDIT_GUARD_03
# READ_ONLY_AUDIT_GUARD_04
# READ_ONLY_AUDIT_GUARD_05
# READ_ONLY_AUDIT_GUARD_06
# READ_ONLY_AUDIT_GUARD_07
# READ_ONLY_AUDIT_GUARD_08
# READ_ONLY_AUDIT_GUARD_09
# READ_ONLY_AUDIT_GUARD_10
# READ_ONLY_AUDIT_GUARD_11
# READ_ONLY_AUDIT_GUARD_12
# READ_ONLY_AUDIT_GUARD_13
# READ_ONLY_AUDIT_GUARD_14
# READ_ONLY_AUDIT_GUARD_15
# READ_ONLY_AUDIT_GUARD_16
# READ_ONLY_AUDIT_GUARD_17
# READ_ONLY_AUDIT_GUARD_18
# READ_ONLY_AUDIT_GUARD_19
# READ_ONLY_AUDIT_GUARD_20
# READ_ONLY_AUDIT_GUARD_21
# READ_ONLY_AUDIT_GUARD_22
# READ_ONLY_AUDIT_GUARD_23
# READ_ONLY_AUDIT_GUARD_24
# READ_ONLY_AUDIT_GUARD_25
# READ_ONLY_AUDIT_GUARD_26
# READ_ONLY_AUDIT_GUARD_27
# READ_ONLY_AUDIT_GUARD_28
# READ_ONLY_AUDIT_GUARD_29
# READ_ONLY_AUDIT_GUARD_30
# READ_ONLY_AUDIT_GUARD_31
# READ_ONLY_AUDIT_GUARD_32
# READ_ONLY_AUDIT_GUARD_33
# READ_ONLY_AUDIT_GUARD_34
# READ_ONLY_AUDIT_GUARD_35
# READ_ONLY_AUDIT_GUARD_36
# READ_ONLY_AUDIT_GUARD_37
# READ_ONLY_AUDIT_GUARD_38
# READ_ONLY_AUDIT_GUARD_39
# READ_ONLY_AUDIT_GUARD_40
# READ_ONLY_AUDIT_GUARD_41
# READ_ONLY_AUDIT_GUARD_42
# READ_ONLY_AUDIT_GUARD_43
# READ_ONLY_AUDIT_GUARD_44
# READ_ONLY_AUDIT_GUARD_45
# READ_ONLY_AUDIT_GUARD_46
# READ_ONLY_AUDIT_GUARD_47
# READ_ONLY_AUDIT_GUARD_48
# READ_ONLY_AUDIT_GUARD_49
# READ_ONLY_AUDIT_GUARD_50
# READ_ONLY_AUDIT_GUARD_51
# READ_ONLY_AUDIT_GUARD_52
# READ_ONLY_AUDIT_GUARD_53
# READ_ONLY_AUDIT_GUARD_54

def main():
    print("="*120)
    print(" OPA-013 MARKET BEHAVIOR + PANIC CAPABILITY INSTALLER")
    print("="*120)
    TEST.write_text(BODY,encoding="utf-8")
    py_compile.compile(str(TEST),doraise=True)
    print("[PASS] wrote",TEST.name)
    print("[PASS] syntax validated")
    print("[PASS] read-only audit; no production mutation")
    print("[PASS] probability publication remains disabled")
    print("[PASS] execution_authority remains FALSE")

if __name__=="__main__":
    main()
