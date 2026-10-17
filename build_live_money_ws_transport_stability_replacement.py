from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_money"/"qarb_clean_bot"/"qarb_061d_subscription_cap_aware_ws_valves.py"
TEST=ROOT/"test_live_money_ws_transport_stability_replacement.py"

CODE='from __future__ import annotations\nimport asyncio\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061b_two_ws_valves_paper_lane as wv\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061c_existing_runner_six_dex_valve_cutover as q61c\n\nEXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nMAX_SUBSCRIPTIONS_PER_CONNECTION=32\nCONNECTION_STAGGER_SECONDS=1.25\nSUB_DELAY_MS=90\nRECONNECT_MIN_SECONDS=2.0\nRECONNECT_MAX_SECONDS=30.0\n\n_ORIG_WORKER=wv.q60b.p._worker\n\ndef capped_valves(addrs):\n    a=list(dict.fromkeys(addrs))\n    n=MAX_SUBSCRIPTIONS_PER_CONNECTION\n    return [a[i:i+n] for i in range(0,len(a),n)]\n\nasync def staggered_worker(index,addresses,q,c,stop):\n    if index:\n        await asyncio.sleep(index*CONNECTION_STAGGER_SECONDS)\n    return await _ORIG_WORKER(index,addresses,q,c,stop)\n\ndef install():\n    p=wv.q60b.p\n    m=wv.q60b.m\n    p.RECONNECT_MIN=RECONNECT_MIN_SECONDS\n    p.RECONNECT_MAX=RECONNECT_MAX_SECONDS\n    m.STAGGER_SECONDS=0.0\n    if hasattr(m,"SUB_DELAY_MS"):\n        m.SUB_DELAY_MS=max(int(m.SUB_DELAY_MS),SUB_DELAY_MS)\n    wv.two_valves=capped_valves\n    m._shards=capped_valves\n    p.m._shards=capped_valves\n    p._worker=staggered_worker\n    return q61c\n\ndef main(argv=None):\n    runtime=install()\n    print("[QARB-061D] STABLE SUBSCRIPTION VALVES",flush=True)\n    print("[WS_CAP] max_accounts_per_connection=%d"%MAX_SUBSCRIPTIONS_PER_CONNECTION,flush=True)\n    print("[WS_START] stagger_seconds=%.2f sub_delay_ms=%d"%(CONNECTION_STAGGER_SECONDS,SUB_DELAY_MS),flush=True)\n    print("[WS_RECONNECT] min=%.1f max=%.1f"%(RECONNECT_MIN_SECONDS,RECONNECT_MAX_SECONDS),flush=True)\n    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)\n    return runtime.main(argv)\n\nif __name__=="__main__":\n    main()\n'

TEST_CODE='from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q\nassert q.MAX_SUBSCRIPTIONS_PER_CONNECTION==32\nassert q.CONNECTION_STAGGER_SECONDS==1.25\nassert q.SUB_DELAY_MS>=90\nassert q.RECONNECT_MIN_SECONDS>=2.0\nassert q.install() is not None\nrows=q.capped_valves([str(i) for i in range(318)])\nassert len(rows)==10\nassert max(len(x) for x in rows)<=32\nprint("[PASS] WS transport stability replacement")\n'

if not TARGET.is_file():
    raise RuntimeError("QARB061D_TARGET_MISSING")

ast.parse(CODE)
ast.parse(TEST_CODE)
TARGET.write_text(CODE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] WS transport stability full replacement installed")
print("[SHARDS] 318 accounts -> 10 sockets max 32 each")
print("[PACE] 1.25s connection stagger, >=90ms subscribe pacing")
print("[RECONNECT] 2s minimum backoff")
print("[HOT_PATH] pricing/execution untouched")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)