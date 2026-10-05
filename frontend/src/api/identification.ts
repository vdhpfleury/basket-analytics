import { API_BASE_URL } from './config'

export interface TrackSummary {
  track_id: number
  point_count: number
  first_timestamp: number
  last_timestamp: number
  dominant_color: string
  suggested_group: number
  player_id: string | null
  player_name: string | null
  manually_verified: boolean
}

export async function getTracksSummary(videoId: string, minPoints = 3): Promise<TrackSummary[]> {
  const url = new URL(`${API_BASE_URL}/videos/${videoId}/tracks/summary`)
  url.searchParams.set('min_points', minPoints.toString())

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Échec de récupération du résumé (HTTP ${response.status})`)
  }
  return response.json()
}

export function thumbnailUrl(videoId: string, trackId: number): string {
  return `${API_BASE_URL}/videos/${videoId}/tracks/${trackId}/thumbnail`
}

export async function identifyTrack(
  videoId: string,
  trackId: number,
  playerId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/videos/${videoId}/tracks/${trackId}/identification`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId }),
    },
  )
  if (!response.ok) throw new Error(`Échec de l'identification (HTTP ${response.status})`)
}

export async function removeIdentification(videoId: string, trackId: number): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/videos/${videoId}/tracks/${trackId}/identification`,
    { method: 'DELETE' },
  )
  if (!response.ok) throw new Error(`Échec de la suppression (HTTP ${response.status})`)
}
