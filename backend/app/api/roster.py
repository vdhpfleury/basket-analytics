from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.storage import roster

router = APIRouter(prefix="/teams", tags=["roster"])


class CreateTeamRequest(BaseModel):
    name: str


class CreatePlayerRequest(BaseModel):
    full_name: str
    jersey_number: int | None = None


class PlayerResponse(BaseModel):
    id: str
    team_id: str
    full_name: str
    jersey_number: int | None


class TeamResponse(BaseModel):
    id: str
    name: str
    players: list[PlayerResponse]


def _to_response(team: roster.Team) -> TeamResponse:
    return TeamResponse(
        id=team.id,
        name=team.name,
        players=[
            PlayerResponse(
                id=p.id, team_id=p.team_id, full_name=p.full_name, jersey_number=p.jersey_number
            )
            for p in team.players
        ],
    )


@router.post("", response_model=TeamResponse, status_code=201)
def create_team(body: CreateTeamRequest) -> TeamResponse:
    team = roster.create_team(body.name)
    return _to_response(team)


@router.get("", response_model=list[TeamResponse])
def list_teams() -> list[TeamResponse]:
    return [_to_response(t) for t in roster.list_teams()]


@router.post("/{team_id}/players", response_model=PlayerResponse, status_code=201)
def add_player(team_id: str, body: CreatePlayerRequest) -> PlayerResponse:
    player = roster.add_player(team_id, body.full_name, body.jersey_number)
    if player is None:
        raise HTTPException(status_code=404, detail="Équipe introuvable")
    return PlayerResponse(
        id=player.id,
        team_id=player.team_id,
        full_name=player.full_name,
        jersey_number=player.jersey_number,
    )
