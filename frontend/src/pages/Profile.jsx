/**
 * ATF Lab - 个人主页（进度 / 徽章 / 已通关列表）
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useApp } from '../store'
import { ErrorBox, Loading, Stars } from '../components/Common'

export default function Profile() {
  const { user } = useApp()
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    if (!user) {
      setLoading(false)
      return
    }
    setLoading(true)
    setErr(null)
    try {
      setData(await api.myProfile())
    } catch (e) {
      setErr(e)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    load()
  }, [load])

  if (!user) {
    return (
      <div className="container">
        <div className="card card-pad-lg center">
          <h2 style={{ marginTop: 0 }}>需要登录</h2>
          <p className="muted">登录后即可查看你的进度与徽章。</p>
          <Link className="btn btn-primary" to="/login">
            去登录
          </Link>
        </div>
      </div>
    )
  }

  if (loading) return <Loading />

  return (
    <div className="container">
      <ErrorBox error={err} onRetry={load} />

      {data && (
        <>
          <div className="card card-pad-lg" style={{ marginBottom: 20 }}>
            <div className="row-between">
              <div>
                <h1 style={{ margin: '0 0 6px', fontSize: 24 }}>
                  {data.username}
                  {data.is_demo && (
                    <span className="tag tag-warn" style={{ marginLeft: 10 }}>
                      🎮 体验账号
                    </span>
                  )}
                  {data.role === 'admin' && (
                    <span className="tag tag-purple" style={{ marginLeft: 10 }}>
                      管理员
                    </span>
                  )}
                </h1>
                <div className="muted" style={{ fontSize: 14 }}>
                  通关 {data.solved_count} / {data.total_count} 关 · 得分{' '}
                  {data.points} / {data.max_points}
                </div>
              </div>
              <div className="center">
                <div
                  style={{
                    fontSize: 30,
                    fontWeight: 800,
                    color: 'var(--accent)',
                  }}
                >
                  {data.progress_percent}%
                </div>
                <div className="faint">完成度</div>
              </div>
            </div>
            <div className="progress-bar mt-16">
              <div style={{ width: `${data.progress_percent}%` }} />
            </div>

            {data.is_demo && (
              <div className="notice notice-warn" style={{ marginTop: 16 }}>
                🎮 <b>这是一个体验账号。</b>
                全部 {data.total_count} 关已预先解锁，方便你直接查看各关内容与原理讲解。
                它的成绩不代表真实水平，因此在排行榜上带有「体验账号」标识。
              </div>
            )}
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <b>🎖️ 成就徽章</b>
            <div className="badge-grid mt-16">
              {(data.all_badges || []).map((b) => (
                <div
                  key={b.id}
                  className={'badge' + (b.earned ? ' earned' : '')}
                  title={b.description}
                >
                  <div className="bi">{b.earned ? '🏅' : '🔒'}</div>
                  <div className="bn">{b.name}</div>
                  <div className="bd">{b.description}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <b>📚 已通关关卡（{data.solved_levels?.length || 0}）</b>
            {(!data.solved_levels || data.solved_levels.length === 0) && (
              <p className="muted mt-16">
                还没有通关记录。<Link to="/levels">去挑战第一关</Link> 吧。
              </p>
            )}
            {data.solved_levels?.length > 0 && (
              <table className="table mt-16">
                <thead>
                  <tr>
                    <th>编号</th>
                    <th>名称</th>
                    <th>分类</th>
                    <th>难度</th>
                    <th>分值</th>
                  </tr>
                </thead>
                <tbody>
                  {data.solved_levels.map((l) => (
                    <tr key={l.id}>
                      <td className="mono">{l.id}</td>
                      <td>
                        <Link to={`/levels/${l.id}`}>{l.name}</Link>
                      </td>
                      <td>
                        <span className="tag">{l.category}</span>
                      </td>
                      <td>
                        <Stars level={l.difficulty} />
                      </td>
                      <td>{l.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}
