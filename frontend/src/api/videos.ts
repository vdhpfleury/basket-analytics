import { API_BASE_URL } from './config'

export interface VideoMetadata {
  id: string
  filename: string
  duration_seconds: number
  fps: number
  width: number
  height: number
  frame_count: number
}

export class VideoUploadError extends Error {}

export async function uploadVideo(file: File): Promise<VideoMetadata> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/videos`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new VideoUploadError(body?.detail ?? `Échec de l'upload (HTTP ${response.status})`)
  }

  return response.json()
}

export function videoFileUrl(metadata: VideoMetadata): string {
  // `filename` est déjà `{id}.{ext}` côté backend (voir app/api/videos.py).
  return `${API_BASE_URL}/media/${metadata.filename}`
}
