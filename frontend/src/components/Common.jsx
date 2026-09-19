/**
 * ATF Lab - 通用组件
 *
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useApp } from '../store'
import { DISCLAIMER_LINES, DISCLAIMER_TITLE } from '../disclaimer'

/* ------------------------------------------------------------ 加载/空态 */
export function Loading({ text = '加载中…' }) {
  return (
    <div className="loading">
      <div className="spinner" />
      {text}
    </div>
  )
}

export function Empty({ text = '暂无数据' }) {
  return <div className="empty">{text}</div>
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  return (
    <div className="notice notice-danger" style={{ marginBottom: 16 }}>
      <div className="row-between">
        <span>⚠️ {error.message || String(error)}</span>
        {onRetry && (
          <button className="btn btn-sm" onClick={onRetry}>
            重试
          </button>
        )}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------ 难度星级 */
export function Stars({ level }) {
  return (
    <span className="diff" title={`难度 ${level}/5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= level ? '' : 'off'}>
          ★
        </span>
      ))}
    </span>
  )
}

/* ------------------------------------------------------------ 免责声明弹窗 */
/**
 * 首次访问时的强制确认弹窗。
 * 用户必须点击"我已阅读并同意"才能进入站点。
 */
export function DisclaimerModal({ onAccept }) {
  const [checked, setChecked] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  return (
    <div className="modal-mask" role="dialog" aria-modal="true">
      <div className="modal">
        <h2>{DISCLAIMER_TITLE}</h2>
        <p className="muted" style={{ marginTop: 0 }}>
          在进入 ATF Lab 之前，请先阅读并确认以下声明。
        </p>

        <div
          className="disclaimer-body"
          onScroll={(e) => {
            const el = e.currentTarget
            if (el.scrollTop + el.clientHeight >= el.scrollHeight - 8) setScrolled(true)
          }}
        >
          {DISCLAIMER_LINES.map((line, i) => (
            <p key={i} style={{ margin: i === 0 ? 0 : '10px 0 0' }}>
              {line.split('**').map((seg, j) =>
                j % 2 === 1 ? <b key={j}>{seg}</b> : <span key={j}>{seg}</span>
              )}
            </p>
          ))}
          <p style={{ margin: '14px 0 0' }}>
            <b>本项目为安全教学靶场。</b>所有"漏洞"均为受控模拟，
            不包含任何可危害真实系统的能力：不执行系统命令、不读写真实文件、
            不发起外部网络请求、不代理任何连接。请仅将所学技术用于
            <b>获得明确授权</b>的目标。
          </p>
        </div>

        <label className="row" style={{ cursor: 'pointer', fontSize: 14 }}>
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
          />
          我已阅读、理解并同意上述声明
        </label>

        <div className="modal-actions">
          <button
            className="btn"
            onClick={() => {
              // 拒绝则离开本站
              window.location.href = 'about:blank'
            }}
          >
            不同意，离开
          </button>
          <button
            className="btn btn-primary"
            disabled={!checked}
            onClick={onAccept}
            title={checked ? '' : '请先勾选同意'}
          >
            同意并进入
          </button>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------ 页脚（强制含免责声明） */
export function Footer() {
  const year = new Date().getFullYear()
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-disclaimer">
          <div style={{ fontWeight: 700, marginBottom: 6 }}>
            {DISCLAIMER_TITLE}
          </div>
          {DISCLAIMER_LINES.map((line, i) => (
            <div key={i}>
              {line.split('**').map((seg, j) =>
                j % 2 === 1 ? <b key={j}>{seg}</b> : <span key={j}>{seg}</span>
              )}
            </div>
          ))}
        </div>
        <div className="footer-meta">
          <span>
            ATF Lab · 安全教学靶场 · 所有漏洞均为受控模拟
          </span>
          <span>
            <Link to="/about">关于</Link> · <Link to="/docs">API 文档</Link> ·{' '}
            © {year}
          </span>
        </div>
      </div>
    </footer>
  )
}

/* ------------------------------------------------------------ 顶部导航 */
export function Nav() {
  const { user, logout, theme, toggleTheme, mode, setMode } = useApp()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)

  const go = (p) => {
    setOpen(false)
    nav(p)
  }

  return (
    <nav className="nav">
      <div className="container nav-inner">
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          🛡️ ATF Lab
          <span className="brand-badge">教学靶场</span>
        </Link>

        {/* 模式切换：显式区分"展示模式"与"靶场模式"，不做伪装 */}
        <div className="mode-switch" title="切换站点模式">
          <button
            className={mode === 'site' ? 'on' : ''}
            onClick={() => {
              setMode('site')
              go('/')
            }}
          >
            展示模式
          </button>
          <button
            className={mode === 'lab' ? 'on lab' : 'lab'}
            onClick={() => {
              setMode('lab')
              go('/lab')
            }}
          >
            CTF 靶场
          </button>
        </div>

        <button
          className="btn btn-sm btn-ghost"
          onClick={() => setOpen((v) => !v)}
          style={{ display: 'none' }}
          aria-hidden="true"
        />

        <div className="nav-links">
          <Link className="nav-link" to="/levels">
            关卡
          </Link>
          <Link className="nav-link" to="/leaderboard">
            排行榜
          </Link>
          {user && (
            <Link className="nav-link" to="/profile">
              我的
            </Link>
          )}
          {user && user.role === 'admin' && (
            <Link className="nav-link" to="/admin">
              管理
            </Link>
          )}
          <button
            className="btn btn-sm btn-ghost"
            onClick={toggleTheme}
            title="切换深浅色主题"
          >
            {theme === 'dark' ? '🌙' : '☀️'}
          </button>
          {user ? (
            <>
              <span className="faint" style={{ padding: '0 4px' }}>
                {user.username}
                {user.role === 'admin' ? ' · 管理员' : ''}
              </span>
              <button
                className="btn btn-sm"
                onClick={() => {
                  logout()
                  nav('/')
                }}
              >
                退出
              </button>
            </>
          ) : (
            <>
              <Link className="btn btn-sm" to="/login">
                登录
              </Link>
              <Link className="btn btn-sm btn-primary" to="/register">
                注册
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

/* ------------------------------------------------------------ 关卡页底部小字（强制要求） */
export function LevelDisclaimer() {
  return (
    <div className="level-disclaimer">
      ⚠️ 本关漏洞为教学模拟，禁止用于未授权测试
    </div>
  )
}
