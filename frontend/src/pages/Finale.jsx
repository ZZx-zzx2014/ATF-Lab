/**
 * ATF Lab - 压轴关 L37「REAPER 行动」
 *
 * ⚠️⚠️ 仅供教学演示（CONTROLLED SIMULATION）⚠️⚠️
 * 本页面呈现一条六阶段模拟攻击链。所有操作均为教学模拟：
 * 不执行系统命令、不读写真实文件、不发起外部请求、
 * 阶段 6 的"销毁"只作用于模拟数据表 sim_archive_records。
 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useApp } from '../store'
import { ErrorBox, LevelDisclaimer, Loading } from '../components/Common'

const STAGE_META = [
  { n: 1, title: '员工名录泄露', tech: '信息泄露', hint: '旧接口未下线' },
  { n: 2, title: 'SQL 注入绕过', tech: 'SQL 注入', hint: 'OR 恒真条件' },
  { n: 3, title: 'JWT 弱密钥提权', tech: 'JWT 伪造', hint: '密钥就是 secret' },
  { n: 4, title: 'SSRF 探测内网', tech: 'SSRF', hint: '健康检查功能' },
  { n: 5, title: 'XXE 读取档案', tech: 'XXE', hint: '外部实体' },
  { n: 6, title: '销毁 REAPER 档案', tech: '数据销毁', hint: '需要销毁令牌' },
]

function Term({ children, title = '输出' }) {
  if (!children) return null
  return (
    <>
      <div className="faint" style={{ margin: '12px 0 6px' }}>
        {title}
      </div>
      <pre className="terminal">
        {typeof children === 'string'
          ? children
          : JSON.stringify(children, null, 2)}
      </pre>
    </>
  )
}

export default function Finale() {
  const nav = useNavigate()
  const { user } = useApp()

  const [brief, setBrief] = useState(null)
  const [prog, setProg] = useState(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)

  // 各阶段产物（保存在组件状态，方便串联下一阶段）
  const [out1, setOut1] = useState(null)
  const [out2, setOut2] = useState(null)
  const [out3, setOut3] = useState(null)
  const [out4, setOut4] = useState(null)
  const [out5, setOut5] = useState(null)
  const [out6, setOut6] = useState(null)

  const [loginUser, setLoginUser] = useState("' OR '1'='1")
  const [adminJwt, setAdminJwt] = useState('')
  const [ssrfUrl, setSsrfUrl] = useState('http://internal.helios-sim.invalid/archive')
  const [xxeXml, setXxeXml] = useState(
    '<?xml version="1.0"?>\n<!DOCTYPE r [\n  <!ENTITY x SYSTEM "file:///etc/helios/archive.conf">\n]>\n<r>&x;</r>'
  )
  const [confirmText, setConfirmText] = useState('')
  const [shot, setShot] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setErr(null)
    try {
      const [b, p] = await Promise.all([
        api.finaleBriefing(),
        api.finaleProgress(),
      ])
      setBrief(b)
      setProg(p)
    } catch (e) {
      setErr(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const wrap = async (fn) => {
    setBusy(true)
    setErr(null)
    try {
      return await fn()
    } catch (e) {
      setErr(e)
      return null
    } finally {
      setBusy(false)
    }
  }

  const s1 = () =>
    wrap(async () => {
      const d = await api.finaleEmployees()
      setOut1(d)
      await refresh()
    })
  const s2 = () =>
    wrap(async () => {
      const d = await api.finaleLogin(loginUser, 'anything')
      setOut2(d)
      if (d.employee_jwt) setAdminJwt(d.employee_jwt)
      await refresh()
    })
  const s3 = () =>
    wrap(async () => {
      const d = await api.finaleAdmin(adminJwt)
      setOut3(d)
      await refresh()
    })
  const s4 = () =>
    wrap(async () => {
      const d = await api.finaleHealthCheck(ssrfUrl)
      setOut4(d)
      await refresh()
    })
  const s5 = () =>
    wrap(async () => {
      const key = out4?.body?.archive_key || ''
      const d = await api.finaleArchiveSearch(xxeXml, key)
      setOut5(d)
      await refresh()
    })
  const s6 = () =>
    wrap(async () => {
      if (!user) {
        setErr(new Error('阶段 6 需要登录后才能执行（操作会记录到你的进度）'))
        return
      }
      const d = await api.finaleDestroy(
        out5?.destruction_token || '',
        confirmText
      )
      setOut6(d)
      await refresh()
    })

  const refresh = async () => {
    try {
      setProg(await api.finaleProgress())
    } catch (e) {
      /* 忽略 */
    }
  }

  const submitFinalFlag = () =>
    wrap(async () => {
      const d = await api.submitFlag('L37', 'flag{reaper_archive_destroyed}')
      setShot(d)
      await refresh()
    })

  if (loading) return <Loading text="正在接入 Helios 门户…" />

  const destroyed = prog?.destroyed
  const done = prog?.completed_stages || 0

  return (
    <div className="container">
      <Link className="faint" to="/levels">
        ← 返回关卡列表
      </Link>

      {/* 简报 */}
      <div
        className="card card-pad-lg"
        style={{
          margin: '14px 0 20px',
          borderColor: 'var(--purple)',
          background:
            'linear-gradient(150deg, rgba(167,139,250,0.09), var(--bg-card))',
        }}
      >
        <div className="row-between">
          <div>
            <div className="row" style={{ gap: 10 }}>
              <span className="tag tag-purple">压轴行动</span>
              <span className="faint">代号 {brief?.codename}</span>
            </div>
            <h1 style={{ margin: '10px 0 6px', fontSize: 26 }}>
              🎬 REAPER 行动
            </h1>
            <p className="muted" style={{ maxWidth: 720, marginBottom: 0 }}>
              {brief?.mission}
            </p>
          </div>
          <div className="center">
            <div style={{ fontSize: 27, fontWeight: 800, color: 'var(--purple)' }}>
              {done}/6
            </div>
            <div className="faint">阶段完成</div>
          </div>
        </div>
        <div className="progress-bar mt-16">
          <div style={{ width: `${(done / 6) * 100}%` }} />
        </div>
        <div className="notice notice-info mt-16">{brief?.disclaimer}</div>
      </div>

      <ErrorBox error={err} />

      {/* 阶段导航 */}
      <div className="stage-list" style={{ marginBottom: 20 }}>
        {STAGE_META.map((s) => {
          const reached = prog?.stages?.find((x) => x.stage === s.n)?.reached
          return (
            <div key={s.n} className={'stage-item' + (reached ? ' done' : '')}>
              <span className="stage-num">{reached ? '✓' : s.n}</span>
              <b>{s.title}</b>
              <span className="tag">{s.tech}</span>
              <span className="spacer" />
              <span className="faint">{s.hint}</span>
            </div>
          )
        })}
      </div>

      <div className="detail-grid">
        <div>
          {/* 阶段 1 */}
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="row-between">
              <b>阶段 1 · 员工名录泄露</b>
              <span className="tag tag-accent">信息泄露</span>
            </div>
            <p className="muted" style={{ fontSize: 13.5 }}>
              门户改版后，旧接口 <code>/api/v1/finale/legacy/employees</code>{' '}
              忘记下线，仍然返回完整员工名录。
            </p>
            <button className="btn btn-primary" onClick={s1} disabled={busy}>
              访问旧接口
            </button>
            <Term title="响应">{out1}</Term>
            {out1 && (
              <div className="notice notice-success" style={{ marginTop: 10 }}>
                拿到员工工号 <b>{out1.employees?.[0]?.employee_id}</b>，可用于阶段 2。
              </div>
            )}
          </div>

          {/* 阶段 2 */}
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="row-between">
              <b>阶段 2 · SQL 注入绕过登录</b>
              <span className="tag tag-accent">SQL 注入</span>
            </div>
            <p className="muted" style={{ fontSize: 13.5 }}>
              登录接口把输入拼进查询，用恒真条件即可绕过认证。
            </p>
            <input
              className="input"
              style={{ fontFamily: 'var(--mono)', fontSize: 13 }}
              value={loginUser}
              onChange={(e) => setLoginUser(e.target.value)}
              placeholder="用户名 / 注入 payload"
            />
            <button
              className="btn btn-primary mt-16"
              onClick={s2}
              disabled={busy}
            >
              尝试登录
            </button>
            <Term title="响应">{out2}</Term>
            {out2?.employee_jwt && (
              <div className="notice notice-success" style={{ marginTop: 10 }}>
                拿到员工 JWT。它的 payload 可以 Base64URL 解码查看，
                注意 <code>role</code> 字段。
              </div>
            )}
          </div>

          {/* 阶段 3 */}
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="row-between">
              <b>阶段 3 · JWT 弱密钥提权</b>
              <span className="tag tag-accent">JWT 伪造</span>
            </div>
            <p className="muted" style={{ fontSize: 13.5 }}>
              token 用极弱的密钥签发（就是 <code>secret</code> 这个词）。
              把 payload 里的 <code>role</code> 改成 <code>admin</code>，用该密钥重新签名。
            </p>
            <textarea
              className="textarea"
              value={adminJwt}
              onChange={(e) => setAdminJwt(e.target.value)}
              placeholder="粘贴伪造好的 admin JWT"
            />
            <button
              className="btn btn-primary mt-16"
              onClick={s3}
              disabled={busy || !adminJwt.trim()}
            >
              以管理员身份访问面板
            </button>
            <Term title="响应">{out3}</Term>
            <div className="notice notice-warn" style={{ marginTop: 10 }}>
              ⚠️ 教学说明：本关的弱密钥与平台真实 JWT 体系<b>完全隔离</b>。
              伪造出的 token 只能通过本关的模拟校验，无法提升平台任何真实权限。
            </div>
          </div>

          {/* 阶段 4 */}
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="row-between">
              <b>阶段 4 · SSRF 探测内网</b>
              <span className="tag tag-accent">SSRF</span>
            </div>
            <p className="muted" style={{ fontSize: 13.5 }}>
              管理员面板的「服务健康检查」接受任意 URL。用它访问内部档案服务。
            </p>
            <input
              className="input"
              style={{ fontFamily: 'var(--mono)', fontSize: 13 }}
              value={ssrfUrl}
              onChange={(e) => setSsrfUrl(e.target.value)}
            />
            <button
              className="btn btn-primary mt-16"
              onClick={s4}
              disabled={busy}
            >
              执行健康检查
            </button>
            <Term title="响应">{out4}</Term>
            <div className="notice notice-warn" style={{ marginTop: 10 }}>
              ⚠️ 教学说明：本沙箱<b>不发起任何真实网络请求</b>。
              只有内置模拟端点会返回预置内容，外部地址一律被拒绝。
            </div>
          </div>

          {/* 阶段 5 */}
          <div className="card" style={{ marginBottom: 14 }}>
            <div className="row-between">
              <b>阶段 5 · XXE 读取档案索引</b>
              <span className="tag tag-accent">XXE</span>
            </div>
            <p className="muted" style={{ fontSize: 13.5 }}>
              档案检索接口接受 XML 且允许外部实体。构造 DOCTYPE 读取服务端文件。
            </p>
            <textarea
              className="textarea"
              value={xxeXml}
              onChange={(e) => setXxeXml(e.target.value)}
            />
            <div className="faint" style={{ marginTop: 6 }}>
              archive_key 会自动取自阶段 4 的结果：
              <code>{out4?.body?.archive_key || '（尚未获取）'}</code>
            </div>
            <button
              className="btn btn-primary mt-16"
              onClick={s5}
              disabled={busy || !out4}
            >
              提交 XML 检索
            </button>
            <Term title="响应">{out5}</Term>
          </div>

          {/* 阶段 6 */}
          <div
            className="card"
            style={{ borderColor: destroyed ? 'var(--success)' : 'var(--danger)' }}
          >
            <div className="row-between">
              <b>阶段 6 · 销毁 REAPER 档案</b>
              <span className="tag tag-danger">数据销毁</span>
            </div>
            <p className="muted" style={{ fontSize: 13.5 }}>
              拿到销毁令牌后，执行档案销毁。需要二次确认短语。
            </p>

            {destroyed ? (
              <div className="notice notice-success">
                ✅ PROJECT_REAPER 已在教学模拟数据表中被标记为 DESTROYED。
              </div>
            ) : (
              <>
                <div className="notice notice-danger">
                  ⚠️ 此操作将把 PROJECT_REAPER 标记为已销毁。
                  本次操作作用于教学模拟数据表，<b>不会影响任何真实数据</b>。
                </div>
                <div className="faint" style={{ margin: '12px 0 6px' }}>
                  请输入确认短语 <code>CONFIRM DESTRUCTION</code>：
                </div>
                <input
                  className="input"
                  style={{ fontFamily: 'var(--mono)' }}
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder="CONFIRM DESTRUCTION"
                />
                <button
                  className="btn btn-danger mt-16"
                  onClick={s6}
                  disabled={busy || !out5 || !user}
                >
                  🔥 执行销毁
                </button>
                {!user && (
                  <div className="faint" style={{ marginTop: 8 }}>
                    阶段 6 需要 <Link to="/login">登录</Link> 后执行。
                  </div>
                )}
              </>
            )}
            <Term title="响应">{out6}</Term>
          </div>
        </div>

        {/* 侧栏 */}
        <div>
          <div className="card">
            <b>📋 行动简报</b>
            <div className="mt-16" style={{ fontSize: 13.5 }}>
              <div className="row-between">
                <span className="muted">身份</span>
                <span>{brief?.role}</span>
              </div>
              <div className="row-between mt-16">
                <span className="muted">目标</span>
                <span style={{ textAlign: 'right' }}>{brief?.target}</span>
              </div>
            </div>
          </div>

          <div className="card mt-16">
            <b>🔑 已获取的凭据</b>
            <div className="mt-16" style={{ fontSize: 12.5 }}>
              <div className="faint">员工工号</div>
              <code>{out1?.employees?.[0]?.employee_id || '—'}</code>
              <div className="faint" style={{ marginTop: 10 }}>
                archive_key
              </div>
              <code style={{ wordBreak: 'break-all' }}>
                {out4?.body?.archive_key || '—'}
              </code>
              <div className="faint" style={{ marginTop: 10 }}>
                销毁令牌
              </div>
              <code style={{ wordBreak: 'break-all' }}>
                {out5?.destruction_token || '—'}
              </code>
            </div>
          </div>

          {destroyed && (
            <div className="card mt-16" style={{ borderColor: 'var(--success)' }}>
              <b>🏁 提交通关 flag</b>
              <p className="muted" style={{ fontSize: 13.5 }}>
                档案已销毁。提交 flag 完成本次行动。
              </p>
              <button
                className="btn btn-primary btn-block"
                onClick={submitFinalFlag}
                disabled={busy || !user}
              >
                提交 flag
              </button>
              {shot && (
                <div
                  className={
                    'flag-result ' + (shot.correct ? 'flag-ok' : 'flag-bad')
                  }
                >
                  {shot.correct
                    ? `✅ 行动完成！获得 ${shot.points_awarded} 分`
                    : '❌ flag 不正确'}
                </div>
              )}
            </div>
          )}

          <div className="card mt-16">
            <b>🧭 攻击链速览</b>
            <ol
              className="muted"
              style={{ fontSize: 13, paddingLeft: 18, marginBottom: 0 }}
            >
              <li>旧接口泄露员工名录</li>
              <li>SQL 注入绕过登录</li>
              <li>JWT 弱密钥伪造 admin</li>
              <li>SSRF 访问内部档案服务</li>
              <li>XXE 读取档案清单</li>
              <li>提交令牌销毁档案</li>
            </ol>
          </div>
        </div>
      </div>

      <LevelDisclaimer />
    </div>
  )
}
