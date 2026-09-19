/**
 * ATF Lab - 落地页（产品级 Hero + 特性介绍）
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useApp } from '../store'

const FEATURES = [
  {
    ico: '🎯',
    title: '37 个实战关卡',
    desc: '覆盖 Web 安全、密码学、取证分析、网络渗透、逆向杂项五大方向，难度由浅入深。',
  },
  {
    ico: '🧪',
    title: '受控模拟环境',
    desc: '所有漏洞均为教学构造：不执行系统命令、不读写真实文件、不发起外部请求。',
  },
  {
    ico: '💡',
    title: '分级提示与原理讲解',
    desc: '每关提供至少 3 条递进提示，通关后解锁完整原理复盘与防御方案。',
  },
  {
    ico: '🏆',
    title: '进度同步与排行榜',
    desc: '进度保存在服务端数据库，跨浏览器、跨设备同步，随时与好友比拼排名。',
  },
  {
    ico: '🎖️',
    title: '成就徽章系统',
    desc: '按通关进度与分类完成度自动授予徽章，记录你的每一步成长。',
  },
  {
    ico: '🖥️',
    title: '仿真网络服务',
    desc: '内置仿 FTP / MySQL / Redis / 调试服务，练习 nmap、nc、redis-cli 等工具。',
  },
]

export default function Landing() {
  const { user } = useApp()
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
  }, [])

  const levels = health?.levels ?? '—'
  const users = health?.users ?? '—'

  return (
    <>
      <section className="hero">
        <div className="container">
          <h1>
            在<span className="grad">受控环境</span>中
            <br />
            打磨你的攻防技能
          </h1>
          <p className="lead">
            ATF Lab 是一个面向安全学习者的实战靶场。从信息泄露到完整攻击链，
            每一关都有明确目标、递进提示与原理复盘 —— 全部在安全的沙箱内完成。
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary btn-lg" to="/levels">
              {user ? '继续挑战 →' : '开始挑战 →'}
            </Link>
            {!user && (
              <Link className="btn btn-lg" to="/register">
                免费注册
              </Link>
            )}
            <Link className="btn btn-lg" to="/leaderboard">
              查看排行榜
            </Link>
          </div>
          <div className="hero-note">
            ⚠️ 本站为安全教学靶场，所有"漏洞"均为受控模拟，禁止公网部署
          </div>

          <div className="stat-row">
            <div className="stat">
              <div className="num">{levels}</div>
              <div className="lbl">实战关卡</div>
            </div>
            <div className="stat">
              <div className="num">5</div>
              <div className="lbl">技术方向</div>
            </div>
            <div className="stat">
              <div className="num">{users}</div>
              <div className="lbl">已注册学员</div>
            </div>
            <div className="stat">
              <div className="num">100%</div>
              <div className="lbl">沙箱模拟</div>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2 className="section-title">为什么选择 ATF Lab</h2>
          <p className="section-sub">
            不止是题库，而是一套完整的安全学习平台
          </p>
          <div className="grid grid-3">
            {FEATURES.map((f) => (
              <div className="feature" key={f.title}>
                <div className="ico">{f.ico}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <div className="card card-pad-lg center">
            <h2 style={{ marginTop: 0 }}>准备好了吗？</h2>
            <p className="muted" style={{ maxWidth: 560, margin: '0 auto 22px' }}>
              从第一关「源码里的注释」开始，一步步走到压轴行动。
              进度自动保存，随时可以接着来。
            </p>
            <div className="hero-actions">
              <Link className="btn btn-primary btn-lg" to="/levels">
                进入关卡列表
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
