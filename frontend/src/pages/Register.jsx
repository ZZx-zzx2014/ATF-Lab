/**
 * ATF Lab - 注册页
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useApp } from '../store'

export default function Register() {
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
      await register(username.trim(), password, email.trim())
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
              placeholder="至少 6 位"
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
        <div className="faint center mt-16">
          提示：本平台<b>第一个注册的用户</b>会自动成为管理员，可访问管理后台。
        </div>
      </div>
    </div>
  )
}
