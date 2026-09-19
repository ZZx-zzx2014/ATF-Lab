/**
 * ATF Lab - 登录 / 注册
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useApp } from '../store'

export function Login() {
  const { login } = useApp()
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    setBusy(true)
    try {
      await login(username.trim(), password)
      nav('/levels')
    } catch (ex) {
      setErr(ex.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container" style={{ maxWidth: 440 }}>
      <div className="card card-pad-lg">
        <h1 style={{ marginTop: 0, fontSize: 23 }}>登录</h1>
        <p className="muted" style={{ fontSize: 14 }}>
          登录后进度会保存到服务器，跨浏览器、跨设备同步。
        </p>
        <form onSubmit={submit}>
          <div className="field">
            <label>用户名</label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div className="field">
            <label>密码</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {err && <div className="notice notice-danger">{err}</div>}
          <button
            className="btn btn-primary btn-block mt-16"
            disabled={busy}
            type="submit"
          >
            {busy ? '登录中…' : '登录'}
          </button>
        </form>
        <p className="center mt-16 faint">
          还没有账号？<Link to="/register">立即注册</Link>
        </p>
        <p className="center faint" style={{ marginTop: 4 }}>
          忘记密码？<Link to="/recover">使用恢复码重置</Link>
        </p>
      </div>
    </div>
  )
}

export function Register() {
  const { register } = useApp()
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [email, setEmail] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    if (password !== confirm) {
      setErr('两次输入的密码不一致')
      return
    }
    if (password.length < 6) {
      setErr('密码至少 6 位')
      return
    }
    setBusy(true)
    try {
      const d = await register(username.trim(), password, email.trim())
      nav('/levels')
      if (d.is_first_user) {
        // 首个用户自动成为管理员，这里不做额外提示，避免打断流程
      }
    } catch (ex) {
      setErr(ex.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container" style={{ maxWidth: 440 }}>
      <div className="card card-pad-lg">
        <h1 style={{ marginTop: 0, fontSize: 23 }}>注册</h1>
        <p className="muted" style={{ fontSize: 14 }}>
          创建账号后即可开始挑战，进度自动保存。
        </p>
        <form onSubmit={submit}>
          <div className="field">
            <label>用户名</label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="3-24 位字母、数字、下划线或连字符"
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
            />
          </div>
          <div className="field">
            <label>密码</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="至少 6 位"
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

export default Login
