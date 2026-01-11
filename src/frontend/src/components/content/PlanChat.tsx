import React from "react";
import {
  CheckmarkRegular,
  DismissRegular,
} from "@fluentui/react-icons";
import { PlanChatProps, MPlanData } from "../../models/plan";
import { AgentMessageData, WebsocketMessageType, WorkflowProgressUpdate } from "@/models";
import renderUserPlanMessage from "./streaming/StreamingUserPlanMessage";
import { renderPlanExecutionMessage, renderThinkingState } from "./streaming/StreamingPlanState";
import ContentNotFound from "../NotFound/ContentNotFound";
import PlanChatBody from "./PlanChatBody";
import renderAgentMessages from "./streaming/StreamingAgentMessage";
import StreamingBufferMessage from "./streaming/StreamingBufferMessage";
import ClarificationUI from "./ClarificationUI";
import PlanApprovalDisplay from "./PlanApprovalDisplay";
import WorkflowProgressDisplay from "./WorkflowProgressDisplay";
import ErrorDisplay from "./ErrorDisplay";
import InlineToaster from "../toast/InlineToaster";

interface SimplifiedPlanChatProps extends PlanChatProps {
  onPlanReceived?: (planData: MPlanData) => void;
  initialTask?: string;
  planApprovalRequest: MPlanData | null;
  waitingForPlan: boolean;
  messagesContainerRef: React.RefObject<HTMLDivElement>;
  streamingMessageBuffer: string;
  showBufferingText: boolean;
  agentMessages: AgentMessageData[];
  showProcessingPlanSpinner: boolean;
  showApprovalButtons: boolean;
  handleApprovePlan: () => Promise<void>;
  handleRejectPlan: () => Promise<void>;
  processingApproval: boolean;
  clarificationMessage?: any;
  workflowProgress?: WorkflowProgressUpdate | null;
  // Error handling props
  workflowError?: {
    title?: string;
    message: string;
  } | null;
  onRestartWorkflow?: () => void;
}

const PlanChat: React.FC<SimplifiedPlanChatProps> = (props) => {
  const {
    planData,
    input,
    setInput,
    submittingChatDisableInput,
    OnChatSubmit,
    onPlanApproval,
    onPlanReceived,
    initialTask,
    planApprovalRequest,
    waitingForPlan,
    messagesContainerRef,
    streamingMessageBuffer,
    showBufferingText,
    agentMessages,
    showProcessingPlanSpinner,
    showApprovalButtons,
    handleApprovePlan,
    handleRejectPlan,
    processingApproval,
    clarificationMessage,
    workflowProgress,
    workflowError,
    onRestartWorkflow
  } = props || {};

  if (!planData)
    return (
      <ContentNotFound subtitle="The requested page could not be found." />
    );
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',

    }}>
      {/* Messages Container */}
      <InlineToaster />
      <div
        ref={messagesContainerRef}
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '32px 0',
          maxWidth: '800px',
          margin: '0 auto',
          width: '100%'
        }}
      >
        {/* User plan message */}
        {renderUserPlanMessage(planApprovalRequest, initialTask, planData)}

        {/* AI thinking state */}
        {renderThinkingState(waitingForPlan)}

        {/* Plan response with approval buttons - only show when NOT in clarification phase */}
        {/* Once plan is approved and we're in clarification, hide this to avoid confusion */}
        {!clarificationMessage && (
          <PlanApprovalDisplay
            planApprovalRequest={planApprovalRequest}
            handleApprovePlan={handleApprovePlan}
            handleRejectPlan={handleRejectPlan}
            processingApproval={processingApproval}
            showApprovalButtons={showApprovalButtons}
          />
        )}

        {/* Error Display - show when workflow encounters an error */}
        {workflowError && onRestartWorkflow && (
          <ErrorDisplay
            title={workflowError.title}
            message={workflowError.message}
            onRestart={onRestartWorkflow}
            isLoading={submittingChatDisableInput}
          />
        )}

        {/* Workflow Progress Display - show when plan is approved and agents are executing */}
        {workflowProgress && !clarificationMessage && !workflowError && (
          <WorkflowProgressDisplay
            progress={workflowProgress}
            planData={planData}
            planApprovalRequest={planApprovalRequest}
          />
        )}

        {/* All agent messages in chronological order */}
        {!workflowError && renderAgentMessages(agentMessages)}

        {/* Clarification UI - shown when user needs to approve or revise */}
        {clarificationMessage && !workflowError && (
          <ClarificationUI
            agentResult={clarificationMessage.agent_result || ''}
            onApprove={() => OnChatSubmit('OK')}
            onRetry={(feedback) => OnChatSubmit(feedback)}
            isLoading={submittingChatDisableInput}
          />
        )}

        {!workflowError && showProcessingPlanSpinner && renderPlanExecutionMessage()}
        {/* Streaming plan updates */}
        {!workflowError && showBufferingText && (
          <StreamingBufferMessage
            streamingMessageBuffer={streamingMessageBuffer}
            isStreaming={true}
          />
        )}
      </div>

      {/* Chat Input - only show if no plan is waiting for approval and no error */}
      {!workflowError && (
        <PlanChatBody
          planData={planData}
          input={input}
          setInput={setInput}
          submittingChatDisableInput={submittingChatDisableInput}
          OnChatSubmit={OnChatSubmit}
          waitingForPlan={waitingForPlan}
          loading={false} />
      )}

    </div>
  );
};

export default PlanChat;