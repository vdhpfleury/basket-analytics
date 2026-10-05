from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_team() -> None:
    response = client.post("/teams", json={"name": "Équipe Test"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Équipe Test"
    assert body["players"] == []


def test_add_player_to_team() -> None:
    team = client.post("/teams", json={"name": "Équipe Test 2"}).json()

    response = client.post(
        f"/teams/{team['id']}/players", json={"full_name": "Alice Dupont", "jersey_number": 7}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Alice Dupont"
    assert body["jersey_number"] == 7
    assert body["team_id"] == team["id"]


def test_add_player_to_unknown_team_returns_404() -> None:
    response = client.post("/teams/does-not-exist/players", json={"full_name": "Bob"})

    assert response.status_code == 404


def test_list_teams_includes_created_team() -> None:
    team = client.post("/teams", json={"name": "Équipe Test 3"}).json()

    response = client.get("/teams")

    assert response.status_code == 200
    assert any(t["id"] == team["id"] for t in response.json())
