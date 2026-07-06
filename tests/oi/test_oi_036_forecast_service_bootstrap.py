from qseries_v2.oracle_intelligence.forecast_service_bootstrap import (
    ForecastServiceBootstrap,
    bootstrap_forecast_service,
)


class FakeService:
    def diagnostics(self):
        return {
            "module": "fake_forecast_service",
            "status": "ok",
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_036_forecast_service_bootstrap():
    bootstrap = ForecastServiceBootstrap(service=FakeService())

    before = bootstrap.diagnostics()
    assert before["status"] == "not_booted"
    assert before["booted"] is False
    assert before["service_ready"] is True
    assert before["read_only"] is True
    assert before["execution_allowed"] is False

    status = bootstrap.bootstrap()
    assert status["status"] == "ok"
    assert status["booted"] is True
    assert status["service_ready"] is True
    assert status["service_diagnostics"]["status"] == "ok"
    assert status["read_only"] is True
    assert status["execution_allowed"] is False

    payload = bootstrap.api_payload()
    assert payload["status"] == "ok"
    assert payload["booted"] is True
    assert payload["service_ready"] is True

    global_status = bootstrap_forecast_service()
    assert global_status["read_only"] is True
    assert global_status["execution_allowed"] is False

    print("[PASS] OI-036 Forecast Service Bootstrap")
    print({
        "status": status["status"],
        "booted": status["booted"],
        "service_ready": status["service_ready"],
    })


if __name__ == "__main__":
    test_oi_036_forecast_service_bootstrap()
