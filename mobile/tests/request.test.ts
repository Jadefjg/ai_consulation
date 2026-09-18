import { describe, expect, it } from 'vitest'
import { asList, createRequestId } from '@/api/request'

describe('request helpers', () => {
  it('creates unique traceable request ids', () => {
    const first = createRequestId()
    const second = createRequestId()
    expect(first).toMatch(/^[a-z0-9]+-[a-z0-9]+$/)
    expect(second).toMatch(/^[a-z0-9]+-[a-z0-9]+$/)
    expect(first).not.toBe(second)
  })

  it('unwraps common paginated list shapes', () => {
    expect(asList([1, 2])).toEqual([1, 2])
    expect(asList({ items: [1] })).toEqual([1])
    expect(asList({ list: [2] })).toEqual([2])
    expect(asList({ results: [3] })).toEqual([3])
    expect(asList({ data: [4] })).toEqual([])
  })
})
