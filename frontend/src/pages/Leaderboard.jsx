/**
 * ATF Lab - 排行榜
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useApp } from '../store'
import { Empty, ErrorBox, Loading } from '../components/Common'

export default function Leaderboard() {
  const { user } = useApp()
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setErr(null)
    try {
      setData(await api.leaderboard())
    } catch (e) {
      setErr(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <Loading />

  return (
    <div className="container">
      <div className="row-between" style={{ marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: '0 0 4px', fontSize: 25 }}>🏆 排行榜</h1>
          <div className="muted" style={{ fontSize: 14 }}>
            按总得分排序，同分者以最早通关时间优先
          </div>
        </div>
        {user && data?.my_rank && (
          <div className="notice notice-info">你的排名：第 {data.my_rank} 名</div>
        )}
      </div>

      <ErrorBox error={err} onRetry={load} />

      {data && data.entries.length === 0 && (
        <Empty text="还没有任何通关记录，快来成为第一个上榜的人" />
      )}

      {data && data.entries.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: 70 }}>排名</th>
                <th>用户</th>
                <th style={{ width: 110 }}>通关数</th>
                <th style={{ width: 100 }}>得分</th>
              </tr>
            </thead>
            <tbody>
              {data.entries.map((e) => {
                const me = user && e.user_id === user.id
                return (
                  <tr
                    key={e.user_id}
                    style={me ? { background: 'var(--accent-soft)' } : undefined}
                  >
                    <td>
                      <b
                        style={{
                          color:
                            e.rank <= 3 ? 'var(--warn)' : 'var(--text-dim)',
                        }}
                      >
                        {e.rank <= 3 ? ['🥇', '🥈', '🥉'][e.rank - 1] : `#${e.rank}`}
                      </b>
                    </td>
                    <td>
                      <Link to={`/u/${e.username}`}>{e.username}</Link>
                      {e.role === 'admin' && (
                        <span className="tag tag-purple" style={{ marginLeft: 8 }}>
                          管理员
                        </span>
                      )}
                      {me && (
                        <span className="tag tag-accent" style={{ marginLeft: 8 }}>
                          你
                        </span>
                      )}
                    </td>
                    <td>{e.solved_count}</td>
                    <td>
                      <b>{e.points}</b>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
