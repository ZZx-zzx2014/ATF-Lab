/**
 * ATF Lab - API 文档页（站内速查）
 *
 * ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
 * 完整的交互式文档由 FastAPI 提供，见 /docs（Swagger UI）与 /redoc。
 */

const GROUPS = [
  {
    title: '系统',
    items: [
      ['GET', '/api/v1/health', '健康检查（含关卡数、netlab 状态）', '无需认证'],
    ],
  },
  {
    title: '认证',
    items: [
      ['POST', '/api/v1/auth/register', '注册新用户（首个用户自动成为管理员）', '无需认证'],
      ['POST', '/api/v1/auth/login', '登录，返回 JWT', '无需认证'],
      ['GET', '/api/v1/auth/me', '获取当前登录用户信息', '需 Bearer Token'],
    ],
  },
  {
    title: '关卡',
    items: [
      ['GET', '/api/v1/levels', '关卡列表，支持 category / difficulty / keyword 筛选', '可选认证'],
      ['GET', '/api/v1/levels/{id}', '关卡详情（含已解锁提示）', '可选认证'],
      ['POST', '/api/v1/levels/{id}/submit', '提交 flag 校验', '需登录'],
      ['POST', '/api/v1/levels/{id}/hint/{index}', '解锁一条提示', '需登录'],
    ],
  },
  {
    title: '用户与排行',
    items: [
      ['GET', '/api/v1/leaderboard', '排行榜', '可选认证'],
      ['GET', '/api/v1/me/profile', '我的主页（含徽章）', '需登录'],
      ['GET', '/api/v1/users/{username}', '查看他人公开主页', '无需认证'],
      ['GET', '/api/v1/progress', '我的全部通关记录', '需登录'],
    ],
  },
  {
    title: '管理后台',
    items: [
      ['GET', '/api/v1/admin/stats', '答题统计', '需管理员'],
      ['GET', '/api/v1/admin/levels', '关卡列表（含 flag 明文）', '需管理员'],
      ['POST', '/api/v1/admin/levels', '新增或覆盖关卡', '需管理员'],
      ['DELETE', '/api/v1/admin/levels/{id}', '删除自定义关卡', '需管理员'],
      ['GET', '/api/v1/admin/users', '用户列表', '需管理员'],
    ],
  },
  {
    title: '压轴关 L37',
    items: [
      ['GET', '/api/v1/finale/briefing', '任务简报', '无需认证'],
      ['GET', '/api/v1/finale/progress', '我的阶段进度', '可选认证'],
      ['GET', '/api/v1/finale/legacy/employees', '阶段1：泄露的员工名录', '可选认证'],
      ['POST', '/api/v1/finale/login', '阶段2：门户登录（存在注入）', '可选认证'],
      ['GET', '/api/v1/finale/admin', '阶段3：管理员面板（需 admin JWT）', '可选认证'],
      ['POST', '/api/v1/finale/health-check', '阶段4：健康检查（SSRF）', '可选认证'],
      ['POST', '/api/v1/finale/archive/search', '阶段5：档案检索（XXE）', '可选认证'],
      ['GET', '/api/v1/finale/archive/destroy/preview', '阶段6：销毁预览', '无需认证'],
      ['POST', '/api/v1/finale/archive/destroy', '阶段6：执行销毁', '需登录'],
    ],
  },
]

const SAMPLE = `{
  "code": 0,
  "message": "ok",
  "data": {
    "id": "L01",
    "name": "源码里的注释",
    "category": "Web 安全",
    "difficulty": 1,
    "points": 50,
    "solved": false,
    "hints": [
      { "index": 0, "text": "...", "unlocked": false }
    ],
    "writeup": null
  }
}`

const ERRORS = [
  [0, '成功', 'HTTP 200'],
  [1001, '参数校验失败', 'HTTP 400'],
  [1002, '未登录 / token 无效', 'HTTP 401'],
  [1003, '无权限', 'HTTP 403'],
  [1004, '资源不存在', 'HTTP 404'],
  [1005, '资源冲突（用户名已占用）', 'HTTP 409'],
  [1006, '请求过于频繁', 'HTTP 429'],
  [1007, 'flag 错误（业务失败）', 'HTTP 200'],
  [1008, '关卡未解锁', 'HTTP 403'],
  [5000, '服务器内部错误', 'HTTP 500'],
]

function Method({ m }) {
  const color =
    m === 'GET'
      ? 'var(--success)'
      : m === 'POST'
        ? 'var(--accent)'
        : 'var(--danger)'
  return (
    <span className="mono" style={{ color, fontWeight: 700, fontSize: 12 }}>
      {m}
    </span>
  )
}

export default function ApiDocs() {
  return (
    <div className="container" style={{ maxWidth: 980 }}>
      <h1 style={{ fontSize: 25 }}>API 文档</h1>
      <p className="muted">
        后端提供纯 REST API，所有接口统一返回{' '}
        <code>{'{ code, message, data }'}</code>，其中 <code>code === 0</code>{' '}
        表示成功。前端全部数据交互都走这些接口 —— 打开浏览器 Network 面板即可验证。
      </p>

      <div className="notice notice-info" style={{ marginBottom: 20 }}>
        📘 交互式文档（可直接在线调试）：
        <a href="/api/docs" target="_blank" rel="noreferrer" style={{ marginLeft: 6 }}>
          /api/docs (Swagger UI)
        </a>
        <span className="muted"> · </span>
        <a href="/api/redoc" target="_blank" rel="noreferrer">
          /api/redoc
        </a>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <b>认证方式</b>
        <p className="muted" style={{ marginBottom: 6 }}>
          除标注"无需认证"的接口外，请在请求头携带 JWT：
        </p>
        <pre>{`Authorization: Bearer <token>\n\n# 示例\ncurl -H "Authorization: Bearer $TOKEN" \\\n     http://127.0.0.1:8899/api/v1/levels`}</pre>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <b>成功响应示例</b>
        <pre>{SAMPLE}</pre>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <b>错误码表</b>
        <table className="table mt-16">
          <thead>
            <tr>
              <th style={{ width: 90 }}>code</th>
              <th>含义</th>
              <th style={{ width: 120 }}>HTTP</th>
            </tr>
          </thead>
          <tbody>
            {ERRORS.map(([c, mean, http]) => (
              <tr key={c}>
                <td className="mono">{c}</td>
                <td>{mean}</td>
                <td className="faint">{http}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {GROUPS.map((g) => (
        <div className="card" key={g.title} style={{ marginBottom: 20 }}>
          <b>{g.title}</b>
          <table className="table mt-16">
            <thead>
              <tr>
                <th style={{ width: 70 }}>方法</th>
                <th>路径</th>
                <th>说明</th>
                <th style={{ width: 130 }}>认证</th>
              </tr>
            </thead>
            <tbody>
              {g.items.map(([m, p, d, a]) => (
                <tr key={m + p}>
                  <td>
                    <Method m={m} />
                  </td>
                  <td className="mono" style={{ fontSize: 12.5 }}>
                    {p}
                  </td>
                  <td>{d}</td>
                  <td className="faint">{a}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      <div className="notice notice-warn">
        ⚠️ 压轴关与模拟交互类接口返回的都是<b>受控模拟数据</b>，
        响应体中会带 <code>_simulation: true</code> 标记。
        它们不对应任何真实系统，也不具备任何真实攻击能力。
      </div>
    </div>
  )
}
