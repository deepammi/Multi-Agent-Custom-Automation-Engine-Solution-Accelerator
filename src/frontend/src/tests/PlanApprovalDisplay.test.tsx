import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import PlanApprovalDisplay from '../components/content/PlanApprovalDisplay';
import { MPlanData } from '../models';

// Mock the utility functions
vi.mock('../utils/agentIconUtils', () => ({
  getAgentIcon: vi.fn(() => <div data-testid="agent-icon">Icon</div>),
  getAgentDisplayName: vi.fn((name: string) => `Display ${name}`)
}));

describe('PlanApprovalDisplay Component', () => {
  const mockHandleApprovePlan = vi.fn();
  const mockHandleRejectPlan = vi.fn();

  const mockPlanData: MPlanData = {
    id: 'test-plan-1',
    status: 'pending',
    user_request: 'Test multi-agent workflow request',
    team: ['gmail', 'accounts_payable', 'crm', 'analysis'],
    facts: 'This is a comprehensive test plan with multiple agents working in sequence.',
    steps: [
      {
        id: 1,
        action: 'Analyze email requirements',
        cleanAction: 'Analyze email requirements',
        agent: 'gmail'
      },
      {
        id: 2,
        action: 'Process financial data',
        cleanAction: 'Process financial data',
        agent: 'accounts_payable'
      },
      {
        id: 3,
        action: 'Update customer records',
        cleanAction: 'Update customer records',
        agent: 'crm'
      },
      {
        id: 4,
        action: 'Generate comprehensive analysis',
        cleanAction: 'Generate comprehensive analysis',
        agent: 'analysis'
      }
    ],
    context: {
      task: 'Multi-agent workflow test',
      participant_descriptions: {
        'gmail': 'Email management and processing agent',
        'accounts_payable': 'Financial data processing and invoice management',
        'crm': 'Customer relationship management and data updates',
        'analysis': 'Data analysis and report generation'
      }
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render plan approval display with all required elements', () => {
    render(
      <PlanApprovalDisplay
        planApprovalRequest={mockPlanData}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Check for main elements
    expect(screen.getByText('Plan Approval Required')).toBeInTheDocument();
    expect(screen.getByText('Test multi-agent workflow request')).toBeInTheDocument();
    expect(screen.getByText('Awaiting Approval')).toBeInTheDocument();
    
    // Check for metadata
    expect(screen.getByText(/Estimated Duration:/)).toBeInTheDocument();
    expect(screen.getByText(/Agents:/)).toBeInTheDocument();
    expect(screen.getByText(/Steps:/)).toBeInTheDocument();
    
    // Check for agent sequence
    expect(screen.getByText('Agent Execution Sequence')).toBeInTheDocument();
    
    // Check for approval buttons
    expect(screen.getByText('Approve Plan')).toBeInTheDocument();
    expect(screen.getByText('Modify Plan')).toBeInTheDocument();
    expect(screen.getByText('Cancel Plan')).toBeInTheDocument();
  });

  it('should display agent sequence with correct information', () => {
    render(
      <PlanApprovalDisplay
        planApprovalRequest={mockPlanData}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Check that agent sequence is displayed
    expect(screen.getByText('Agent Execution Sequence')).toBeInTheDocument();
    
    // Check for agent display names (mocked to return "Display {name}")
    expect(screen.getByText('Display gmail')).toBeInTheDocument();
    expect(screen.getByText('Display accounts_payable')).toBeInTheDocument();
    expect(screen.getByText('Display crm')).toBeInTheDocument();
    expect(screen.getByText('Display analysis')).toBeInTheDocument();
  });

  it('should handle approve plan button click', async () => {
    render(
      <PlanApprovalDisplay
        planApprovalRequest={mockPlanData}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    const approveButton = screen.getByText('Approve Plan');
    fireEvent.click(approveButton);

    expect(mockHandleApprovePlan).toHaveBeenCalledTimes(1);
  });

  it('should handle cancel plan button click', async () => {
    render(
      <PlanApprovalDisplay
        planApprovalRequest={mockPlanData}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    const cancelButton = screen.getByText('Cancel Plan');
    fireEvent.click(cancelButton);

    expect(mockHandleRejectPlan).toHaveBeenCalledTimes(1);
  });

  it('should show loading state when creating plan', () => {
    const emptyPlanData: MPlanData = {
      id: 'test-plan-1',
      status: 'creating',
      user_request: 'Test request',
      team: [],
      facts: '',
      steps: [],
      context: {
        task: 'Test task',
        participant_descriptions: {}
      }
    };

    render(
      <PlanApprovalDisplay
        planApprovalRequest={emptyPlanData}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    expect(screen.getByText('Creating comprehensive multi-agent plan...')).toBeInTheDocument();
  });

  it('should disable buttons when processing approval', () => {
    render(
      <PlanApprovalDisplay
        planApprovalRequest={mockPlanData}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={true}
        showApprovalButtons={true}
      />
    );

    const approveButton = screen.getByText('Approving...');
    const modifyButton = screen.getByText('Modify Plan');
    const cancelButton = screen.getByText('Cancel Plan');

    expect(approveButton).toBeDisabled();
    expect(modifyButton).toBeDisabled();
    expect(cancelButton).toBeDisabled();
  });

  it('should not show buttons when showApprovalButtons is false', () => {
    render(
      <PlanApprovalDisplay
        planApprovalRequest={mockPlanData}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={false}
        showApprovalButtons={false}
      />
    );

    expect(screen.queryByText('Approve Plan')).not.toBeInTheDocument();
    expect(screen.queryByText('Modify Plan')).not.toBeInTheDocument();
    expect(screen.queryByText('Cancel Plan')).not.toBeInTheDocument();
  });

  it('should return null when no plan approval request is provided', () => {
    const { container } = render(
      <PlanApprovalDisplay
        planApprovalRequest={null}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should display expandable sections with plan details', () => {
    render(
      <PlanApprovalDisplay
        planApprovalRequest={mockPlanData}
        handleApprovePlan={mockHandleApprovePlan}
        handleRejectPlan={mockHandleRejectPlan}
        processingApproval={false}
        showApprovalButtons={true}
      />
    );

    // Check for expandable sections
    expect(screen.getByText('Plan Context & Analysis')).toBeInTheDocument();
    expect(screen.getByText('Detailed Execution Steps')).toBeInTheDocument();
    expect(screen.getByText('Team Configuration')).toBeInTheDocument();
  });
});