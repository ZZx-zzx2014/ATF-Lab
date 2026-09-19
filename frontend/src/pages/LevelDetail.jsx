/**
 * ATF Lab - 关卡详情（目标 / 提示 / 模拟交互 / 提交 flag / 原理讲解）
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useApp } from '../store'
import {
  Empty, ErrorBox, LevelDisclaimer, Loading, Stars,
} from '../components/Common'

/* -------------------------------------------------- 各关卡的模拟交互面板 */
function SimPanel({ levelId }) {
  const [extra, setExtra] = useState('')
  const [out, setOut] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const run = async (fn) => {
    setBusy(true)
    setErr(null)
    try {
      setOut(await fn())
    } catch (e) {
      setErr(e)
      setOut(null)
    } finally {
      setBusy(false)
    }
  }

  // 每关的交互形态不同，按 id 分派
  const panels = {
    L01: {
      label: '获取页面源码',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L04: {
      label: '尝试登录',
      placeholder: '要尝试的密码，如 123456',
      action: () => run(() => api.simLogin(levelId, 'admin', extra)),
    },
    L05: {
      label: '提交用户名',
      placeholder: "注入 payload，如 ' OR '1'='1",
      action: () => run(() => api.simLogin(levelId, extra, 'x')),
    },
    L06: {
      label: '读取文件',
      placeholder: '路径，如 ../../etc/passwd',
      action: () => run(() => api.simFile(levelId, extra)),
    },
    L07: {
      label: '执行 ping',
      placeholder: 'IP，如 127.0.0.1; id',
      action: () => run(() => api.simPing(levelId, extra)),
    },
    L08: {
      label: '查询用户资料',
      placeholder: 'user_id，如 1',
      action: () => run(() => api.simProfile(levelId, extra || '1')),
    },
    L09: {
      label: '搜索',
      placeholder: '搜索词，如 <script>alert(1)</script>',
      action: () => run(() => api.simSearch(levelId, extra)),
    },
    L10: {
      label: '发起转账',
      placeholder: '收款人，如 attacker@sim.invalid',
      action: () => run(() => api.simTransfer(levelId, extra, 9999)),
    },
    L11: {
      label: '抓取 URL',
      placeholder: 'URL，如 http://internal.helios-sim.invalid/archive',
      action: () => run(() => api.simFetch(levelId, extra)),
    },
    L12: {
      label: '上传文件',
      placeholder: '文件名，如 shell.phtml',
      action: () => run(() => api.simUpload(levelId, extra)),
    },
    L13: {
      label: '提交序列化数据',
      placeholder: 'payload，如 cos\\n...__reduce__...',
      action: () => run(() => api.simDeserialize(levelId, extra)),
    },
    L14: {
      label: '提交 XML',
      placeholder: 'XML 含 DOCTYPE 与 ENTITY SYSTEM',
      action: () => run(() => api.simParse(levelId, extra)),
    },
    L19: {
      label: '查看弱随机数预览',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L03: {
      label: '获取响应头',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L02: {
      label: '获取编码字符串',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L22: {
      label: '查看文件尾部',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L23: {
      label: '读取 EXIF',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L24: {
      label: '查看流量包',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L25: {
      label: '查看日志',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L26: {
      label: '查看 LSB 信息',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L30: {
      label: '查看目录扫描结果',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L31: {
      label: '伪造请求头访问',
      placeholder: 'X-Forwarded-For 值，如 127.0.0.1',
      action: () => run(() => api.simPage(levelId)),
    },
    L34: {
      label: '查看伪代码',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L35: {
      label: '查看混淆脚本',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
    L36: {
      label: '查看邮件全文',
      placeholder: '',
      action: () => run(() => api.simPage(levelId)),
    },
  }

  const p = panels[levelId]
  if (!p) return null

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="row-between" style={{ marginBottom: 10 }}>
        <b>🧪 模拟交互台</b>
        <span className="tag tag-warn">受控模拟</span>
      </div>
      <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
        {p.placeholder && (
          <input
            className="input"
            style={{ flex: 1, minWidth: 200 }}
            placeholder={p.placeholder}
            value={extra}
            onChange={(e) => setExtra(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && p.action()}
          />
        )}
        <button className="btn btn-primary" onClick={p.action} disabled={busy}>
          {busy ? '执行中…' : p.label}
        </button>
      </div>
      <ErrorBox error={err} />
      {out && (
        <pre className="terminal" style={{ marginTop: 12 }}>
          {JSON.stringify(out, null, 2)}
        </pre>
      )}
      <div className="faint" style={{ marginTop: 9 }}>
        提示：打开浏览器 Network 面板，可以看到这次请求打在
        <code> /api/v1/sim/…</code> 上，返回的是预置模拟数据。
      </div>
    </div>
  )
}

/* -------------------------------------------------- 主页面 */
export default function LevelDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { user } = useApp()

  const [lv, setLv] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [flag, setFlag] = useState('')
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [hintBusy, setHintBusy] = useState(-1)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setLv(await api.level(id))
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
    setResult(null)
    setFlag('')
  }, [load])

  const submit = async () => {
    if (!user) {
      setResult({ needLogin: true })
      return
    }
    setSubmitting(true)
    setResult(null)
    try {
      const d = await api.submitFlag(id, flag)
      setResult(d)
      if (d.correct) {
        setLv((prev) =>
          prev
            ? { ...prev, solved: true, writeup: d.writeup || prev.writeup }
            : prev
        )
      }
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setSubmitting(false)
    }
  }

  const unlockHint = async (index) => {
    if (!user) {
      setResult({ needLogin: true })
      return
    }
    setHintBusy(index)
    try {
      await api.unlockHint(id, index)
      setLv(await api.level(id))
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setHintBusy(-1)
    }
  }

  if (loading) return <Loading />
  if (error) {
    return (
      <div className="container">
        <ErrorBox error={error} onRetry={load} />
        <Link className="btn" to="/levels">
          ← 返回关卡列表
        </Link>
      </div>
    )
  }
  if (!lv) return <Empty text="关卡不存在" />

  // 压轴关跳转到专属沉浸式页面
  if (lv.special === 'finale') {
    return (
      <div className="container">
        <div className="card card-pad-lg center">
          <h1>🎬 {lv.name}</h1>
          <p className="muted">{lv.objective}</p>
          {lv.unlocked === false ? (
            <div className="notice notice-warn" style={{ marginTop: 16 }}>
              该关卡尚未解锁 —— 需要先通关至少 5 个教学关。
            </div>
          ) : (
            <Link className="btn btn-primary btn-lg mt-16" to="/finale">
              进入行动
            </Link>
          )}
          <LevelDisclaimer />
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <Link className="faint" to="/levels">
        ← 返回关卡列表
      </Link>

      <div className="row-between" style={{ margin: '14px 0 18px' }}>
        <div>
          <div className="row" style={{ gap: 9 }}>
            <span className="level-id">{lv.id}</span>
            <h1 style={{ margin: 0, fontSize: 23 }}>{lv.name}</h1>
            {lv.solved && <span className="tag tag-success">已通关</span>}
          </div>
          <div className="row mt-16" style={{ gap: 10 }}>
            <span className="tag tag-accent">{lv.category}</span>
            <Stars level={lv.difficulty} />
            <span className="faint">{lv.points} 分</span>
            {lv.tags?.map((t) => (
              <span className="tag" key={t}>
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="detail-grid">
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <b>🎯 关卡目标</b>
            <p style={{ marginBottom: 0 }}>{lv.objective}</p>
          </div>

          <SimPanel levelId={lv.id} />

          <div className="card">
            <b>🚩 提交 flag</b>
            <div className="row mt-16" style={{ gap: 8, flexWrap: 'wrap' }}>
              <input
                className="input"
                style={{ flex: 1, minWidth: 220, fontFamily: 'var(--mono)' }}
                placeholder="flag{...}"
                value={flag}
                onChange={(e) => setFlag(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && submit()}
              />
              <button
                className="btn btn-primary"
                onClick={submit}
                disabled={submitting || !flag.trim()}
              >
                {submitting ? '校验中…' : '提交'}
              </button>
            </div>

            {result?.needLogin && (
              <div className="flag-result flag-bad">
                请先 <Link to="/login">登录</Link> 才能提交 flag 并保存进度。
              </div>
            )}
            {result?.error && (
              <div className="flag-result flag-bad">⚠️ {result.error}</div>
            )}
            {result?.correct && (
              <div className="flag-result flag-ok">
                ✅ 正确！{result.first_solve
                  ? `首次通关，获得 ${result.points_awarded} 分。`
                  : '（此前已通关，不重复计分）'}
                <div className="faint" style={{ marginTop: 5 }}>
                  当前进度：{result.solved_count} / {result.total_count}
                </div>
              </div>
            )}
            {result && result.correct === false && (
              <div className="flag-result flag-bad">
                ❌ flag 不正确，再想想。可以逐条解锁提示。
              </div>
            )}
          </div>

          {lv.solved && lv.writeup && (
            <div className="card" style={{ marginTop: 16 }}>
              <b>📖 原理讲解与防御方案</b>
              <div
                style={{ whiteSpace: 'pre-wrap', marginTop: 10, fontSize: 14 }}
              >
                {lv.writeup}
              </div>
            </div>
          )}

          <LevelDisclaimer />
        </div>

        {/* 侧栏：分级提示 */}
        <div>
          <div className="card">
            <div className="row-between" style={{ marginBottom: 10 }}>
              <b>💡 分级提示</b>
              <span className="faint">
                {lv.unlocked_hints} / {lv.hint_count} 已解锁
              </span>
            </div>
            {(lv.hints || []).map((h) => (
              <div
                key={h.index}
                className={'hint-item' + (h.unlocked ? '' : ' locked')}
              >
                {h.unlocked ? (
                  <>
                    <b className="faint">提示 {h.index + 1}</b>
                    <div style={{ marginTop: 4 }}>{h.text}</div>
                  </>
                ) : (
                  <div className="row-between">
                    <span>🔒 提示 {h.index + 1} 尚未解锁</span>
                    <button
                      className="btn btn-sm"
                      onClick={() => unlockHint(h.index)}
                      disabled={hintBusy === h.index}
                    >
                      {hintBusy === h.index ? '…' : '解锁'}
                    </button>
                  </div>
                )}
              </div>
            ))}
            <div className="faint">
              提示按顺序解锁。建议先自己尝试，卡住了再看。
            </div>
          </div>

          {lv.solved && (
            <div className="card mt-16">
              <b>✅ 已完成</b>
              <p className="muted mb-0 mt-16" style={{ fontSize: 14 }}>
                你已通关本关。原理讲解已显示在左侧。
              </p>
              <button
                className="btn btn-block mt-16"
                onClick={() => nav('/levels')}
              >
                挑战下一关
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
