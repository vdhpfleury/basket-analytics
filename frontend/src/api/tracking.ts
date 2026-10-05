import { API_BASE_URL } from './config'
import type { BoundingBox } from './detections'

export interface TrackPoint {
  track_id: number
  timestamp: number
  bbox: BoundingBox
  confidence: number
  x_pixel: number
  y_pixel: number
}

export async function trackPlayers(
  videoId: string,
  confidenceThreshold: number,
  sampleEveryNFrames: number,
): Promise<TrackPoint[]> {
  const url = new URL(`${API_BASE_URL}/videos/${videoId}/tracks`)
  url.searchParams.set('confidence', confidenceThreshold.toString())
  url.searchParams.set('sample_every_n_frames', sampleEveryNFrames.toString())

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Échec du tracking (HTTP ${response.status})`)
  }
  return response.json()
}
