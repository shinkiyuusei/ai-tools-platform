export function formatLargeNumber(num, thresholds) {
  const v = Number(num || 0)
  for (const [limit, divisor, suffix] of thresholds) {
    if (v >= limit) return (v / divisor).toFixed(1) + suffix
  }
  return String(v)
}

const TOKEN_THRESHOLDS = [[1000000, 1000000, 'M'], [1000, 1000, 'K']]
const CHINESE_THRESHOLDS = [[100000000, 100000000, '亿'], [10000, 10000, '万']]

export const formatTokens = (num) => formatLargeNumber(num, TOKEN_THRESHOLDS)
export const formatHot = (num) => formatLargeNumber(num, CHINESE_THRESHOLDS)

