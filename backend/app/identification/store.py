"""Associations track -> joueur (M5.4) : stockage temporaire en mémoire,
remplacé par la vraie persistance en M12. Conforme à
`PlayerIdentification` dans `docs/data_model.md`.

Un track sans entrée ici est explicitement "non identifié" : on ne lui
assigne jamais de joueur par défaut (voir tests M5.5).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerIdentification:
    video_id: str
    track_id: int
    player_id: str
    method: str
    manually_verified: bool
    verified_by: str | None = None


_identifications: dict[tuple[str, int], PlayerIdentification] = {}


def set_identification(
    video_id: str,
    track_id: int,
    player_id: str,
    method: str = "manual",
    manually_verified: bool = True,
    verified_by: str | None = None,
) -> PlayerIdentification:
    record = PlayerIdentification(
        video_id=video_id,
        track_id=track_id,
        player_id=player_id,
        method=method,
        manually_verified=manually_verified,
        verified_by=verified_by,
    )
    _identifications[(video_id, track_id)] = record
    return record


def get_identification(video_id: str, track_id: int) -> PlayerIdentification | None:
    return _identifications.get((video_id, track_id))


def remove_identification(video_id: str, track_id: int) -> bool:
    return _identifications.pop((video_id, track_id), None) is not None


def list_identifications(video_id: str) -> list[PlayerIdentification]:
    return [record for (vid, _), record in _identifications.items() if vid == video_id]
