/**
 * ATF Lab - 关于页
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { Link } from 'react-router-dom'
import {
  DISCLAIMER_LINES, DISCLAIMER_TITLE,
} from '../disclaimer'

export default function About() {
  return (
    <div className="container" style={{ maxWidth: 840 }}>
      <h1 style={{ fontSize: 25 }}>关于 ATF Lab</h1>

      <div
        className="disclaimer-body"
        style={{ borderLeftColor: 'var(--warn)', background: 'var(--warn-soft)' }}
      >
        <div style={{ fontWeight: 700, marginBottom: 6 }}>{DISCLAIMER_TITLE}</div>
        {DISCLAIMER_LINES.map((line, i) => (
          <div key={i}>
            {line.split('**').map((seg, j) =>
              j % 2 === 1 ? <b key={j}>{seg}</b> : <span key={j}>{seg}</span>
            )}
          </div>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>这是什么</h3>
        <p className="muted mb-0">
          ATF Lab 是一个面向安全学习者的实战靶场平台。它包含 37 个关卡，
          覆盖 Web 安全、密码学、取证分析、网络渗透、逆向与杂项五个方向，
          以及一个串联多种技术的压轴行动关卡。
        </p>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>安全边界（重要）</h3>
        <p className="muted">
          本项目的所有"漏洞"都是<b>为教学设计而刻意实现的模拟逻辑</b>，
          不具备任何危害真实系统的能力：
        </p>
        <ul className="muted" style={{ marginBottom: 0 }}>
          <li>不执行任何系统命令（无 subprocess / os.system）</li>
          <li>不读写真实文件系统（路径穿越作用于内存中的虚拟文件树）</li>
          <li>不发起任何外部网络请求（SSRF 只打内置模拟端点）</li>
          <li>不调用真实的反序列化函数（无 pickle / yaml.load）</li>
          <li>仿真网络服务只返回预置静态文本，仅监听回环地址</li>
          <li>
            压轴关的"数据销毁"只更新模拟数据表
            <code> sim_archive_records</code> 的状态字段
          </li>
        </ul>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>技术栈</h3>
        <p className="muted mb-0">
          后端 FastAPI + SQLite + PyJWT（统一 JSON 响应格式，REST API）；
          前端 React + Vite（独立 SPA，全部数据经 <code>/api/v1/*</code> 获取）。
          前后端可同域托管，也可分离部署。
        </p>
      </div>

      <div className="hero-actions" style={{ justifyContent: 'flex-start' }}>
        <Link className="btn btn-primary" to="/levels">
          开始挑战
        </Link>
        <Link className="btn" to="/docs">
          API 文档
        </Link>
      </div>
    </div>
  )
}
