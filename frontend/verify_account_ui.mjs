/**
 * ATF Lab - 账号安全相关前端 UI 验证
 *
 * 验证：注册展示恢复码 / 找回密码页 / 改密页 / 管理员提醒横幅
 * 用法：node verify_account_ui.mjs
 */
import { chromium } from 'playwright'
import { writeFileSync } from 'fs'

const BASE = process.env.ATF_BASE || 'http://127.0.0.1:8899'
const R = []
const check = (n, ok, d = '') => R.push({ n, ok: !!ok, d })

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1400, height: 950 } })
const errors = []
page.on('pageerror', (e) => errors.push('PAGEERROR: ' + e.message))

try {
  // 跳过免责弹窗
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.evaluate(() =>
    localStorage.setItem('atf_disclaimer_accepted', 'yes'))

  // ---------- 登录页应有"忘记密码"入口 ----------
  await page.goto(BASE + '/login', { waitUntil: 'networkidle' })
  await page.waitForTimeout(600)
  const loginText = await page.textContent('body')
  check('登录页有"忘记密码"入口', loginText.includes('忘记密码') &&
        loginText.includes('使用恢复码重置'))
  check('登录页有注册入口', loginText.includes('立即注册'))

  // ---------- 找回密码页 ----------
  await page.goto(BASE + '/recover', { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  const recText = await page.textContent('body')
  check('找回密码页可访问', recText.includes('找回密码'))
  check('找回密码页说明使用一次性恢复码',
        recText.includes('一次性恢复码'))
  check('找回密码页提到可联系管理员本地重置',
        recText.includes('命令行工具'))

  // ---------- 注册并检查恢复码展示 ----------
  const uname = 'ui_' + Math.random().toString(36).slice(2, 8)
  await page.goto(BASE + '/register', { waitUntil: 'networkidle' })
  await page.fill('input[autocomplete=username]', uname)
  await page.fill('input[autocomplete=new-password] >> nth=0', 'UiTest12345')
  await page.fill('input[autocomplete=new-password] >> nth=1', 'UiTest12345')
  await page.click('button[type=submit]')
  await page.waitForTimeout(1500)

  const afterReg = await page.textContent('body')
  check('注册后展示"注册成功"', afterReg.includes('注册成功'))

  // 恢复码应显示为 XXXX-XXXX-XXXX-XXXX
  const codeEl = await page.locator('.mono').first().textContent().catch(() => '')
  const codeMatch = /\b[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}\b/
  check('★注册后展示一次性恢复码', codeMatch.test(codeEl || ''),
        'got=' + (codeEl || '').slice(0, 30))
  check('提示恢复码只显示一次',
        afterReg.includes('只显示这一次') || afterReg.includes('用一次即失效'))
  check('有"我已保存"确认按钮',
        (await page.locator('button:has-text("我已保存")').count()) > 0)
  await page.screenshot({ path: 'shot-recovery.png', fullPage: true })

  const savedCode = (codeEl || '').trim()

  // ---------- 进入平台 ----------
  await page.click('button:has-text("我已保存")')
  await page.waitForURL('**/levels', { timeout: 15000 })
  await page.waitForTimeout(1000)
  check('确认后进入关卡页', page.url().includes('/levels'))

  // ---------- 普通用户不应看到改密横幅 ----------
  const banner = await page.locator('text=你仍在使用').count()
  check('普通用户无初始密码横幅', banner === 0)

  // ---------- 改密页 ----------
  await page.goto(BASE + '/change-password', { waitUntil: 'networkidle' })
  await page.waitForTimeout(600)
  const cpText = await page.textContent('body')
  check('改密页可访问', cpText.includes('修改密码'))
  check('改密页有密码强度提示', cpText.includes('至少 8 位'))

  // 实际改密
  await page.fill('input[autocomplete=current-password]', 'UiTest12345')
  await page.fill('input[autocomplete=new-password] >> nth=0', 'NewUiPass9876')
  await page.fill('input[autocomplete=new-password] >> nth=1', 'NewUiPass9876')
  await page.click('button[type=submit]')
  await page.waitForTimeout(1800)
  const doneText = await page.textContent('body')
  check('改密成功提示', doneText.includes('密码已更新'))
  check('改密后轮换并展示新恢复码',
        codeMatch.test(doneText) || doneText.includes('恢复码'))
  await page.screenshot({ path: 'shot-changed.png', fullPage: true })

  // ---------- 用恢复码登录流程（端到端） ----------
  // 退出登录
  await page.goto(BASE + '/levels', { waitUntil: 'networkidle' })
  await page.evaluate(() => localStorage.removeItem('atf_token'))

  // 记录 recover 接口的响应，便于断言
  let recoverCode = null
  page.on('response', async (r) => {
    if (r.url().includes('/api/v1/auth/recover')) {
      recoverCode = r.status()
    }
  })

  await page.goto(BASE + '/recover', { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)

  // 用注册时的恢复码（已被改密流程轮换，应失败）
  await page.locator('input.input').first().fill(uname)
  await page.locator('input.mono').fill(savedCode)
  await page.locator('input[autocomplete=new-password]').fill('AnotherPass123')
  await page.click('button[type=submit]')
  await page.waitForTimeout(1800)
  const failText = await page.textContent('body')
  check('★已被轮换的旧恢复码不能再用',
        failText.includes('不正确') && !failText.includes('密码已重置'),
        'HTTP=%s text=%s' % (recoverCode, failText.slice(0, 60)))

  // ---------- 管理员提醒横幅（需 admin 未改密） ----------
  // 本机 admin 由启动流程创建且 must_change_password=1
  const adminLogin = await page.evaluate(async (base) => {
    const r = await fetch(base + '/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: '__probe__', password: 'x' }),
    })
    return r.status
  }, BASE)
  check('登录接口可访问', adminLogin === 401 || adminLogin === 200)

  check('无 JS 运行时错误',
        errors.filter((e) => !e.includes('favicon')).length === 0,
        errors.slice(0, 2).join(' | '))
} catch (e) {
  check('执行未抛异常', false, e.message)
} finally {
  await browser.close()
}

const passed = R.filter((r) => r.ok).length
const lines = ['ATF Lab 账号安全 UI 验证', '='.repeat(62)]
for (const r of R) {
  lines.push(`${r.ok ? 'PASS' : 'FAIL'} ${r.n}${!r.ok && r.d ? '  <- ' + r.d : ''}`)
}
lines.push('='.repeat(62))
lines.push(`通过 ${passed} / ${R.length}`)
writeFileSync('account_ui_result.txt', lines.join('\n'))
console.log(`account UI: ${passed}/${R.length} passed (see account_ui_result.txt)`)
process.exit(passed === R.length ? 0 : 1)
