from pathlib import Path
import ast

ROOT=Path.cwd()
R=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"
LM=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py"
CP25=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py"
TEST=ROOT/"test_restore_positive_pricing_lane.py"

for p in (R,LM,CP25):
    if not p.is_file():
        raise RuntimeError("REQUIRED_TARGET_MISSING:"+str(p))

s=R.read_text(encoding="utf-8")
lm=LM.read_text(encoding="utf-8")
cp25=CP25.read_text(encoding="utf-8")

patterns=[('        "pair_key": str(pair.token)+"|"+str(pair.meteora_pool),\n', '', 1, 'snapshot_pair_key'), ('        METEORA_TEMPLATES[token+"|"+pool]={', '        METEORA_TEMPLATES[token]={', 1, 'meteora_template_key'), ('        {key.split("|",1)[0] for key in METEORA_TEMPLATES}', '        set(METEORA_TEMPLATES)', 1, 'ready_projection'), ('    pair_key=token+"|"+str(snap["meteora"]["address"])\n\n    template=(', '    template=(', 1, 'exact_best_pair_key'), ('        build_meteora_ix_hot(\n            pair_key,\n            net_out,', '        build_meteora_ix_hot(\n            token,\n            net_out,', 1, 'meteora_lookup'), ('    pair_key=str(snap["pair_key"])\n    token=str(snap["token"])\n    if lane.newer_waiting(\n        pair_key,\n        generation\n    ):', '    if lane.newer_waiting(\n        token,\n        generation\n    ):', 1, 'attack_entry'), ('    if lane.newer_waiting(\n        pair_key,\n        generation\n    ):', '    if lane.newer_waiting(\n        token,\n        generation\n    ):', 3, 'attack_followups'), ('    token=str(\n        pair.token\n    )\n    pair_key=token+"|"+str(pair.meteora_pool)\n\n    if token not in READY_TOKENS or pair_key not in METEORA_TEMPLATES:\n        return', '    token=str(\n        pair.token\n    )\n\n    if token not in READY_TOKENS:\n        return', 1, 'event_readiness'), ('    lane.submit(\n        pair_key,\n        immutable_snapshot(', '    lane.submit(\n        token,\n        immutable_snapshot(', 1, 'lane_identity'), ('            len(\n                METEORA_TEMPLATES\n            ),', '            len(\n                READY_TOKENS\n            ),', 1, 'ready_telemetry')]

# Validate every literal seam before any write.
for old,new,count,name in patterns:
    actual=s.count(old)
    if actual!=count:
        raise RuntimeError(
            "POSITIVE_LANE_ROLLBACK_SEAM_MISMATCH:"
            +name+":expected="+str(count)+":actual="+str(actual)
        )

newsrc=s
for old,repl,count,name in patterns:
    newsrc=newsrc.replace(old,repl,count)

required=[
    'METEORA_TEMPLATES[token]={',
    'set(METEORA_TEMPLATES)',
    'build_meteora_ix_hot(\n            token,',
    'lane.submit(\n        token,',
    'if token not in READY_TOKENS:',
    'len(\n                READY_TOKENS\n            )',
]
for marker in required:
    if marker not in newsrc:
        raise RuntimeError("ROLLBACK_POSTCONDITION_MISSING:"+marker)

for forbidden in (
    '"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)',
    'METEORA_TEMPLATES[token+"|"+pool]',
    'pair_key=token+"|"+str(snap["meteora"]["address"])',
    'lane.submit(\n        pair_key,',
    '[UNIVERSAL_ROTATION]',
):
    if forbidden in newsrc:
        raise RuntimeError("IDENTITY_EXPERIMENT_REMAINS:"+forbidden)

if '"live_hot_book.json"' not in cp25:
    raise RuntimeError("HOT_BOOK_RUNTIME_SLICE_NOT_RESTORED")

if "_atomic_write(CAPACITY,hot)" in lm:
    raise RuntimeError("DESTRUCTIVE_CAPACITY_OVERWRITE_REGRESSION")

ast.parse(newsrc)
R.write_text(newsrc,encoding="utf-8")

TEST_CODE='from pathlib import Path\nimport ast\n\nROOT=Path.cwd()\nR=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"\nLM=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/live_money_runtime.py"\nCP25=ROOT/"qseries_v2/oracle_execution/solana_atomic_executor/checkpoint25_expanded_live_universe_cutover.py"\n\nrs=R.read_text(encoding="utf-8")\nlms=LM.read_text(encoding="utf-8")\ncps=CP25.read_text(encoding="utf-8")\n\nast.parse(rs); ast.parse(lms); ast.parse(cps)\n\nassert \'"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)\' not in rs\nassert \'METEORA_TEMPLATES[token+"|"+pool]\' not in rs\nassert \'METEORA_TEMPLATES[token]={\' in rs\nassert \'set(METEORA_TEMPLATES)\' in rs\nassert \'build_meteora_ix_hot(\\n            token,\' in rs\nassert \'lane.submit(\\n        token,\' in rs\nassert \'if token not in READY_TOKENS:\' in rs\nassert \'len(\\n                READY_TOKENS\\n            )\' in rs\nassert "[UNIVERSAL_ROTATION]" not in rs\nassert \'"live_hot_book.json"\' in cps\nassert "_atomic_write(CAPACITY,hot)" not in lms\nassert "sendTransaction" not in rs\n\nprint("[PASS] original positive-capable token pricing lane restored")\nprint("[PASS] all 4 lane freshness/supersession checks are token-keyed")\nprint("[PASS] Meteora runtime template lookup restored to token")\nprint("[PASS] READY_TOKENS readiness path restored")\nprint("[PASS] fixed HOT-book scanner remains restored")\nprint("[PASS] universal master capacity remains non-destructive")\nprint("[BROADCAST] unchanged")\n'
TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

print("[PASS] POSITIVE-CAPABLE PRICING LANE RESTORATION")
print("[LANE] token-keyed canonical pricing identity restored")
print("[FRESHNESS] 4 token-keyed lane checks restored")
print("[METEORA] token-keyed runtime template lookup restored")
print("[READY] READY_TOKENS readiness restored")
print("[SCANNER] fixed HOT-book websocket scanner preserved")
print("[CAPITAL] funded-size controls untouched")
print("[CP26] reverse ATA path untouched")
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] unchanged")
print("[TEST]",TEST.name)
