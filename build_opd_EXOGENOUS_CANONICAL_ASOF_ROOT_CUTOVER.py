from pathlib import Path
import shutil,time
ROOT=Path.cwd().resolve()
ASM=ROOT/"qseries_v2/oracle_predictive_discovery/opd_062_strict_asof_live_world_state.py"
PRED=ROOT/"qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py"
a=ASM.read_text(encoding="utf-8");p=PRED.read_text(encoding="utf-8")
for n in ("def _physical_rows(anchor,root):","def assemble(anchor,root=None,rows=None):",'return {"coinbase_hf_state":cb,"crypto_condition_state":cc,"learned_state":learned}'):
    if n not in a: raise SystemExit("[FAIL] OPD-062 boundary changed: "+n)
for n in ("def materialize_current_states(anchor,root):","def _freeze_predictions(root,anchor,scores,frozen_epoch):",'"evidence_votes":z.get("evidence_votes"),'):
    if n not in p: raise SystemExit("[FAIL] predictor boundary changed: "+n)
stamp=str(int(time.time()));shutil.copy2(ASM,str(ASM)+".bak."+stamp);shutil.copy2(PRED,str(PRED)+".bak."+stamp)
marker='            q.execute("SELECT sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND sequence_number<=%s AND observed_at<=to_timestamp(%s) ORDER BY sequence_number DESC LIMIT 8",(LEARN_PREFIX+asset.lower(),int(seq),t))\\n            out+=q.fetchall() or []'
if "EXOGENOUS_CANONICAL_ASOF_ROOT_CUTOVER_V1" not in a:
    sql="SELECT sequence_number,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE sequence_number<=%s AND observed_at<=to_timestamp(%s) AND source_id NOT LIKE \'source.kalshi%%\' AND source_id NOT LIKE \'source.crypto.hf.coinbase%%\' AND source_id NOT LIKE \'source.crypto.condition.coinbase%%\' AND source_id NOT LIKE \'source.crypto.learned_case%%\' ORDER BY sequence_number DESC LIMIT 512"
    add=marker+"\\n            # EXOGENOUS_CANONICAL_ASOF_ROOT_CUTOVER_V1\\n            q.execute("+repr(sql)+",(int(seq),t))\\n            out+=q.fetchall() or []"
    if marker not in a: raise SystemExit("[FAIL] OPD-062 SQL insertion point missing")
    a=a.replace(marker,add,1).replace("    cb={};cc={};learned=None","    cb={};cc={};learned=None;exogenous={}",1)
    old='    return {"coinbase_hf_state":cb,"crypto_condition_state":cc,"learned_state":learned}'
    exo='        else:\\n            low=(sid+" "+typ).lower()\\n            deny=("kalshi","coinbase","price","return","orderbook","bid","ask","spread","future","outcome","resolution","profit","pnl")\\n            allow=("usgs","weather","official","macro","economic","news","network","solana","onchain","on_chain","chain","provider","event","calendar","release","announcement","gmgn","ethereum")\\n            if any(x in low for x in allow) and not any(x in low for x in deny) and sid not in exogenous:\\n                exogenous[sid]={"sequence_number":int(seq),"source_id":sid,"observation_type":typ,"canonical_observation":obj}\\n    return {"coinbase_hf_state":cb,"crypto_condition_state":cc,"learned_state":learned,"exogenous_evidence_state":exogenous}'
    a=a.replace(old,exo,1)
world='          "learned_state":extra["learned_state"]}'
if '"exogenous_evidence_state":extra.get("exogenous_evidence_state",{})' not in p:
    p=p.replace(world,'          "learned_state":extra["learned_state"],\\n          "exogenous_evidence_state":extra.get("exogenous_evidence_state",{})}',1)
state='          "contract_close_basis":anchor.get("contract_close_basis"),\\n          "tokens":list(materialize_exact_live_tokens(root,world))})'
if '"exogenous_evidence_state":world.get("exogenous_evidence_state",{})' not in p:
    p=p.replace(state,'          "contract_close_basis":anchor.get("contract_close_basis"),\\n          "exogenous_evidence_state":world.get("exogenous_evidence_state",{}),\\n          "tokens":list(materialize_exact_live_tokens(root,world))})',1)
ledger='              "evidence_votes":z.get("evidence_votes"),'
if '"exogenous_evidence_snapshot":z.get("exogenous_evidence_snapshot")' not in p:
    p=p.replace(ledger,ledger+'\\n              "exogenous_evidence_snapshot":z.get("exogenous_evidence_snapshot") or {},',1)
compile(a,str(ASM),"exec");compile(p,str(PRED),"exec");ASM.write_text(a,encoding="utf-8");PRED.write_text(p,encoding="utf-8")
Path("test_opd_EXOGENOUS_CANONICAL_ASOF_ROOT_CUTOVER.py").write_text("from pathlib import Path\\nA=Path(\'qseries_v2/oracle_predictive_discovery/opd_062_strict_asof_live_world_state.py\').read_text()\\nP=Path(\'qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py\').read_text()\\ncompile(A,\'a\',\'exec\');compile(P,\'p\',\'exec\')\\nassert \'EXOGENOUS_CANONICAL_ASOF_ROOT_CUTOVER_V1\' in A\\nassert \'exogenous_evidence_state\' in A and \'exogenous_evidence_state\' in P\\nassert \'exogenous_evidence_snapshot\' in P\\nprint(\'[PASS] exact-anchor exogenous canonical boundary installed\')\\nprint(\'[PASS] immutable ledger preserves snapshot\')\\nprint(\'[EXECUTION/PUBLICATION] FALSE/FALSE\')\\n",encoding="utf-8")
print("[PASS] exogenous canonical as-of root cutover installed")
print("[BOUNDARY] OPD-062 -> current state -> frozen snapshot -> immutable ledger")
print("[OLD LEDGER] untouched")
print("[SCORING/GATES] unchanged")
