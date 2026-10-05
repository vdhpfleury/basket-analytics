import { API_BASE_URL } from './config'
import type { VideoMetadata } from './videos'

export interface BoundingBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface Detection {
  bbox: BoundingBox
  confidence: number
  label: string
}

export async function detectPlayers(
  videoId: string,
  timestamp: number,
  confidenceThreshold: number,
): Promise<Detection[]> {
  const url = new URL(`${API_BASE_URL}/videos/${videoId}/detections`)
  url.searchParams.set('t', timestamp.toString())
  url.searchParams.set('confidence', confidenceThreshold.toString())

  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Échec de la détection (HTTP ${response.status})`)
  }
  return response.json()
}

export function frameUrl(metadata: VideoMetadata, timestamp: number): string {
  return `${API_BASE_URL}/videos/${metadata.id}/frame?t=${timestamp}`
}
