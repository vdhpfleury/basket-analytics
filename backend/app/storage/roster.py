"""Effectif (équipes/joueurs) : stockage temporaire en mémoire.

Comme les registres de `app/api/videos.py` et `app/api/tracking.py`, ceci
sera remplacé par la vraie persistance SQLite en M12. Conforme au modèle
logique de `docs/data_model.md` (`Team`, `Player`), simplifié pour le MVP :
pas de notion de match liant deux équipes, l'effectif est global au club.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Player:
    id: str
    team_id: str
    full_name: str
    jersey_number: int | None = None


@dataclass
class Team:
    id: str
    name: str
    players: list[Player] = field(default_factory=list)


_teams: dict[str, Team] = {}


def create_team(name: str) -> Team:
    team = Team(id=uuid.uuid4().hex, name=name)
    _teams[team.id] = team
    return team


def get_team(team_id: str) -> Team | None:
    return _teams.get(team_id)


def list_teams() -> list[Team]:
    return list(_teams.values())


def add_player(team_id: str, full_name: str, jersey_number: int | None) -> Player | None:
    team = _teams.get(team_id)
    if team is None:
        return None
    player = Player(id=uuid.uuid4().hex, team_id=team_id, full_name=full_name, jersey_number=jersey_number)
    team.players.append(player)
    return player


def get_player(player_id: str) -> Player | None:
    for team in _teams.values():
        for player in team.players:
            if player.id == player_id:
                return player
    return None


def list_all_players() -> list[Player]:
    return [player for team in _teams.values() for player in team.players]
