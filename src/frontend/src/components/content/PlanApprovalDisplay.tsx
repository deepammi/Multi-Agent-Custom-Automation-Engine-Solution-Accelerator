import React from 'react';
import { MPlanData } from '@/models';
import renderPlanResponse from './streaming/StreamingPlanResponse';

interface PlanApprovalDisplayProps {
  planApprovalRequest: MPlanData | null;
  handleApprovePlan: () => Promise<void>;
  handleRejectPlan: () => Promise<void>;
  processingApproval: boolean;
  showApprovalButtons: boolean;
}

/**
 * Component wrapper for plan approval display
 * Ensures hooks are called consistently
 */
const PlanApprovalDisplay: React.FC<PlanApprovalDisplayProps> = ({
  planApprovalRequest,
  handleApprovePlan,
  handleRejectPlan,
  processingApproval,
  showApprovalButtons
}) => {
  // Always render, but return null if no approval request
  if (!planApprovalRequest) {
    return null;
  }

  return (
    <>
      {renderPlanResponse(
        planApprovalRequest,
        handleApprovePlan,
        handleRejectPlan,
        processingApproval,
        showApprovalButtons
      )}
    </>
  );
};

export default PlanApprovalDisplay;
