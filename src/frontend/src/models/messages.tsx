import { AgentType, StepStatus, PlanStatus, WebsocketMessageType } from './enums';
import { MPlanData } from './plan';



/**
 * Message sent to request approval for a step
 */
export interface ApprovalRequest {
    /** Step identifier */
    step_id: string;
    /** Plan identifier */
    plan_id: string;
    /** Session identifier */
    session_id: string;
    /** User identifier */
    user_id: string;
    /** Action to be performed */
    action: string;
    /** Agent assigned to this step */
    agent: AgentType;
}

/**
 * Message containing human feedback on a step
 */
export interface HumanFeedback {
    /** Optional step identifier */
    step_id?: string;
    /** Plan identifier */
    plan_id: string;
    /** Session identifier */
    session_id: string;
    /** Whether the step is approved */
    approved: boolean;
    /** Optional feedback from human */
    human_feedback?: string;
    /** Optional updated action */
    updated_action?: string;
}

/**
 * Message containing human clarification on a plan
 */
export interface HumanClarification {
    request_id: string;
    answer: string;
    plan_id: string;
    m_plan_id: string;
}

/**
 * Message sent to an agent to perform an action
 */
export interface ActionRequest {
    /** Step identifier */
    step_id: string;
    /** Plan identifier */
    plan_id: string;
    /** Session identifier */
    session_id: string;
    /** Action to be performed */
    action: string;
    /** Agent assigned to this step */
    agent: AgentType;
}

/**
 * Message containing the response from an agent after performing an action
 */
export interface ActionResponse {
    /** Step identifier */
    step_id: string;
    /** Plan identifier */
    plan_id: string;
    /** Session identifier */
    session_id: string;
    /** Result of the action */
    result: string;
    /** Status after performing the action */
    status: StepStatus;
}

/**
 * Message for updating the plan state
 */
export interface PlanStateUpdate {
    /** Plan identifier */
    plan_id: string;
    /** Session identifier */
    session_id: string;
    /** Overall status of the plan */
    overall_status: PlanStatus;
}



export interface StreamMessage {
    type: WebsocketMessageType
    plan_id?: string;
    session_id?: string;
    data?: any;
    timestamp?: string | number;
}

export interface StreamingPlanUpdate {
    plan_id: string;
    session_id?: string;
    step_id?: string;
    agent_name?: string;
    content?: string;
    status?: 'in_progress' | 'completed' | 'error' | 'creating_plan' | 'pending_approval';
    message_type?: 'thinking' | 'action' | 'result' | 'clarification_needed' | 'plan_approval_request';
    timestamp?: number;
    is_final?: boolean;
}

export interface PlanApprovalRequestData {
    plan_id: string;
    session_id: string;
    plan: {
        steps: Array<{
            id: string;
            description: string;
            agent: string;
            estimated_duration?: string;
        }>;
        total_steps: number;
        estimated_completion?: string;
    };
    status: 'PENDING_APPROVAL';
}

export interface PlanApprovalResponseData {
    plan_id: string;
    session_id: string;
    approved: boolean;
    feedback?: string;
}

// Structured plan approval request
export interface ParsedPlanApprovalRequest {
    type: WebsocketMessageType.PLAN_APPROVAL_REQUEST;
    plan_id: string;
    parsedData: MPlanData;
    rawData: string;
}

export interface ParsedUserClarification {
    type: WebsocketMessageType.USER_CLARIFICATION_REQUEST;
    question: string;
    request_id: string;
    agent_result?: string;
}

// New interfaces for comprehensive multi-agent workflow

export interface AgentResult {
    status: 'completed' | 'error';
    result: string | object;
    metadata: {
        service_used: string;
        data_quality: 'high' | 'medium' | 'low';
        execution_time: number;
        // Additional metadata fields for analysis agent
        analysis_length?: number;
        correlation_score?: number;
        llm_used?: string;
    };
}

export interface ComprehensiveResultsMessage {
    plan_id: string;
    results: {
        gmail?: AgentResult;
        accounts_payable?: AgentResult;
        crm?: AgentResult;
        analysis?: AgentResult;
    };
    correlations: {
        cross_references: number;
        data_consistency: number;
        vendor_mentions: number;
        quality_score: number;
    };
    executive_summary: string;
    recommendations: string[];
    timestamp: string;
}

export interface FinalResultsApprovalRequest {
    plan_id: string;
    comprehensive_results: ComprehensiveResultsMessage;
    question: string;
    revision_options: {
        full_replan: boolean;
        specific_agents: string[];
        analysis_only: boolean;
    };
}

export interface FinalResultsApprovalResponse {
    plan_id: string;
    approved: boolean;
    revision_type: 'none' | 'full_replan' | 'specific_agents' | 'analysis_only';
    target_agents?: string[];
    feedback?: string;
    export_results?: boolean;
}

export interface WorkflowProgressUpdate {
    plan_id: string;
    current_stage: 'plan_creation' | 'plan_approval' | 'gmail_execution' | 'ap_execution' | 'crm_execution' | 'analysis_execution' | 'results_compilation' | 'final_approval' | 'completed';
    progress_percentage: number;
    current_agent?: string;
    estimated_remaining?: number;
    completed_agents: string[];
    pending_agents: string[];
}