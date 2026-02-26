from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_type_and_seed_history(
    database_url: str,
    type_name: str,
    rows_sql: str,
) -> tuple[TestClient, int]:
    """Create a type via API, insert raw history rows, return (client, type_id)."""
    client = TestClient(create_app())
    engine = create_engine(database_url)

    created = client.post("/api/v1/types", json={"name": type_name})
    assert created.status_code == 201
    type_id: int = created.json()["id"]

    with engine.begin() as conn:
        conn.execute(text(rows_sql))

    engine.dispose()
    return client, type_id


# ---------------------------------------------------------------------------
# Compound boundary test: 299 / 300 / 301 seconds in one sequence
# ---------------------------------------------------------------------------


def test_get_type_history_groups_adjacent_events_by_299_300_301_seconds(
    database_url: str,
) -> None:
    """Events chained at 299s, 300s, 301s gaps.

    Timeline:
      E1  10:00:00  (start)
      E2  10:04:59  (+299s from E1 → groups)
      E3  10:09:59  (+300s from E2 → groups, <=300)
      E4  10:15:00  (+301s from E3 → new group, >300)

    Expected: 2 groups  [E1+E2+E3 qty=6], [E4 qty=4].
    """
    client, type_id = _create_type_and_seed_history(
        database_url,
        "Necrons",
        """
        INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
        VALUES
            (1, 'IN_BOX', 'BUILDING', 1, '2026-02-25 10:00:00'),
            (1, 'IN_BOX', 'BUILDING', 2, '2026-02-25 10:04:59'),
            (1, 'IN_BOX', 'BUILDING', 3, '2026-02-25 10:09:59'),
            (1, 'IN_BOX', 'BUILDING', 4, '2026-02-25 10:15:00')
        """,
    )

    try:
        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["items"][0] == {
        "from_stage": "IN_BOX",
        "to_stage": "BUILDING",
        "qty": 6,
        "timestamp": "2026-02-25T10:00:00Z",
    }
    assert body["items"][1] == {
        "from_stage": "IN_BOX",
        "to_stage": "BUILDING",
        "qty": 4,
        "timestamp": "2026-02-25T10:15:00Z",
    }


# ---------------------------------------------------------------------------
# Non-adjacent same-transition events must NOT be grouped
# ---------------------------------------------------------------------------


def test_get_type_history_does_not_group_non_adjacent_equal_transitions(
    database_url: str,
) -> None:
    """A→B, then B→C, then A→B again — the two A→B events are separated
    by a different transition and must stay in separate groups even if
    the time gap is under 300s."""
    client, type_id = _create_type_and_seed_history(
        database_url,
        "Aeldari",
        """
        INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
        VALUES
            (1, 'IN_BOX', 'BUILDING', 2, '2026-02-25 11:00:00'),
            (1, 'BUILDING', 'PRIMING', 5, '2026-02-25 11:01:00'),
            (1, 'IN_BOX', 'BUILDING', 3, '2026-02-25 11:02:00')
        """,
    )

    try:
        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "from_stage": "IN_BOX",
                "to_stage": "BUILDING",
                "qty": 2,
                "timestamp": "2026-02-25T11:00:00Z",
            },
            {
                "from_stage": "BUILDING",
                "to_stage": "PRIMING",
                "qty": 5,
                "timestamp": "2026-02-25T11:01:00Z",
            },
            {
                "from_stage": "IN_BOX",
                "to_stage": "BUILDING",
                "qty": 3,
                "timestamp": "2026-02-25T11:02:00Z",
            },
        ]
    }


# ---------------------------------------------------------------------------
# Exact boundary: 300 seconds (two events only) → MUST group
# ---------------------------------------------------------------------------


def test_get_type_history_exactly_300_seconds_groups(database_url: str) -> None:
    """Two events of the same transition exactly 300s apart → one group."""
    client, type_id = _create_type_and_seed_history(
        database_url,
        "Tyranids",
        """
        INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
        VALUES
            (1, 'IN_BOX', 'BUILDING', 3, '2026-02-25 12:00:00'),
            (1, 'IN_BOX', 'BUILDING', 7, '2026-02-25 12:05:00')
        """,
    )

    try:
        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0] == {
        "from_stage": "IN_BOX",
        "to_stage": "BUILDING",
        "qty": 10,
        "timestamp": "2026-02-25T12:00:00Z",
    }


# ---------------------------------------------------------------------------
# Exact boundary: 301 seconds (two events only) → MUST NOT group
# ---------------------------------------------------------------------------


def test_get_type_history_exactly_301_seconds_does_not_group(database_url: str) -> None:
    """Two events of the same transition 301s apart → two separate groups."""
    client, type_id = _create_type_and_seed_history(
        database_url,
        "Orks",
        """
        INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
        VALUES
            (1, 'BUILDING', 'PRIMING', 4, '2026-02-25 13:00:00'),
            (1, 'BUILDING', 'PRIMING', 6, '2026-02-25 13:05:01')
        """,
    )

    try:
        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    assert items[0] == {
        "from_stage": "BUILDING",
        "to_stage": "PRIMING",
        "qty": 4,
        "timestamp": "2026-02-25T13:00:00Z",
    }
    assert items[1] == {
        "from_stage": "BUILDING",
        "to_stage": "PRIMING",
        "qty": 6,
        "timestamp": "2026-02-25T13:05:01Z",
    }


# ---------------------------------------------------------------------------
# Sliding window: comparison is against previous event, not group start
# ---------------------------------------------------------------------------


def test_get_type_history_sliding_window_groups_beyond_300s_from_start(
    database_url: str,
) -> None:
    """Chain of events each 299s apart. Total span from first to last is
    897s (>>300s), but every consecutive pair is within 300s so they all
    belong to a single group."""
    client, type_id = _create_type_and_seed_history(
        database_url,
        "Tau",
        """
        INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
        VALUES
            (1, 'PRIMING', 'PAINTING', 1, '2026-02-25 14:00:00'),
            (1, 'PRIMING', 'PAINTING', 2, '2026-02-25 14:04:59'),
            (1, 'PRIMING', 'PAINTING', 3, '2026-02-25 14:09:58'),
            (1, 'PRIMING', 'PAINTING', 4, '2026-02-25 14:14:57')
        """,
    )

    try:
        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0] == {
        "from_stage": "PRIMING",
        "to_stage": "PAINTING",
        "qty": 10,
        "timestamp": "2026-02-25T14:00:00Z",
    }


# ---------------------------------------------------------------------------
# Empty history
# ---------------------------------------------------------------------------


def test_get_type_history_empty_returns_empty_items(database_url: str) -> None:
    """A type with no history events returns an empty items list."""
    client = TestClient(create_app())
    try:
        created = client.post("/api/v1/types", json={"name": "EmptyType"})
        assert created.status_code == 201
        type_id = created.json()["id"]

        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"items": []}


# ---------------------------------------------------------------------------
# Single event → exactly one group
# ---------------------------------------------------------------------------


def test_get_type_history_single_event_returns_one_group(database_url: str) -> None:
    client, type_id = _create_type_and_seed_history(
        database_url,
        "SingleEvent",
        """
        INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
        VALUES
            (1, 'PAINTING', 'DONE', 5, '2026-02-25 15:00:00')
        """,
    )

    try:
        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0] == {
        "from_stage": "PAINTING",
        "to_stage": "DONE",
        "qty": 5,
        "timestamp": "2026-02-25T15:00:00Z",
    }


# ---------------------------------------------------------------------------
# Multiple disjoint groups in one sequence
# ---------------------------------------------------------------------------


def test_get_type_history_multiple_disjoint_groups(database_url: str) -> None:
    """Sequence with interleaving transitions forming 3 distinct groups.

    E1+E2 group (same transition, within 300s), E3 alone, E4+E5 group.
    """
    client, type_id = _create_type_and_seed_history(
        database_url,
        "MultiGroup",
        """
        INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
        VALUES
            (1, 'IN_BOX',   'BUILDING', 2, '2026-02-25 16:00:00'),
            (1, 'IN_BOX',   'BUILDING', 3, '2026-02-25 16:03:00'),
            (1, 'BUILDING', 'PRIMING',  1, '2026-02-25 16:04:00'),
            (1, 'PRIMING',  'PAINTING', 1, '2026-02-25 16:05:00'),
            (1, 'PRIMING',  'PAINTING', 1, '2026-02-25 16:06:00')
        """,
    )

    try:
        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 3
    assert items[0] == {
        "from_stage": "IN_BOX",
        "to_stage": "BUILDING",
        "qty": 5,
        "timestamp": "2026-02-25T16:00:00Z",
    }
    assert items[1] == {
        "from_stage": "BUILDING",
        "to_stage": "PRIMING",
        "qty": 1,
        "timestamp": "2026-02-25T16:04:00Z",
    }
    assert items[2] == {
        "from_stage": "PRIMING",
        "to_stage": "PAINTING",
        "qty": 2,
        "timestamp": "2026-02-25T16:05:00Z",
    }


# ---------------------------------------------------------------------------
# Simultaneous events (0-second gap) → MUST group
# ---------------------------------------------------------------------------


def test_get_type_history_simultaneous_events_group(database_url: str) -> None:
    """Events at the exact same timestamp must be grouped together."""
    client, type_id = _create_type_and_seed_history(
        database_url,
        "Simultaneous",
        """
        INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
        VALUES
            (1, 'IN_BOX', 'BUILDING', 1, '2026-02-25 17:00:00'),
            (1, 'IN_BOX', 'BUILDING', 2, '2026-02-25 17:00:00'),
            (1, 'IN_BOX', 'BUILDING', 3, '2026-02-25 17:00:00')
        """,
    )

    try:
        response = client.get(f"/api/v1/types/{type_id}/history")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0] == {
        "from_stage": "IN_BOX",
        "to_stage": "BUILDING",
        "qty": 6,
        "timestamp": "2026-02-25T17:00:00Z",
    }
