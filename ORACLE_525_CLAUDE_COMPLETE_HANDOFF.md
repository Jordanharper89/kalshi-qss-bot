# ORACLE CONTROL CENTER — CLAUDE CODE MASTER HANDOFF

**Owner request:** Finish the software, not another numbered diagnostic sequence. Work in the actual LOCAL Windows checkout first. Build **two integrated bots**—a live scanner and an atomic arbitrage executor—plus one usable management dashboard. This directive is permission to develop and test software in a safe isolated branch/worktree; **it is NOT permission to broadcast transactions or access/expose wallet secrets**.

## 0. Read this carefully before changing anything

You are a senior Solana DEX engineer, distributed systems engineer, and full-stack engineer taking over the existing Q Series / Oracle system. Your job is to locate, verify, and consolidate the code already developed, not fabricate an alternate trading engine. Start by enumerating source files, actual function signatures, recent tests, and the present Git state. Then immediately implement the two deliverable builds described in §10, using source-grounded adapters and an actual runnable application. Work through tests, fix failures, and report exactly what works and does not.

There is no guarantee of arbitrage profit. Scanner hints, fixture PASS, offline unit tests, RPC simulation, and realized on-chain P&L are **different** states. Never claim funds were earned unless a real on-chain signature is confirmed and full wallet/token balance reconciliation supports the calculation. Do not ask for repository ZIP files. Do not delete/truncate old code or existing private runtime data.

## 1. Where the REAL source is

- **LOCAL authoritative checkout:** `C:\Users\jorda\OneDrive\Documents\GitHub\kalshi-qss-bot`
- Connected GitHub: `Jordanharper89/kalshi-qss-bot`, public `main`. Previously inspected remote tree has an older `qseries_v2/oracle_execution/solana_atomic_executor/runtime.py`; the latest `oracle_500_scanner_machine.py`, `oracle_504_execution_engine.py`, ORACLE-522–525 and V1 modules were **not present on remote main** at the last check. Do not derive their source or readiness from that older branch.
- The user's Windows CMD physically verified `qseries_v2/oracle_execution/solana_atomic_executor/oracle_504_execution_engine.py` exists locally and is 613 lines. `build_oracle_v1_003_production_bots.py` installed local V1 wrappers; 7 offline tests passed. A runtime scanner launch hit `V16_SUPERVISOR_LOCK_EXISTS`.
- FIRST inspect `git status --short`, `git branch --show-current`, `git remote -v`, `.gitignore`, `AGENTS.md`, actual local module paths and file hashes. The user previously saw many untracked files and attempts to stage files; do not assume anything was committed or pushed. Do not indiscriminately `git add -A`, stage runtime files, or publish secrets to the PUBLIC GitHub repository. Back up source safely and work on a feature branch or isolated worktree without disrupting running processes.
- `AGENTS.md` on older remote main says Oracle Intelligence is read-only and Q Series is the only executor, with historical Codex migration/read-only instructions and `py` as a Windows default. The user has **superseded the Solana execution ownership**: Oracle-owned Solana execution now lives under `oracle_execution`; unrelated Oracle intelligence remains strictly read-only. Use the verified active Windows venv and `python` (not `py`). Document any contract conflicts; do not silently break unrelated behavior. The old *Codex-specific initial audit policy* is not a direction to stop this newly authorized Claude engineering task after making a plan.

## 2. Nonnegotiable operator constraints

- Windows **CMD** startup and test commands; `cd /d`, `venv\Scripts\activate`, `python`. No PowerShell requirement. No Codex. No repo ZIP request.
- The frozen original scanner (ORACLE-322/Q25/Q20/Q18, V16/ORACLE-500) must not be casually replaced, restarted, or duplicated. The canonical SQLite ORACLE-344 event bus must not be destroyed or casually migrated. Never assume a supervisor lock is stale; verify actual PID, lease identity and recent heartbeat before action.
- Two trading bots (scanner and atomic executor) are distinct processes. Dashboard/API is an independent management plane **without signing capability**.
- Solana strategy: **same token** PumpSwap ↔ Meteora DLMM, direction `PUMP_TO_METEORA` and `METEORA_TO_PUMP`, **single atomic v0** transaction. Don't restore legacy HOT_SIGNAL fake economics or fixed 120-bps constant-product PumpSwap approximations.
- Scanner production **capacity**: up to **28 fully qualified pairs**, **56 possible direction templates**, roughly **318 watched addresses** historically. Preserve actual 19-size pricing grid where implemented. 28/56 are CAPACITIES, not certified counts of live-ready instruments. Never replace them with the 8 ORACLE-524 diagnostic tokens.
- The first funded canary when fully authorized is **exactly 0.010 SOL** = 10,000,000 lamports (not 0.050). This assignment **does not authorize any real transaction, even 0.010**. Never auto-arm LIVE upon restart, on UI load, or from a positive simulation. After a separately authorized, confirmed, reconciled canary, design for guarded autonomous trading without per-trade clicks, with hard caps/circuit breakers.
- Never log, reveal, upload, hardcode, clear, or expose a private key/seed/Helius credential/API token. ORACLE-503 established Windows Credential Manager storage for a simulation signer; use only through an isolated signer process and do not expose secrets in API, UI, reports, or Git. Do not wipe wallet environment variables or credential entries.
- Keep reports honest, show code changed/tests actually run, avoid fake positive quotes, mock profits, fabricated RPC responses, or 'PASS' flags from merely existing files.

## 3. Historical engineering checkpoints and current verified status

### Scanner, bus, and market intelligence

- Original Q25 / Q20 / Q18 exact live WebSocket pricing, same-token physical discovery and warm reusable pair state.
- **ORACLE-322:** canonical isolated-discovery frozen scanner, single writer. Installer historically `build_oracle_322_scanner_isolated_discovery.py` (local scanner installer about 510 lines).
- **V16:** final boss native supervisor/scanner startup, preserving ORACLE-322 algorithms. Old V8/V10/V15/V16 staged/native handoff artifacts exist; audit actually installed versions.
- **ORACLE-344:** canonical SQLite WAL scanner-to-executor event bus. Check producer+epoch, event ID, native token/pool triple, direction, slot, source age, expiry, freshness, size, lineage. Related ORACLE-359 exclusive lock, ORACLE-363 verified scanner bus binding, ORACLE-365 columnar event handoff.
- **ORACLE-500:** canonical scanner launcher. Local attempted launch through V1-003 printed `[ORACLE500_SCANNER] {"broadcast":false,"mode":"V16_CANONICAL_SINGLE_WRITER","pairs_capacity":28,"gross_best_size_grid":19,"shared_bus":"ORACLE344_EVENTS_SQLITE"...}` then `[FINAL_BOSS_V16_HOLD] V16_SUPERVISOR_LOCK_EXISTS`. This does not certify the scanner was running; inspect lock owner and heartbeat safely. The V1 wrapper prints a 28/56 contract but wrapper output is NOT proof of active market coverage.
- **ORACLE-522:** observed 87 real WS quotes, **zero positive** in that window. No profitable opportunity certified.
- **ORACLE-523:** eight historical quoted identities missing from an older executor registry.
- **ORACLE-524:** matched eight historical token/pool triples (diagnostic set), not a production-cap universe.
- **ORACLE-525:** native inventory hydration work. Original failed at missing `decimals_x`; source-specific fix required if not already present in latest version. V1 scanner 1.1 reportedly hydrated/warmed 8 diagnostic pairs, then `RuntimeError` after warmup; no certified continuous production runtime from that observation.
- **V1-003:** `qseries_v2/oracle_execution/solana_atomic_executor/V1/production_scanner.py` and `production_executor.py` wrappers installed; `test_oracle_v1_003_production_bots.py` ran 7 tests PASS in ~0.018 sec, and both entrypoint preflights PASS. These are entrypoint/static contract tests, not physical market/native execution certification.

### Executor, native transaction, security

- **ORACLE-504** local canonical executor: `qseries_v2/oracle_execution/solana_atomic_executor/oracle_504_execution_engine.py` (613 lines verified). Based on user's physical source readback:
  - `precheck(row, producer, epoch, now_ms)` around lines 219–232 rejects producer/epoch drift, grid/direction mismatch, stale expiration, nonpositive scanner nomination.
  - `proof_contract(row,proof,bank_gate)` around lines 234–246 requires exact event/token/direction/size/pool identity; flags `single_bank_context_verified`, `native_unsigned`, `alt_resolved`, `atomic_single_transaction`; v0, size <=1232, correct leg order: PUMP_BUY→DLMM_SELL or DLMM_BUY→PUMP_SELL; bank gate.
  - `work(seconds,wallet,signed_sim=False,fixture=None)` at 257; `m363/m365/m379/m359` around 322–340; source row ingestion around 342–354; on-demand hydration, refuse using event consumed for warmup; require next event.
  - `provider.prepare_unsigned(row)` around 419 and `proof_contract` around 420; ORACLE-401 `bridge.signed_preflight(row,proof,wallet,key,native._rpc)` around 432, checked fee-adjusted conservative simulation net >0 at 433–436.
  - `state['signed_sim_protected_min_out']=False` around 444; **protected min-out not certified**. No broadcast route. Worker `oracle402_native_nonbroadcast` ~451. CLI `--test`, `--observe`, `--fixture`, `--signed-sim`, `--seconds`, `--wallet` near 594–613. Signed sim uses ORACLE-503 simulation vault; no key in reports.
- **ORACLE-401:** canonical signed preflight. Source needs precise review: reverse validator program drift flag may force hold.
- **ORACLE-503:** Windows Credential Manager signer. Do NOT extract credential bytes into UI/logs.
- Historical native tooling across ORACLE-050/054/074/077/079/080/104, ORACLE-320–379, ORACLE-368, `qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py`, and `.../solana_atomic_executor/runtime.py`. Audit source rather than making up APIs.
- Older separate runtime reported `[LIVE_010_MODE] armed=False exact_size=0.050` and `broadcast=FALSE` with ALT preload. **That is not** an authorized funded 0.010 canary. `ORACLE-504` source physically shows no broadcast; don't claim working LIVE.

### Actual recurring holds to resolve based on CURRENT source and CURRENT logs

`DLMM_PARTIAL`; `SAVED_ALT_NOT_LIVE`; `SWAP2_TEMPLATE_PREFIX_DRIFT`; `NO_PREBUILT_TEMPLATE`; incomplete or wrong token decimals; ALT missing account coverage; `ATOMIC_TX_TOO_LARGE` and <=1232 byte cap; reverse validator program mismatch; insufficient source token account funding; `user_token_out` ATA missing; WSOL wrap/unwrapping and cleanup; latest bin-array completeness and vault state; mixed bank context; `HOLD_WARM_CACHE_EXPIRED`; WS/RPC 429 backoff; scanner lock contention; expired/superseded scanner events; stale signatures/blockhash; positive gross with negative realizable net; unknown transactions after crash. Older logs are historical; timestamp/provenance matters.

### Absolute accounting truths

- NO externally verified profitable funded atomic trade supplied to this handoff.
- Don't guarantee money or no losses: failed transactions can consume fees; token rent/residue/fees and stale quotes can turn purportedly profitable trades negative.
- Show separate values for quoted gross, simulated conservative net, authorized sends, confirmed settlements, actual reconciled net SOL+WSOL+token residue.

## 4. Product goal — one platform, NOT a mockup

Product: **Oracle Control Center**. Three managed processes, two trading bots:

1. `scanner` — existing frozen 28-slot WS live quote scanner with automatic safe pool replenishment, canonical SQLite event output, read-only.
2. `executor` — existing canonical native ORACLE-504 integration with trustworthy v0 two-leg construction, ALTs, signed simulation and fee-aware risk. Add a separately permissioned future live send/reconciliation state machine, but keep all sends disabled during this assignment.
3. `dashboard/API` — secure local control and monitoring only; no signer loaded, no direct browser database access.

Build as cohesive `oracle_control_center/` package with `core/contracts`, `adapters/legacy_oracle`, `scanner`, `executor`, `risk`, `storage`, `api`, `web`, `tests`, `scripts`, `docs`. FastAPI/Pydantic backend, React+TypeScript+Vite dark responsive frontend, WebSocket realtime stream, SQLite WAL compatible reader for canonical scanner events and a separate controlled persistent settings/audit/execution-intent store. Prefer existing deps where feasible; do not invent missing RPC fields. Secure bind `127.0.0.1` by default. Screens must show real outputs with explicit offline/disconnected/empty states.

## 5. Required scanner implementation contract

- Strict maximum capacity 28 unique `(token_mint,pumpswap_pool,meteora_dlmm_pool)` identities; 56 potential directions. Separate actually qualified count and executable-ready count. Reliable continuous replenishment under controlled RPC budget, without changing frozen scanner quote algorithms or duplicate WS processes. If scanner is already running, *attach read-only to its bus*; do not spawn another.
- WebSockets are primary hot path; exact current venue math from existing modules, accurate fees/decimals/bin liquidity and slot/account freshness; 19-size pricing grid is preserved from source (do not invent individual sizes). Do not issue RPC per quote. Hot/Warm tiering can optimize but never substitute approximate profitability for exact native execution economics.
- On chain/WS gaps, invalidate old state, resync at bounded rate, preserve epoch/event ID/fork lineage and latest bank consistency. Publish typed candidates to ORACLE-344 WAL, include TTL, quote proof, immutable identity/slot and source. Retain previous schema or migrate with explicit compatibility, backup and rollback.
- UI control surface: target 28, WS health, qualified versus warm, watched account budget, replenishment cadence, scanner size grid, enable/disable direction, quote age TTL, pool eligibility, RPC 429 and event lag. Versioned settings; don't hot reload unsafe scanner state.

## 6. Required executor implementation contract

- Consume only latest canonical events from ORACLE-344/365; preserve producer/epoch/ID, token mint/pool identity, direction, size and expiration, slot/bank and on-chain ownership. Dedup all intents, reject fixtures/history and stale/superseded events for LIVE.
- Both physical native legs for both routes, exact program/account metas and required helper instructions. Require token ATA creation readiness, WSOL funding/unwrapping/cleanup, rent/fee reserves, token residue, and explicit token-program distinction (legacy/Token-2022). Never omit helpers merely to shorten transaction.
- Compile one **atomic v0** transaction; verify on-chain ALT state/account mappings ahead of time, packet <=1232 serialized bytes, signer/readonly/writable flags and compute bounds. Do not fabricate account metas, fee tables or liquidity. If unverified, specific HOLD.
- Signed `simulateTransaction` on same native packet (isolated signer only), decode instruction-level errors, token before/after deltas, slippage, venue fees, base+priority network fees, compute, ATA rent effects, any dust/residue, then conservative net in lamports; require positive margin after buffers. No gross quote counts as a proven opportunity.
- Fresh reprice + exact size + pool/account snapshot revalidation after prep/sim, before send. Reverse program ID drift and min-out certification must remain hard holds until physically resolved.
- Design execution state transitions `DISCOVERED → QUOTED → IDENTITY_VERIFIED → NATIVE_BUILT → ALT_VERIFIED → SIGNED_SIMULATED → NET_ADMITTED → FRESH_REVALIDATED → SENT → CONFIRMED → RECONCILED` or terminal HOLD/EXPIRED/FAILED/UNKNOWN; durable idempotency, send signature tracking, no blind retries for unknown in-flight, rate/size exposure limits, kill switch, fee reserve and settlement/reconciliation.
- Modes `STOPPED`, `OBSERVE`, `PAPER`, `SIGNED_SIM`, `LIVE_CANARY`, `LIVE_GUARDED`. Default OBSERVE/SIGNED_SIM and broadcast disabled. Live activation requires separate operator authorization, physical certification, signer isolation and audit receipt. First funded canary exactly 0.010 SOL, never 0.050; after confirmed fully reconciled canary, guarded automatic execution can be an operator-controlled feature within caps, not active by default. **No live sends now.**

## 7. Dashboard and backend — actual functional screens

1. **Overview:** true PID/lease/heartbeat states, scanner 0–28 and 0–56 qualified versus ready, WS throughput, event queue latency, RPC 429 counts, native builds, verified sims, real sends/confirmed/reconciled trades and P&L. Distinguish source provenance: historical/fixture/estimate/sim/live.
2. **Scanner inventory:** 28 slots, search/sort, exact pool identities, decimals and program owners, slot age, liquidity/fees, warm account counts, side-native readiness, errors, replenishment history.
3. **Opportunities:** live candidate stream, both directions, exact size, gross bps and lamports, conservative simulated net when independently verified, expiry/hold reasons, evidence trace, filters.
4. **Execution terminal:** native stages, signed sim logs (redacted), ALT packet size, fee/rent/cost breakdown, status, real tx signature/explorer only if sent and verified.
5. **Wallet & P&L:** public wallet, SOL/WSOL/token account balances and rents, exposure/fees, realized net only after account reconciliation, residual tokens/dust, charts and daily trade count.
6. **Scanner settings:** validated persisted versioned forms, limits/budgets and safe restart annotations; no browser DB writes.
7. **Execution settings:** max size, net-profit floor, allowed directions, slippage, priority/compute fee caps, max in-flight=1 default, daily loss/drawdown limits, mode toggle with physical gates, first canary 0.010 hard invariant.
8. **Operations & security:** authenticated start/stop/drain controls checking PID/lease, logs/metrics, emergency kill (stops NEW sends immediately), 429 health, recovery and audit trail. No deletion of active lock files.

REST + WebSocket endpoints: `/api/v1/status`, `/inventory`, `/opportunities`, `/executions`, `/wallet`, `/settings`, `/risk`, `/audit`, `/healthz`, `/readyz`, plus `/ws/live` (or versioned equivalents documented). Token/session authentication for mutations, CSRF/origin protections, local-only defaults, careful CORS, rate limits, input validation, tamper-resistant audit trail, and no signer in API. Avoid insecure default passwords/tokens. The dashboard must work and show readable offline status even without funded wallet or Helius access.

## 8. Cross-process and testing requirements

- Never fake online counts or positive profits. Dedicated WS scanner lane, bounded executor ingress, coalescing without laundering stale data, WAL busy timeouts and `query_only=ON` for dashboard canonical bus reads; durable separate config/audit store.
- Replay tests from actual saved event shapes, deterministic fixtures, mock-safe RPCs and chain forks; idempotent crash recovery; worker lease/heartbeat tests; no duplicate scanners. E2E smoke tests for UI+API. Validation on 28 capacity and 56 potential sides does not certify live coverage.
- Tests for correct live ALT lookups, account ownership/decimals, both native sides, ATA & WSOL correctness, minout, 1232 cap, fee-adjusted net, false profit rejection, 429/stale, signer absence, live broadcast default false, tampered settings, signed preflight economics, restart fail-closed.
- Unit/integration/test harness should not require a real private key or live funding. Observe-only on-chain inspection if credentials present and operator specifically allows it. Never broadcast live during development.

## 9. Source-grounded quick-start discovery targets

Inspect these file names locally when present (do not assume naming without checking):

`build_oracle_322_scanner_isolated_discovery.py`, `build_oracle_500_scanner_machine.py`, `qseries_v2/oracle_execution/solana_atomic_executor/oracle_500_scanner_machine.py`, `qseries_v2/oracle_execution/solana_atomic_executor/oracle_504_execution_engine.py`, `qseries_v2/oracle_execution/solana_atomic_executor/V1/production_scanner.py`, `qseries_v2/oracle_execution/solana_atomic_executor/V1/production_executor.py`, `build_oracle_v1_003_production_bots.py`, `test_oracle_v1_003_production_bots.py`, ORACLE-344/359/363/365/368/379/401/503/522/523/524/525 files, `native_atomic_money_machine/core.py`, `qseries_v2/oracle_execution/solana_atomic_executor/runtime.py`, native v0/ALT helper source and existing runtime-state heartbeats. The V1 wrappers are simple launchers; do not mistake them for complete real executor certifications.

Run `python -m ...oracle_504_execution_engine --test` only if source confirms correct module path and test mode is non-broadcast. Use AST/read-only scans first if unsure. Examine the V16 supervisor lock guards before starting or stopping any process. Treat `V16_SUPERVISOR_LOCK_EXISTS` as a **lock-exists** event, not automatic proof the scanner is healthy, and never blindly delete it.

## 10. Exactly TWO build deliverables — implement, not plan

### BUILD A — Oracle Scanner + Control Center (RUNNABLE)

Create and test:

- A Python scanner manager/adaptor anchored to the original ORACLE-500/322/V16 scanner, with no duplicate processes, capacity=28, up to 56 directions, true bus+heartbeat ingestion, guarded control actions, real inventory/status and replenishment visibility.
- Typed contracts, backend API, auth + settings, event stream, operational audit.
- Functional React/TypeScript/Vite Control Center with 8 pages and all relevant screens, truthful data/empty states.
- Windows CMD installation/test/start scripts and local authenticated dashboard URL.
- Scanner offline/live-health integration tests that do NOT trigger live orders. If frozen scanner is already running, attach to it rather than relaunching.
- End BUILD A by running tests and showing exact filenames, operating status and any remaining sources not found; dashboard must be genuinely usable even if scanner is offline.

### BUILD B — Oracle Native Atomic Executor + Guarded Automation (RUNNABLE)

Create and test:

- Single canonical runtime/adaptor consuming fresh ORACLE-344 events and using vetted ORACLE-504/401 native preparers, both true venue legs, verified ALTs, ATAs/WSOL, conservative fee simulation and explicit hold reasons.
- Persistent risk/settings mode machine, signed sim, atomic tx validation <=1232, fresh checks, in-flight idempotency, reconciliation data model and UI binding.
- Isolated signer interface and explicit nonbroadcast default. Future guarded send is gated behind source-proven safety, direct authorization, first 0.010 SOL canary, transaction confirmation and reconciliation. Do **not** enable or conduct any LIVE trades in this task.
- Tests proving both directions / packet safety / economics / signer isolation / restart safe mode / no duplicate send, plus UI execution/settings integration.
- Update the same Control Center, not a competing dashboard. Report remaining real-world HOLD gates rather than passing dummy fixtures as production certification.

**No third 'audit build' or chains of numbered patches.** Limited discovery, then create finished components. If missing current local source prevents a specific adapter, complete all independent software, document the missing exact source, and fail closed at that adapter. Do not pretend a missing adapter is ready.

## 11. Operational expectations and deliverable report

Prefer real files in a coherent package rather than huge generated installers. Keep original frozen source untouched when possible. Ship complete file changes and unit tests; nothing truncated, nothing destructive, no secrets. Follow existing Git safety. Windows CMD scripts: `scripts\install.cmd`, `scripts\test.cmd`, `scripts\start_scanner.cmd`, `scripts\start_executor.cmd`, `scripts\start_dashboard.cmd`, `scripts\stop_all.cmd`; use `python` and verified venv. Include a short practical README with login setup, launch sequence, actual localhost dashboard URL, what a healthy scanner and signed-simulation executor look like, and what to do about a supervisor lock.

Final response should list **(1) changed files, (2) tests actually run/results, (3) current scanner/bus/executor/dashboard states, (4) exact remaining blocker for each unverified physical execution gate, (5) how to operate from Windows CMD, (6) security review and secret-free Git staging advice**. Status should be PASS / HOLD / NOT_TESTED using evidence, not aspiration.

**Start by reading this full directive and inspecting the available LOCAL repository; then directly implement BUILD A followed by BUILD B. Treat this as permission for ordinary local source changes and safe tests. No funded trading, wallet mutations, Git push, or publication without separate explicit approval.**
