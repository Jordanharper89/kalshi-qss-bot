
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.ops.qseries_runtime import (
    QSeriesRuntime,
    create_qseries_runtime,
    qseries_runtime,
)


def test_ops_008_qseries_runtime_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        runtime = create_qseries_runtime()

        assert isinstance(runtime, QSeriesRuntime)
        assert qseries_runtime is create_qseries_runtime

        assert runtime.runtime_root == RuntimePaths.runtime_root()
        assert runtime.data_dir == RuntimePaths.data_dir()
        assert runtime.logs_dir == RuntimePaths.logs_dir()
        assert runtime.cache_dir == RuntimePaths.cache_dir()
        assert runtime.state_dir == RuntimePaths.state_dir()
        assert runtime.raw_dir == RuntimePaths.raw_dir()
        assert runtime.test_data_dir == RuntimePaths.test_data_dir()

        for path in [
            runtime.runtime_root,
            runtime.data_dir,
            runtime.logs_dir,
            runtime.cache_dir,
            runtime.state_dir,
            runtime.raw_dir,
            runtime.test_data_dir,
        ]:
            assert path.exists()
            assert path.is_dir()
            assert "qseries_v2/data" not in str(path).replace("\\", "/")

        start_status = runtime.start()
        assert start_status.status == "running"

        svc = runtime.register_service(
            name="oracle",
            status="running",
            metadata={"mode": "read_only"},
        )
        assert svc.name == "oracle"
        assert svc.status == "running"

        runtime.update_service(
            name="oracle",
            status="healthy",
            metadata={"checks": 1},
        )

        oracle_status = runtime.service_status("oracle")
        assert oracle_status is not None
        assert oracle_status.status == "healthy"
        assert oracle_status.metadata["mode"] == "read_only"
        assert oracle_status.metadata["checks"] == 1

        runtime.register_service(name="executor", status="idle", metadata={"mode": "execution"})
        assert len(runtime.services()) == 2

        job = runtime.add_scheduler_job("job.scan", {"interval": "60s"})
        assert job["job_id"] == "job.scan"
        assert len(runtime.scheduler_jobs()) == 1

        watchdog = runtime.watchdog_check("initial check")
        assert watchdog.status == "ok"
        assert watchdog.checks == 1

        state_path = runtime.write_state("sample_state.json", {"ok": True})
        assert state_path.exists()
        assert state_path.parent == RuntimePaths.state_dir()
        assert runtime.read_state("sample_state.json") == {"ok": True}

        log_path = runtime.write_log("runtime.log", "runtime started")
        assert log_path.exists()
        assert log_path.parent == RuntimePaths.logs_dir()

        report = runtime.runtime_paths_report()
        assert report["qseries_history_db"] == str(RuntimePaths.qseries_history_db())
        assert report["oracle_memory_db"] == str(RuntimePaths.oracle_memory_db())
        assert report["oracle_runtime_state_db"] == str(RuntimePaths.oracle_runtime_state_db())

        health = runtime.health()
        assert health["status"] == "ok"
        assert health["runtime_status"] == "running"
        assert health["uses_runtime_paths"] is True
        assert health["scheduler_jobs"] == 1
        assert health["services"] == 2
        assert health["watchdog_checks"] == 1

        assert runtime.remove_scheduler_job("job.scan") is True
        assert len(runtime.scheduler_jobs()) == 0

        stop_status = runtime.stop()
        assert stop_status.status == "stopped"

        print("[PASS] OPS-008 Q Series Runtime Runtime Path Migration")
        print(health)

        del stop_status
        del health
        del report
        del log_path
        del state_path
        del watchdog
        del job
        del oracle_status
        del svc
        del start_status
        del runtime
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_008_qseries_runtime_runtime_path_migration()
