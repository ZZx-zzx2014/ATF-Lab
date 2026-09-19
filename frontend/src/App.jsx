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
import Profile from './pages/Profile'
import Leaderboard from './pages/Leaderboard'
import Admin from './pages/Admin'
import About from './pages/About'
import ApiDocs from './pages/ApiDocs'
import NotFound from './pages/NotFound'

const ACCEPT_KEY = 'atf_disclaimer_accepted'

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
