import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import WorkflowProgressDisplay from '../components/content/WorkflowProgressDisplay';
import { WorkflowProgressUpdate } from '../models';

// Mock FluentUI components for testing
const mockProgressUpdate: WorkflowProgressUpdate = {
  plan_id: 'test-plan-123',
  current_stage: 'gmail_execution',
  progress_percentage: 45,
  current_agent: 'Gmail_Agent',
  completed_agents: ['Planner_Agent'],
  pending_agents: ['AP_Agent', 'CRM_Agent', 'Analysis_Agent']
};

describe('WorkflowProgressDisplay', () => {
  it('renders progress information correctly', () => {
    render(<WorkflowProgressDisplay progress={mockProgressUpdate} />);
    
    // Check for stage display
    expect(screen.getByText('Processing Gmail Data')).toBeInTheDocument();
    
    // Check for progress percentage
    expect(screen.getByText('45%')).toBeInTheDocument();
    
    // Check for agent progress section
    expect(screen.getByText('Agent Progress:')).toBeInTheDocument();
  });

  it('shows completed workflow state', () => {
    const completedProgress: WorkflowProgressUpdate = {
      ...mockProgressUpdate,
      current_stage: 'completed',
      progress_percentage: 100,
      current_agent: undefined,
      completed_agents: ['Planner_Agent', 'Gmail_Agent', 'AP_Agent', 'CRM_Agent', 'Analysis_Agent'],
      pending_agents: []
    };

    render(<WorkflowProgressDisplay progress={completedProgress} />);
    
    expect(screen.getByText('Workflow Complete')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('does not render when progress is null', () => {
    const { container } = render(<WorkflowProgressDisplay progress={null as any} />);
    expect(container.firstChild).toBeNull();
  });

  it('validates requirements for real-time progress display', () => {
    // Property 12: Real-time Progress Display
    // Validates: Requirements 3.2, 3.3
    
    render(<WorkflowProgressDisplay progress={mockProgressUpdate} />);
    
    // Requirement 3.2: Agent-specific status indicators
    expect(screen.getByText('Agent Progress:')).toBeInTheDocument();
    
    // Requirement 3.3: Progress bar for workflow completion  
    // Progress bar should be present (tested via percentage display)
    expect(screen.getByText('45%')).toBeInTheDocument();
    
    // Should show current stage information
    expect(screen.getByText('Processing Gmail Data')).toBeInTheDocument();
  });
});