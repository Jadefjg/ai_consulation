export function validateAge(value: string | number | undefined): string | null {
  if (value === undefined || value === '') return null
  const age = Number(value)
  return Number.isInteger(age) && age >= 0 && age <= 150 ? null : '年龄请输入 0-150 的整数'
}

export function validatePhone(value: string): string | null {
  if (!value) return null
  return /^1\d{10}$/.test(value.trim()) ? null : '请输入正确的手机号'
}
