import { useEffect, useState } from 'react'
import { frameUrl } from '../api/detections'
import {
  getLandmarks,
  setCalibration,
  type CalibrationPoint,
  type CalibrationSummary,
  type Landmark,
} from '../api/court'
import type { VideoMetadata } from '../api/videos'
import { CourtDiagram } from './CourtDiagram'

const DISPLAY_WIDTH = 480

interface Props {
  metadata: VideoMetadata
}

export function CalibrationViewer({ metadata }: Props) {
  const [landmarks, setLandmarks] = useState<Landmark[]>([])
  const [points, setPoints] = useState<CalibrationPoint[]>([])
  const [summary, setSummary] = useState<CalibrationSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    getLandmarks()
      .then(setLandmarks)
      .catch(() => setError('Impossible de charger les repères du terrain'))
  }, [])

  const displayHeight = Math.round((DISPLAY_WIDTH * metadata.height) / metadata.width)
  const scale = metadata.width / DISPLAY_WIDTH

  function handleImageClick(event: React.MouseEvent<HTMLImageElement>) {
    const rect = event.currentTarget.getBoundingClientRect()
    const pixel_x = (event.clientX - rect.left) * scale
    const pixel_y = (event.clientY - rect.top) * scale
    const landmark_id = landmarks[0]?.id ?? ''
    setPoints((prev) => [...prev, { pixel_x, pixel_y, landmark_id }])
  }

  function updateLandmark(index: number, landmarkId: string) {
    setPoints((prev) => prev.map((p, i) => (i === index ? { ...p, landmark_id: landmarkId } : p)))
  }

  function removePoint(index: number) {
    setPoints((prev) => prev.filter((_, i) => i !== index))
  }

  async function handleCalibrate() {
    setError(null)
    try {
      const result = await setCalibration(metadata.id, points)
      setSummary(result)
      setRefreshKey((key) => key + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec de la calibration')
      setSummary(null)
    }
  }

  return (
    <section>
      <h2>Calibration du terrain</h2>
      <p>
        Clique sur l'image à l'endroit d'un repère connu du terrain (un coin, le centre…), puis
        indique de quel repère il s'agit dans la liste. Au moins 4 points sont nécessaires.
      </p>

      <div style={{ position: 'relative', width: DISPLAY_WIDTH, display: 'inline-block' }}>
        <img
          src={frameUrl(metadata, 0)}
          width={DISPLAY_WIDTH}
          height={displayHeight}
          alt="Frame de calibration"
          onClick={handleImageClick}
          style={{ cursor: 'crosshair', display: 'block' }}
        />
        {points.map((point, index) => (
          <div
            key={index}
            data-testid="calibration-marker"
            style={{
              position: 'absolute',
              left: point.pixel_x / scale - 4,
              top: point.pixel_y / scale - 4,
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'red',
              border: '1px solid white',
              pointerEvents: 'none',
            }}
          />
        ))}
      </div>

      <ul>
        {points.map((point, index) => (
          <li key={index} data-testid="calibration-point-row">
            ({point.pixel_x.toFixed(0)}, {point.pixel_y.toFixed(0)}) ={' '}
            <select
              data-testid="calibration-landmark-select"
              value={point.landmark_id}
              onChange={(event) => updateLandmark(index, event.target.value)}
            >
              {landmarks.map((landmark) => (
                <option key={landmark.id} value={landmark.id}>
                  {landmark.label}
                </option>
              ))}
            </select>
            <button type="button" onClick={() => removePoint(index)}>
              Supprimer
            </button>
          </li>
        ))}
      </ul>

      <button type="button" onClick={handleCalibrate} disabled={points.length < 4}>
        Calculer la calibration ({points.length} point{points.length > 1 ? 's' : ''})
      </button>

      {error && <p role="alert">❌ {error}</p>}

      {summary && (
        <p data-testid="calibration-summary">
          Calibration effectuée avec {summary.point_count} points. Erreur de reprojection
          moyenne : {summary.mean_reprojection_error_m.toFixed(2)} m (max{' '}
          {summary.max_reprojection_error_m.toFixed(2)} m).
        </p>
      )}

      {summary && <CourtDiagram videoId={metadata.id} refreshKey={refreshKey} />}
    </section>
  )
}
