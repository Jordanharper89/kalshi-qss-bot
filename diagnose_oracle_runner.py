from run_oracle_live_shadow_FINAL_FIXED import (
    ROOT,
    _load_runtime_environment,
    build_real_oracle_shadow_graph,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_persistent_service_activation import (
    OracleProductionLiveShadowPersistentServiceActivator,
)


environment = _load_runtime_environment()

graph = build_real_oracle_shadow_graph(
    runtime_root=ROOT.resolve(),
    environment=environment,
    service_tick_interval_seconds=5,
)

activator = OracleProductionLiveShadowPersistentServiceActivator()

resolved = activator._resolve_runner(graph)
expected = graph["runner"]

print("=" * 72)
print(" ORACLE LIVE-SHADOW RUNNER RESOLUTION DIAGNOSTIC")
print("=" * 72)

print()
print("[EXPECTED]")
print("graph['runner'] class:")
print(type(expected).__module__ + "." + type(expected).__name__)

print()
print("[RESOLVED]")
print("OLA-063 _resolve_runner() class:")
print(type(resolved).__module__ + "." + type(resolved).__name__)

print()
print("[IDENTITY]")
print("resolved is graph['runner']:", resolved is expected)

print()
print("[GRAPH KEYS POINTING TO RESOLVED OBJECT]")
for key, value in graph.items():
    if value is resolved:
        print(" ", key)

print()
print("[ALL POSSIBLE FALLBACK RUNNER CANDIDATES]")

start_methods = (
    "run",
    "start",
    "run_service",
    "start_service",
    "serve",
)

for key, value in graph.items():
    methods = tuple(
        name
        for name in start_methods
        if callable(getattr(value, name, None))
    )

    if (
        getattr(value, "read_only", None) is True
        and getattr(value, "execution_allowed", None) is False
        and methods
    ):
        print(
            f"  {key}: "
            f"{type(value).__module__}.{type(value).__name__} "
            f"methods={methods}"
        )

print()
print("[DONE] Diagnostic only — no service activation performed")