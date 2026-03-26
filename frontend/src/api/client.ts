import axios from 'axios'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: apiBase,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ManufacturingRequest {
  product_type_id: number
  runs: number
  me_level: number
  structure_bonus?: number
  rig_bonus?: number
  build_intermediates?: boolean
}

export interface CostSummary {
  material_cost: number
  install_cost: number
  total_cost: number
  jita_sell_price: number
  margin: number
  margin_percent: number
}

export interface MaterialNode {
  type_id: number
  type_name: string
  quantity_needed: number
  quantity_owned: number
  quantity_to_buy: number
  unit_price: number
  total_cost: number
  is_buildable: boolean
  me_level: number
  children: MaterialNode[]
}

export interface ManufacturingResponse {
  product: { typeID: number; typeName: string }
  runs: number
  me_level: number
  material_tree: MaterialNode
  flat_materials: MaterialNode[]
  cost_summary: CostSummary
}

export const manufacturingApi = {
  calculate: (request: ManufacturingRequest) =>
    api.post<ManufacturingResponse>('/manufacturing/calculate', request),

  search: (q: string, limit?: number) =>
    api.get('/manufacturing/search', { params: { q, limit } }),
}

// Auth is on the root, not /api
const authBase = axios.create({ baseURL: import.meta.env.VITE_API_BASE?.replace('/api', '') || 'http://localhost:8000' })

export interface AuthStatus {
  authenticated: boolean
  character_id?: number
  character_name?: string
  portrait?: string
}

export interface CharacterSkills {
  total_sp: number
  industry_skills: Record<string, number>
}

export interface IndustryJob {
  job_id: number
  activity_id: number
  blueprint_type_id: number
  product_type_id: number
  runs: number
  status: string
  start_date: string
  end_date: string
  cost: number
}

export const authApi = {
  status: () => authBase.get<AuthStatus>('/auth/status'),
  logout: () => authBase.get('/auth/logout'),
  loginUrl: 'http://localhost:8000/auth/login',
}

export const characterApi = {
  wallet: () => authBase.get<{ balance: number }>('/api/character/wallet'),
  skills: () => authBase.get<CharacterSkills>('/api/character/skills'),
  jobs: () => authBase.get<IndustryJob[]>('/api/character/jobs'),
}
