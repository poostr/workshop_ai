#!/usr/bin/env python3
"""
Minimal e2e smoke test for Miniatures Progress Tracker.

Runs a full scenario against a live stack:
  create type -> move -> history -> export -> import -> verify merge

Usage:
    python tests/e2e_smoke.py [BASE_URL]

BASE_URL defaults to http://localhost:8000/api/v1
(use http://localhost:8080/api/v1 to test through nginx)
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10
UNIQUE_SUFFIX = str(int(time.time() * 1000))


class SmokeTestError(Exception):
    pass


def _request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    expected_status: int = 200,
) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            resp_body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        status = exc.code
        resp_body = json.loads(exc.read())

    if status != expected_status:
        raise SmokeTestError(
            f"{method} {path} -> {status} (expected {expected_status})\n{json.dumps(resp_body, indent=2)}"
        )
    return resp_body


def _step(label: str) -> None:
    print(f"  [{label}]", end=" ", flush=True)


def _ok() -> None:
    print("OK")


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise SmokeTestError(f"Assertion failed: {msg}")


def run() -> None:
    type_name = f"SmokeTest_{UNIQUE_SUFFIX}"

    # --- Step 1: Health ---
    _step("health")
    health_url = BASE_URL.rsplit("/api/v1", 1)[0] + "/health"
    req = urllib.request.Request(health_url)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        _assert(resp.status == 200, "health endpoint should return 200")
    _ok()

    # --- Step 2: Create type ---
    _step("create type")
    created = _request("POST", "/types", body={"name": type_name}, expected_status=201)
    type_id = created["id"]
    _assert(created["name"] == type_name, "created type name mismatch")
    _assert(created["counts"]["in_box"] == 0, "initial in_box should be 0")
    _ok()

    # --- Step 3: Get type details ---
    _step("get type")
    details = _request("GET", f"/types/{type_id}")
    _assert(details["name"] == type_name, "type name mismatch in details")
    _ok()

    # --- Step 4: Duplicate type name should fail ---
    _step("duplicate type")
    dup_resp = _request("POST", "/types", body={"name": type_name}, expected_status=400)
    _assert(dup_resp["code"] == "ERR_DUPLICATE_TYPE_NAME", "expected duplicate name error")
    _ok()

    # --- Step 5: Move (need to import some initial counts first) ---
    _step("seed via import")
    import_payload = {
        "types": [
            {
                "name": type_name,
                "stage_counts": [
                    {"stage": "IN_BOX", "count": 10},
                    {"stage": "BUILDING", "count": 0},
                    {"stage": "PRIMING", "count": 0},
                    {"stage": "PAINTING", "count": 0},
                    {"stage": "DONE", "count": 0},
                ],
                "history": [],
            }
        ]
    }
    _request("POST", "/import", body=import_payload)
    _ok()

    # Verify seeded counts
    _step("verify seed")
    after_seed = _request("GET", f"/types/{type_id}")
    _assert(after_seed["counts"]["in_box"] == 10, f"in_box should be 10, got {after_seed['counts']['in_box']}")
    _ok()

    # --- Step 6: Move forward IN_BOX -> BUILDING ---
    _step("move IN_BOX->BUILDING")
    moved = _request(
        "POST",
        f"/types/{type_id}/move",
        body={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": 3},
    )
    _assert(moved["counts"]["in_box"] == 7, "in_box should be 7 after move")
    _assert(moved["counts"]["building"] == 3, "building should be 3 after move")
    _ok()

    # --- Step 7: Move forward BUILDING -> DONE (skip stages) ---
    _step("move BUILDING->DONE")
    moved2 = _request(
        "POST",
        f"/types/{type_id}/move",
        body={"from_stage": "BUILDING", "to_stage": "DONE", "qty": 1},
    )
    _assert(moved2["counts"]["building"] == 2, "building should be 2")
    _assert(moved2["counts"]["done"] == 1, "done should be 1")
    _ok()

    # --- Step 8: Move backward should fail ---
    _step("move backward (expect error)")
    err = _request(
        "POST",
        f"/types/{type_id}/move",
        body={"from_stage": "DONE", "to_stage": "IN_BOX", "qty": 1},
        expected_status=400,
    )
    _assert(err["code"] == "ERR_INVALID_STAGE_TRANSITION", "expected transition error")
    _ok()

    # --- Step 9: Move with insufficient qty ---
    _step("move insufficient qty (expect error)")
    err2 = _request(
        "POST",
        f"/types/{type_id}/move",
        body={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": 999},
        expected_status=400,
    )
    _assert(err2["code"] == "ERR_INSUFFICIENT_QTY", "expected insufficient qty error")
    _ok()

    # --- Step 10: History ---
    _step("history")
    history = _request("GET", f"/types/{type_id}/history")
    _assert(len(history["items"]) >= 2, f"expected at least 2 history groups, got {len(history['items'])}")
    first_group = history["items"][0]
    _assert(first_group["from_stage"] == "IN_BOX", "first group from_stage")
    _assert(first_group["to_stage"] == "BUILDING", "first group to_stage")
    _ok()

    # --- Step 11: Export ---
    _step("export")
    export = _request("GET", "/export")
    _assert(len(export["types"]) >= 1, "export should contain at least 1 type")
    smoke_types = [t for t in export["types"] if t["name"] == type_name]
    _assert(len(smoke_types) == 1, "export should contain our smoke test type")
    exported_type = smoke_types[0]
    _assert(len(exported_type["history"]) >= 2, "exported history should have at least 2 events")
    _ok()

    # --- Step 12: Import (merge) ---
    _step("import merge")
    merge_payload = {
        "types": [
            {
                "name": type_name,
                "stage_counts": [
                    {"stage": "IN_BOX", "count": 5},
                    {"stage": "BUILDING", "count": 0},
                    {"stage": "PRIMING", "count": 0},
                    {"stage": "PAINTING", "count": 0},
                    {"stage": "DONE", "count": 0},
                ],
                "history": [
                    {
                        "from_stage": "IN_BOX",
                        "to_stage": "PRIMING",
                        "qty": 5,
                        "created_at": "2025-01-01T00:00:00",
                    }
                ],
            }
        ]
    }
    _request("POST", "/import", body=merge_payload)
    _ok()

    # --- Step 13: Verify merge ---
    _step("verify merge")
    after_merge = _request("GET", f"/types/{type_id}")
    _assert(after_merge["counts"]["in_box"] == 12, f"in_box should be 12 after merge, got {after_merge['counts']['in_box']}")
    _ok()

    _step("verify history after merge")
    history_after = _request("GET", f"/types/{type_id}/history")
    _assert(
        len(history_after["items"]) >= 3,
        f"expected at least 3 history groups after merge, got {len(history_after['items'])}",
    )
    _ok()

    # --- Step 14: List types ---
    _step("list types")
    all_types = _request("GET", "/types")
    _assert(len(all_types["items"]) >= 1, "list should contain at least 1 type")
    _ok()

    # --- Step 15: Import invalid payload should fail ---
    _step("import invalid (expect error)")
    bad_payload = {"types": [{"name": "X", "stage_counts": [], "history": []}]}
    _request("POST", "/import", body=bad_payload, expected_status=400)
    _ok()


def wait_for_health(max_retries: int = 30, interval: float = 2.0) -> None:
    """Poll health endpoint until the service is ready."""
    health_url = BASE_URL.rsplit("/api/v1", 1)[0] + "/health"
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(health_url)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            pass
        if attempt < max_retries - 1:
            time.sleep(interval)
    raise SmokeTestError(f"Service not healthy after {max_retries * interval:.0f}s at {health_url}")


def main() -> None:
    global BASE_URL
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1].rstrip("/")

    print(f"E2E Smoke Test — target: {BASE_URL}")
    print("Waiting for service health...")
    wait_for_health()
    print("Service is healthy. Running scenario...\n")

    try:
        run()
    except SmokeTestError as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\nAll smoke tests passed.")


if __name__ == "__main__":
    main()
