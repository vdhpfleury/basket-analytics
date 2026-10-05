import { useRef, useState } from 'react'
import { uploadVideo, videoFileUrl, VideoUploadError, type VideoMetadata } from '../api/videos'

type UploadState = 'idle' | 'uploading' | 'done' | 'error'

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remaining = Math.round(seconds % 60)
  return `${minutes}:${remaining.toString().padStart(2, '0')}`
}

export function VideoImport() {
  const [state, setState] = useState<UploadState>('idle')
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    setState('uploading')
    setError(null)
    setMetadata(null)

    try {
      const result = await uploadVideo(file)
      setMetadata(result)
      setState('done')
    } catch (err) {
      setError(err instanceof VideoUploadError ? err.message : "Erreur inattendue à l'upload")
      setState('error')
    }
  }

  return (
    <section>
      <h2>Importer une vidéo de match</h2>
      <input
        ref={inputRef}
        type="file"
        accept="video/mp4"
        onChange={handleFileChange}
        disabled={state === 'uploading'}
      />

      {state === 'uploading' && <p>Import en cours…</p>}
      {state === 'error' && <p role="alert">❌ {error}</p>}

      {metadata && (
        <>
          <dl>
            <dt>Durée</dt>
            <dd>{formatDuration(metadata.duration_seconds)}</dd>
            <dt>FPS</dt>
            <dd>{metadata.fps.toFixed(1)}</dd>
            <dt>Résolution</dt>
            <dd>
              {metadata.width}×{metadata.height}
            </dd>
          </dl>
          <video controls width={480} src={videoFileUrl(metadata)}>
            Votre navigateur ne supporte pas la lecture vidéo HTML5.
          </video>
        </>
      )}
    </section>
  )
}
