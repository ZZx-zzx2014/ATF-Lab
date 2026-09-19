/**
 * ATF Lab - 注册页
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 *
 * 注册成功后会展示一次性恢复码，用于日后忘记密码时自助重置。
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useApp } from '../store'
import { RecoveryCodeBox } from './Account'

export default function Register() {
  const { register } = useApp()
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [email, setEmail] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [recovery, setRecovery] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    if (password !== confirm) {
      setErr('两次输入的密码不一致')
      return
    }
    if (password.length < 8) {
      setErr('密码至少 8 位')
      return
    }
    if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      setErr('密码需同时包含字母和数字')
      return
    }
    setBusy(true)
    try {
      const d = await register(username.trim(), password, email.trim())
      // 先展示恢复码，用户确认后再进入平台
      if (d.recovery_code) {
        setRecovery(d)
      } else {
        nav('/levels')
      }
    } catch (ex) {
      setErr(ex.message)
    } finally {
      setBusy(false)
    }
  }

  // 注册成功：展示恢复码
  if (recovery) {
    return (
      <div className="container" style={{ maxWidth: 560 }}>
        <div className="card card-pad-lg">
          <h2 style={{ marginTop: 0 }}>🎉 注册成功</h2>
          <p className="muted">
            账号 <b>{recovery.user.username}</b> 已创建。
            {recovery.is_first_user && (
              <span>
                {' '}
                你是本站第一个用户，已自动获得<b>管理员权限</b>。
              </span>
            )}
          </p>

          <RecoveryCodeBox
            code={recovery.recovery_code}
            notice={recovery.recovery_notice}
          />

          <div className="notice notice-info" style={{ marginTop: 14 }}>
            💡 请把恢复码保存到密码管理器。忘记密码时，它是在登录页自助重置的
            唯一凭据；用一次即失效，重置后会下发新的。
          </div>

          <button
            className="btn btn-primary btn-block mt-16"
            onClick={() => nav('/levels')}
          >
            我已保存，开始挑战 →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container" style={{ maxWidth: 440 }}>
      <div className="card card-pad-lg">
        <h1 style={{ marginTop: 0, fontSize: 23 }}>注册</h1>
        <p className="muted" style={{ fontSize: 14 }}>
          创建账号后即可开始挑战，进度自动保存到服务器。
        </p>
        <form onSubmit={submit}>
          <div className="field">
            <label>用户名</label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="3-24 位字母、数字、下划线或连字符"
              autoComplete="username"
              required
            />
          </div>
          <div className="field">
            <label>邮箱（可选）</label>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>
          <div className="field">
            <label>密码</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="至少 8 位，需含字母和数字"
              autoComplete="new-password"
              required
            />
          </div>
          <div className="field">
            <label>确认密码</label>
            <input
              className="input"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>
          {err && <div className="notice notice-danger">{err}</div>}
          <button
            className="btn btn-primary btn-block mt-16"
            disabled={busy}
            type="submit"
          >
            {busy ? '注册中…' : '创建账号'}
          </button>
        </form>
        <p className="center mt-16 faint">
          已有账号？<Link to="/login">去登录</Link>
        </p>
      </div>
    </div>
  )
}
