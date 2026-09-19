/**
 * ATF Lab - 修改密码 / 使用恢复码重置
 *
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 *
 * 这是"忘记密码"的正当实现方式：使用注册时生成的一次性恢复码。
 * 本项目刻意不提供任何通用后门密码。
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useApp } from '../store'

function StrengthHint({ pw }) {
  const rules = [
    ['至少 8 位', (pw || '').length >= 8],
    ['包含字母', /[A-Za-z]/.test(pw || '')],
    ['包含数字', /\d/.test(pw || '')],
  ]
  return (
    <div className="faint" style={{ marginTop: 6 }}>
      {rules.map(([label, ok]) => (
        <span
          key={label}
          style={{
            marginRight: 12,
            color: ok ? 'var(--success)' : 'var(--text-faint)',
          }}
        >
          {ok ? '✓' : '○'} {label}
        </span>
      ))}
    </div>
  )
}

/** 复制恢复码的提示框 */
export function RecoveryCodeBox({ code, notice }) {
  const [copied, setCopied] = useState(false)
  if (!code) return null
  return (
    <div
      className="notice notice-warn"
      style={{ marginTop: 14, borderLeft: '3px solid var(--warn)' }}
    >
      <div style={{ fontWeight: 700, marginBottom: 6 }}>
        🔑 你的恢复码（只显示这一次）
      </div>
      <div
        className="mono"
        style={{
          fontSize: 17,
          letterSpacing: 1.5,
          padding: '8px 10px',
          background: 'var(--bg-card)',
          borderRadius: 6,
          userSelect: 'all',
          wordBreak: 'break-all',
        }}
      >
        {code}
      </div>
      <div style={{ marginTop: 8, fontSize: 13 }}>
        {notice || '请立即保存。忘记密码时用它重置，用后即失效。'}
      </div>
      <button
        className="btn btn-sm"
        style={{ marginTop: 8 }}
        onClick={() => {
          navigator.clipboard?.writeText(code)
          setCopied(true)
          setTimeout(() => setCopied(false), 1500)
        }}
      >
        {copied ? '✓ 已复制' : '复制'}
      </button>
    </div>
  )
}

/* ---------------------------------------------------------- 修改密码 */
export function ChangePassword() {
  const { user, setUser } = useApp()
  const nav = useNavigate()
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirm, setConfirm] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [done, setDone] = useState(false)

  if (!user) {
    return (
      <div className="container" style={{ maxWidth: 480 }}>
        <div className="card card-pad-lg center">
          <h2 style={{ marginTop: 0 }}>需要登录</h2>
          <Link className="btn btn-primary" to="/login">
            去登录
          </Link>
        </div>
      </div>
    )
  }

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    if (newPw !== confirm) return setErr('两次输入的新密码不一致')
    if (newPw.length < 8) return setErr('新密码至少 8 位')
    setBusy(true)
    try {
      const d = await api.changePassword(oldPw, newPw)
      setUser(d.user)
      setDone(true)
      // 顺手轮换恢复码，让旧码失效
      try {
        const r = await api.regenerateRecovery()
        setNewCode(r.recovery_code)
      } catch (e2) {
        /* 轮换失败不影响改密结果 */
      }
    } catch (ex) {
      setErr(ex.message)
    } finally {
      setBusy(false)
    }
  }

  if (done) {
    return (
      <div className="container" style={{ maxWidth: 560 }}>
        <div className="card card-pad-lg">
          <h2 style={{ marginTop: 0 }}>✅ 密码已更新</h2>
          <p className="muted">
            你的密码已成功修改。为确保安全，我们同时为你轮换了恢复码，
            旧的恢复码已失效。
          </p>
          <RecoveryCodeBox
            code={newCode}
            notice="请保存新的恢复码。旧码已失效。"
          />
          <div className="hero-actions" style={{ marginTop: 20 }}>
            <button className="btn btn-primary" onClick={() => nav('/levels')}>
              去挑战关卡
            </button>
            <button className="btn" onClick={() => nav('/profile')}>
              查看个人主页
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container" style={{ maxWidth: 480 }}>
      <div className="card card-pad-lg">
        <h2 style={{ marginTop: 0 }}>修改密码</h2>
        {user.must_change_password && (
          <div className="notice notice-warn">
            ⚠️ 你正在使用初始密码。为账号安全，请立即修改。
          </div>
        )}
        <form onSubmit={submit} className="mt-16">
          <div className="field">
            <label>当前密码</label>
            <input
              className="input"
              type="password"
              value={oldPw}
              onChange={(e) => setOldPw(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          <div className="field">
            <label>新密码</label>
            <input
              className="input"
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              autoComplete="new-password"
              required
            />
            <StrengthHint pw={newPw} />
          </div>
          <div className="field">
            <label>确认新密码</label>
            <input
              className="input"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              required
            />
            {confirm && confirm !== newPw && (
              <div className="faint" style={{ color: 'var(--danger)' }}>
                两次输入不一致
              </div>
            )}
          </div>
          {err && <div className="notice notice-danger">{err}</div>}
          <button
            className="btn btn-primary btn-block mt-16"
            disabled={busy}
            type="submit"
          >
            {busy ? '提交中…' : '确认修改'}
          </button>
        </form>
        <p className="center mt-16 faint">
          想轮换恢复码？在个人主页可以重新生成。
        </p>
      </div>
    </div>
  )
}

/* ---------------------------------------------------------- 找回密码 */
export function Recover() {
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [code, setCode] = useState('')
  const [newPw, setNewPw] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    if (newPw.length < 8) return setErr('新密码至少 8 位')
    setBusy(true)
    try {
      const d = await api.recover(username.trim(), code.trim(), newPw)
      setResult(d)
    } catch (ex) {
      setErr(ex.message)
    } finally {
      setBusy(false)
    }
  }

  if (result) {
    return (
      <div className="container" style={{ maxWidth: 560 }}>
        <div className="card card-pad-lg">
          <h2 style={{ marginTop: 0 }}>✅ 密码已重置</h2>
          <p className="muted">
            你现在可以用新密码登录了。旧的恢复码已失效，
            这是新的恢复码：
          </p>
          <RecoveryCodeBox code={result.recovery_code} notice={result.recovery_notice} />
          <button
            className="btn btn-primary btn-block mt-16"
            onClick={() => nav('/login')}
          >
            去登录
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container" style={{ maxWidth: 480 }}>
      <div className="card card-pad-lg">
        <h2 style={{ marginTop: 0 }}>找回密码</h2>
        <p className="muted" style={{ fontSize: 14 }}>
          使用注册时生成的<span style={{ color: 'var(--warn)' }}>一次性恢复码</span>
          重置密码。若恢复码已丢失，请联系服务器管理员在本地使用命令行工具重置。
        </p>
        <form onSubmit={submit}>
          <div className="field">
            <label>用户名</label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label>恢复码</label>
            <input
              className="input mono"
              placeholder="XXXX-XXXX-XXXX-XXXX"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label>新密码</label>
            <input
              className="input"
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              autoComplete="new-password"
              required
            />
            <StrengthHint pw={newPw} />
          </div>
          {err && <div className="notice notice-danger">{err}</div>}
          <button
            className="btn btn-primary btn-block mt-16"
            disabled={busy}
            type="submit"
          >
            {busy ? '提交中…' : '重置密码'}
          </button>
        </form>
        <p className="center mt-16 faint">
          想起来了？<Link to="/login">返回登录</Link>
        </p>
      </div>
    </div>
  )
}
