import { API_BASE_URL } from './config'

export interface Landmark {
  id: string
  label: string
  x_meters: number
  y_meters: number
}

export interface CalibrationPoint {
  pixel_x: number
  pixel_y: number
  landmark_id: string
}

export interface CalibrationSummary {
  video_id: string
  point_count: number
  mean_reprojection_error_m: number
  max_reprojection_error_m: number
}

export interface ProjectedTrackPoint {
  track_id: number
  timestamp: number
  court_x: number
  court_y: number
}

export class CourtApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new CourtApiError(body?.detail ?? `HTTP ${response.status}`, response.status)
  }
  return response.json()
}

export async function getLandmarks(): Promise<Landmark[]> {
  return handle(await fetch(`${API_BASE_URL}/court/landmarks`))
}

export async function setCalibration(
  videoId: string,
  points: CalibrationPoint[],
): Promise<CalibrationSummary> {
  return handle(
    await fetch(`${API_BASE_URL}/videos/${videoId}/court/calibration`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ points }),
    }),
  )
}

export async function getProjectedTracks(videoId: string): Promise<ProjectedTrackPoint[]> {
  return handle(await fetch(`${API_BASE_URL}/videos/${videoId}/court/tracks`))
}
