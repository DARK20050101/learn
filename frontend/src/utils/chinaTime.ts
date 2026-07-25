const CHINA_TIME_ZONE = 'Asia/Shanghai'

export function chinaDateKey(value: Date | string): string {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: CHINA_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(typeof value === 'string' ? new Date(value) : value)
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find(item => item.type === type)?.value ?? ''
  return `${part('year')}-${part('month')}-${part('day')}`
}

export function chinaDateText(value: Date = new Date()): string {
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: CHINA_TIME_ZONE,
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(value)
}

export function chinaGreeting(value: Date = new Date()): string {
  const hour = Number(new Intl.DateTimeFormat('en-US', {
    timeZone: CHINA_TIME_ZONE,
    hour: '2-digit',
    hourCycle: 'h23',
  }).format(value))
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

export function recentChinaDays(count: number): { key: string; label: string }[] {
  const today = chinaDateKey(new Date())
  const [year, month, day] = today.split('-').map(Number)
  const base = new Date(Date.UTC(year, month - 1, day, 12))
  return Array.from({ length: count }, (_, index) => {
    const date = new Date(base)
    date.setUTCDate(base.getUTCDate() - (count - index - 1))
    return {
      key: chinaDateKey(date),
      label: new Intl.DateTimeFormat('zh-CN', {
        timeZone: CHINA_TIME_ZONE,
        weekday: 'short',
      }).format(date).replace('周', ''),
    }
  })
}
