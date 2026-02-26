"""QA-002: Move endpoint – concurrency and invariant tests.

Verifies pessimistic locking (SELECT ... FOR UPDATE) prevents negative counts
under concurrent load, and validates additional move invariants not covered
by the basic API-005 tests.
"""

from __future__ import annotations

import concurrent.futures

from fastapi.testclient import TestClient
from sqlalchemy import text



def _seed_stage(db_engine, type_id: int, stage: str, count: int) -> None:
    with db_engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE stage_counts SET count = :count "
                "WHERE type_id = :type_id AND stage_name = :stage"
            ),
            {"type_id": type_id, "count": count, "stage": stage},
        )


def _get_counts(db_engine, type_id: int) -> dict[str, int]:
    with db_engine.begin() as conn:
        rows = (
            conn.execute(
                text("SELECT stage_name, count FROM stage_counts WHERE type_id = :type_id"),
                {"type_id": type_id},
            )
            .mappings()
            .all()
        )
    return {row["stage_name"]: row["count"] for row in rows}


def _count_history(db_engine, type_id: int) -> int:
    with db_engine.begin() as conn:
        return conn.execute(
            text("SELECT COUNT(*) FROM history_logs WHERE type_id = :tid"),
            {"tid": type_id},
        ).scalar_one()


# ── Concurrency ──────────────────────────────────────────────────────────────


def test_concurrent_single_unit_moves_never_overdraw(client: TestClient, db_engine) -> None:
    """
    20 parallel requests each moving 1 unit from IN_BOX (seeded with 10).
    Pessimistic lock must guarantee exactly 10 succeed, 10 fail, and
    final IN_BOX=0, BUILDING=10.
    """

    initial_qty = 10
    parallel_requests = 20

    if True:
        created = client.post("/api/v1/types", json={"name": "Concurrency A"})
        assert created.status_code == 201
        type_id = created.json()["id"]
        _seed_stage(db_engine, type_id, "IN_BOX", initial_qty)

        def fire_move(_: int) -> int:
            thread_client = client
            resp = thread_client.post(
                f"/api/v1/types/{type_id}/move",
                json={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": 1},
            )
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            codes = list(pool.map(fire_move, range(parallel_requests)))

        assert codes.count(200) == initial_qty
        assert codes.count(400) == parallel_requests - initial_qty

        counts = _get_counts(db_engine, type_id)
        assert counts["IN_BOX"] == 0
        assert counts["BUILDING"] == initial_qty
        assert _count_history(db_engine, type_id) == initial_qty


def test_concurrent_batch_moves_respect_available_qty(client: TestClient, db_engine) -> None:
    """
    6 parallel requests each moving 5 units from IN_BOX (seeded with 15).
    Exactly 3 should succeed (15 / 5), 3 should fail.
    """

    initial_qty = 15
    move_qty = 5
    parallel_requests = 6

    if True:
        created = client.post("/api/v1/types", json={"name": "Concurrency B"})
        assert created.status_code == 201
        type_id = created.json()["id"]
        _seed_stage(db_engine, type_id, "IN_BOX", initial_qty)

        def fire_move(_: int) -> int:
            thread_client = client
            resp = thread_client.post(
                f"/api/v1/types/{type_id}/move",
                json={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": move_qty},
            )
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            codes = list(pool.map(fire_move, range(parallel_requests)))

        expected_successes = initial_qty // move_qty
        assert codes.count(200) == expected_successes
        assert codes.count(400) == parallel_requests - expected_successes

        counts = _get_counts(db_engine, type_id)
        assert counts["IN_BOX"] == 0
        assert counts["BUILDING"] == initial_qty


def test_concurrent_moves_on_different_stages_are_independent(client: TestClient, db_engine) -> None:
    """
    Concurrent moves from different source stages do not block each other
    and produce correct totals.
    """

    if True:
        created = client.post("/api/v1/types", json={"name": "Multi Stage"})
        assert created.status_code == 201
        type_id = created.json()["id"]

        _seed_stage(db_engine, type_id, "IN_BOX", 5)
        _seed_stage(db_engine, type_id, "BUILDING", 5)

        def move_inbox_to_building(_: int) -> int:
            return client.post(
                f"/api/v1/types/{type_id}/move",
                json={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": 1},
            ).status_code

        def move_building_to_painting(_: int) -> int:
            return client.post(
                f"/api/v1/types/{type_id}/move",
                json={"from_stage": "BUILDING", "to_stage": "PAINTING", "qty": 1},
            ).status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            inbox_futures = [pool.submit(move_inbox_to_building, i) for i in range(5)]
            building_futures = [pool.submit(move_building_to_painting, i) for i in range(5)]

            inbox_codes = [f.result() for f in inbox_futures]
            building_codes = [f.result() for f in building_futures]

        inbox_ok = inbox_codes.count(200)
        building_ok = building_codes.count(200)

        assert inbox_ok == 5
        assert building_ok <= 10  # at most 5 original + 5 incoming

        counts = _get_counts(db_engine, type_id)
        assert counts["IN_BOX"] == 0
        assert counts["BUILDING"] == 5 + inbox_ok - building_ok
        assert counts["PAINTING"] == building_ok


# ── Invariants ───────────────────────────────────────────────────────────────


def test_move_exact_qty_drains_source_to_zero(client: TestClient, db_engine) -> None:
    """Moving exactly the available count leaves source at 0."""

    if True:
        created = client.post("/api/v1/types", json={"name": "Drain"})
        assert created.status_code == 201
        type_id = created.json()["id"]
        _seed_stage(db_engine, type_id, "IN_BOX", 7)

        resp = client.post(
            f"/api/v1/types/{type_id}/move",
            json={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": 7},
        )

        assert resp.status_code == 200
        assert resp.json()["counts"]["in_box"] == 0
        assert resp.json()["counts"]["building"] == 7


def test_move_skip_stages_is_allowed(client: TestClient, db_engine) -> None:
    """IN_BOX -> DONE is a valid forward transition (skip intermediate stages)."""

    if True:
        created = client.post("/api/v1/types", json={"name": "Skip"})
        assert created.status_code == 201
        type_id = created.json()["id"]
        _seed_stage(db_engine, type_id, "IN_BOX", 3)

        resp = client.post(
            f"/api/v1/types/{type_id}/move",
            json={"from_stage": "IN_BOX", "to_stage": "DONE", "qty": 2},
        )

        assert resp.status_code == 200
        assert resp.json()["counts"]["in_box"] == 1
        assert resp.json()["counts"]["done"] == 2


def test_move_same_stage_is_rejected(client: TestClient, db_engine) -> None:
    """from_stage == to_stage is not a forward transition."""

    if True:
        created = client.post("/api/v1/types", json={"name": "SameStage"})
        assert created.status_code == 201
        type_id = created.json()["id"]

        resp = client.post(
            f"/api/v1/types/{type_id}/move",
            json={"from_stage": "IN_BOX", "to_stage": "IN_BOX", "qty": 1},
        )

        assert resp.status_code == 400
        assert resp.json()["code"] == "ERR_INVALID_STAGE_TRANSITION"


def test_move_nonexistent_type_returns_404(client: TestClient, db_engine) -> None:

    if True:
        resp = client.post(
            "/api/v1/types/999999/move",
            json={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": 1},
        )
        assert resp.status_code == 404


def test_sequential_moves_accumulate_correctly(client: TestClient, db_engine) -> None:
    """Multi-step moves through the pipeline accumulate as expected."""

    if True:
        created = client.post("/api/v1/types", json={"name": "MultiStep"})
        assert created.status_code == 201
        type_id = created.json()["id"]
        _seed_stage(db_engine, type_id, "IN_BOX", 10)

        assert (
            client.post(
                f"/api/v1/types/{type_id}/move",
                json={"from_stage": "IN_BOX", "to_stage": "BUILDING", "qty": 3},
            ).status_code
            == 200
        )

        assert (
            client.post(
                f"/api/v1/types/{type_id}/move",
                json={"from_stage": "BUILDING", "to_stage": "PAINTING", "qty": 2},
            ).status_code
            == 200
        )

        resp = client.post(
            f"/api/v1/types/{type_id}/move",
            json={"from_stage": "IN_BOX", "to_stage": "DONE", "qty": 5},
        )
        assert resp.status_code == 200

        final = resp.json()["counts"]
        assert final == {
            "in_box": 2,
            "building": 1,
            "priming": 0,
            "painting": 2,
            "done": 5,
        }
        assert _count_history(db_engine, type_id) == 3
