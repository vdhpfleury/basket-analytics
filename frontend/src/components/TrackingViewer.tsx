import { useState } from 'react'
import { frameUrl } from '../api/detections'
import { trackPlayers, type TrackPoint } from '../api/tracking'
import type { VideoMetadata } from '../api/videos'

const DISPLAY_WIDTH = 480
const TRACK_COLORS = ['#ef4444', '#22c55e', '#3b82f6', '#eab308', '#a855f7', '#ec4899', '#14b8a6', '#f97316']

function colorForTrack(trackId: number): string {
  return TRACK_COLORS[trackId % TRACK_COLORS.length]
}

interface Props {
  metadata: VideoMetadata
}

export function TrackingViewer({ metadata }: Props) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [trackPoints, setTrackPoints] = useState<TrackPoint[]>([])

  async function handleTrack() {
    setStatus('loading')
    try {
      const results = await trackPlayers(metadata.id, 0.5, 2)
      setTrackPoints(results)
      setStatus('done')
    } catch {
      setStatus('error')
    }
  }

  const displayHeight = Math.round((DISPLAY_WIDTH * metadata.height) / metadata.width)
  const scale = DISPLAY_WIDTH / metadata.width

  const byTrack = new Map<number, TrackPoint[]>()
  for (const point of trackPoints) {
    const existing = byTrack.get(point.track_id)
    if (existing) existing.push(point)
    else byTrack.set(point.track_id, [point])
  }

  return (
    <section>
      <h2>Trajectoires des joueurs (vidéo entière)</h2>
      <p>Traite toute la vidéo (une frame sur deux) : peut prendre quelques secondes.</p>

      <button type="button" onClick={handleTrack} disabled={status === 'loading'}>
        {status === 'loading' ? 'Suivi en cours…' : 'Suivre les joueurs sur toute la vidéo'}
      </button>

      {status === 'error' && <p role="alert">❌ Échec du tracking</p>}

      {status === 'done' && (
        <>
          <div style={{ position: 'relative', width: DISPLAY_WIDTH, height: displayHeight }}>
            <img
              src={frameUrl(metadata, 0)}
              width={DISPLAY_WIDTH}
              height={displayHeight}
              alt="Première frame de la vidéo"
            />
            <svg
              width={DISPLAY_WIDTH}
              height={displayHeight}
              style={{ position: 'absolute', top: 0, left: 0 }}
            >
              {[...byTrack.entries()].map(([trackId, points]) => (
                <polyline
                  key={trackId}
                  data-testid="track-polyline"
                  points={points.map((p) => `${p.x_pixel * scale},${p.y_pixel * scale}`).join(' ')}
                  fill="none"
                  stroke={colorForTrack(trackId)}
                  strokeWidth={2}
                />
              ))}
            </svg>
          </div>
          <p>
            {byTrack.size} trajectoire(s) distincte(s), {trackPoints.length} points au total
          </p>
        </>
      )}
    </section>
  )
}
