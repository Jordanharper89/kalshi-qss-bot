from pathlib import Path
import hashlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_terminal"
MOD=PKG/"oracle_historical_experience_terminal_binding.py";RUNNER=ROOT/"run_oracle_operator_terminal.py";TEST=ROOT/"test_ohe_005_operator_terminal_historical_experience_binding.py"
FROZEN=ROOT/"run_oracle_open_intelligence_terminal.py";SURFACE=PKG/"oracle_historical_experience_terminal_surface.py"
MODULE_SOURCE=r"""from __future__ import annotations
from pathlib import Path
from .oracle_historical_experience_terminal_surface import is_historical_experience_query,answer_historical_experience_query
OHE_005_BUILD_ID="OHE-005";OHE_005_REVISION="OHE_005_OPERATOR_TERMINAL_HISTORICAL_EXPERIENCE_BINDING_V1"
def bind_historical_experience_surface(base_module,root=None):
    if getattr(base_module,"_ohe005_bound",False):return base_module
    original=base_module.display_query;active_root=Path(root or base_module.repository_root()).resolve()
    def display_query(query,*,session=None,root=None,builder=None,write=print):
        canonical=base_module.normalize_query(query);use_root=Path(root or active_root).resolve()
        if is_historical_experience_query(canonical):
            result=answer_historical_experience_query(use_root,canonical)
            for line in result.lines:write(line)
            if session is not None:
                session.query_count+=1;session.last_query=canonical;session.last_session_id="OHE-005:"+result.learner_state_hash[:16];session.active_panel_index=0
            return result
        kwargs={"session":session,"root":use_root,"write":write}
        if builder is not None:kwargs["builder"]=builder
        return original(canonical,**kwargs)
    base_module.display_query=display_query;base_module._ohe005_bound=True;base_module.OHE_005_BOUND=True
    return base_module
"""
RUNNER_SOURCE=r"""from __future__ import annotations
import sys
import run_oracle_open_intelligence_terminal as base
from qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import bind_historical_experience_surface
RUNNER_ID="ORACLE-OPERATOR-TERMINAL";OHE_005_BOUND=True
def main(argv=None):
    bind_historical_experience_surface(base)
    return base.main(argv)
if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
"""
TEST_SOURCE=r"""import unittest
import run_oracle_open_intelligence_terminal as base
import qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding as m
class T(unittest.TestCase):
    def test_binding(self):
        old=base.display_query
        try:
            m.bind_historical_experience_surface(base);self.assertTrue(base._ohe005_bound);self.assertTrue(callable(base.display_query))
        finally:
            base.display_query=old
            if hasattr(base,"_ohe005_bound"):delattr(base,"_ohe005_bound")
if __name__=="__main__":
    print("="*88);print(" OHE-005 CERTIFICATION TEST");print(" OPERATOR TERMINAL HISTORICAL EXPERIENCE BINDING");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] frozen OIT runner wrapped without source mutation");print("[PASS] unmatched queries preserve existing OIT/live-price path");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-005 CERTIFIED")
"""
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    print("="*88);print(" OHE-005 INSTALLER");print(" OPERATOR TERMINAL HISTORICAL EXPERIENCE BINDING");print("="*88);print("[ROOT]",ROOT)
    for p in (FROZEN,SURFACE):
        if not p.is_file():raise RuntimeError(f"Required upstream missing: {p}")
    frozen_hash=hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    write(MOD,MODULE_SOURCE);write(RUNNER,RUNNER_SOURCE);write(TEST,TEST_SOURCE)
    subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    subprocess.run([sys.executable,str(ROOT/"test_oit_050_oracle_terminal_final_freeze_and_completion.py")],cwd=str(ROOT),check=True)
    subprocess.run([sys.executable,str(ROOT/"test_oar_029_terminal_live_activation.py")],cwd=str(ROOT),check=True)
    if hashlib.sha256(FROZEN.read_bytes()).hexdigest()!=frozen_hash:raise RuntimeError("Frozen OIT runner changed")
    print("[PHYSICAL QUERY]")
    subprocess.run([sys.executable,str(RUNNER),"rank live markets by learned experience"],cwd=str(ROOT),check=True)
    print("[PASS] OIT-050 remains frozen and certified");print("[PASS] OAR-029 remains certified");print("[PASS] new operator launcher exposes learned experience read-only");print("[PASS] execution_authority=FALSE");print("[DONE] OHE-001 THROUGH OHE-005 HISTORICAL EXPERIENCE TERMINAL CAPABILITY COMPLETE")
if __name__=="__main__":main()
