import { describe, expect, it } from 'vitest'
import { validateAge, validatePhone } from '@/utils/validation'

describe('profile validation', () => {
  it('accepts empty and valid ages', () => {
    expect(validateAge('')).toBeNull()
    expect(validateAge('36')).toBeNull()
    expect(validateAge(150)).toBeNull()
  })

  it('rejects invalid ages', () => {
    expect(validateAge('-1')).toBeTruthy()
    expect(validateAge('36.5')).toBeTruthy()
    expect(validateAge('151')).toBeTruthy()
  })

  it('validates mainland mobile numbers', () => {
    expect(validatePhone('13800138000')).toBeNull()
    expect(validatePhone('')).toBeNull()
    expect(validatePhone('123')).toBeTruthy()
  })
})
