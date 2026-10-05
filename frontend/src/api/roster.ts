import { API_BASE_URL } from './config'

export interface Player {
  id: string
  team_id: string
  full_name: string
  jersey_number: number | null
}

export interface Team {
  id: string
  name: string
  players: Player[]
}

export async function createTeam(name: string): Promise<Team> {
  const response = await fetch(`${API_BASE_URL}/teams`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!response.ok) throw new Error(`Échec de création d'équipe (HTTP ${response.status})`)
  return response.json()
}

export async function listTeams(): Promise<Team[]> {
  const response = await fetch(`${API_BASE_URL}/teams`)
  if (!response.ok) throw new Error(`Échec de récupération des équipes (HTTP ${response.status})`)
  return response.json()
}

export async function addPlayer(
  teamId: string,
  fullName: string,
  jerseyNumber: number | null,
): Promise<Player> {
  const response = await fetch(`${API_BASE_URL}/teams/${teamId}/players`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ full_name: fullName, jersey_number: jerseyNumber }),
  })
  if (!response.ok) throw new Error(`Échec d'ajout de joueur (HTTP ${response.status})`)
  return response.json()
}
