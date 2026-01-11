import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ClarificationUI from '../components/content/ClarificationUI';

// Mock the FluentUI components
vi.mock('@fluentui/react-components', () => ({
  Button: ({ children, onClick, disabled, icon, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {icon && <span data-testid="icon">{icon}</span>}
      {children}
    </button>
  ),
  Text: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  Body1: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  Body2: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  Title3: ({ children, ...props }: any) => <h3 {...props}>{children}</h3>,
  makeStyles: () => () => ({}),
  tokens: {},
  Textarea: ({ value, onChange, placeholder, disabled, ...props }: any) => (
    <textarea
      value={value}
      onChange={(e) => onChange?.(e, { value: e.target.value })}
      placeholder={placeholder}
      disabled={disabled}
      {...props}
    />
  ),
  Card: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardHeader: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  CardPreview: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  Badge: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  Dialog: ({ children, open, onOpenChange }: any) => 
    open ? <div data-testid="dialog">{children}</div> : null,
  DialogTrigger: ({ children }: any) => <div>{children}</div>,
  DialogSurface: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  DialogTitle: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
  DialogContent: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  DialogBody: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  DialogActions: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  Field: ({ children, label, ...props }: any) => (
    <div {...props}>
      {label && <label>{label}</label>}
      {children}
    </div>
  )
}));

// Mock the icons
vi.mock('@fluentui/react-icons', () => ({
  CheckmarkCircle20Regular: () => <span data-testid="checkmark-icon">✓</span>,
  ArrowReply20Regular: () => <span data-testid="arrow-reply-icon">↩</span>,
  Save20Regular: () => <span data-testid="save-icon">💾</span>,
  Share20Regular: () => <span data-testid="share-icon">📤</span>,
  Dismiss20Regular: () => <span data-testid="dismiss-icon">✕</span>,
  Warning20Regular: () => <span data-testid="warning-icon">⚠</span>
}));

// Mock navigator.clipboard and navigator.share
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(undefined)
  },
  share: vi.fn().mockResolvedValue(undefined)
});

// Mock URL.createObjectURL and URL.revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'mock-url');
global.URL.revokeObjectURL = vi.fn();

describe('ClarificationUI - Simplified Final Approval', () => {
  const mockProps = {
    agentResult: 'Test agent result content',
    onApprove: vi.fn(),
    onRetry: vi.fn(),
    isLoading: false
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock document.createElement and appendChild/removeChild for export functionality
    const mockLink = {
      href: '',
      download: '',
      click: vi.fn()
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any);
    vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any);
  });

  it('renders final approval UI with simplified options', () => {
    const { container } = render(<ClarificationUI {...mockProps} />);
    
    // Check for main elements
    expect(screen.getByText('🎯 Final Results Ready for Review')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Final Approval Required')).toBeInTheDocument();
    
    // Check for simplified buttons
    expect(screen.getByText('Approve Results')).toBeInTheDocument();
    expect(screen.getByText('Start New Task')).toBeInTheDocument();
    expect(screen.getByText('Export Results')).toBeInTheDocument();
    expect(screen.getByText('Share')).toBeInTheDocument();
  });

  it('displays agent result content', () => {
    render(<ClarificationUI {...mockProps} />);
    
    expect(screen.getByText('Test agent result content')).toBeInTheDocument();
  });

  it('calls onApprove when approve button is clicked', async () => {
    render(<ClarificationUI {...mockProps} />);
    
    const approveButton = screen.getByText('Approve Results');
    fireEvent.click(approveButton);
    
    expect(mockProps.onApprove).toHaveBeenCalledTimes(1);
  });

  it('shows restart dialog when Start New Task is clicked', async () => {
    render(<ClarificationUI {...mockProps} />);
    
    const startNewTaskButton = screen.getByText('Start New Task');
    fireEvent.click(startNewTaskButton);
    
    await waitFor(() => {
      expect(screen.getByText('Start New Task')).toBeInTheDocument();
      expect(screen.getByText('This will end the current workflow.')).toBeInTheDocument();
    });
  });

  it('handles restart workflow with reason', async () => {
    render(<ClarificationUI {...mockProps} />);
    
    // Open restart dialog
    const startNewTaskButton = screen.getByText('Start New Task');
    fireEvent.click(startNewTaskButton);
    
    await waitFor(() => {
      const textarea = screen.getByPlaceholderText('Describe why you want to start a new task or what should be different...');
      fireEvent.change(textarea, { target: { value: 'Need different parameters' } });
      
      const submitButton = screen.getByRole('button', { name: 'Start New Task' });
      fireEvent.click(submitButton);
    });
    
    expect(mockProps.onRetry).toHaveBeenCalledWith('restart: Need different parameters');
  });

  it('exports results when export button is clicked', async () => {
    render(<ClarificationUI {...mockProps} />);
    
    const exportButton = screen.getByText('Export Results');
    fireEvent.click(exportButton);
    
    await waitFor(() => {
      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(global.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  it('handles share functionality', async () => {
    render(<ClarificationUI {...mockProps} />);
    
    const shareButton = screen.getByText('Share');
    fireEvent.click(shareButton);
    
    await waitFor(() => {
      expect(navigator.share).toHaveBeenCalledWith({
        title: 'Workflow Results',
        text: 'Check out these workflow results',
        url: window.location.href
      });
    });
  });

  it('falls back to clipboard when share is not available', async () => {
    // Mock navigator.share to be undefined
    const originalShare = navigator.share;
    delete (navigator as any).share;
    
    render(<ClarificationUI {...mockProps} />);
    
    const shareButton = screen.getByText('Share');
    fireEvent.click(shareButton);
    
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(window.location.href);
    });
    
    // Restore navigator.share
    (navigator as any).share = originalShare;
  });

  it('disables buttons when loading', () => {
    render(<ClarificationUI {...mockProps} isLoading={true} />);
    
    const approveButton = screen.getByText('Approving...');
    const startNewTaskButton = screen.getByText('Start New Task');
    const shareButton = screen.getByText('Share');
    
    expect(approveButton).toBeDisabled();
    expect(startNewTaskButton).toBeDisabled();
    expect(shareButton).toBeDisabled();
  });

  it('shows appropriate instructions for simplified workflow', () => {
    render(<ClarificationUI {...mockProps} />);
    
    expect(screen.getByText(/Please review the results above and choose one of the following options/)).toBeInTheDocument();
    expect(screen.getByText(/Approve Results:/)).toBeInTheDocument();
    expect(screen.getByText(/Start New Task:/)).toBeInTheDocument();
    expect(screen.getByText(/Export Results:/)).toBeInTheDocument();
  });

  it('validates requirements for simplified clarification UI functionality', () => {
    // Property 11: Simplified Clarification UI Functionality
    // Validates: Requirements 9.1, 9.2, 9.3
    
    render(<ClarificationUI {...mockProps} />);
    
    // Requirement 9.1: Simple approve/restart options
    expect(screen.getByText('Approve Results')).toBeInTheDocument();
    expect(screen.getByText('Start New Task')).toBeInTheDocument();
    
    // Requirement 9.2: Export/save functionality
    expect(screen.getByText('Export Results')).toBeInTheDocument();
    expect(screen.getByText('Share')).toBeInTheDocument();
    
    // Requirement 9.3: No complex revision targeting (simplified UI)
    expect(screen.queryByText('Request Revisions')).not.toBeInTheDocument();
    expect(screen.queryByText('Re-run Analysis Only')).not.toBeInTheDocument();
    expect(screen.queryByText('Re-run Specific Agents')).not.toBeInTheDocument();
  });
});