import { describe, expect, it } from 'vitest'
import { formatAvatar, parseListData } from './format'

describe('format utilities', () => {
  it('normalizes relative avatar paths', () => {
    expect(formatAvatar('avatar/a.png')).toBe('/uploads33/avatar/a.png')
  })

  it('reads paginated response items', () => {
    expect(parseListData({ data: { items: [{ id: 1 }] } })).toEqual([{ id: 1 }])
  })
})
