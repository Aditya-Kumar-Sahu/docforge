import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Home from '@/app/page'

describe('Home', () => {
  it('renders a heading', () => {
    render(<Home />)
    const heading = screen.getByText(/Welcome to DocForge/i)
    expect(heading).toBeDefined()
  })
})
