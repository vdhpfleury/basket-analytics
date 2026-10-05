import { useState, type RefObject } from 'react'
import { detectPlayers, frameUrl, type Detection } from '../api/detections'
import type { VideoMetadata } from '../api/videos'

const DISPLAY_WIDTH = 480

interface Props {
  metadata: VideoMetadata
  videoRef: RefObject<HTMLVideoElement | null>
}

export function DetectionViewer({ metadata, videoRef }: Props) {
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.5)
  const [timestamp, setTimestamp] = useState<number | null>(null)
  const [detections, setDetections] = useState<Detection[]>([])
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle')

  async function handleDetect() {
    const video = videoRef.current
    if (!video) return
    const t = video.currentTime

    setStatus('loading')
    try {
      const results = await detectPlayers(metadata.id, t, confidenceThreshold)
      setTimestamp(t)
      setDetections(results)
      setStatus('idle')
    } catch {
      setStatus('error')
    }
  }

  const displayHeight = Math.round((DISPLAY_WIDTH * metadata.height) / metadata.width)
  const scale = DISPLAY_WIDTH / metadata.width

  return (
    <section>
      <h2>Détection des joueurs (frame courante)</h2>

      <label>
        Seuil de confiance : {confidenceThreshold.toFixed(2)}
        <input
          type="range"
          min={0.1}
          max={0.9}
          step={0.05}
          value={confidenceThreshold}
          onChange={(event) => setConfidenceThreshold(Number(event.target.value))}
        />
      </label>

      <button type="button" onClick={handleDetect} disabled={status === 'loading'}>
        {status === 'loading' ? 'Détection en cours…' : 'Détecter sur la frame courante'}
      </button>

      {status === 'error' && <p role="alert">❌ Échec de la détection</p>}

      {timestamp !== null && (
        <>
          <div style={{ position: 'relative', width: DISPLAY_WIDTH, height: displayHeight }}>
            <img
              src={frameUrl(metadata, timestamp)}
              width={DISPLAY_WIDTH}
              height={displayHeight}
              alt={`Frame à ${timestamp.toFixed(2)}s`}
            />
            {detections.map((detection, index) => (
              <div
                key={index}
                data-testid="detection-box"
                style={{
                  position: 'absolute',
                  left: detection.bbox.x1 * scale,
                  top: detection.bbox.y1 * scale,
                  width: (detection.bbox.x2 - detection.bbox.x1) * scale,
                  height: (detection.bbox.y2 - detection.bbox.y1) * scale,
                  border: '2px solid #22c55e',
                  boxSizing: 'border-box',
                }}
              >
                <span style={{ background: '#22c55e', color: '#000', fontSize: 10, padding: '0 2px' }}>
                  {(detection.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
          <p>
            {detections.length} joueur(s) détecté(s) à t={timestamp.toFixed(2)}s
          </p>
        </>
      )}
    </section>
  )
}
