/**
 * ATF Lab - API 客户端
 *
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 *
 * 前端所有数据交互都经由本模块发出，全部为 /api/v1/* 的 fetch 请求。
 * 打开浏览器 Network 面板即可看到每一笔数据的来源。
 *
 * 统一响应格式：{ code, message, data }，code === 0 表示成功。
 */

const API_BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

const TOKEN_KEY = 'atf_token'

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch (e) {
    return ''
  }
}

export function setToken(t) {
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
  } catch (e) {
    /* 忽略隐私模式下的存储异常 */
  }
}

export class ApiError extends Error {
  constructor(code, message, data) {
    super(message || '请求失败')
    this.code = code
    this.data = data
  }
}

async function request(method, path, body, opts = {}) {
  const url = API_BASE + path
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = 'Bearer ' + token

  const init = { method, headers }
  if (body !== undefined && body !== null) {
    init.body = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(url, init)
  } catch (e) {
    throw new ApiError(-1, '无法连接后端服务，请确认服务已启动')
  }

  let payload
  try {
    payload = await res.json()
  } catch (e) {
    throw new ApiError(-1, `响应不是合法 JSON（HTTP ${res.status}）`)
  }

  if (!payload || typeof payload.code !== 'number') {
    throw new ApiError(-1, '响应格式不符合统一约定')
  }

  if (payload.code !== 0) {
    // 401 时清理本地登录态，避免界面停留在"假登录"状态
    if (payload.code === 1002 && !opts.silent) setToken('')
    throw new ApiError(payload.code, payload.message, payload.data)
  }
  return payload.data
}

const get = (p, o) => request('GET', p, null, o)
const post = (p, b, o) => request('POST', p, b, o)
const del = (p, o) => request('DELETE', p, null, o)

/* ------------------------------------------------------------------ 系统 */
export const api = {
  health: () => get('/api/v1/health'),

  /* ---------------------------------------------------------------- 认证 */
  register: (username, password, email) =>
    post('/api/v1/auth/register', { username, password, email }),
  login: (username, password) =>
    post('/api/v1/auth/login', { username, password }),
  me: (opts) => get('/api/v1/auth/me', opts),

  /* ---------------------------------------------------------------- 关卡 */
  levels: (params = {}) => {
    const q = new URLSearchParams()
    if (params.category) q.set('category', params.category)
    if (params.difficulty) q.set('difficulty', String(params.difficulty))
    if (params.keyword) q.set('keyword', params.keyword)
    const qs = q.toString()
    return get('/api/v1/levels' + (qs ? '?' + qs : ''))
  },
  level: (id) => get(`/api/v1/levels/${encodeURIComponent(id)}`),
  submitFlag: (id, flag) =>
    post(`/api/v1/levels/${encodeURIComponent(id)}/submit`, { flag }),
  unlockHint: (id, index) =>
    post(`/api/v1/levels/${encodeURIComponent(id)}/hint/${index}`),

  /* ------------------------------------------------------------ 用户/排行 */
  leaderboard: () => get('/api/v1/leaderboard'),
  myProfile: () => get('/api/v1/me/profile'),
  userProfile: (username) =>
    get(`/api/v1/users/${encodeURIComponent(username)}`),
  progress: () => get('/api/v1/progress'),

  /* ---------------------------------------------------------------- 管理 */
  adminStats: () => get('/api/v1/admin/stats'),
  adminLevels: () => get('/api/v1/admin/levels'),
  adminUsers: () => get('/api/v1/admin/users'),
  adminUpsertLevel: (level) => post('/api/v1/admin/levels', level),
  adminDeleteLevel: (id) =>
    del(`/api/v1/admin/levels/${encodeURIComponent(id)}`),

  /* ------------------------------------------------------- 教学模拟（L01-L36） */
  simPage: (id) => get(`/api/v1/sim/level/${id}/page`),
  simFile: (id, name) =>
    get(`/api/v1/sim/level/${id}/file?name=${encodeURIComponent(name)}`),
  simSearch: (id, q) =>
    get(`/api/v1/sim/level/${id}/search?q=${encodeURIComponent(q)}`),
  simProfile: (id, userId) =>
    get(`/api/v1/sim/level/${id}/profile?user_id=${encodeURIComponent(userId)}`),
  simLogin: (id, username, password) =>
    post(`/api/v1/sim/level/${id}/login`, { username, password }),
  simPing: (id, ip) => post(`/api/v1/sim/level/${id}/ping`, { ip }),
  simFetch: (id, url) => post(`/api/v1/sim/level/${id}/fetch`, { url }),
  simUpload: (id, filename) =>
    post(`/api/v1/sim/level/${id}/upload`, { filename, size: 1024 }),
  simDeserialize: (id, payload) =>
    post(`/api/v1/sim/level/${id}/deserialize`, { payload }),
  simParse: (id, xml) => post(`/api/v1/sim/level/${id}/parse`, { xml }),
  simTransfer: (id, to, amount) =>
    post(`/api/v1/sim/level/${id}/transfer`, { to, amount }),

  /* --------------------------------------------------- 压轴关 L37 REAPER */
  finaleBriefing: () => get('/api/v1/finale/briefing'),
  finaleProgress: () => get('/api/v1/finale/progress'),
  finaleEmployees: () => get('/api/v1/finale/legacy/employees'),
  finaleLogin: (username, password) =>
    post('/api/v1/finale/login', { username, password }),
  finaleAdmin: (token) =>
    get('/api/v1/finale/admin?token=' + encodeURIComponent(token)),
  finaleHealthCheck: (url) =>
    post('/api/v1/finale/health-check', { url }),
  finaleArchiveSearch: (xml, archiveKey) =>
    post('/api/v1/finale/archive/search', { xml, archive_key: archiveKey }),
  finaleDestroyPreview: () => get('/api/v1/finale/archive/destroy/preview'),
  finaleDestroy: (token, confirm) =>
    post('/api/v1/finale/archive/destroy', {
      destruction_token: token,
      confirm,
    }),
}
