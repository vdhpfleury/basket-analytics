from app.storage import roster


def test_create_team_and_add_player() -> None:
    team = roster.create_team("Équipe Test")
    player = roster.add_player(team.id, "Alice Dupont", 7)

    assert player is not None
    assert player.team_id == team.id
    assert roster.get_player(player.id) == player
    assert team.players == [player]


def test_add_player_to_unknown_team_returns_none() -> None:
    assert roster.add_player("does-not-exist", "Bob", None) is None


def test_get_player_unknown_returns_none() -> None:
    assert roster.get_player("does-not-exist") is None


def test_list_all_players_spans_teams() -> None:
    team_a = roster.create_team("A")
    team_b = roster.create_team("B")
    player_a = roster.add_player(team_a.id, "Joueur A", None)
    player_b = roster.add_player(team_b.id, "Joueur B", None)

    all_players = roster.list_all_players()

    assert player_a in all_players
    assert player_b in all_players
