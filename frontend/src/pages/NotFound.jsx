/**
 * ATF Lab - 404
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 */
import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="container">
      <div className="card card-pad-lg center">
        <h1 style={{ fontSize: 46, margin: 0 }}>404</h1>
        <p className="muted">这条路径不存在，也许它被"销毁"了？</p>
        <div className="hero-actions">
          <Link className="btn btn-primary" to="/">
            回到首页
          </Link>
          <Link className="btn" to="/levels">
            去看关卡
          </Link>
        </div>
      </div>
    </div>
  )
}
