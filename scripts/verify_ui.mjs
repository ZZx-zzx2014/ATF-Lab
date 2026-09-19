/**
 * ATF Lab - 前端 UI 冒烟验证（无头浏览器）
 *
 * ⚠️ 仅供教学演示：用于验证 SPA 能正常渲染、免责弹窗出现、
 *    并且所有数据交互确实走 /api/v1/* 请求。
 *
 * 用法：node scripts/verify_ui.mjs
 */
import { chromium } from 'playwright'

const BASE = process.env.ATF_BASE || 'http://127.0.0.1:8899'
const results = []
const apiCalls = []

function check(name, ok, detail = '') {
  results.push({ name, ok: !!ok, detail })
}

const browser = await chromium.launch()
const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } })
const page = await ctx.newPage()

// 记录所有请求，用于验证"数据都走 API"
page.on('request', (r) => {
  const u = r.url()
  if (u.includes('/api/')) apiCalls.push(`${r.method()} ${u.replace(BASE, '')}`)
})
const consoleErrors = []
page.on('console', (m) => {
  if (m.type() === 'error') consoleErrors.push(m.text())
})
page.on('pageerror', (e) => consoleErrors.push('PAGEERROR: ' + e.message))

try {
  // ---------- 1. 首访应弹出免责声明确认框 ----------
  await page.goto(BASE, { waitUntil: 'networkidle', timeout: 30000 })
  const modalTitle = await page.textContent('.modal h2').catch(() => '')
  check('首访弹出免责声明弹窗', modalTitle.includes('免责声明'),
        '标题=' + modalTitle.trim())

  const bodyText = await page.textContent('.disclaimer-body').catch(() => '')
  check('弹窗含完整免责声明文本',
        bodyText.includes('仅供本人自行娱乐与安全学习使用') &&
        bodyText.includes('请勿在互联网上公开发布、部署或传播') &&
        bodyText.includes('由使用者自行承担'))

  // 未勾选时按钮应禁用
  const btnDisabled = await page.getAttribute('.modal-actions .btn-primary', 'disabled')
  check('未勾选时"同意并进入"按钮禁用', btnDisabled !== null)

  await page.screenshot({ path: 'shot-1-disclaimer.png' })

  // 勾选并进入
  await page.check('.modal input[type=checkbox]')
  await page.click('.modal-actions .btn-primary')
  await page.waitForTimeout(800)
  check('勾选后可进入站点', (await page.locator('.modal').count()) === 0)

  // ---------- 2. 落地页 ----------
  const heroText = await page.textContent('.hero h1').catch(() => '')
  check('落地页 Hero 渲染', heroText.length > 0, heroText.replace(/\s+/g, ' ').trim())
  check('落地页有开始按钮',
        (await page.locator('.hero-actions a').count()) > 0)

  const statNums = await page.locator('.stat .num').allTextContents()
  check('落地页显示关卡数 37', statNums.includes('37'), 'stats=' + statNums.join(','))

  await page.screenshot({ path: 'shot-2-landing.png', fullPage: true })

  // ---------- 3. 页脚免责声明（每一页都要有） ----------
  const footerText = await page.textContent('.footer-disclaimer').catch(() => '')
  check('落地页页脚含免责声明', footerText.includes('免责声明'))

  // ---------- 4. 注册登录 ----------
  const uname = 'ui_' + Math.random().toString(36).slice(2, 8)
  await page.goto(BASE + '/register', { waitUntil: 'networkidle' })
  await page.fill('input[autocomplete=username]', uname)
  await page.fill('input[autocomplete=new-password] >> nth=0', 'UiTest123!')
  await page.fill('input[autocomplete=new-password] >> nth=1', 'UiTest123!')
  await page.click('button[type=submit]')
  await page.waitForURL('**/levels', { timeout: 15000 })
  check('注册后跳转到关卡页', page.url().includes('/levels'))

  await page.waitForTimeout(1200)
  const levelCards = await page.locator('.level-card').count()
  check('关卡列表渲染出卡片', levelCards >= 37, 'cards=' + levelCards)

  await page.screenshot({ path: 'shot-3-levels.png', fullPage: true })

  // ---------- 5. 深色/浅色主题切换 ----------
  const themeBefore = await page.getAttribute('html', 'data-theme')
  await page.click('.nav-links .btn-ghost')
  await page.waitForTimeout(400)
  const themeAfter = await page.getAttribute('html', 'data-theme')
  check('主题可切换', themeBefore !== themeAfter,
        themeBefore + ' -> ' + themeAfter)
  await page.screenshot({ path: 'shot-4-theme.png' })
  // 切回来
  await page.click('.nav-links .btn-ghost')
  await page.waitForTimeout(300)

  // ---------- 6. 关卡详情 + 模拟交互 ----------
  await page.goto(BASE + '/levels/L01', { waitUntil: 'networkidle' })
  await page.waitForTimeout(600)
  check('关卡详情页有目标', (await page.locator('.card').count()) > 0)

  const lvlFooter = await page.textContent('.level-disclaimer').catch(() => '')
  check('关卡页底部有教学模拟小字提示',
        lvlFooter.includes('本关漏洞为教学模拟，禁止用于未授权测试'),
        lvlFooter.trim())

  // 点击模拟交互按钮
  const simBtn = page.locator('button:has-text("获取页面源码")')
  if (await simBtn.count()) {
    await simBtn.click()
    await page.waitForTimeout(1200)
    const term = await page.textContent('.terminal').catch(() => '')
    check('模拟交互返回数据并展示', term.includes('flag{html_comment_leak}'))
  }
  await page.screenshot({ path: 'shot-5-level-detail.png', fullPage: true })

  // ---------- 7. 提交 flag ----------
  await page.fill('input[placeholder="flag{...}"]', 'flag{html_comment_leak}')
  await page.click('button:has-text("提交")')
  await page.waitForTimeout(1200)
  const okBox = await page.textContent('.flag-ok').catch(() => '')
  check('提交正确 flag 显示成功', okBox.includes('正确'), okBox.slice(0, 40))

  // ---------- 8. 未解锁的压轴关 ----------
  await page.goto(BASE + '/levels/L37', { waitUntil: 'networkidle' })
  await page.waitForTimeout(600)
  const locked = await page.textContent('.notice-warn').catch(() => '')
  check('L37 未达标时显示未解锁', locked.includes('尚未解锁'), locked.trim().slice(0, 50))

  // ---------- 9. 排行榜 ----------
  await page.goto(BASE + '/leaderboard', { waitUntil: 'networkidle' })
  await page.waitForTimeout(800)
  check('排行榜有数据行', (await page.locator('.table tbody tr').count()) >= 1)
  await page.screenshot({ path: 'shot-6-leaderboard.png' })

  // ---------- 10. API 文档页 ----------
  await page.goto(BASE + '/docs', { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  const apiDocsText = await page.textContent('body')
  check('API 文档页渲染', apiDocsText.includes('/api/v1/levels'))

  // ---------- 11. 页脚在多个页面都存在 ----------
  let footerEverywhere = true
  for (const p of ['/levels', '/leaderboard', '/docs', '/about']) {
    await page.goto(BASE + p, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(300)
    const f = await page.textContent('.footer-disclaimer').catch(() => '')
    if (!f.includes('免责声明')) {
      footerEverywhere = false
      check('页脚缺失于 ' + p, false)
    }
  }
  check('免责声明页脚存在于所有页面', footerEverywhere)

  // ---------- 12. 验证数据确实走 API ----------
  const apiHits = apiCalls.filter((c) => c.includes('/api/v1/'))
  check('前端数据交互均走 /api/v1/*', apiHits.length >= 8,
        'api calls=' + apiHits.length)

  // ---------- 13. 检查控制台错误 ----------
  const realErrors = consoleErrors.filter(
    (e) => !e.includes('favicon') && !e.includes('404 (Not Found)')
  )
  check('无 JavaScript 运行时错误', realErrors.length === 0,
        realErrors.slice(0, 2).join(' | '))
} catch (e) {
  check('执行过程未抛异常', false, e.message)
} finally {
  await browser.close()
}

// ---------------------------------------------------------------- 输出
const passed = results.filter((r) => r.ok).length
const lines = ['ATF Lab 前端 UI 验证报告', '='.repeat(64)]
for (const r of results) {
  lines.push(`${r.ok ? 'PASS' : 'FAIL'} ${r.name}${r.detail && !r.ok ? '  <- ' + r.detail : ''}`)
}
lines.push('='.repeat(64))
lines.push(`通过 ${passed} / ${results.length}`)
lines.push('')
lines.push('捕获到的 API 调用（证明数据走 REST API）：')
for (const c of [...new Set(apiCalls)].slice(0, 25)) lines.push('  ' + c)

const report = lines.join('\n')
const { writeFileSync } = await import('fs')
writeFileSync('ui_result.txt', report)
console.log(`UI verification: ${passed}/${results.length} passed (see ui_result.txt)`)
process.exit(passed === results.length ? 0 : 1)
