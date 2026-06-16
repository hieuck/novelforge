import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConfirmDialog from '@/components/ConfirmDialog'

describe('ConfirmDialog', () => {
  it('renders nothing when closed', () => {
    const { container } = render(<ConfirmDialog open={false} title="Test" message="Msg" onConfirm={() => {}} onCancel={() => {}} />)
    expect(container.innerHTML).toBe('')
  })

  it('renders title and message when open', () => {
    render(<ConfirmDialog open={true} title="Delete?" message="Are you sure?" onConfirm={() => {}} onCancel={() => {}} />)
    expect(screen.getByText('Delete?')).toBeTruthy()
    expect(screen.getByText('Are you sure?')).toBeTruthy()
  })

  it('calls onCancel when clicking backdrop', () => {
    const onCancel = vi.fn()
    render(<ConfirmDialog open={true} title="T" message="M" onConfirm={() => {}} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('M').parentElement!.parentElement!)
    expect(onCancel).toHaveBeenCalled()
  })

  it('calls onCancel when clicking Cancel button', () => {
    const onCancel = vi.fn()
    render(<ConfirmDialog open={true} title="T" message="M" onConfirm={() => {}} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('Hủy'))
    expect(onCancel).toHaveBeenCalled()
  })

  it('calls onConfirm when clicking confirm button', async () => {
    const onConfirm = vi.fn()
    render(<ConfirmDialog open={true} title="T" message="M" onConfirm={onConfirm} onCancel={() => {}} />)
    fireEvent.click(screen.getByText('Xóa'))
    // Wait for microtask
    await new Promise(r => setTimeout(r, 10))
    expect(onConfirm).toHaveBeenCalled()
  })
})
