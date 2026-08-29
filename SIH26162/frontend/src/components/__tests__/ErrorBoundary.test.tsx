import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { JSX } from 'react'
import { ErrorBoundary } from '../ErrorBoundary'

function BuggyComponent(): JSX.Element {
  throw new Error('Simulated test rendering crash')
}

describe('ErrorBoundary', () => {
  it('should render children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Normal content</div>
      </ErrorBoundary>
    )

    expect(screen.getByText('Normal content')).toBeInTheDocument()
  })

  it('should render fallback UI and reload button when an error is caught', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary>
        <BuggyComponent />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Reload Page')).toBeInTheDocument()

    spy.mockRestore()
  })
})
