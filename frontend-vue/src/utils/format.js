/**
 * 格式化金额
 */
export function formatMoney(value) {
  if (value === null || value === undefined) return '--'
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(value)
}

/**
 * 格式化百分比
 */
export function formatPercent(value, showSign = true) {
  if (value === null || value === undefined) return '--'
  const percent = (value * 100).toFixed(2)
  return showSign ? `${percent > 0 ? '+' : ''}${percent}%` : `${percent}%`
}

/**
 * 格式化日期
 */
export function formatDate(dateStr) {
  if (!dateStr) return '--'
  return dateStr.split('T')[0]
}

/**
 * 格式化日期时间
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return '--'
  return dateStr.replace('T', ' ').substring(0, 19)
}

/**
 * 资产类型名称
 */
export function getAssetTypeName(type) {
  const names = {
    'stock': '股票',
    'etf_index': '宽基ETF',
    'etf_sector': '行业ETF',
    'fund': '基金',
    'gold': '黄金',
    'silver': '白银',
    'bank_deposit': '银行定期存款',
    'bank_current': '银行活期存款',
    'bank_wealth': '银行理财产品',
    'treasury_bond': '国债',
    'corporate_bond': '企业债',
    'money_fund': '货币基金',
    'insurance': '保险理财',
    'trust': '信托产品',
    'other': '其他'
  }
  return names[type] || type
}

/**
 * 显示 Toast 提示
 */
export function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container')
  if (!container) return

  const toast = document.createElement('div')
  toast.className = `toast ${type}`
  toast.textContent = message
  container.appendChild(toast)

  setTimeout(() => toast.remove(), 3000)
}