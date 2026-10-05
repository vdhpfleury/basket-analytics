import { useState } from 'react'
import {
  getTracksSummary,
  identifyTrack,
  removeIdentification,
  thumbnailUrl,
  type TrackSummary,
} from '../api/identification'
import type { Team } from '../api/roster'
import type { VideoMetadata } from '../api/videos'

interface Props {
  metadata: VideoMetadata
  teams: Team[]
}

export function IdentificationViewer({ metadata, teams }: Props) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [summaries, setSummaries] = useState<TrackSummary[]>([])

  const allPlayers = teams.flatMap((team) => team.players)

  async function handleLoad() {
    setStatus('loading')
    try {
      const result = await getTracksSummary(metadata.id)
      setSummaries(result)
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  async function handleAssign(trackId: number, playerId: string) {
    if (playerId === '') {
      await removeIdentification(metadata.id, trackId)
    } else {
      await identifyTrack(metadata.id, trackId, playerId)
    }
    await handleLoad()
  }

  return (
    <section>
      <h2>Identification des joueurs</h2>
      <p>Nécessite que le tracking ait déjà été calculé ci-dessus.</p>

      <button type="button" onClick={handleLoad} disabled={status === 'loading'}>
        {status === 'loading' ? 'Chargement…' : 'Charger les tracks à identifier'}
      </button>

      {status === 'error' && (
        <p role="alert">❌ Impossible de charger les tracks (lancer le tracking d'abord)</p>
      )}

      {status === 'done' && (
        <table>
          <thead>
            <tr>
              <th>Vignette</th>
              <th>Track</th>
              <th>Couleur</th>
              <th>Groupe suggéré</th>
              <th>Joueur</th>
            </tr>
          </thead>
          <tbody>
            {summaries.map((summary) => (
              <tr key={summary.track_id} data-testid="track-row">
                <td>
                  <img
                    src={thumbnailUrl(metadata.id, summary.track_id)}
                    alt={`Track ${summary.track_id}`}
                    width={60}
                  />
                </td>
                <td>#{summary.track_id}</td>
                <td>
                  <span
                    data-testid="color-swatch"
                    style={{
                      display: 'inline-block',
                      width: 16,
                      height: 16,
                      background: summary.dominant_color,
                      border: '1px solid #999',
                    }}
                  />
                </td>
                <td>{summary.suggested_group}</td>
                <td>
                  <select
                    data-testid="player-select"
                    value={summary.player_id ?? ''}
                    onChange={(event) => handleAssign(summary.track_id, event.target.value)}
                  >
                    <option value="">Non identifié</option>
                    {allPlayers.map((player) => (
                      <option key={player.id} value={player.id}>
                        {player.full_name}
                        {player.jersey_number != null ? ` (#${player.jersey_number})` : ''}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
