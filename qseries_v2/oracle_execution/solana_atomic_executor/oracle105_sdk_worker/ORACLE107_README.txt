ORACLE-107 is a read-only, offline source-to-SDK identity bridge.
Run: node oracle107.mjs <existing-scanner-json-file>
Only explicitly named PumpSwap pool, Meteora pool, token mint, direction are admitted.
Old ORACLE-094 PUBLIC_ACCOUNT_KEYS_ONLY captures intentionally HOLD.
Meteora SDK hydration is implemented as a callable function; it requires a real
Connection and exact pool identity. PumpSwap SDK constructor/hydration and exact
pricing are NOT connected yet. This is NOT a live executable trade path.
No RPC calls from CLI, no key access, signing, broadcasting or scanner edits.
