/**
 * 验证体验账号标识在前端正确显示。
 */
import { chromium } from 'playwright'
import { writeFileSync } from 'fs'

const BASE = 'http://127.0.0.1:8899'
const R = []
const check = (n, ok, d = '') => R.push({ n, ok: !!ok, d })

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1400, height: 950 } })

try {
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.evaluate(() =>
    localStorage.setItem('atf_disclaimer_accepted', 'yes'))

  // 排行榜
  await page.goto(BASE + '/leaderboard', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  const lbText = await page.textContent('body')
  check('★排行榜显示「体验账号」标识', lbText.includes('体验账号'),
        lbText.slice(0, 80))
  check('demo 出现在排行榜', lbText.includes('demo'))

  // 用 demo 登录
  await page.goto(BASE + '/login', { waitUntil: 'networkidle' })
  await page.fill('input[autocomplete=username]', 'demo')
  await page.fill('input[autocomplete=current-password]', 'DemoAccess2026')
  await page.click('button[type=submit]')
  await page.waitForTimeout(2000)

  const afterLogin = await page.textContent('body')
  check('demo 可登录', page.url().includes('/levels') || afterLogin.includes('关卡'))

  // 个人主页应显示体验标识与说明
  await page.goto(BASE + '/profile', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1200)
  const profText = await page.textContent('body')
  check('★个人主页显示「体验账号」标识', profText.includes('体验账号'))
  check('个人主页有体验账号说明', profText.includes('预先解锁') ||
        profText.includes('体验账号'))
  check('个人主页显示满分', profText.includes('4710'))
  check('个人主页显示 37/37', profText.includes('37'))
  await page.screenshot({ path: 'shot-demo-profile.png', fullPage: true })

  // 关卡页：应显示已通关
  await page.goto(BASE + '/levels/L01', { waitUntil: 'networkidle' })
  await page.waitForTimeout(900)
  const lvText = await page.textContent('body')
  check('★关卡显示已通关', lvText.includes('已通关'))
  check('★writeup 可见（无需自己通关）',
        lvText.includes('原理讲解') || lvText.includes('信息泄露是最常见'))

  // 压轴关应可进入
  await page.goto(BASE + '/levels/L37', { waitUntil: 'networkidle' })
  await page.waitForTimeout(900)
  const fText = await page.textContent('body')
  check('★压轴关已解锁可直接进入',
        !fText.includes('尚未解锁'), fText.slice(0, 70))

  // 不应看到管理入口
  const adminLinks = await page.locator('a[href="/admin"]').count()
  check('★导航中无管理后台入口', adminLinks === 0, 'count=%d' % adminLinks)
} catch (e) {
  check('执行未抛异常', false, e.message)
} finally {
  await browser.close()
}

const passed = R.filter((r) => r.ok).length
const lines = ['体验账号 UI 验证', '='.repeat(60)]
for (const r of R) {
  lines.push(`${r.ok ? 'PASS' : 'FAIL'} ${r.n}${!r.ok && r.d ? '  <- ' + r.d : ''}`)
}
lines.push('='.repeat(60))
lines.push(`通过 ${passed} / ${R.length}`)
writeFileSync('demo_ui_result.txt', lines.join('\n'))
console.log(`demo UI: ${passed}/${R.length} passed`)
process.exit(passed === R.length ? 0 : 1)
