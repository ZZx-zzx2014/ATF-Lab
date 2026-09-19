/**
 * ATF Lab - 应用入口与路由
 *
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 * 前端为独立 SPA，所有数据均通过 /api/v1/* 获取。
 */
import { useEffect, useState } from 'react'
import {
  BrowserRouter, Navigate, Route, Routes, useLocation,
} from 'react-router-dom'

import { AppProvider, useApp } from './store'
import { DisclaimerModal, Footer, Nav } from './components/Common'

import Landing from './pages/Landing'
import Levels from './pages/Levels'
import LevelDetail from './pages/LevelDetail'
import Finale from './pages/Finale'
import Login from './pages/Login'
import Register from './pages/Register'
import { ChangePassword, Recover } from './pages/Account'
import Profile from './pages/Profile'
import Leaderboard from './pages/Leaderboard'
import Admin from './pages/Admin'
import About from './pages/About'
import ApiDocs from './pages/ApiDocs'
import NotFound from './pages/NotFound'

const ACCEPT_KEY = 'atf_disclaimer_accepted'

/**
 * 初始密码提醒横幅。
 *
 * 管理员由部署流程自动创建时会被标记 must_change_password，
 * 在改密之前，站内所有页面顶部都会持续显示这条红色警示。
 */
function PasswordWarning() {
  const { user } = useApp()
  if (!user || !user.must_change_password) return null
  return (
    <div
      style={{
        background: 'var(--danger)',
        color: '#fff',
        padding: '9px 0',
        fontSize: 14,
      }}
    >
      <div className="container row-between">
        <span>
          🔐 <b>安全提醒：</b>你仍在使用<b>初始密码</b>，请立即修改后再使用平台。
        </span>
        <a
          href="/change-password"
          className="btn btn-sm"
          style={{
            background: '#fff',
            color: 'var(--danger)',
            borderColor: '#fff',
            fontWeight: 700,
          }}
        >
          立即修改
        </a>
      </div>
    </div>
  )
}

function Shell() {
  const { authReady, mode, setMode } = useApp()
  const loc = useLocation()
  const [accepted, setAccepted] = useState(() => {
    try {
      return localStorage.getItem(ACCEPT_KEY) === 'yes'
    } catch (e) {
      return false
    }
  })

  // 路由与模式保持一致：/lab 与 /finale 属于靶场模式
  useEffect(() => {
    const isLab = loc.pathname.startsWith('/lab') || loc.pathname.startsWith('/finale')
    if (isLab && mode !== 'lab') setMode('lab')
    if (!isLab && mode === 'lab' && loc.pathname === '/') setMode('site')
  }, [loc.pathname, mode, setMode])

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [loc.pathname])

  const accept = () => {
    try {
      localStorage.setItem(ACCEPT_KEY, 'yes')
    } catch (e) {
      /* 忽略 */
    }
    setAccepted(true)
  }

  // 首访必须确认免责声明后才进入
  if (!accepted) return <DisclaimerModal onAccept={accept} />

  return (
    <div className="app">
      <Nav />
      <PasswordWarning />
      <main className="page">
        {!authReady ? (
          <div className="loading">
            <div className="spinner" />
            正在恢复登录状态…
          </div>
        ) : (
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/levels" element={<Levels />} />
            <Route path="/levels/:id" element={<LevelDetail />} />
            <Route path="/lab" element={<Levels labMode />} />
            <Route path="/lab/:id" element={<LevelDetail />} />
            <Route path="/finale" element={<Finale />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/recover" element={<Recover />} />
            <Route path="/change-password" element={<ChangePassword />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="/about" element={<About />} />
            <Route path="/docs" element={<ApiDocs />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        )}
      </main>
      <Footer />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Shell />
      </AppProvider>
    </BrowserRouter>
  )
}
