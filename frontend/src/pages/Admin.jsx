/**
 * ATF Lab - 管理后台（关卡管理 / 答题统计）
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useApp } from '../store'
import { ErrorBox, Loading } from '../components/Common'

const BLANK = {
  id: 'C01',
  name: '',
  category: 'Web 安全',
  difficulty: 1,
  objective: '',
  writeup: '',
  flag: '',
  points: 100,
  tags: '',
  hints: ['', '', ''],
}

export default function Admin() {
  const { user } = useApp()
  const [tab, setTab] = useState('stats')
  const [stats, setStats] = useState(null)
  const [levels, setLevels] = useState(null)
  const [users, setUsers] = useState(null)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(BLANK)
  const [msg, setMsg] = useState('')

  const load = useCallback(async () => {
    if (!user || user.role !== 'admin') {
      setLoading(false)
      return
    }
    setLoading(true)
    setErr(null)
    try {
      const [s, l, u] = await Promise.all([
        api.adminStats(),
        api.adminLevels(),
        api.adminUsers(),
      ])
      setStats(s)
      setLevels(l.levels)
      setUsers(u.users)
    } catch (e) {
      setErr(e)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    load()
  }, [load])

  if (!user || user.role !== 'admin') {
    return (
      <div className="container">
        <div className="card card-pad-lg center">
          <h2 style={{ marginTop: 0 }}>🔒 需要管理员权限</h2>
          <p className="muted">
            只有管理员可以访问后台。本平台的<b>第一个注册用户</b>会自动成为管理员。
          </p>
          {!user && (
            <Link className="btn btn-primary" to="/login">
              去登录
            </Link>
          )}
        </div>
      </div>
    )
  }

  if (loading) return <Loading />

  const saveLevel = async (e) => {
    e.preventDefault()
    setMsg('')
    try {
      await api.adminUpsertLevel({
        ...form,
        difficulty: Number(form.difficulty),
        points: Number(form.points),
        tags: form.tags
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        hints: form.hints.filter((h) => h.trim()),
      })
      setMsg('✅ 关卡已保存')
      setForm(BLANK)
      await load()
    } catch (ex) {
      setMsg('❌ ' + ex.message)
    }
  }

  return (
    <div className="container">
      <h1 style={{ margin: '0 0 6px', fontSize: 25 }}>⚙️ 管理后台</h1>
      <div className="muted" style={{ marginBottom: 20, fontSize: 14 }}>
        查看答题统计、管理关卡、浏览用户
      </div>

      <div className="row" style={{ gap: 8, marginBottom: 20 }}>
        {[
          ['stats', '📊 答题统计'],
          ['levels', '📚 关卡管理'],
          ['users', '👥 用户列表'],
        ].map(([k, label]) => (
          <button
            key={k}
            className={'btn btn-sm' + (tab === k ? ' btn-primary' : '')}
            onClick={() => setTab(k)}
          >
            {label}
          </button>
        ))}
      </div>

      <ErrorBox error={err} onRetry={load} />

      {tab === 'stats' && stats && (
        <>
          <div className="grid grid-4" style={{ marginBottom: 20 }}>
            {[
              ['用户总数', stats.total_users],
              ['通关总次数', stats.total_solves],
              ['提交总次数', stats.total_submissions],
              ['正确率', stats.accuracy + '%'],
            ].map(([label, v]) => (
              <div className="card center" key={label}>
                <div
                  style={{ fontSize: 25, fontWeight: 800, color: 'var(--accent)' }}
                >
                  {v}
                </div>
                <div className="faint">{label}</div>
              </div>
            ))}
          </div>

          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>编号</th>
                  <th>关卡</th>
                  <th>分类</th>
                  <th>难度</th>
                  <th>通关人数</th>
                  <th>提交次数</th>
                </tr>
              </thead>
              <tbody>
                {stats.per_level.map((l) => (
                  <tr key={l.level_id}>
                    <td className="mono">{l.level_id}</td>
                    <td>{l.name}</td>
                    <td>
                      <span className="tag">{l.category}</span>
                    </td>
                    <td>{'★'.repeat(l.difficulty)}</td>
                    <td>
                      <b style={{ color: l.solve_count ? 'var(--success)' : 'var(--text-faint)' }}>
                        {l.solve_count}
                      </b>
                    </td>
                    <td className="muted">{l.submit_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'levels' && (
        <div className="detail-grid">
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>编号</th>
                  <th>名称</th>
                  <th>分类</th>
                  <th>flag</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {(levels || []).map((l) => (
                  <tr key={l.id}>
                    <td className="mono">{l.id}</td>
                    <td>{l.name}</td>
                    <td>
                      <span className="tag">{l.category}</span>
                    </td>
                    <td className="mono faint" style={{ fontSize: 11.5 }}>
                      {l.flag}
                    </td>
                    <td>
                      {!l.builtin && (
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={async () => {
                            if (!window.confirm(`确认删除关卡 ${l.id}？`)) return
                            try {
                              await api.adminDeleteLevel(l.id)
                              await load()
                            } catch (ex) {
                              setMsg('❌ ' + ex.message)
                            }
                          }}
                        >
                          删除
                        </button>
                      )}
                      {l.builtin && <span className="faint">内置</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card">
            <b>➕ 新增 / 覆盖关卡</b>
            <p className="faint">
              自定义关卡 ID 建议用 C 开头（如 C01），内置关卡不可删除但可被覆盖。
            </p>
            {msg && <div className="notice mb-0">{msg}</div>}
            <form onSubmit={saveLevel} className="mt-16">
              <div className="field">
                <label>关卡 ID</label>
                <input
                  className="input"
                  value={form.id}
                  onChange={(e) => setForm({ ...form, id: e.target.value })}
                  required
                />
              </div>
              <div className="field">
                <label>名称</label>
                <input
                  className="input"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
              <div className="field">
                <label>分类</label>
                <input
                  className="input"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  required
                />
              </div>
              <div className="row" style={{ gap: 10 }}>
                <div className="field" style={{ flex: 1 }}>
                  <label>难度 (1-5)</label>
                  <input
                    className="input"
                    type="number"
                    min="1"
                    max="5"
                    value={form.difficulty}
                    onChange={(e) =>
                      setForm({ ...form, difficulty: e.target.value })
                    }
                  />
                </div>
                <div className="field" style={{ flex: 1 }}>
                  <label>分值</label>
                  <input
                    className="input"
                    type="number"
                    min="0"
                    value={form.points}
                    onChange={(e) => setForm({ ...form, points: e.target.value })}
                  />
                </div>
              </div>
              <div className="field">
                <label>关卡目标</label>
                <textarea
                  className="textarea"
                  value={form.objective}
                  onChange={(e) => setForm({ ...form, objective: e.target.value })}
                  required
                />
              </div>
              <div className="field">
                <label>flag</label>
                <input
                  className="input"
                  style={{ fontFamily: 'var(--mono)' }}
                  value={form.flag}
                  onChange={(e) => setForm({ ...form, flag: e.target.value })}
                  placeholder="flag{...}"
                  required
                />
              </div>
              <div className="field">
                <label>标签（逗号分隔）</label>
                <input
                  className="input"
                  value={form.tags}
                  onChange={(e) => setForm({ ...form, tags: e.target.value })}
                />
              </div>
              {form.hints.map((h, i) => (
                <div className="field" key={i}>
                  <label>提示 {i + 1}（至少 3 条）</label>
                  <input
                    className="input"
                    value={h}
                    onChange={(e) => {
                      const next = [...form.hints]
                      next[i] = e.target.value
                      setForm({ ...form, hints: next })
                    }}
                  />
                </div>
              ))}
              <div className="field">
                <label>原理讲解</label>
                <textarea
                  className="textarea"
                  value={form.writeup}
                  onChange={(e) => setForm({ ...form, writeup: e.target.value })}
                />
              </div>
              <button className="btn btn-primary btn-block" type="submit">
                保存关卡
              </button>
            </form>
          </div>
        </div>
      )}

      {tab === 'users' && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>角色</th>
                <th>通关数</th>
                <th>得分</th>
              </tr>
            </thead>
            <tbody>
              {(users || []).map((u) => (
                <tr key={u.id}>
                  <td className="mono">{u.id}</td>
                  <td>{u.username}</td>
                  <td>
                    <span
                      className={
                        u.role === 'admin' ? 'tag tag-purple' : 'tag'
                      }
                    >
                      {u.role}
                    </span>
                  </td>
                  <td>{u.solved_count}</td>
                  <td>
                    <b>{u.points}</b>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
