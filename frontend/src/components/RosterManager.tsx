import { useEffect, useState } from 'react'
import { addPlayer, createTeam, listTeams, type Team } from '../api/roster'

interface Props {
  onTeamsChange: (teams: Team[]) => void
}

export function RosterManager({ onTeamsChange }: Props) {
  const [teams, setTeams] = useState<Team[]>([])
  const [newTeamName, setNewTeamName] = useState('')
  const [selectedTeamId, setSelectedTeamId] = useState('')
  const [playerName, setPlayerName] = useState('')
  const [jerseyNumber, setJerseyNumber] = useState('')

  async function refresh() {
    const result = await listTeams()
    setTeams(result)
    onTeamsChange(result)
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleCreateTeam(event: React.FormEvent) {
    event.preventDefault()
    if (!newTeamName.trim()) return

    const team = await createTeam(newTeamName.trim())
    setNewTeamName('')
    setSelectedTeamId(team.id)
    await refresh()
  }

  async function handleAddPlayer(event: React.FormEvent) {
    event.preventDefault()
    if (!selectedTeamId || !playerName.trim()) return

    await addPlayer(selectedTeamId, playerName.trim(), jerseyNumber ? Number(jerseyNumber) : null)
    setPlayerName('')
    setJerseyNumber('')
    await refresh()
  }

  return (
    <section>
      <h2>Effectif</h2>

      <form onSubmit={handleCreateTeam}>
        <input
          placeholder="Nom de l'équipe"
          value={newTeamName}
          onChange={(event) => setNewTeamName(event.target.value)}
        />
        <button type="submit">Créer l'équipe</button>
      </form>

      {teams.length > 0 && (
        <form onSubmit={handleAddPlayer}>
          <select
            value={selectedTeamId}
            onChange={(event) => setSelectedTeamId(event.target.value)}
          >
            <option value="">-- choisir une équipe --</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
          <input
            placeholder="Nom du joueur"
            value={playerName}
            onChange={(event) => setPlayerName(event.target.value)}
          />
          <input
            placeholder="N° maillot"
            type="number"
            value={jerseyNumber}
            onChange={(event) => setJerseyNumber(event.target.value)}
          />
          <button type="submit" disabled={!selectedTeamId}>
            Ajouter le joueur
          </button>
        </form>
      )}

      <ul>
        {teams.map((team) => (
          <li key={team.id}>
            <strong>{team.name}</strong>
            <ul>
              {team.players.map((player) => (
                <li key={player.id}>
                  {player.full_name}
                  {player.jersey_number != null ? ` (#${player.jersey_number})` : ''}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </section>
  )
}
