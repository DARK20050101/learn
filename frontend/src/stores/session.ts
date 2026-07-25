import { reactive } from 'vue'
import { api } from '../services/api'
import type { User } from '../types'
import { resetStudy } from './study'

const state = reactive<{ user: User | null; ready: boolean }>({ user: null, ready: false })

export function useSession() {
  async function restore() {
    if (!localStorage.getItem('access_token')) { state.ready = true; return }
    try { state.user = await api.me() } catch { state.user = null }
    finally { state.ready = true }
  }
  async function login(username: string, password: string) {
    const result = await api.login(username, password)
    localStorage.setItem('access_token', result.access_token)
    state.user = await api.me()
  }
  function logout() { localStorage.removeItem('access_token'); state.user = null; resetStudy() }
  return { state, restore, login, logout }
}
