/**
 * ATF Lab - 免责声明文本（单一来源）
 *
 * ⚠️ 此文本为项目强制要求，必须原样呈现于：
 *   1. README.md 最顶部
 *   2. 网站每一页的页脚
 *   3. 首次访问的确认弹窗
 *   4. LICENSE 文件
 * 任何修改都必须四处同步。
 */

export const DISCLAIMER_LINES = [
  '本项目是一个 **API 调动的** 学习与演示项目，**仅供本人自行娱乐与安全学习使用**。',
  '**请勿在互联网上公开发布、部署或传播**。',
  '若因违反本约定造成任何后果，由使用者自行承担。',
]

export const DISCLAIMER_TITLE = '⚠️ 免责声明'

/** 纯文本版本，用于 <title>、元数据或复制场景 */
export const DISCLAIMER_TEXT = DISCLAIMER_LINES.join('\n')
  .replace(/\*\*/g, '')

/** 关卡页底部的小字提示（强制要求） */
export const LEVEL_HINT = '本关漏洞为教学模拟，禁止用于未授权测试'
