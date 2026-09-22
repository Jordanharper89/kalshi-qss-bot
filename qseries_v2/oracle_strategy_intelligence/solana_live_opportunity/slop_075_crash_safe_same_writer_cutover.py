from pathlib import Path
import json, os
from .slop_074_safe_same_writer_learning_intake import prepare_pending_slop, commit_consumed
JREL=Path("runtime_state/solana_live_opportunity/slop_075_learning_commit_journal.json")
def _journal(root): return Path(root or Path.cwd())/JREL
def recover_or_prepare(state,root=None,progress=print):
 root=Path(root or Path.cwd()); jp=_journal(root)
 if jp.exists():
  j=json.loads(jp.read_text(encoding="utf-8"))
  if state.ocl_state.applied_through_sequence>=int(j["end_sequence"]):
   return "RECOVER_COMMIT",state,tuple(),j
  jp.unlink()
 result,new,rows=prepare_pending_slop(state,root,progress)
 if not rows: return "EMPTY",state,tuple(),None
 j={"start_sequence":state.ocl_state.applied_through_sequence+1,
    "end_sequence":new.ocl_state.applied_through_sequence,
    "keys":[x[0] for x in rows]}
 tmp=jp.with_suffix(".tmp"); jp.parent.mkdir(parents=True,exist_ok=True)
 tmp.write_text(json.dumps(j,sort_keys=True),encoding="utf-8"); os.replace(tmp,jp)
 return "APPLY",new,rows,j
def finalize(rows,root=None,progress=print):
 root=Path(root or Path.cwd()); n=commit_consumed(rows,root,progress) if rows else 0
 jp=_journal(root)
 if jp.exists(): jp.unlink()
 return n
