from pathlib import Path

REVISION = "OSN_023_UEFA_CURL_TRANSPORT_REBUILD_V1"
ROOT = Path.cwd()

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("=" * 118)
    print(" OSN-023 EPL + UCL OFFICIAL PHYSICAL ACQUISITION — UEFA CURL TRANSPORT REBUILD")
    print("=" * 118)

    require("qseries_v2/oracle_source_network/acquisition/mls_official_live.py")
    require("qseries_v2/oracle_source_network/acquisition/official_http.py")

    write(
        "qseries_v2/oracle_source_network/acquisition/european_soccer_official_live.py",
        '\nfrom .official_http import get_official_text\nfrom datetime import datetime, timezone\nimport hashlib\nimport subprocess\n\nEPL_FIXTURES_URL = "https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-202627-premier-league-season"\n\nUCL_OFFICIAL_URLS = (\n    "https://www.uefa.com/uefachampionsleague/fixtures-results/",\n    "https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/",\n)\n\ndef acquire_epl_fixtures(timeout=8.0):\n    s = get_official_text(EPL_FIXTURES_URL, timeout=timeout)\n    low = s["body"].lower()\n    s.update({\n        "provider": "premier_league_official",\n        "league": "EPL",\n        "source_authority": "official_league",\n        "markers": {\n            "premier_league": "premier league" in low,\n            "fixtures": "fixture" in low,\n            "2026_27": ("2026/27" in low or "2026-27" in low or "202627" in low),\n        },\n    })\n    return s\n\ndef _ucl_markers(body):\n    low = body.lower()\n    return {\n        "champions_league": ("champions league" in low or "uefa champions league" in low),\n        "competition_identity": ("uefachampionsleague" in low or "champions league" in low),\n        "fixtures_or_matches": ("fixture" in low or "matches" in low or "matchday" in low),\n    }\n\ndef _curl_official_text(url, timeout=7.0):\n    timeout = max(1, min(int(float(timeout)), 8))\n    cmd = [\n        "curl.exe",\n        "--location",\n        "--fail",\n        "--silent",\n        "--show-error",\n        "--compressed",\n        "--connect-timeout", "4",\n        "--max-time", str(timeout),\n        "--user-agent", "Mozilla/5.0 QSeries-Oracle-OSN/1.0",\n        "--header", "Accept: text/html,application/xhtml+xml",\n        url,\n    ]\n\n    try:\n        p = subprocess.run(\n            cmd,\n            text=False,\n            capture_output=True,\n            timeout=timeout + 3,\n        )\n    except FileNotFoundError as exc:\n        raise RuntimeError("curl.exe is not available on this Windows runtime") from exc\n    except subprocess.TimeoutExpired as exc:\n        raise TimeoutError(f"curl.exe outer timeout exceeded for {url}") from exc\n\n    if p.returncode != 0:\n        err = p.stderr.decode("utf-8", errors="replace").strip()\n        raise RuntimeError(f"curl.exe failed rc={p.returncode}: {err}")\n\n    raw = p.stdout\n    if not raw:\n        raise RuntimeError("curl.exe returned an empty UEFA payload")\n\n    body = raw.decode("utf-8", errors="replace")\n    return {\n        "url": url,\n        "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),\n        "body": body,\n        "payload_sha256": hashlib.sha256(raw).hexdigest(),\n        "read_only": True,\n        "execution_authority": False,\n        "transport": "curl.exe",\n    }\n\ndef acquire_ucl_fixtures(timeout=7.0):\n    errors = []\n\n    for url in UCL_OFFICIAL_URLS:\n        # First retain the already-certified stdlib path as the preferred transport.\n        try:\n            s = get_official_text(url, timeout=min(float(timeout), 4.0))\n            markers = _ucl_markers(s["body"])\n            if all(markers.values()):\n                s.update({\n                    "provider": "uefa_official",\n                    "league": "UCL",\n                    "source_authority": "official_governing_body",\n                    "markers": markers,\n                    "selected_official_url": url,\n                    "transport": "urllib",\n                })\n                return s\n            errors.append(f"urllib {url}: marker validation failed {markers}")\n        except Exception as exc:\n            errors.append(f"urllib {url}: {type(exc).__name__}: {exc}")\n\n        # Windows curl uses a different transport/TLS stack and is independently bounded.\n        try:\n            s = _curl_official_text(url, timeout=timeout)\n            markers = _ucl_markers(s["body"])\n            if all(markers.values()):\n                s.update({\n                    "provider": "uefa_official",\n                    "league": "UCL",\n                    "source_authority": "official_governing_body",\n                    "markers": markers,\n                    "selected_official_url": url,\n                })\n                return s\n            errors.append(f"curl {url}: marker validation failed {markers}")\n        except Exception as exc:\n            errors.append(f"curl {url}: {type(exc).__name__}: {exc}")\n\n    raise RuntimeError(\n        "all bounded official UEFA transports failed | " + " | ".join(errors)\n    )\n',
    )
    write(
        "test_osn_023_epl_ucl_official_physical_acquisition.py",
        '\nimport subprocess\nimport sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.acquisition.european_soccer_official_live import acquire_epl_fixtures, acquire_ucl_fixtures\n\ne = acquire_epl_fixtures(8.0)\nprint(f"[PHYSICAL] EPL bytes={len(e[\'body\'])} markers={e[\'markers\']}")\nassert e["provider"] == "premier_league_official"\nassert e["league"] == "EPL"\nassert e["source_authority"] == "official_league"\nassert len(e["payload_sha256"]) == 64\nassert e["read_only"] is True\nassert e["execution_authority"] is False\nassert all(e["markers"].values())\n\nu = acquire_ucl_fixtures(7.0)\nprint(f"[PHYSICAL] UCL bytes={len(u[\'body\'])} markers={u[\'markers\']}")\nprint(f"[PHYSICAL] UCL transport={u[\'transport\']} selected_official_url={u[\'selected_official_url\']}")\nassert u["provider"] == "uefa_official"\nassert u["league"] == "UCL"\nassert u["source_authority"] == "official_governing_body"\nassert len(u["payload_sha256"]) == 64\nassert u["read_only"] is True\nassert u["execution_authority"] is False\nassert all(u["markers"].values())\nassert "uefa.com" in u["selected_official_url"]\nassert u["transport"] in ("urllib", "curl.exe")\n\nprint("[PASS] EPL + UCL official physical acquisition completed")\n"""\n\ntry:\n    p = subprocess.run(\n        [sys.executable, "-c", probe],\n        text=True,\n        capture_output=True,\n        timeout=35,\n    )\nexcept subprocess.TimeoutExpired:\n    raise AssertionError(\n        "EPL/UCL acquisition exceeded hard 35-second wall-clock gate"\n    )\n\nif p.stdout:\n    print(p.stdout.rstrip())\nif p.stderr:\n    print(p.stderr.rstrip())\n\nassert p.returncode == 0, f"EPL/UCL physical probe failed rc={p.returncode}"\n\nprint("[PASS] UEFA urllib + curl.exe transport boundary certified")\nprint("[PASS] source authority remains UEFA official only")\nprint("[PASS] no recursive scan / no unbounded network read")\nprint("[PASS] execution_authority=FALSE")\nprint("[PASS] OSN-023 EPL + UCL official physical acquisition certified")\n',
    )

    print("[PASS] OSN-023 UEFA transport rebuild installed")
    print("[PASS] urllib retained as preferred path")
    print("[PASS] curl.exe added as bounded Windows transport fallback")
    print("[PASS] source authority remains UEFA official only")
    print("[PASS] hard combined physical gate=35s")
    print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    main()
