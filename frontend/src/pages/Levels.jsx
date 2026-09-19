/**
 * ATF Lab - 关卡列表（分类筛选 / 关键词搜索 / 难度过滤）
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useApp } from '../store'
import { ErrorBox, Loading, Stars } from '../components/Common'

function LevelCard({ lv, onOpen }) {
  const cls = [
    'level-card',
    lv.solved ? 'solved' : '',
    lv.unlocked === false ? 'locked' : '',
    lv.special === 'finale' ? 'finale' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={cls}
      onClick={() => lv.unlocked !== false && onOpen(lv.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' && lv.unlocked !== false) onOpen(lv.id)
      }}
    >
      <div className="level-card-head">
        <span className="level-id">{lv.id}</span>
        <span className="level-name">{lv.name}</span>
        {lv.solved && <span className="tag tag-success">已通关</span>}
        {lv.unlocked === false && <span className="tag">🔒 未解锁</span>}
      </div>
      <p className="level-obj">{lv.objective}</p>
      <div className="level-foot">
        <span
          className={
            lv.special === 'finale' ? 'tag tag-purple' : 'tag tag-accent'
          }
        >
          {lv.category}
        </span>
        <Stars level={lv.difficulty} />
        <span className="spacer" />
        <span className="faint">{lv.points} 分</span>
      </div>
    </div>
  )
}

export default function Levels({ labMode = false }) {
  const nav = useNavigate()
  const { user } = useApp()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const [category, setCategory] = useState('')
  const [difficulty, setDifficulty] = useState(0)
  const [keyword, setKeyword] = useState('')
  const [debounced, setDebounced] = useState('')

  // 关键词防抖，避免每次按键都打一次 API
  useEffect(() => {
    const t = setTimeout(() => setDebounced(keyword), 350)
    return () => clearTimeout(t)
  }, [keyword])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const d = await api.levels({
        category,
        difficulty,
        keyword: debounced,
      })
      setData(d)
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }, [category, difficulty, debounced])

  useEffect(() => {
    load()
  }, [load])

  const pct = data
    ? Math.round((data.solved_count / Math.max(1, data.total_count)) * 100)
    : 0

  return (
    <div className="container">
      <div className="row-between" style={{ marginBottom: 18 }}>
        <div>
          <h1 style={{ margin: '0 0 4px', fontSize: 25 }}>
            {labMode ? '🎯 CTF 靶场' : '关卡列表'}
          </h1>
          <div className="muted" style={{ fontSize: 14 }}>
            {data
              ? `已通关 ${data.solved_count} / ${data.total_count} · 得分 ${data.earned_points} / ${data.total_points}`
              : '加载中…'}
          </div>
        </div>
        {!user && (
          <div className="notice notice-info">
            登录后进度才会保存到服务器（跨设备同步）
          </div>
        )}
      </div>

      {data && (
        <div className="progress-bar" style={{ marginBottom: 20 }}>
          <div style={{ width: `${pct}%` }} />
        </div>
      )}

      {/* 筛选区 */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="grid grid-3" style={{ gap: 12 }}>
          <div>
            <label className="faint">关键词搜索</label>
            <input
              className="input"
              placeholder="关卡名 / 考点 / 标签，如 redis"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </div>
          <div>
            <label className="faint">分类</label>
            <select
              className="select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">全部分类</option>
              {(data?.categories || []).map((c) => (
                <option key={c.category} value={c.category}>
                  {c.category}（{c.solved}/{c.total}）
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="faint">难度</label>
            <select
              className="select"
              value={difficulty}
              onChange={(e) => setDifficulty(Number(e.target.value))}
            >
              <option value={0}>全部难度</option>
              {[1, 2, 3, 4, 5].map((d) => (
                <option key={d} value={d}>
                  {'★'.repeat(d)} 难度 {d}
                </option>
              ))}
            </select>
          </div>
        </div>
        {(category || difficulty || keyword) && (
          <div className="mt-16">
            <button
              className="btn btn-sm"
              onClick={() => {
                setCategory('')
                setDifficulty(0)
                setKeyword('')
              }}
            >
              清除筛选
            </button>
          </div>
        )}
      </div>

      {loading && <Loading />}
      <ErrorBox error={error} onRetry={load} />

      {!loading && data && data.levels.length === 0 && (
        <div className="empty">没有符合条件的关卡，试试放宽筛选条件</div>
      )}

      {!loading && data && data.levels.length > 0 && (
        <div className="grid grid-2">
          {data.levels.map((lv) => (
            <LevelCard key={lv.id} lv={lv} onOpen={(id) => nav(`/levels/${id}`)} />
          ))}
        </div>
      )}
    </div>
  )
}
