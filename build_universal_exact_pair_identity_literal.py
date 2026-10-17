from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"runtime.py"
OWNERSHIP=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"live_money_runtime.py"
TEST=ROOT/"test_universal_exact_pair_identity_literal.py"

src=TARGET.read_text(encoding="utf-8")
owner=OWNERSHIP.read_text(encoding="utf-8")
patterns=[('def immutable_snapshot(pair):\n    return {\n        "token":', 'def immutable_snapshot(pair):\n    return {\n        "pair_key": str(pair.token)+"|"+str(pair.meteora_pool),\n        "token":', 1, 'snapshot_pair_key'), ('        METEORA_TEMPLATES[token]={', '        METEORA_TEMPLATES[token+"|"+pool]={', 1, 'meteora_pair_key'), ('        set(METEORA_TEMPLATES)', '        {key.split("|",1)[0] for key in METEORA_TEMPLATES}', 1, 'ready_token_projection'), ('    token=str(\n        snap["token"]\n    )\n\n    template=(', '    token=str(\n        snap["token"]\n    )\n    pair_key=token+"|"+str(snap["meteora"]["address"])\n\n    template=(', 1, 'exact_best_pair_key'), ('        build_meteora_ix_hot(\n            token,\n            net_out,', '        build_meteora_ix_hot(\n            pair_key,\n            net_out,', 1, 'meteora_exact_lookup'), ('    generation\n):\n    if lane.newer_waiting(\n        token,\n        generation\n    ):', '    generation\n):\n    pair_key=str(snap["pair_key"])\n    token=str(snap["token"])\n    if lane.newer_waiting(\n        pair_key,\n        generation\n    ):', 1, 'attack_pair_identity'), ('    if lane.newer_waiting(\n        token,\n        generation\n    ):\n\n        print(\n            "[CANONICAL_SUPERSEDED] "\n            "token=%s phase=first_sim"', '    if lane.newer_waiting(\n        pair_key,\n        generation\n    ):\n\n        print(\n            "[CANONICAL_SUPERSEDED] "\n            "token=%s phase=first_sim"', 1, 'attack_first_sim_pair_identity'), ('    if lane.newer_waiting(\n        token,\n        generation\n    ):\n\n        print(\n            "[CANONICAL_SUPERSEDED] "\n            "token=%s "\n            "phase=chain_reprice"', '    if lane.newer_waiting(\n        pair_key,\n        generation\n    ):\n\n        print(\n            "[CANONICAL_SUPERSEDED] "\n            "token=%s "\n            "phase=chain_reprice"', 1, 'attack_reprice_pair_identity'), ('    token=str(\n        pair.token\n    )\n\n    if token not in READY_TOKENS:\n        return', '    token=str(\n        pair.token\n    )\n    pair_key=token+"|"+str(pair.meteora_pool)\n\n    if token not in READY_TOKENS or pair_key not in METEORA_TEMPLATES:\n        return', 1, 'event_exact_pair_ready'), ('    lane.submit(\n        token,\n        immutable_snapshot(', '    lane.submit(\n        pair_key,\n        immutable_snapshot(', 1, 'lane_pair_identity'), ('            len(\n                READY_TOKENS\n            ),', '            len(\n                METEORA_TEMPLATES\n            ),', 1, 'ready_pair_telemetry')]

for old,new,expected,name in patterns:
    count=src.count(old)
    if count!=expected:
        raise RuntimeError("LITERAL_SEAM_MISMATCH:%s expected=%d actual=%d"%(name,expected,count))

if '_atomic_write(CAPACITY,hot)' in owner:
    raise RuntimeError("UNIVERSAL_OWNERSHIP_REGRESSION")
if 'live_hot_book.json' not in owner:
    raise RuntimeError("HOT_BOOK_STATE_OWNER_MISSING")

newsrc=src
for old,new,expected,name in patterns:
    newsrc=newsrc.replace(old,new,expected)

required=[
    '"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)',
    'METEORA_TEMPLATES[token+"|"+pool]',
    '{key.split("|",1)[0] for key in METEORA_TEMPLATES}',
    'pair_key=token+"|"+str(snap["meteora"]["address"])',
    'build_meteora_ix_hot(\n            pair_key,',
    'pair_key=str(snap["pair_key"])',
    'pair_key=token+"|"+str(pair.meteora_pool)',
    'lane.submit(\n        pair_key,',
]
for marker in required:
    if marker not in newsrc:
        raise RuntimeError("POSTCONDITION_MISSING:"+marker[:80])

ast.parse(newsrc)
TARGET.write_text(newsrc,encoding="utf-8")

TEST_CODE='from pathlib import Path\nimport ast\nfrom qseries_v2.oracle_execution.solana_atomic_executor import runtime as r\nfrom qseries_v2.oracle_execution.solana_atomic_executor import live_money_runtime as lm\n\ns=Path(r.__file__).read_text(encoding="utf-8")\no=Path(lm.__file__).read_text(encoding="utf-8")\nast.parse(s)\nast.parse(o)\n\nassert \'"pair_key": str(pair.token)+"|"+str(pair.meteora_pool)\' in s\nassert \'METEORA_TEMPLATES[token+"|"+pool]\' in s\nassert \'pair_key=token+"|"+str(snap["meteora"]["address"])\' in s\nassert \'build_meteora_ix_hot(\\n            pair_key,\' in s\nassert \'pair_key=str(snap["pair_key"])\' in s\nassert \'lane.submit(\\n        pair_key,\' in s\nassert \'_atomic_write(CAPACITY,hot)\' not in o\nassert \'live_hot_book.json\' in o\nassert \'sendTransaction\' not in s\n\nclass P:\n    token="TOKEN_A"\n    meteora_pool="POOL_1"\n    pump_pool="PUMP"\n    token_x="TOKEN_A"\n    token_y="WSOL"\n    decimals_x=6\n    decimals_y=9\n    dlmm_state={}\n    pump_base_reserve=1\n    pump_quote_reserve=1\n\np=P()\na=r.immutable_snapshot(p)\np.meteora_pool="POOL_2"\nb=r.immutable_snapshot(p)\nassert a["pair_key"]=="TOKEN_A|POOL_1"\nassert b["pair_key"]=="TOKEN_A|POOL_2"\nassert a["pair_key"]!=b["pair_key"]\n\nprint("[PASS] literal exact-pair identity replacement")\nprint("[PASS] same-token alternate Meteora pools remain distinct")\nprint("[PASS] lane/freshness/template identity=token|meteora_pool")\nprint("[PASS] universal/HOT ownership preserved")\nprint("[BROADCAST] unchanged")\n'
TEST.write_text(TEST_CODE,encoding="utf-8")
ast.parse(TEST_CODE)

print("[PASS] UNIVERSAL EXACT-PAIR IDENTITY LITERAL REPLACEMENT")
print("[METHOD] prevalidated literal source blocks; zero AST seam guessing")
print("[IDENTITY] token|meteora_pool")
print("[UNIVERSAL] ownership certification preserved")
print("[KEY] untouched")
print("[WALLET] untouched")
print("[BROADCAST] unchanged")
print("[TEST]",TEST.name)
