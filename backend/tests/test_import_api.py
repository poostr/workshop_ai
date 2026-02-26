from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.main import create_app


ERR_INVALID_IMPORT_FORMAT = {
    "code": "ERR_INVALID_IMPORT_FORMAT",
    "message": "Import payload is invalid.",
}


def _all_stages_zero(overrides: dict[str, int] | None = None) -> list[dict]:
    base = {"IN_BOX": 0, "BUILDING": 0, "PRIMING": 0, "PAINTING": 0, "DONE": 0}
    if overrides:
        base.update(overrides)
    return [{"stage": s, "count": c} for s, c in base.items()]


# ---------------------------------------------------------------------------
# Merge semantics: counts summed + history appended
# ---------------------------------------------------------------------------


def test_post_import_merges_counts_and_appends_history(database_url: str) -> None:
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        created = client.post("/api/v1/types", json={"name": "Alpha"})
        assert created.status_code == 201

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE stage_counts
                    SET count = CASE
                        WHEN stage_name = 'IN_BOX' THEN 10
                        WHEN stage_name = 'BUILDING' THEN 2
                        ELSE count
                    END
                    WHERE type_id = 1
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at)
                    VALUES (1, 'IN_BOX', 'BUILDING', 1, '2026-02-25 08:00:00')
                    """
                )
            )

        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "Alpha",
                        "stage_counts": _all_stages_zero(
                            {"IN_BOX": 3, "BUILDING": 1, "PRIMING": 4, "DONE": 2}
                        ),
                        "history": [
                            {
                                "from_stage": "BUILDING",
                                "to_stage": "PRIMING",
                                "qty": 2,
                                "created_at": "2026-02-25T09:00:00Z",
                            }
                        ],
                    },
                    {
                        "name": "Beta",
                        "stage_counts": _all_stages_zero({"IN_BOX": 5, "PAINTING": 1}),
                        "history": [
                            {
                                "from_stage": "IN_BOX",
                                "to_stage": "PAINTING",
                                "qty": 1,
                                "created_at": "2026-02-25T10:00:00Z",
                            }
                        ],
                    },
                ]
            },
        )
        export_response = client.get("/api/v1/export")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert export_response.status_code == 200
    assert export_response.json() == {
        "types": [
            {
                "name": "Alpha",
                "stage_counts": [
                    {"stage": "IN_BOX", "count": 13},
                    {"stage": "BUILDING", "count": 3},
                    {"stage": "PRIMING", "count": 4},
                    {"stage": "PAINTING", "count": 0},
                    {"stage": "DONE", "count": 2},
                ],
                "history": [
                    {
                        "from_stage": "IN_BOX",
                        "to_stage": "BUILDING",
                        "qty": 1,
                        "created_at": "2026-02-25T08:00:00Z",
                    },
                    {
                        "from_stage": "BUILDING",
                        "to_stage": "PRIMING",
                        "qty": 2,
                        "created_at": "2026-02-25T09:00:00Z",
                    },
                ],
            },
            {
                "name": "Beta",
                "stage_counts": [
                    {"stage": "IN_BOX", "count": 5},
                    {"stage": "BUILDING", "count": 0},
                    {"stage": "PRIMING", "count": 0},
                    {"stage": "PAINTING", "count": 1},
                    {"stage": "DONE", "count": 0},
                ],
                "history": [
                    {
                        "from_stage": "IN_BOX",
                        "to_stage": "PAINTING",
                        "qty": 1,
                        "created_at": "2026-02-25T10:00:00Z",
                    }
                ],
            },
        ]
    }


def test_post_import_creates_new_type_with_counts_and_history(database_url: str) -> None:
    """Import a type that does not yet exist — it should be created with given
    counts and history (pure creation, not a merge)."""
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "NewOnly",
                        "stage_counts": _all_stages_zero({"IN_BOX": 7, "DONE": 3}),
                        "history": [
                            {
                                "from_stage": "IN_BOX",
                                "to_stage": "DONE",
                                "qty": 3,
                                "created_at": "2026-02-25T08:00:00Z",
                            }
                        ],
                    }
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200

    with engine.begin() as conn:
        type_row = conn.execute(text("SELECT id FROM miniature_types WHERE name = 'NewOnly'")).one()
        counts = dict(
            conn.execute(
                text("SELECT stage_name, count FROM stage_counts WHERE type_id = :tid"),
                {"tid": type_row[0]},
            ).all()
        )
        history = (
            conn.execute(
                text("SELECT from_stage, to_stage, qty FROM history_logs WHERE type_id = :tid"),
                {"tid": type_row[0]},
            )
            .mappings()
            .all()
        )

    assert counts == {"IN_BOX": 7, "BUILDING": 0, "PRIMING": 0, "PAINTING": 0, "DONE": 3}
    assert list(history) == [{"from_stage": "IN_BOX", "to_stage": "DONE", "qty": 3}]


def test_post_import_repeated_import_doubles_counts_and_history(database_url: str) -> None:
    """Importing the same payload twice doubles counts and appends history
    without deduplication (per PRD: dedupe не делаем)."""
    client = TestClient(create_app())
    engine = create_engine(database_url)

    payload = {
        "types": [
            {
                "name": "Doubles",
                "stage_counts": _all_stages_zero({"IN_BOX": 5, "BUILDING": 2}),
                "history": [
                    {
                        "from_stage": "IN_BOX",
                        "to_stage": "BUILDING",
                        "qty": 2,
                        "created_at": "2026-02-25T09:00:00Z",
                    }
                ],
            }
        ]
    }

    try:
        first = client.post("/api/v1/import", json=payload)
        assert first.status_code == 200
        second = client.post("/api/v1/import", json=payload)
        assert second.status_code == 200
    finally:
        get_settings.cache_clear()

    with engine.begin() as conn:
        type_row = conn.execute(text("SELECT id FROM miniature_types WHERE name = 'Doubles'")).one()
        counts = dict(
            conn.execute(
                text("SELECT stage_name, count FROM stage_counts WHERE type_id = :tid"),
                {"tid": type_row[0]},
            ).all()
        )
        history_count = conn.execute(
            text("SELECT COUNT(*) FROM history_logs WHERE type_id = :tid"),
            {"tid": type_row[0]},
        ).scalar_one()

    assert counts["IN_BOX"] == 10
    assert counts["BUILDING"] == 4
    assert history_count == 2


def test_post_import_empty_types_list_is_noop(database_url: str) -> None:
    """Importing an empty types list succeeds without side effects."""
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        client.post("/api/v1/types", json={"name": "Existing"})
        response = client.post("/api/v1/import", json={"types": []})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    with engine.begin() as conn:
        type_count = conn.execute(text("SELECT COUNT(*) FROM miniature_types")).scalar_one()

    assert type_count == 1


# ---------------------------------------------------------------------------
# Rollback: all-or-nothing on invalid payload
# ---------------------------------------------------------------------------


def test_post_import_rolls_back_all_changes_on_invalid_payload(database_url: str) -> None:
    """When the second type has duplicate stage_counts, the whole import
    (including the valid first type) must be rolled back."""
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        created = client.post("/api/v1/types", json={"name": "Base"})
        assert created.status_code == 201

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE stage_counts
                    SET count = 10
                    WHERE type_id = 1 AND stage_name = 'IN_BOX'
                    """
                )
            )

        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "Base",
                        "stage_counts": _all_stages_zero({"IN_BOX": 2}),
                        "history": [],
                    },
                    {
                        "name": "Broken",
                        "stage_counts": [
                            {"stage": "IN_BOX", "count": 1},
                            {"stage": "IN_BOX", "count": 2},
                            {"stage": "PRIMING", "count": 0},
                            {"stage": "PAINTING", "count": 0},
                            {"stage": "DONE", "count": 0},
                        ],
                        "history": [],
                    },
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == ERR_INVALID_IMPORT_FORMAT

    with engine.begin() as connection:
        in_box_count = connection.execute(
            text("SELECT count FROM stage_counts WHERE type_id = 1 AND stage_name = 'IN_BOX'")
        ).scalar_one()
        broken_type_count = connection.execute(
            text("SELECT COUNT(*) FROM miniature_types WHERE name = 'Broken'")
        ).scalar_one()
        history_count = connection.execute(text("SELECT COUNT(*) FROM history_logs")).scalar_one()

    assert in_box_count == 10
    assert broken_type_count == 0
    assert history_count == 0


def test_post_import_rejects_missing_stage_counts(database_url: str) -> None:
    client = TestClient(create_app())

    try:
        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "Gamma",
                        "stage_counts": [
                            {"stage": "IN_BOX", "count": 1},
                            {"stage": "BUILDING", "count": 0},
                            {"stage": "PRIMING", "count": 0},
                            {"stage": "PAINTING", "count": 0},
                        ],
                        "history": [],
                    }
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == ERR_INVALID_IMPORT_FORMAT


def test_post_import_rejects_completely_malformed_payload(database_url: str) -> None:
    """A payload without the required 'types' key must be rejected."""
    client = TestClient(create_app())

    try:
        response = client.post("/api/v1/import", json={"invalid": True})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == ERR_INVALID_IMPORT_FORMAT


def test_post_import_rejects_invalid_stage_name_in_counts(database_url: str) -> None:
    """A stage_counts entry with an unknown stage value must be rejected."""
    client = TestClient(create_app())

    try:
        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "BadStage",
                        "stage_counts": [
                            {"stage": "NONEXISTENT", "count": 1},
                            {"stage": "BUILDING", "count": 0},
                            {"stage": "PRIMING", "count": 0},
                            {"stage": "PAINTING", "count": 0},
                            {"stage": "DONE", "count": 0},
                        ],
                        "history": [],
                    }
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == ERR_INVALID_IMPORT_FORMAT


def test_post_import_rejects_invalid_stage_name_in_history(database_url: str) -> None:
    """History with an unknown from_stage/to_stage must be rejected."""
    client = TestClient(create_app())

    try:
        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "BadHistory",
                        "stage_counts": _all_stages_zero({"IN_BOX": 1}),
                        "history": [
                            {
                                "from_stage": "NONEXISTENT",
                                "to_stage": "BUILDING",
                                "qty": 1,
                                "created_at": "2026-02-25T08:00:00Z",
                            }
                        ],
                    }
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == ERR_INVALID_IMPORT_FORMAT


def test_post_import_rejects_negative_count(database_url: str) -> None:
    """Negative count values in stage_counts must be rejected."""
    client = TestClient(create_app())

    try:
        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "NegCount",
                        "stage_counts": [
                            {"stage": "IN_BOX", "count": -1},
                            {"stage": "BUILDING", "count": 0},
                            {"stage": "PRIMING", "count": 0},
                            {"stage": "PAINTING", "count": 0},
                            {"stage": "DONE", "count": 0},
                        ],
                        "history": [],
                    }
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == ERR_INVALID_IMPORT_FORMAT


def test_post_import_rejects_extra_fields(database_url: str) -> None:
    """Extra fields in the import payload must be rejected (extra='forbid')."""
    client = TestClient(create_app())

    try:
        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "ExtraField",
                        "stage_counts": _all_stages_zero(),
                        "history": [],
                        "unexpected_field": 42,
                    }
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400
    assert response.json() == ERR_INVALID_IMPORT_FORMAT


def test_post_import_atomicity_valid_type_rolled_back_when_later_type_fails(
    database_url: str,
) -> None:
    """If the first type in the payload would succeed but a later type causes
    a DB-level error, the entire import is rolled back — including changes
    to the first type."""
    client = TestClient(create_app())
    engine = create_engine(database_url)

    try:
        created = client.post("/api/v1/types", json={"name": "Survivor"})
        assert created.status_code == 201

        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE stage_counts SET count = 5 WHERE type_id = 1 AND stage_name = 'IN_BOX'"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO history_logs (type_id, from_stage, to_stage, qty, created_at) "
                    "VALUES (1, 'IN_BOX', 'BUILDING', 1, '2026-02-25 07:00:00')"
                )
            )

        response = client.post(
            "/api/v1/import",
            json={
                "types": [
                    {
                        "name": "Survivor",
                        "stage_counts": _all_stages_zero({"IN_BOX": 3}),
                        "history": [
                            {
                                "from_stage": "IN_BOX",
                                "to_stage": "DONE",
                                "qty": 1,
                                "created_at": "2026-02-25T09:00:00Z",
                            }
                        ],
                    },
                    {
                        "name": "Crasher",
                        "stage_counts": _all_stages_zero({"IN_BOX": 1}),
                        "history": [
                            {
                                "from_stage": "IN_BOX",
                                "to_stage": "BUILDING",
                                "qty": -5,
                                "created_at": "2026-02-25T09:00:00Z",
                            }
                        ],
                    },
                ]
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 400

    with engine.begin() as conn:
        in_box = conn.execute(
            text("SELECT count FROM stage_counts WHERE type_id = 1 AND stage_name = 'IN_BOX'")
        ).scalar_one()
        crasher_exists = conn.execute(
            text("SELECT COUNT(*) FROM miniature_types WHERE name = 'Crasher'")
        ).scalar_one()
        history_count = conn.execute(
            text("SELECT COUNT(*) FROM history_logs WHERE type_id = 1")
        ).scalar_one()

    assert in_box == 5, "Survivor counts must remain unchanged"
    assert crasher_exists == 0, "Crasher type must not be created"
    assert history_count == 1, "Only the pre-existing history row should remain"
