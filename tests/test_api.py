"""Endpoint tests driven through FastAPI's TestClient.

Each test gets a fresh in-memory store via dependency override, so there
is no shared state between tests.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from item_bench.api import app, get_store
from item_bench.store import InMemoryItemStore


@pytest.fixture
def client() -> Iterator[TestClient]:
    store = InMemoryItemStore()
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def _generate(client: TestClient, **body: object) -> list[dict]:
    payload = {"item_type": "multiple_choice", "skill_tag": "arithmetic", **body}
    response = client.post("/generate", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_generate_creates_and_persists(client: TestClient) -> None:
    items = _generate(client, count=2)

    assert len(items) == 2
    assert all(i["type"] == "multiple_choice" for i in items)
    assert all(i["prompt_version"] == "stub-v1" for i in items)
    assert len(client.get("/items").json()) == 2


def test_generate_short_answer_defaults_to_one(client: TestClient) -> None:
    items = _generate(client, item_type="short_answer")

    assert len(items) == 1
    assert items[0]["type"] == "short_answer"


def test_generate_rejects_unknown_item_type(client: TestClient) -> None:
    assert (
        client.post(
            "/generate", json={"item_type": "essay", "skill_tag": "arithmetic"}
        ).status_code
        == 422
    )


def test_generate_rejects_count_out_of_range(client: TestClient) -> None:
    assert (
        client.post(
            "/generate",
            json={
                "item_type": "multiple_choice",
                "skill_tag": "arithmetic",
                "count": 99,
            },
        ).status_code
        == 422
    )


def test_list_filters(client: TestClient) -> None:
    _generate(client, item_type="multiple_choice", skill_tag="arithmetic")
    _generate(client, item_type="short_answer", skill_tag="algebra")

    assert len(client.get("/items", params={"item_type": "short_answer"}).json()) == 1
    assert len(client.get("/items", params={"skill_tag": "arithmetic"}).json()) == 1


def test_list_pagination(client: TestClient) -> None:
    _generate(client, count=5)

    assert len(client.get("/items", params={"limit": 2}).json()) == 2
    assert len(client.get("/items", params={"offset": 4}).json()) == 1


def test_get_item_ok_and_missing(client: TestClient) -> None:
    created = _generate(client)[0]

    assert client.get(f"/items/{created['id']}").json()["id"] == created["id"]
    assert client.get("/items/does-not-exist").status_code == 404


def test_patch_updates_and_persists(client: TestClient) -> None:
    created = _generate(client)[0]

    patched = client.patch(f"/items/{created['id']}", json={"stem": "A brand new stem"})

    assert patched.status_code == 200
    assert patched.json()["stem"] == "A brand new stem"
    assert patched.json()["updated_at"] >= created["updated_at"]
    assert client.get(f"/items/{created['id']}").json()["stem"] == "A brand new stem"


def test_patch_rejects_protected_field(client: TestClient) -> None:
    created = _generate(client)[0]

    response = client.patch(f"/items/{created['id']}", json={"type": "short_answer"})

    assert response.status_code == 422


def test_patch_revalidates_shape(client: TestClient) -> None:
    created = _generate(client)[0]

    response = client.patch(f"/items/{created['id']}", json={"options": ["only one"]})

    assert response.status_code == 422


def test_patch_missing_item(client: TestClient) -> None:
    assert client.patch("/items/nope", json={"stem": "x"}).status_code == 404


def test_evaluate_returns_and_persists_report(client: TestClient) -> None:
    created = _generate(client)[0]

    report = client.post(f"/items/{created['id']}/evaluate")

    assert report.status_code == 200
    body = report.json()
    assert body["item_id"] == created["id"]
    assert body["passed"] is True
    assert body["score"] == 1.0
    assert len(body["results"]) == 5


def test_evaluate_missing_item(client: TestClient) -> None:
    assert client.post("/items/nope/evaluate").status_code == 404


def test_pass_rate_starts_empty(client: TestClient) -> None:
    assert client.get("/stats/pass-rate").json() == []


def test_pass_rate_aggregates_by_prompt_version(client: TestClient) -> None:
    ids = [item["id"] for item in _generate(client, count=2)]
    for item_id in ids:
        client.post(f"/items/{item_id}/evaluate")

    # Break one item's skill tag, then evaluate it again: 3 evaluations, 2 passing.
    client.patch(f"/items/{ids[0]}", json={"skill_tag": "not-a-real-tag"})
    client.post(f"/items/{ids[0]}/evaluate")

    rows = client.get("/stats/pass-rate").json()

    assert len(rows) == 1
    assert rows[0]["prompt_version"] == "stub-v1"
    assert rows[0]["evaluations"] == 3
    assert rows[0]["passed"] == 2
    assert rows[0]["pass_rate"] == 2 / 3
