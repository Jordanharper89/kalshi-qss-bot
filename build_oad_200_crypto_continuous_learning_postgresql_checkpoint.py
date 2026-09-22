from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_200_CRYPTO_CONTINUOUS_LEARNING_POSTGRESQL_CHECKPOINT_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass,asdict\nfrom datetime import datetime,timezone\nfrom hashlib import sha256\nimport json\nfrom qseries_v2.oracle_production_learning.opl_001_production_learning_foundation import connect\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nTABLE="oracle_crypto_continuous_learning_checkpoint"\nSTATE_ID=1\n\ndef _h(v):\n    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\n@dataclass(frozen=True,slots=True)\nclass CryptoContinuousLearningCheckpoint:\n    cycle_sequence:int\n    experiences_formed:int\n    exact_outcomes_matured:int\n    learned_cases_committed:int\n    last_snapshot_at:str\n    last_outcome_at:str\n    parent_state_hash:str\n    state_hash:str\n    execution_authority:bool=False\n\ndef _raw(cycle_sequence,experiences_formed,exact_outcomes_matured,learned_cases_committed,last_snapshot_at,last_outcome_at,parent_state_hash):\n    return {\n        "cycle_sequence":int(cycle_sequence),\n        "experiences_formed":int(experiences_formed),\n        "exact_outcomes_matured":int(exact_outcomes_matured),\n        "learned_cases_committed":int(learned_cases_committed),\n        "last_snapshot_at":str(last_snapshot_at or ""),\n        "last_outcome_at":str(last_outcome_at or ""),\n        "parent_state_hash":str(parent_state_hash),\n        "execution_authority":False,\n    }\n\ndef genesis_checkpoint():\n    raw=_raw(0,0,0,0,"","","0"*64)\n    return CryptoContinuousLearningCheckpoint(0,0,0,0,"","","0"*64,_h(raw),False)\n\ndef verify_checkpoint(x):\n    if x.execution_authority: return False\n    raw=_raw(x.cycle_sequence,x.experiences_formed,x.exact_outcomes_matured,x.learned_cases_committed,x.last_snapshot_at,x.last_outcome_at,x.parent_state_hash)\n    return (\n        x.cycle_sequence>=0 and x.experiences_formed>=0 and x.exact_outcomes_matured>=0 and\n        x.learned_cases_committed>=0 and len(x.parent_state_hash)==64 and x.state_hash==_h(raw)\n    )\n\ndef advance_checkpoint(previous,experiences_formed,exact_outcomes_matured,learned_cases_committed,last_snapshot_at="",last_outcome_at=""):\n    if not verify_checkpoint(previous): raise ValueError("previous checkpoint invalid")\n    raw=_raw(\n        previous.cycle_sequence+1,\n        previous.experiences_formed+int(experiences_formed),\n        previous.exact_outcomes_matured+int(exact_outcomes_matured),\n        previous.learned_cases_committed+int(learned_cases_committed),\n        last_snapshot_at or previous.last_snapshot_at,\n        last_outcome_at or previous.last_outcome_at,\n        previous.state_hash,\n    )\n    return CryptoContinuousLearningCheckpoint(\n        raw["cycle_sequence"],raw["experiences_formed"],raw["exact_outcomes_matured"],\n        raw["learned_cases_committed"],raw["last_snapshot_at"],raw["last_outcome_at"],\n        raw["parent_state_hash"],_h(raw),False\n    )\n\ndef ensure_checkpoint_schema(root=None):\n    ddl=f"""\n    CREATE TABLE IF NOT EXISTS public.{TABLE}(\n      state_id INTEGER PRIMARY KEY CHECK(state_id=1),\n      cycle_sequence BIGINT NOT NULL,\n      experiences_formed BIGINT NOT NULL,\n      exact_outcomes_matured BIGINT NOT NULL,\n      learned_cases_committed BIGINT NOT NULL,\n      last_snapshot_at TEXT NOT NULL,\n      last_outcome_at TEXT NOT NULL,\n      parent_state_hash TEXT NOT NULL,\n      state_hash TEXT NOT NULL,\n      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()\n    );\n    """\n    with connect(root,autocommit=True) as conn:\n        with conn.cursor() as cur: cur.execute(ddl)\n    return True\n\ndef read_checkpoint(root=None):\n    ensure_checkpoint_schema(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""SELECT cycle_sequence,experiences_formed,exact_outcomes_matured,\n                learned_cases_committed,last_snapshot_at,last_outcome_at,parent_state_hash,state_hash\n                FROM public.{TABLE} WHERE state_id=1""")\n            row=cur.fetchone()\n    if row is None: return genesis_checkpoint()\n    x=CryptoContinuousLearningCheckpoint(\n        int(row[0]),int(row[1]),int(row[2]),int(row[3]),str(row[4]),str(row[5]),str(row[6]),str(row[7]),False\n    )\n    if not verify_checkpoint(x): raise RuntimeError("stored crypto continuous-learning checkpoint invalid")\n    return x\n\ndef write_checkpoint(next_state,root=None,expected_parent_hash=None):\n    if not verify_checkpoint(next_state): raise ValueError("next checkpoint invalid")\n    expected=str(expected_parent_hash or next_state.parent_state_hash)\n    ensure_checkpoint_schema(root)\n    with connect(root) as conn:\n        with conn.cursor() as cur:\n            cur.execute(f"""SELECT state_hash FROM public.{TABLE} WHERE state_id=1 FOR UPDATE""")\n            row=cur.fetchone()\n            current_hash=str(row[0]) if row else genesis_checkpoint().state_hash\n            if current_hash!=expected:\n                raise RuntimeError("checkpoint parent mismatch; concurrent/replayed learning cycle rejected")\n            if row is None:\n                cur.execute(f"""INSERT INTO public.{TABLE}\n                  (state_id,cycle_sequence,experiences_formed,exact_outcomes_matured,learned_cases_committed,\n                   last_snapshot_at,last_outcome_at,parent_state_hash,state_hash)\n                  VALUES(1,%s,%s,%s,%s,%s,%s,%s,%s)""",\n                  (next_state.cycle_sequence,next_state.experiences_formed,next_state.exact_outcomes_matured,\n                   next_state.learned_cases_committed,next_state.last_snapshot_at,next_state.last_outcome_at,\n                   next_state.parent_state_hash,next_state.state_hash))\n            else:\n                cur.execute(f"""UPDATE public.{TABLE} SET\n                  cycle_sequence=%s,experiences_formed=%s,exact_outcomes_matured=%s,\n                  learned_cases_committed=%s,last_snapshot_at=%s,last_outcome_at=%s,\n                  parent_state_hash=%s,state_hash=%s,updated_at=clock_timestamp()\n                  WHERE state_id=1""",\n                  (next_state.cycle_sequence,next_state.experiences_formed,next_state.exact_outcomes_matured,\n                   next_state.learned_cases_committed,next_state.last_snapshot_at,next_state.last_outcome_at,\n                   next_state.parent_state_hash,next_state.state_hash))\n        conn.commit()\n    rb=read_checkpoint(root)\n    if rb.state_hash!=next_state.state_hash:\n        raise RuntimeError("checkpoint exact readback mismatch")\n    return rb\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_200_crypto_continuous_learning_postgresql_checkpoint import genesis_checkpoint,advance_checkpoint,verify_checkpoint\nclass T(unittest.TestCase):\n    def test_hash_chain(self):\n        g=genesis_checkpoint()\n        a=advance_checkpoint(g,3,0,0,"2026-08-30T00:00:00+00:00","")\n        b=advance_checkpoint(a,3,3,3,"2026-08-30T00:02:00+00:00","2026-08-30T00:01:00+00:00")\n        print("[CYCLES]",g.cycle_sequence,a.cycle_sequence,b.cycle_sequence)\n        print("[FORMED]",b.experiences_formed); print("[LEARNED]",b.learned_cases_committed)\n        self.assertTrue(verify_checkpoint(b))\n        self.assertEqual(b.parent_state_hash,a.state_hash)\n        self.assertEqual(b.learned_cases_committed,3)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-200 monotonic hash-chained PostgreSQL restart checkpoint contract certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    r=root()
    pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_200_crypto_continuous_learning_postgresql_checkpoint.py'
    test=r/'test_oad_200_crypto_continuous_learning_postgresql_checkpoint.py'
    init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-200 CRYPTO CONTINUOUS LEARNING POSTGRESQL CHECKPOINT INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",r)
    for dep in []:
        if not (pkg/dep).is_file():
            raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in ['qseries_v2/oracle_production_learning/opl_001_production_learning_foundation.py']:
        if not (r/dep).is_file():
            raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE)
        write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        export="from .oad_200_crypto_continuous_learning_postgresql_checkpoint import *"
        if export not in lines:
            lines.append(export)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-200 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise
if __name__=="__main__":
    main()
