ORACLE-106 installs SDK-native instruction builder and simulation handoff.
Existing scanner and ORACLE-105 worker remain unchanged.
IMPORTANT: This is not a live connected executor. The scanner must supply
hydrated SDK pool objects, swap state, exact integer bounds, and a real RPC
connection. No secrets, signatures, broadcast, or realized profit are used.
Run: npm test && node oracle106.mjs
