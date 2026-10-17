ORACLE-105: Official-SDK-based fail-closed atomic simulation worker.
No custom swap layouts. No signing. No broadcast. No scanner modifications.

SETUP (Windows CMD, venv active):
cd qseries_v2\oracle_execution\solana_atomic_executor\oracle105_sdk_worker
npm install
npm test
node --check worker.mjs

INTEGRATION STATUS: SDK-based instruction adapter requires the actual hydrated PumpSwap and
Meteora pool objects and SDK calls matching installed SDK versions. A scanner quote alone
is insufficient. buildOfficialSdkLegs requires explicit SDK build callbacks; this build
intentionally does not pretend a generic callback is a verified integration.

SIMULATION STATUS: unsigned complete transaction simulation; not signed simulation.
No verified profit calculation or transaction broadcasting is implemented.
