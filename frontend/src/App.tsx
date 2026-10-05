import { useEffect, useState } from 'react'
import { API_BASE_URL } from './api/config'
import type { Team } from './api/roster'
import { RosterManager } from './components/RosterManager'
import { VideoImport } from './components/VideoImport'

type BackendStatus = 'loading' | 'ok' | 'error'

function App() {
  const [status, setStatus] = useState<BackendStatus>('loading')
  const [teams, setTeams] = useState<Team[]>([])

  useEffect(() => {
    fetch(`${API_BASE_URL}/health`)
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json()
      })
      .then((data) => setStatus(data.status === 'ok' ? 'ok' : 'error'))
      .catch(() => setStatus('error'))
  }, [])

  return (
    <main>
      <h1>basket-analytics</h1>
      <p>
        Backend :{' '}
        {status === 'loading' && 'vérification…'}
        {status === 'ok' && '✅ connecté'}
        {status === 'error' && '❌ injoignable'}
      </p>

      {status === 'ok' && (
        <>
          <RosterManager onTeamsChange={setTeams} />
          <VideoImport teams={teams} />
        </>
      )}
    </main>
  )
}

export default App
