import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ComprehensiveResultsDisplay from '../components/content/ComprehensiveResultsDisplay';

// Mock the utility functions
vi.mock('../utils/agentIconUtils', () => ({
  getAgentIcon: vi.fn(() => <div data-testid="agent-icon">Icon</div>),
  getAgentDisplayName: vi.fn((name: string) => `Display ${name}`)
}));

describe('ComprehensiveResultsDisplay Component', () => {
  const mockHandleApproveResults = vi.fn();
  const mockHandleRequestRevision = vi.fn();

  const mockComprehensiveResults = {
    plan_id: 'test-plan-1',
    results: {
      gmail: {
        status: 'completed' as const,
        result: 'Found 5 relevant emails regarding the invoice inquiry. All emails have been processed and categorized.',
        metadata: {
          service_used: 'gmail_mcp',
          data_quality: 'high' as const,
          execution_time: 12.5
        }
      },
      accounts_payable: {
        status: 'completed' as const,
        result: 'Retrieved invoice data from Bill.com. Found 3 matching invoices with total value of $15,420.',
        metadata: {
          service_used: 'bill_com_mcp',
          data_quality: 'high' as const,
          execution_time: 8.2
        }
      },
      crm: {
        status: 'completed' as const,
        result: 'Updated customer records in Salesforce. Customer status changed to "Active" with recent payment history.',
        metadata: {
          service_used: 'salesforce_mcp',
          data_quality: 'medium' as const,
          execution_time: 15.7
        }
      },
      analysis: {
        status: 'completed' as const,
        result: 'Comprehensive analysis shows strong correlation between email inquiries and invoice processing times. Recommendation: Implement automated email-to-invoice matching.',
        metadata: {
          service_used: 'analysis_llm',
          data_quality: 'high' as const,
          execution_time: 22.3,
          analysis_length: 1250,
          correlation_score: 0.87,
          llm_used: 'gpt-4'
        }
      }
    },
    correlations: {
      cross_references: 12,
      data_consistency: 0.92,
      vendor_mentions: 8,
      quality_score: 0.89
    },
    executive_summary: 'The multi-agent analysis successfully processed email inquiries, retrieved relevant invoice data, and updated customer records. Strong data correlations were found across all systems, indicating high data quality and consistency.',
    recommendations: [
      'Implement automated email-to-invoice matching system',
      'Set up real-time notifications for invoice status changes',
      'Create dashboard for cross-system data correlation monitoring'
    ],
    timestamp: '2024-01-15T10:30:00Z'
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render comprehensive results display with all required elements', () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Check for main elements
    expect(screen.getByText('Comprehensive Analysis Results')).toBeInTheDocument();
    expect(screen.getByText(/4\/4 agents completed/)).toBeInTheDocument();
    expect(screen.getByText('All Completed')).toBeInTheDocument();
    
    // Check for tab navigation using role="tab"
    expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Email Results' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'AP Results' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'CRM Results' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Analysis' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Data Correlations' })).toBeInTheDocument();
    
    // Check for approval buttons
    expect(screen.getByText('Approve Results')).toBeInTheDocument();
    expect(screen.getByText('Start New Workflow')).toBeInTheDocument();
    expect(screen.getByText('Export Results')).toBeInTheDocument();
  });

  it('should display executive summary and recommendations in overview tab', () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Check executive summary
    expect(screen.getByText('Executive Summary')).toBeInTheDocument();
    expect(screen.getByText(/The multi-agent analysis successfully processed/)).toBeInTheDocument();
    
    // Check recommendations
    expect(screen.getByText('Recommendations')).toBeInTheDocument();
    expect(screen.getByText('Implement automated email-to-invoice matching system')).toBeInTheDocument();
    expect(screen.getByText('Set up real-time notifications for invoice status changes')).toBeInTheDocument();
    expect(screen.getByText('Create dashboard for cross-system data correlation monitoring')).toBeInTheDocument();
  });

  it('should switch between tabs and display appropriate content', async () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Click on Email Results tab using role
    fireEvent.click(screen.getByRole('tab', { name: 'Email Results' }));
    
    await waitFor(() => {
      expect(screen.getByText('Display gmail')).toBeInTheDocument();
      expect(screen.getByText(/Found 5 relevant emails/)).toBeInTheDocument();
    });

    // Click on Data Correlations tab using role
    fireEvent.click(screen.getByRole('tab', { name: 'Data Correlations' }));
    
    await waitFor(() => {
      expect(screen.getByText('Data Correlation Analysis')).toBeInTheDocument();
      expect(screen.getByText('Cross References')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument(); // cross_references value
      expect(screen.getByText('92%')).toBeInTheDocument(); // data_consistency percentage
    });
  });

  it('should display agent results with metadata', async () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Switch to AP Results tab using role
    fireEvent.click(screen.getByRole('tab', { name: 'AP Results' }));
    
    await waitFor(() => {
      expect(screen.getByText('Display accounts_payable')).toBeInTheDocument();
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('bill_com_mcp')).toBeInTheDocument();
      expect(screen.getByText('8.2s')).toBeInTheDocument();
      expect(screen.getByText(/Retrieved invoice data/)).toBeInTheDocument();
    });
  });

  it('should handle approve results button click', async () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    const approveButton = screen.getByText('Approve Results');
    fireEvent.click(approveButton);

    expect(mockHandleApproveResults).toHaveBeenCalledTimes(1);
  });

  it('should open revision dialog and handle revision submission', async () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Open revision dialog (now "Start New Workflow") - get the first one (trigger button)
    const revisionButtons = screen.getAllByText('Start New Workflow');
    const triggerButton = revisionButtons[0]; // The first one should be the trigger
    fireEvent.click(triggerButton);

    await waitFor(() => {
      // Check if dialog opened by looking for dialog title
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Fill out the feedback textarea
    const feedbackTextarea = screen.getByPlaceholderText('Describe what should be different in the new workflow...');
    fireEvent.change(feedbackTextarea, { target: { value: 'Please start a new workflow' } });

    // Submit revision (simplified - just starts new workflow) - get the submit button inside dialog
    const dialogButtons = screen.getAllByText('Start New Workflow');
    const submitButton = dialogButtons[dialogButtons.length - 1]; // The last one should be the submit button
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockHandleRequestRevision).toHaveBeenCalledWith(
        'restart',
        [],
        'restart: Please start a new workflow'
      );
    });
  });

  it('should show error status when agents have errors', () => {
    const resultsWithError = {
      ...mockComprehensiveResults,
      results: {
        ...mockComprehensiveResults.results,
        gmail: {
          ...mockComprehensiveResults.results.gmail,
          status: 'error' as const
        }
      }
    };

    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={resultsWithError}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    expect(screen.getByText('Completed with Issues')).toBeInTheDocument();
  });

  it('should disable buttons when processing approval', () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={true}
        showApprovalButtons={true}
      />
    );

    const approveButton = screen.getByText('Approving...');
    const revisionButton = screen.getByText('Start New Workflow');
    const exportButton = screen.getByText('Export Results');

    expect(approveButton).toBeDisabled();
    expect(revisionButton).toBeDisabled();
    expect(exportButton).toBeDisabled();
  });

  it('should not show buttons when showApprovalButtons is false', () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={false}
      />
    );

    expect(screen.queryByText('Approve Results')).not.toBeInTheDocument();
    expect(screen.queryByText('Start New Workflow')).not.toBeInTheDocument();
    expect(screen.queryByText('Export Results')).not.toBeInTheDocument();
  });

  it('should return null when no comprehensive results are provided', () => {
    const { container } = render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={null}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should display quality indicators correctly', async () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Switch to CRM Results tab to see medium quality using role
    fireEvent.click(screen.getByRole('tab', { name: 'CRM Results' }));
    
    await waitFor(() => {
      expect(screen.getByText('medium')).toBeInTheDocument();
    });

    // Switch to Email Results tab to see high quality using role
    fireEvent.click(screen.getByRole('tab', { name: 'Email Results' }));
    
    await waitFor(() => {
      expect(screen.getByText('high')).toBeInTheDocument();
    });
  });

  it('should display correlation metrics correctly', async () => {
    render(
      <ComprehensiveResultsDisplay
        comprehensiveResults={mockComprehensiveResults}
        handleApproveResults={mockHandleApproveResults}
        handleRequestRevision={mockHandleRequestRevision}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Switch to correlations tab using role
    fireEvent.click(screen.getByRole('tab', { name: 'Data Correlations' }));
    
    await waitFor(() => {
      expect(screen.getByText('12')).toBeInTheDocument(); // cross_references
      expect(screen.getByText('92%')).toBeInTheDocument(); // data_consistency
      expect(screen.getByText('8')).toBeInTheDocument(); // vendor_mentions
      expect(screen.getByText('89%')).toBeInTheDocument(); // quality_score
    });
  });
});