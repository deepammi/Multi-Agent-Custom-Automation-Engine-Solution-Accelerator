import React, { useEffect, useState } from "react";
import {
  Body1,
  Caption1,
} from "@fluentui/react-components";
import {
  ArrowTurnDownRightRegular,
  CheckmarkCircle20Filled,
  Clock20Regular,
  ArrowSync20Regular,
} from "@fluentui/react-icons";
import { MPlanData, PlanDetailsProps, AgentProgress } from "../../models";
import { getAgentIcon, getAgentDisplayNameWithSuffix } from '../../utils/agentIconUtils';
import ContentNotFound from "../NotFound/ContentNotFound";
import "../../styles/planpanelright.css";


const PlanPanelRight: React.FC<PlanDetailsProps> = ({
  planData,
  loading,
  planApprovalRequest,
  agentMessages
}) => {
  const [agentProgress, setAgentProgress] = useState<Map<string, AgentProgress>>(new Map());

  // Build chronological activity list - keep ALL activities, not just latest per agent
  useEffect(() => {
    const progressMap = new Map<string, AgentProgress>();
    let activityIndex = 0;
    
    // For completed tasks, prioritize stored agent_progress from planData
    if (planData && (planData as any).overall_status === 'completed' && (planData as any).agent_progress) {
      console.log('📜 Loading agent progress from completed task');
      (planData as any).agent_progress.forEach((p: AgentProgress) => {
        progressMap.set(`activity-${activityIndex++}`, p);
      });
      setAgentProgress(progressMap);
      return; // Use stored progress for completed tasks
    }
    
    // For active tasks, build from real-time messages
    // 1. Always add Planner first if we have a plan approval request
    if (planApprovalRequest) {
      progressMap.set(`activity-${activityIndex++}`, {
        agent_name: 'Planner',
        status: 'routing completed',
        timestamp: planApprovalRequest.timestamp || new Date().toISOString()
      });
    }
    
    // 2. Add ALL agent messages chronologically (don't overwrite, keep all)
    if (agentMessages && agentMessages.length > 0) {
      agentMessages.forEach((msg) => {
        const agentName = msg.agent || 'Unknown';
        
        // Skip Group_Chat_Manager (old Azure backend artifact)
        if (agentName === 'Group_Chat_Manager') return;
        
        const content = msg.content || '';
        const contentLower = content.toLowerCase();
        
        // Determine meaningful status
        let status = '';
        
        // Check for specific status keywords
        if (contentLower.includes('📊 processing invoice extraction')) {
          status = 'extracting invoice data';
        } else if (contentLower.includes('✅ invoice extraction complete')) {
          status = 'extraction complete';
        } else if (contentLower.includes('awaiting approval')) {
          status = 'awaiting approval';
        } else if (contentLower.includes('approved and stored')) {
          status = 'completed';
        } else if (contentLower.includes('extraction approved')) {
          status = 'approved';
        } else if (contentLower.includes('completed')) {
          status = 'completed';
        } else if (contentLower.includes('processing')) {
          status = 'processing';
        } else {
          // For other messages, extract first meaningful part
          const firstLine = content.split('\n')[0].trim();
          if (firstLine.length > 0 && firstLine.length < 60) {
            status = firstLine;
          } else if (firstLine.length >= 60) {
            status = firstLine.substring(0, 50) + '...';
          } else {
            status = 'active';
          }
        }
        
        // Add as new entry with unique key (don't overwrite!)
        progressMap.set(`activity-${activityIndex++}`, {
          agent_name: agentName,
          status: status,
          timestamp: typeof msg.timestamp === 'string' ? msg.timestamp : new Date().toISOString()
        });
      });
    }
    
    // 3. Fallback: Load from planData if no messages yet
    if (progressMap.size === 0 && planData && (planData as any).agent_progress) {
      (planData as any).agent_progress.forEach((p: AgentProgress) => {
        progressMap.set(`activity-${activityIndex++}`, p);
      });
    }
    
    setAgentProgress(progressMap);
  }, [agentMessages, planData, planApprovalRequest]);

  if (!planData && !loading) {
    return <ContentNotFound subtitle="The requested page could not be found." />;
  }

  // Extract plan steps from the planApprovalRequest
  const extractPlanSteps = () => {
    if (!planApprovalRequest || !planApprovalRequest.steps || planApprovalRequest.steps.length === 0) {
      return [];
    }

    return planApprovalRequest.steps.map((step, index) => {
      const action = step.action || step.cleanAction || '';
      const isHeading = action.trim().endsWith(':');

      return {
        text: action.trim(),
        isHeading,
        key: `${index}-${action.substring(0, 20)}`
      };
    }).filter(step => step.text.length > 0);
  };

  // Render Plan Section
  const renderPlanSection = () => {
    const planSteps = extractPlanSteps();

    return (
      <div className="plan-section">
        <Body1 className="plan-section__title">
          Plan Overview
        </Body1>

        {planSteps.length === 0 ? (
          <div className="plan-section__empty">
            Plan is being generated...
          </div>
        ) : (
          <div className="plan-steps">
            {planSteps.map((step, index) => (
              <div key={step.key} className="plan-step">
                {step.isHeading ? (
                  // Heading - larger text, bold
                  <Body1 className="plan-step__heading">
                    {step.text}
                  </Body1>
                ) : (
                  // Sub-step - with arrow
                  <div className="plan-step__content">
                    <ArrowTurnDownRightRegular className="plan-step__arrow" />
                    <Body1 className="plan-step__text">
                      {step.text}
                    </Body1>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Get status icon based on status text
  const getStatusIcon = (status: string) => {
    if (status.includes('completed')) {
      return <CheckmarkCircle20Filled style={{ color: 'var(--colorPaletteGreenForeground1)' }} />;
    } else if (status.includes('waiting')) {
      return <Clock20Regular style={{ color: 'var(--colorPaletteYellowForeground1)' }} />;
    } else if (status.includes('processing')) {
      return <ArrowSync20Regular style={{ color: 'var(--colorBrandForeground1)' }} />;
    }
    return <Clock20Regular style={{ color: 'var(--colorNeutralForeground3)' }} />;
  };

  // Render Progress Dashboard Section
  const renderProgressDashboard = () => {
    const progressArray = Array.from(agentProgress.values());
    
    return (
      <div className="progress-dashboard">
        <Body1 className="progress-dashboard__title">
          Progress Dashboard
        </Body1>

        {progressArray.length === 0 ? (
          <div className="progress-dashboard__empty">
            <Caption1>No agent activity yet...</Caption1>
          </div>
        ) : (
          <div className="progress-list">
            {progressArray.map((progress) => (
              <div key={`${progress.agent_name}-${progress.timestamp}`} className="progress-item">
                {/* Status Icon */}
                <div className="progress-item__icon">
                  {getStatusIcon(progress.status)}
                </div>

                {/* Agent Info */}
                <div className="progress-item__info">
                  <Body1 className="progress-item__agent">
                    {progress.agent_name}
                  </Body1>
                  <Caption1 className="progress-item__status">
                    {progress.status}
                  </Caption1>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Render Agents Section
  const renderAgentsSection = () => {
    const agents = planApprovalRequest?.team || [];

    return (
      <div className="agents-section">
        <Body1 className="agents-section__title">
          Agent Team
        </Body1>

        {agents.length === 0 ? (
          <div className="agents-section__empty">
            No agents assigned yet...
          </div>
        ) : (
          <div className="agents-list">
            {agents.map((agentName, index) => (
              <div key={`${agentName}-${index}`} className="agent-item">
                {/* Agent Icon */}
                <div className="agent-item__icon">
                  {getAgentIcon(agentName, planData, planApprovalRequest)}
                </div>

                {/* Agent Info - just name */}
                <div className="agent-item__info">
                  <Body1 className="agent-item__name">
                    {getAgentDisplayNameWithSuffix(agentName)}
                  </Body1>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Main render
  return (
    <div className="plan-panel-right">
      {/* Progress Dashboard on top - always show */}
      {renderProgressDashboard()}

      {/* Plan section - only show if we have approval request */}
      {planApprovalRequest && renderPlanSection()}

      {/* Agents section - only show if we have approval request */}
      {planApprovalRequest && renderAgentsSection()}
    </div>
  );
};

export default PlanPanelRight;