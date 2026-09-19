/**
 * ATF Lab - 全局状态（认证 / 主题 / 模式）
 *
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'

const AppCtx = createContext(null)

const THEME_KEY = 'atf_theme'
const MODE_KEY = 'atf_mode'

function readLS(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback
  } catch (e) {
    return fallback
  }
}
function writeLS(key, val) {
  try {
    localStorage.setItem(key, val)
  } catch (e) {
    /* 忽略 */
  }
}

export function AppProvider({ children }) {
  const [user, setUser] = useState(null)
  const [authReady, setAuthReady] = useState(false)
  const [theme, setThemeState] = useState(() => {
    const saved = readLS(THEME_KEY, '')
    if (saved) return saved
    const prefersLight =
      window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches
    return prefersLight ? 'light' : 'dark'
  })
  // 模式：site = 展示型网站；lab = CTF 靶场。两者都用显式标识区分，不做伪装。
  const [mode, setModeState] = useState(() => readLS(MODE_KEY, 'site'))

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    writeLS(THEME_KEY, theme)
  }, [theme])

  useEffect(() => {
    writeLS(MODE_KEY, mode)
  }, [mode])

  // 启动时若本地有 token，尝试拉取用户信息
  useEffect(() => {
    let alive = true
    ;(async () => {
      if (!getToken()) {
        setAuthReady(true)
        return
      }
      try {
        const me = await api.me({ silent: true })
        if (alive) setUser(me)
      } catch (e) {
        setToken('')
      } finally {
        if (alive) setAuthReady(true)
      }
    })()
    return () => {
      alive = false
    }
  }, [])

  const login = useCallback(async (username, password) => {
    const d = await api.login(username, password)
    setToken(d.token)
    setUser(d.user)
    return d
  }, [])

  const register = useCallback(async (username, password, email) => {
    const d = await api.register(username, password, email)
    setToken(d.token)
    setUser(d.user)
    return d
  }, [])

  const logout = useCallback(() => {
    setToken('')
    setUser(null)
  }, [])

  const toggleTheme = useCallback(
    () => setThemeState((t) => (t === 'dark' ? 'light' : 'dark')),
    []
  )
  const setMode = useCallback((m) => setModeState(m), [])

  const value = {
    user, setUser, authReady,
    login, register, logout,
    theme, toggleTheme,
    mode, setMode,
  }
  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>
}

export function useApp() {
  const ctx = useContext(AppCtx)
  if (!ctx) throw new Error('useApp 必须在 AppProvider 内部使用')
  return ctx
}
