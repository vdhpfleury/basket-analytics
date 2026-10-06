import { useEffect, useState } from 'react'
import { CourtApiError, getProjectedTracks, type ProjectedTrackPoint } from '../api/court'

const PX_PER_M = 15
const MARGIN = 10
const COURT_LENGTH_M = 28
const COURT_WIDTH_M = 15
const CENTER_CIRCLE_RADIUS_M = 1.8

const TRACK_COLORS = ['#ef4444', '#22c55e', '#3b82f6', '#eab308', '#a855f7', '#ec4899', '#14b8a6', '#f97316']

function colorForTrack(trackId: number): string {
  return TRACK_COLORS[trackId % TRACK_COLORS.length]
}

function toSvg(xMeters: number, yMeters: number): [number, number] {
  return [MARGIN + xMeters * PX_PER_M, MARGIN + (COURT_WIDTH_M - yMeters) * PX_PER_M]
}

interface Props {
  videoId: string
  refreshKey: number
}

type Status = 'loading' | 'done' | 'no-tracking' | 'error'

export function CourtDiagram({ videoId, refreshKey }: Props) {
  const [points, setPoints] = useState<ProjectedTrackPoint[]>([])
  const [status, setStatus] = useState<Status>('loading')

  useEffect(() => {
    setStatus('loading')
    getProjectedTracks(videoId)
      .then((result) => {
        setPoints(result)
        setStatus('done')
      })
      .catch((err) => {
        setStatus(err instanceof CourtApiError && err.status === 409 ? 'no-tracking' : 'error')
      })
  }, [videoId, refreshKey])

  if (status === 'loading') return <p>Chargement de la projection…</p>
  if (status === 'no-tracking') {
    return (
      <p>
        Lance le tracking (section « Trajectoires des joueurs » ci-dessus) pour voir les joueurs
        projetés sur le terrain.
      </p>
    )
  }
  if (status === 'error') return <p role="alert">❌ Impossible de charger la projection</p>

  const width = MARGIN * 2 + COURT_LENGTH_M * PX_PER_M
  const height = MARGIN * 2 + COURT_WIDTH_M * PX_PER_M
  const [x0, y0] = toSvg(0, 0)
  const [x1, y1] = toSvg(COURT_LENGTH_M, COURT_WIDTH_M)
  const [centerX, centerY] = toSvg(COURT_LENGTH_M / 2, COURT_WIDTH_M / 2)
  const [halfTopX, halfTopY] = toSvg(COURT_LENGTH_M / 2, COURT_WIDTH_M)
  const [halfBottomX, halfBottomY] = toSvg(COURT_LENGTH_M / 2, 0)

  return (
    <div>
      <h3>Projection terrain (2D)</h3>
      <svg
        width={width}
        height={height}
        data-testid="court-diagram"
        style={{ background: '#2f6b3a' }}
      >
        <rect
          x={Math.min(x0, x1)}
          y={Math.min(y0, y1)}
          width={Math.abs(x1 - x0)}
          height={Math.abs(y1 - y0)}
          fill="none"
          stroke="white"
          strokeWidth={2}
        />
        <line x1={halfTopX} y1={halfTopY} x2={halfBottomX} y2={halfBottomY} stroke="white" strokeWidth={2} />
        <circle
          cx={centerX}
          cy={centerY}
          r={CENTER_CIRCLE_RADIUS_M * PX_PER_M}
          fill="none"
          stroke="white"
          strokeWidth={2}
        />
        {points.map((point, index) => {
          const [px, py] = toSvg(point.court_x, point.court_y)
          return (
            <circle
              key={index}
              data-testid="projected-point"
              cx={px}
              cy={py}
              r={4}
              fill={colorForTrack(point.track_id)}
            />
          )
        })}
      </svg>
      <p>{points.length} point(s) projeté(s)</p>
    </div>
  )
}
