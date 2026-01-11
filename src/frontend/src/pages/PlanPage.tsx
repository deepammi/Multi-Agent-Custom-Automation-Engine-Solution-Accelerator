import React, { useCallback, useEffect, useRef, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Spinner, Text } from "@fluentui/react-components";
import { PlanDataService } from "../services/PlanDataService";
import { ProcessedPlanData, WebsocketMessageType, MPlanData, AgentMessageData, AgentMessageType, ParsedUserClarification, AgentType, PlanStatus, FinalMessage, TeamConfig, ComprehensiveResultsMessage, FinalResultsApprovalRequest, WorkflowProgressUpdate, AgentResult } from "../models";
import PlanChat from "../components/content/PlanChat";
import PlanPanelRight from "../components/content/PlanPanelRight";
import PlanPanelLeft from "../components/content/PlanPanelLeft";
import CoralShellColumn from "../coral/components/Layout/CoralShellColumn";
import CoralShellRow from "../coral/components/Layout/CoralShellRow";
import Content from "../coral/components/Content/Content";
import ContentToolbar from "../coral/components/Content/ContentToolbar";
import {
    useInlineToaster,
} from "../components/toast/InlineToaster";
import Octo from "../coral/imports/Octopus.png";
import PanelRightToggles from "../coral/components/Header/PanelRightToggles";
import { TaskListSquareLtr } from "../coral/imports/bundleicons";
import LoadingMessage, { loadingMessages } from "../coral/components/LoadingMessage";
import webSocketService from "../services/WebSocketService";
import { APIService } from "../api/apiService";
import { StreamMessage, StreamingPlanUpdate } from "../models";
import { usePlanCancellationAlert } from "../hooks/usePlanCancellationAlert";
import PlanCancellationDialog from "../components/common/PlanCancellationDialog";

import "../styles/PlanPage.css"

// Create API service instance
const apiService = new APIService();

/**
 * Page component for displaying a specific plan
 * Accessible via the route /plan/{plan_id}
 */
const PlanPage: React.FC = () => {
    const { planId } = useParams<{ planId: string }>();
    const navigate = useNavigate();
    const { showToast, dismissToast } = useInlineToaster();
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const [input, setInput] = useState<string>("");
    const [planData, setPlanData] = useState<ProcessedPlanData | any>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [submittingChatDisableInput, setSubmittingChatDisableInput] = useState<boolean>(true);
    const [errorLoading, setErrorLoading] = useState<boolean>(false);
    const [clarificationMessage, setClarificationMessage] = useState<ParsedUserClarification | null>(null);
    const [processingApproval, setProcessingApproval] = useState<boolean>(false);
    const [planApprovalRequest, setPlanApprovalRequest] = useState<MPlanData | null>(null);
    const [reloadLeftList, setReloadLeftList] = useState<boolean>(true);
    const [waitingForPlan, setWaitingForPlan] = useState<boolean>(true);
    const [showProcessingPlanSpinner, setShowProcessingPlanSpinner] = useState<boolean>(false);
    const [showApprovalButtons, setShowApprovalButtons] = useState<boolean>(true);
    const [continueWithWebsocketFlow, setContinueWithWebsocketFlow] = useState<boolean>(false);
    const [selectedTeam, setSelectedTeam] = useState<TeamConfig | null>(null);
    // WebSocket connection state
    const [wsConnected, setWsConnected] = useState<boolean>(false);
    const [streamingMessages, setStreamingMessages] = useState<StreamingPlanUpdate[]>([]);
    const [streamingMessageBuffer, setStreamingMessageBuffer] = useState<string>("");
    const [showBufferingText, setShowBufferingText] = useState<boolean>(false);
    const [agentMessages, setAgentMessages] = useState<AgentMessageData[]>([]);

    // Plan approval state - track when plan is approved
    const [planApproved, setPlanApproved] = useState<boolean>(false);
    
    // Track if task is completed to prevent spinner from showing again
    const [taskCompleted, setTaskCompleted] = useState<boolean>(false);

    // Extraction approval state
    const [extractionApprovalData, setExtractionApprovalData] = useState<any>(null);
    const [showExtractionApproval, setShowExtractionApproval] = useState<boolean>(false);
    const [editableInvoiceJson, setEditableInvoiceJson] = useState<string>('');
    const [jsonError, setJsonError] = useState<string>('');
    const [visualizationUrl, setVisualizationUrl] = useState<string | null>(null);

    // Plan cancellation dialog state
    const [showCancellationDialog, setShowCancellationDialog] = useState<boolean>(false);
    const [pendingNavigation, setPendingNavigation] = useState<(() => void) | null>(null);
    const [cancellingPlan, setCancellingPlan] = useState<boolean>(false);

    const [loadingMessage, setLoadingMessage] = useState<string>(loadingMessages[0]);

    // Workflow progress state for real-time progress display
    const [workflowProgress, setWorkflowProgress] = useState<WorkflowProgressUpdate | null>(null);

    // Error handling state for workflow failures
    const [workflowError, setWorkflowError] = useState<{
        title?: string;
        message: string;
    } | null>(null);

    // Plan cancellation alert hook
    const { isPlanActive, handleNavigationWithConfirmation } = usePlanCancellationAlert({
        planData,
        planApprovalRequest,
        onNavigate: pendingNavigation || (() => {})
    });

    // Reset plan variables function - defined early to avoid temporal dead zone
    const resetPlanVariables = useCallback(() => {
        setInput("");
        setPlanData(null);
        setLoading(true);
        setSubmittingChatDisableInput(true);
        setErrorLoading(false);
        setClarificationMessage(null);
        setProcessingApproval(false);
        setPlanApprovalRequest(null);
        setReloadLeftList(true);
        setWaitingForPlan(true);
        setShowProcessingPlanSpinner(false);
        setShowApprovalButtons(true);
        setContinueWithWebsocketFlow(false);
        setWsConnected(false);
        setStreamingMessages([]);
        setStreamingMessageBuffer("");
        setShowBufferingText(false);
        setAgentMessages([]);
        setTaskCompleted(false);
    }, [
        setInput,
        setPlanData,
        setLoading,
        setSubmittingChatDisableInput,
        setErrorLoading,
        setClarificationMessage,
        setProcessingApproval,
        setPlanApprovalRequest,
        setReloadLeftList,
        setWaitingForPlan,
        setShowProcessingPlanSpinner,
        setShowApprovalButtons,
        setContinueWithWebsocketFlow,
        setWsConnected,
        setStreamingMessages,
        setStreamingMessageBuffer,
        setShowBufferingText,
        setAgentMessages,
        setTaskCompleted
    ]);

    // Handle workflow restart after error
    const handleRestartWorkflow = useCallback(() => {
        console.log('🔄 Restarting workflow after error');
        
        // Clear error state
        setWorkflowError(null);
        
        // Reset all workflow state
        resetPlanVariables();
        
        // Navigate to home page to start new task
        navigate('/', { state: { focusInput: true } });
    }, [navigate, resetPlanVariables]);

    // Enable WebSocket flow immediately when plan page loads to prevent race conditions
    useEffect(() => {
        if (planId) {
            console.log('🔌 [INIT] Plan page loaded, enabling WebSocket flow for plan:', planId);
            setContinueWithWebsocketFlow(true);
        }
    }, [planId]);

    // Handle navigation with plan cancellation check
    const handleNavigationWithAlert = useCallback((navigationFn: () => void) => {
        if (!isPlanActive()) {
            // Plan is not active, proceed with navigation
            navigationFn();
            return;
        }

        // Plan is active, show confirmation dialog
        setPendingNavigation(() => navigationFn);
        setShowCancellationDialog(true);
    }, [isPlanActive]);

    // Handle confirmation dialog response
    const handleConfirmCancellation = useCallback(async () => {
        setCancellingPlan(true);
        
        try {
            if (planApprovalRequest?.id) {
                await apiService.approvePlan({
                    m_plan_id: planApprovalRequest.id,
                    plan_id: planData?.plan?.id,
                    approved: false,
                    feedback: 'Plan cancelled by user navigation'
                });
            }

            // Execute the pending navigation
            if (pendingNavigation) {
                pendingNavigation();
            }
        } catch (error) {
            console.error('❌ Failed to cancel plan:', error);
            showToast('Failed to cancel the plan properly, but navigation will continue.', 'error');
            // Still proceed with navigation even if cancellation failed
            if (pendingNavigation) {
                pendingNavigation();
            }
        } finally {
            setCancellingPlan(false);
            setShowCancellationDialog(false);
            setPendingNavigation(null);
        }
    }, [planApprovalRequest, planData, pendingNavigation, showToast]);

    const handleCancelDialog = useCallback(() => {
        setShowCancellationDialog(false);
        setPendingNavigation(null);
    }, []);



    const processAgentMessage = useCallback((agentMessageData: AgentMessageData, planData: ProcessedPlanData, is_final: boolean = false, streaming_message: string = '') => {

        // Don't persist WebSocket messages to avoid duplicates
        // Messages from WebSocket are already stored on the backend
        console.log('📤 Skipping persistence for WebSocket message:', agentMessageData.agent);
        
        // Only persist final messages for task list refresh
        if (!is_final) {
            return Promise.resolve();
        }

        // Persist final message only
        const agentMessageResponse = PlanDataService.createAgentMessageResponse(agentMessageData, planData, is_final, streaming_message);
        console.log('📤 Persisting final message:', agentMessageResponse);
        const sendPromise = apiService.sendAgentMessage(agentMessageResponse)
            .then(saved => {
                console.log('[agent_message][persisted]', {
                    agent: agentMessageData.agent,
                    type: agentMessageData.agent_type,
                    ts: agentMessageData.timestamp
                });
                
                // If this is a final message, refresh the task list after successful persistence
                if (is_final) {
                    // Single refresh with a delay to ensure backend processing is complete
                    setTimeout(() => {
                        setReloadLeftList(true);
                    }, 1000);
                }
            })
            .catch(err => {
                console.warn('[agent_message][persist-failed]', err);
                // Even if persistence fails, still refresh the task list for final messages
                // The local plan data has been updated, so the UI should reflect that
                if (is_final) {
                    setTimeout(() => {
                        setReloadLeftList(true);
                    }, 1000);
                }
            });

        return sendPromise;

    }, [setReloadLeftList]);

    // Auto-scroll helper
    const scrollToBottom = useCallback(() => {
        setTimeout(() => {
            if (messagesContainerRef.current) {
                //messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
                messagesContainerRef.current?.scrollTo({
                    top: messagesContainerRef.current.scrollHeight,
                    behavior: "smooth",
                });
            }
        }, 100);
    }, []);

    //WebsocketMessageType.PLAN_APPROVAL_REQUEST
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.PLAN_APPROVAL_REQUEST, (approvalRequest: any) => {
            console.log('📋 Plan received:', approvalRequest);

            let mPlanData: MPlanData | null = null;

            // Handle the different message structures
            if (approvalRequest.parsedData) {
                // Direct parsedData property
                mPlanData = approvalRequest.parsedData;
            } else if (approvalRequest.data && typeof approvalRequest.data === 'object') {
                // Data property with nested object
                if (approvalRequest.data.parsedData) {
                    mPlanData = approvalRequest.data.parsedData;
                } else {
                    // Try to parse the data object directly
                    mPlanData = approvalRequest.data;
                }
            } else if (approvalRequest.rawData) {
                // Parse the raw data string
                mPlanData = PlanDataService.parsePlanApprovalRequest(approvalRequest.rawData);
            } else {
                // Try to parse the entire object
                mPlanData = PlanDataService.parsePlanApprovalRequest(approvalRequest);
            }

            if (mPlanData) {
                console.log('✅ Parsed plan data:', mPlanData);
                console.log('🔘 Setting showApprovalButtons to TRUE');
                setPlanApprovalRequest(mPlanData);
                
                // Also add plan approval as an agent message for chronological display
                const planApprovalMessage = {
                    agent: AgentType.GROUP_CHAT_MANAGER,
                    agent_type: AgentMessageType.AI_AGENT,
                    timestamp: new Date().toISOString(),
                    steps: [],
                    next_steps: [],
                    content: `📋 Plan created - awaiting approval`,
                    raw_data: JSON.stringify(mPlanData) || '',
                } as AgentMessageData;
                
                setAgentMessages(prev => [...prev, planApprovalMessage]);
                
                setWaitingForPlan(false);
                setShowProcessingPlanSpinner(false);
                // ✅ CRITICAL: Enable approval buttons when approval request is received
                setShowApprovalButtons(true);
                console.log('🔘 showApprovalButtons state updated');
                scrollToBottom();
            } else {
                console.error('❌ Failed to parse plan data', approvalRequest);
            }
        });

        return () => unsubscribe();
    }, [scrollToBottom]);

    //(WebsocketMessageType.AGENT_MESSAGE_STREAMING
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.AGENT_MESSAGE_STREAMING, (streamingMessage: any) => {
            console.log('📋 Streaming Message received:', streamingMessage);
            
            // The streamingMessage is already parsed by WebSocketService.parseAgentMessageStreaming()
            // It has structure: {type, agent, content, is_final, raw_data}
            if (!streamingMessage) {
                console.warn('Received null streaming message');
                return;
            }
            
            // Check if it has content property (parsed structure)
            let content = '';
            if (streamingMessage.content) {
                content = streamingMessage.content;
            } else if (streamingMessage.data && streamingMessage.data.content) {
                // Fallback: check if content is nested in data
                content = streamingMessage.data.content;
            } else {
                console.warn('Streaming message has no content:', {
                    type: typeof streamingMessage,
                    keys: Object.keys(streamingMessage || {}),
                    streamingMessage
                });
                return;
            }
            
            // Process the content
            const line = PlanDataService.simplifyHumanClarification(content);
            setShowBufferingText(true);
            setStreamingMessageBuffer(prev => prev + line);
            //scrollToBottom();

        });

        return () => unsubscribe();
    }, [scrollToBottom]);

    //WebsocketMessageType.USER_CLARIFICATION_REQUEST
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.USER_CLARIFICATION_REQUEST, (clarificationMessage: any) => {
            console.log('📋 Clarification Message', clarificationMessage);
            console.log('📋 Current plan data User clarification', planData);
            if (!clarificationMessage) {
                console.warn('⚠️ clarification message missing data:', clarificationMessage);
                return;
            }
            
            // Handle both old format (with .data) and new format (direct properties)
            const messageData = clarificationMessage.data || clarificationMessage;
            const question = messageData.question || 'Please approve or provide revision';
            const request_id = messageData.request_id || '';
            const agent_result = messageData.agent_result || '';
            
            console.log('✅ Parsed clarification message with agent_result:', agent_result);
            
            // Store the clarification message with agent_result for ClarificationUI
            // Do NOT add to agentMessages - ClarificationUI will be rendered directly
            setClarificationMessage({
                type: WebsocketMessageType.USER_CLARIFICATION_REQUEST,
                question,
                request_id,
                agent_result
            } as any);
            
            // Log current agent messages when clarification is shown
            console.log('🔍 CLARIFICATION SHOWN - Current agent messages:', agentMessages.map(m => ({
                agent: m.agent,
                content: m.content.substring(0, 30),
                timestamp: m.timestamp
            })));
            
            setShowBufferingText(false);
            setShowProcessingPlanSpinner(false);
            setSubmittingChatDisableInput(false);
            scrollToBottom();

        });

        return () => unsubscribe();
    }, [scrollToBottom, planData, processAgentMessage, agentMessages]);
    //WebsocketMessageType.AGENT_TOOL_MESSAGE
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.AGENT_TOOL_MESSAGE, (toolMessage: any) => {
            console.log('📋 Tool Message', toolMessage);
            // scrollToBottom()

        });

        return () => unsubscribe();
    }, [scrollToBottom]);

    // Extraction Approval Request
    useEffect(() => {
        const unsubscribe = webSocketService.on('extraction_approval_request', (message: any) => {
            console.log('📊 Extraction approval request received:', message);
            console.log('📊 Message type:', typeof message);
            console.log('📊 Message keys:', Object.keys(message));
            
            if (!message) {
                console.warn('⚠️ Extraction approval message is null/undefined');
                return;
            }
            
            // Handle different message structures
            let extractionData = null;
            
            // Check if message.data.data exists (double nested)
            if (message.data?.data) {
                extractionData = message.data.data;
                console.log('📊 Using message.data.data (double nested):', extractionData);
            } else if (message.data) {
                // Message has data property
                extractionData = message.data;
                console.log('📊 Using message.data:', extractionData);
            } else if (message.type === 'extraction_approval_request') {
                // Message is the data itself
                extractionData = message;
                console.log('📊 Using message directly:', extractionData);
            }
            
            if (!extractionData) {
                console.warn('⚠️ Could not extract approval data from message');
                return;
            }
            
            console.log('📊 Extraction data plan_id:', extractionData.plan_id);
            console.log('📊 Extraction data keys:', Object.keys(extractionData));
            console.log('📊 Extraction result:', extractionData.extraction_result);
            console.log('📊 Invoice data:', extractionData.extraction_result?.invoice_data);
            
            // Hide spinner when approval is needed
            setShowProcessingPlanSpinner(false);
            setShowBufferingText(false);
            
            // Store extraction data and show approval dialog
            setExtractionApprovalData(extractionData);
            
            // Set visualization URL if provided
            if (extractionData.visualization_url) {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                setVisualizationUrl(`${apiUrl}${extractionData.visualization_url}`);
                console.log('📊 Visualization URL set:', `${apiUrl}${extractionData.visualization_url}`);
            } else {
                setVisualizationUrl(null);
            }
            
            // Initialize editable JSON with formatted invoice data
            if (extractionData.extraction_result?.invoice_data) {
                console.log('✅ Initializing JSON editor with invoice data');
                setEditableInvoiceJson(JSON.stringify(extractionData.extraction_result.invoice_data, null, 2));
                setJsonError('');
            } else {
                console.warn('⚠️ No invoice data found in extraction result - validation may have failed');
                // Provide an empty invoice template for user to fill in
                const emptyTemplate = {
                    vendor_name: "",
                    vendor_address: "",
                    invoice_number: "",
                    invoice_date: "",
                    due_date: "",
                    total_amount: "0.00",
                    subtotal: "0.00",
                    tax_amount: "0.00",
                    currency: "USD",
                    line_items: [],
                    payment_terms: "",
                    notes: "Extraction failed - please fill in manually"
                };
                setEditableInvoiceJson(JSON.stringify(emptyTemplate, null, 2));
                setJsonError('');
            }
            
            setShowExtractionApproval(true);
            
            scrollToBottom();
        });

        return () => unsubscribe();
    }, [scrollToBottom]);

    //WebsocketMessageType.FINAL_RESULT_MESSAGE
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.FINAL_RESULT_MESSAGE, (finalMessage: any) => {
            console.log('📋 Final Result Message received:', finalMessage);
            console.log('📋 Final Result Message data:', finalMessage?.data);
            console.log('📋 Final Result Message status:', finalMessage?.data?.status);
            
            if (!finalMessage) {
                console.warn('⚠️ Final result message missing data:', finalMessage);
                return;
            }
            
            // ALWAYS mark task as completed and hide spinner when final result is received
            // This prevents any race conditions with agent messages
            console.log('✅ Final result received, marking task as completed and hiding spinner');
            console.log('🔍 Current showProcessingPlanSpinner:', showProcessingPlanSpinner);
            console.log('🔍 Current taskCompleted:', taskCompleted);
            
            // Use functional updates to ensure we're working with the latest state
            setTaskCompleted(true);
            setShowProcessingPlanSpinner(false);
            setShowBufferingText(false);
            setWaitingForPlan(false);  // ✅ FIX: Hide "creating your plan" spinner
            
            console.log('🔍 After setting - taskCompleted should be true, spinner should be false');
            
            const agentMessageData = {
                agent: AgentType.GROUP_CHAT_MANAGER,
                agent_type: AgentMessageType.AI_AGENT,
                timestamp: new Date().toISOString(),
                steps: [],   // intentionally always empty
                next_steps: [],  // intentionally always empty
                content: "🎉🎉 " + (finalMessage.data?.content || ''),
                raw_data: finalMessage || '',
            } as AgentMessageData;

            console.log('✅ Parsed final result message:', agentMessageData);
            
            // Handle both "completed" and "COMPLETED" status values
            const status = finalMessage?.data?.status?.toLowerCase();
            if (status === 'completed') {
                console.log('✅ Task completed successfully');
                
                // Clear approval request to hide approval buttons
                setPlanApprovalRequest(null);
                
                setAgentMessages(prev => [...prev, agentMessageData]);
                setSelectedTeam(planData?.team || null);
                
                scrollToBottom();
                
                // Persist the agent message
                const is_final = true;
                if (planData?.plan) {
                    planData.plan.overall_status = PlanStatus.COMPLETED;
                    setPlanData({ ...planData });
                }

                // Wait for the agent message to be processed and persisted
                // The processAgentMessage function will handle refreshing the task list
                processAgentMessage(agentMessageData, planData, is_final, streamingMessageBuffer);
            } else if (status === 'rejected') {
                console.log('✅ Task rejected');
                
                // Clear approval request to hide approval buttons
                setPlanApprovalRequest(null);
                
                setAgentMessages(prev => [...prev, agentMessageData]);
                
                scrollToBottom();
            } else {
                console.warn('⚠️ Unknown final result status:', status);
                // Still add the message even if status is unknown
                setAgentMessages(prev => [...prev, agentMessageData]);
                scrollToBottom();
            }
        });

        return () => unsubscribe();
    }, [scrollToBottom, planData, processAgentMessage, streamingMessageBuffer, setSelectedTeam]);

    // WebsocketMessageType.COMPREHENSIVE_RESULTS_READY
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.COMPREHENSIVE_RESULTS_READY, (comprehensiveResults: any) => {
            console.log('📊 Comprehensive Results Ready received:', comprehensiveResults);
            
            if (!comprehensiveResults) {
                console.warn('⚠️ Comprehensive results message missing data:', comprehensiveResults);
                return;
            }
            
            // Hide spinner when comprehensive results are ready
            setShowProcessingPlanSpinner(false);
            setShowBufferingText(false);
            
            // Add comprehensive results message to agent messages for display
            const comprehensiveResultsMessage = {
                agent: AgentType.GROUP_CHAT_MANAGER,
                agent_type: AgentMessageType.AI_AGENT,
                timestamp: new Date().toISOString(),
                steps: [],
                next_steps: [],
                content: `📊 Comprehensive results compiled from all agents - ready for review`,
                raw_data: JSON.stringify(comprehensiveResults) || '',
            } as AgentMessageData;
            
            setAgentMessages(prev => [...prev, comprehensiveResultsMessage]);
            scrollToBottom();
        });

        return () => unsubscribe();
    }, [scrollToBottom]);

    // WebsocketMessageType.FINAL_RESULTS_APPROVAL_REQUEST
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.FINAL_RESULTS_APPROVAL_REQUEST, (approvalRequest: any) => {
            console.log('📋 Final Results Approval Request received:', approvalRequest);
            
            if (!approvalRequest) {
                console.warn('⚠️ Final results approval request missing data:', approvalRequest);
                return;
            }
            
            // Hide spinner when approval is requested
            setShowProcessingPlanSpinner(false);
            setShowBufferingText(false);
            
            // Add final approval request message to agent messages
            const finalApprovalMessage = {
                agent: AgentType.GROUP_CHAT_MANAGER,
                agent_type: AgentMessageType.AI_AGENT,
                timestamp: new Date().toISOString(),
                steps: [],
                next_steps: [],
                content: `🎯 Final results ready for approval - please review the comprehensive analysis`,
                raw_data: JSON.stringify(approvalRequest) || '',
            } as AgentMessageData;
            
            setAgentMessages(prev => [...prev, finalApprovalMessage]);
            
            // TODO: Set state for final results approval UI
            // This will be implemented when the ComprehensiveResultsDisplay component is integrated
            
            scrollToBottom();
        });

        return () => unsubscribe();
    }, [scrollToBottom]);

    // WebsocketMessageType.WORKFLOW_PROGRESS_UPDATE
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.WORKFLOW_PROGRESS_UPDATE, (progressUpdate: any) => {
            console.log('📈 Workflow Progress Update received:', progressUpdate);
            
            if (!progressUpdate) {
                console.warn('⚠️ Workflow progress update missing data:', progressUpdate);
                return;
            }
            
            // Store the progress data for the progress display component
            setWorkflowProgress(progressUpdate);
            
            // Update UI state based on the progress update
            const { current_stage, progress_percentage, current_agent, completed_agents, pending_agents } = progressUpdate;
            
            // Show appropriate spinner state based on current stage
            if (current_stage === 'completed') {
                setShowProcessingPlanSpinner(false);
                setTaskCompleted(true);
                // Clear progress display when completed
                setTimeout(() => setWorkflowProgress(null), 3000);
            } else if (current_stage !== 'plan_approval' && current_stage !== 'final_approval') {
                // Show spinner for execution stages, but not for approval stages
                setShowProcessingPlanSpinner(true);
            }
            
            // Optional: Add a simplified progress message to chat (less verbose than before)
            if (current_stage === 'completed' || (progress_percentage % 25 === 0 && progress_percentage > 0)) {
                const progressMessage = {
                    agent: AgentType.GROUP_CHAT_MANAGER,
                    agent_type: AgentMessageType.AI_AGENT,
                    timestamp: new Date().toISOString(),
                    steps: [],
                    next_steps: [],
                    content: `📈 ${current_stage === 'completed' ? 'Workflow completed!' : `Progress: ${Math.round(progress_percentage)}% complete`}`,
                    raw_data: JSON.stringify(progressUpdate) || '',
                } as AgentMessageData;
                
                setAgentMessages(prev => [...prev, progressMessage]);
                scrollToBottom();
            }
        });

        return () => unsubscribe();
    }, [scrollToBottom]);

    // WebSocket error handling
    useEffect(() => {
        const unsubscribe = webSocketService.on('workflow_error', (errorMessage: any) => {
            console.log('❌ Workflow Error received:', errorMessage);
            
            if (!errorMessage) {
                console.warn('⚠️ Workflow error message missing data:', errorMessage);
                return;
            }
            
            // Hide all spinners and progress indicators
            setShowProcessingPlanSpinner(false);
            setShowBufferingText(false);
            setWaitingForPlan(false);
            setWorkflowProgress(null);
            
            // Set error state
            const errorData = errorMessage.data || errorMessage;
            setWorkflowError({
                title: errorData.title || 'Workflow Error',
                message: errorData.message || 'An unexpected error occurred during workflow execution. Please start a new task.'
            });
            
            console.log('❌ Workflow error state set:', errorData);
        });

        return () => unsubscribe();
    }, []);

    //WebsocketMessageType.AGENT_MESSAGE
    useEffect(() => {
        const unsubscribe = webSocketService.on(WebsocketMessageType.AGENT_MESSAGE, (agentMessage: any) => {
            console.log('📋 Agent Message received:', agentMessage);
            console.log('📋 Current plan data:', planData);
            console.log('📋 Clarification message pending:', !!clarificationMessage);
            console.log('📋 Task completed status:', taskCompleted);
            
            // The parsed agent message might be wrapped in a data property or be direct
            let agentMessageData: AgentMessageData | null;
            
            if (agentMessage && agentMessage.data && (agentMessage.data.agent || agentMessage.data.agent_name)) {
                // Wrapped structure: { data: { agent: "...", content: "..." } }
                // Map agent_name to agent for consistency
                const data = agentMessage.data;
                agentMessageData = {
                    ...data,
                    agent: data.agent || data.agent_name || 'Unknown'
                } as AgentMessageData;
            } else if (agentMessage && (agentMessage.agent || agentMessage.agent_name)) {
                // Direct structure: { agent: "...", content: "..." }
                // Map agent_name to agent for consistency
                agentMessageData = {
                    ...agentMessage,
                    agent: agentMessage.agent || agentMessage.agent_name || 'Unknown'
                } as AgentMessageData;
            } else {
                agentMessageData = null;
            }
            
            console.log('🔍 Debug agent message parsing:', {
                hasContent: !!agentMessageData?.content,
                contentLength: agentMessageData?.content?.length || 0,
                agent: agentMessageData?.agent,
                type: typeof agentMessageData
            });
            
            if (agentMessageData && agentMessageData.content) {
                console.log('✅ Adding agent message to state:', agentMessageData.agent);
                
                agentMessageData.content = PlanDataService.simplifyHumanClarification(agentMessageData?.content);
                setAgentMessages(prev => {
                    const updated = [...prev];
                    
                    // Check for duplicate messages (same agent, same content, within 1 second)
                    const isDuplicate = updated.some(msg => {
                        if (msg.agent !== agentMessageData.agent) return false;
                        if (msg.content !== agentMessageData.content) return false;
                        
                        // Check if timestamps are within 1 second of each other
                        const msgTime = typeof msg.timestamp === 'number' ? msg.timestamp : new Date(msg.timestamp).getTime();
                        const newTime = typeof agentMessageData.timestamp === 'number' ? agentMessageData.timestamp : new Date(agentMessageData.timestamp).getTime();
                        return Math.abs(msgTime - newTime) < 1000;
                    });
                    
                    if (isDuplicate) {
                        console.log('⚠️ Duplicate message detected, skipping:', {
                            agent: agentMessageData.agent,
                            content: agentMessageData.content.substring(0, 50),
                            timestamp: agentMessageData.timestamp
                        });
                        return prev; // Return original array without adding duplicate
                    }
                    
                    console.log('✅ Adding new message:', {
                        agent: agentMessageData.agent,
                        content: agentMessageData.content.substring(0, 50),
                        timestamp: agentMessageData.timestamp,
                        totalMessages: updated.length + 1,
                        allAgents: updated.map(m => m.agent).join(', ')
                    });
                    
                    // Add the agent message
                    updated.push(agentMessageData);
                    console.log('📊 Agent messages count:', updated.length);
                    return updated;
                });
                
                // Only show spinner if task is not completed and this is not a completion message
                const isCompletionMessage = agentMessageData.content?.includes('🎉') || 
                                           agentMessageData.content?.includes('completed successfully') ||
                                           agentMessageData.content?.includes('Task approved');
                
                if (!taskCompleted && !isCompletionMessage) {
                    setShowProcessingPlanSpinner(true);
                    console.log('🔄 Showing spinner for agent message');
                } else {
                    console.log('✅ Task completed or completion message, not showing spinner');
                    // Ensure spinner is hidden if task is completed
                    setShowProcessingPlanSpinner(false);
                }
                
                scrollToBottom();
                processAgentMessage(agentMessageData, planData);
            } else {
                console.warn('⚠️ No agent message data found or missing content');
            }
        });

        return () => unsubscribe();
    }, [scrollToBottom, planData, processAgentMessage, clarificationMessage, taskCompleted]); //onPlanReceived, scrollToBottom

    // Loading message rotation effect
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (loading) {
            let index = 0;
            interval = setInterval(() => {
                index = (index + 1) % loadingMessages.length;
                setLoadingMessage(loadingMessages[index]);
            }, 3000);
        }
        return () => clearInterval(interval);
    }, [loading]);

    // Timeout protection for spinner - prevent infinite spinning
    useEffect(() => {
        if (showProcessingPlanSpinner && !taskCompleted) {
            const timeout = setTimeout(() => {
                console.warn('⚠️ Spinner timeout - hiding spinner after 30 seconds');
                setShowProcessingPlanSpinner(false);
            }, 30000);
            
            return () => clearTimeout(timeout);
        }
    }, [showProcessingPlanSpinner, taskCompleted]);

    // WebSocket connection with proper error handling and v3 backend compatibility
    useEffect(() => {
        if (planId && continueWithWebsocketFlow) {
            console.log('🔌 Connecting WebSocket:', { planId, continueWithWebsocketFlow });

            const connectWebSocket = async () => {
                try {
                    // Small delay to ensure listeners are attached before connecting
                    await new Promise(resolve => setTimeout(resolve, 100));
                    console.log('🔌 [CONNECT] Attempting WebSocket connection...');
                    await webSocketService.connect(planId);
                    console.log('✅ WebSocket connected successfully');
                } catch (error) {
                    console.error('❌ WebSocket connection failed:', error);
                    // Continue without WebSocket - the app should still work
                }
            };

            connectWebSocket();

            const handleConnectionChange = (connected: boolean) => {
                setWsConnected(connected);
                console.log('🔗 WebSocket connection status:', connected);
            };

            const handleStreamingMessage = (message: StreamMessage) => {
                console.log('📨 Received streaming message:', message);
                if (message.data && message.data.plan_id) {
                    setStreamingMessages(prev => [...prev, message.data]);
                }
            };

            const handlePlanApprovalResponse = (message: StreamMessage) => {
                console.log('✅ Plan approval response received:', message);
                if (message.data && message.data.approved) {
                    setPlanApproved(true);
                }
            };

            const handlePlanApprovalRequest = (message: StreamMessage) => {
                console.log('📥 Plan approval request received:', message);
                // This is handled by PlanChat component through its own listener
            };

            // Subscribe to all relevant v3 backend events
            const unsubscribeConnection = webSocketService.on('connection_status', (message) => {
                handleConnectionChange(message.data?.connected || false);
            });

            const unsubscribeStreaming = webSocketService.on(WebsocketMessageType.AGENT_MESSAGE, handleStreamingMessage);
            const unsubscribePlanApproval = webSocketService.on(WebsocketMessageType.PLAN_APPROVAL_RESPONSE, handlePlanApprovalResponse);
            const unsubscribePlanApprovalRequest = webSocketService.on(WebsocketMessageType.PLAN_APPROVAL_REQUEST, handlePlanApprovalRequest);
            const unsubscribeParsedPlanApprovalRequest = webSocketService.on(WebsocketMessageType.PLAN_APPROVAL_REQUEST, handlePlanApprovalRequest);

            return () => {
                console.log('🔌 Cleaning up WebSocket connections');
                unsubscribeConnection();
                unsubscribeStreaming();
                unsubscribePlanApproval();
                unsubscribePlanApprovalRequest();
                unsubscribeParsedPlanApprovalRequest();
                webSocketService.disconnect();
            };
        }
    }, [planId, loading, continueWithWebsocketFlow]);

    // Create loadPlanData function with useCallback to memoize it
    const loadPlanData = useCallback(
        async (useCache = true): Promise<ProcessedPlanData | null> => {
            if (!planId) return null;
            resetPlanVariables();
            setLoading(true);
            try {

                let planResult: ProcessedPlanData | null = null;
                console.log("Fetching plan with ID:", planId);
                planResult = await PlanDataService.fetchPlanData(planId, useCache);
                console.log("Plan data fetched:", planResult);
                // Don't set showApprovalButtons here - let the WebSocket listener handle it
                // when the approval request is received
                if (planResult?.plan?.overall_status !== PlanStatus.IN_PROGRESS) {
                    setWaitingForPlan(false);
                }
                if (planResult?.plan?.overall_status !== PlanStatus.COMPLETED) {
                    setContinueWithWebsocketFlow(true);
                }
                // Load messages from database for completed tasks (no WebSocket updates expected)
                // For in-progress tasks, messages will come via WebSocket
                if (planResult?.messages && planResult?.plan?.overall_status === PlanStatus.COMPLETED) {
                    console.log('📜 Loading historical messages for completed task:', planResult.messages.length);
                    
                    // Map messages to ensure proper format (database uses agent_name, frontend uses agent)
                    const mappedMessages = planResult.messages.map((msg: any) => ({
                        ...msg,
                        agent: msg.agent || msg.agent_name || 'System',
                        agent_type: msg.agent_type || AgentMessageType.AI_AGENT
                    }));
                    
                    setAgentMessages(mappedMessages);
                    
                    // If extraction data exists, add it as an Invoice Agent message
                    if ((planResult.plan as any).extraction_data) {
                        console.log('📊 Found extraction data in completed task');
                        const extractionData = (planResult.plan as any).extraction_data;
                        
                        // Format extraction data in a user-friendly way
                        const invoiceData = extractionData.invoice_data;
                        let formattedContent = '📊 **Invoice Extraction Results**\n\n';
                        
                        if (invoiceData) {
                            formattedContent += `**Vendor:** ${invoiceData.vendor_name || 'N/A'}\n`;
                            formattedContent += `**Invoice Number:** ${invoiceData.invoice_number || 'N/A'}\n`;
                            formattedContent += `**Invoice Date:** ${invoiceData.invoice_date || 'N/A'}\n`;
                            formattedContent += `**Due Date:** ${invoiceData.due_date || 'N/A'}\n`;
                            formattedContent += `**PO Number:** ${invoiceData.po_number || 'N/A'}\n\n`;
                            
                            formattedContent += `**Amounts:**\n`;
                            formattedContent += `  • Subtotal: $${invoiceData.subtotal || '0.00'}\n`;
                            formattedContent += `  • Tax: $${invoiceData.tax_amount || '0.00'}\n`;
                            if (invoiceData.discount_amount) {
                                formattedContent += `  • Discount: -$${invoiceData.discount_amount}\n`;
                            }
                            formattedContent += `  • **Total: $${invoiceData.total_amount || '0.00'}**\n\n`;
                            
                            if (invoiceData.line_items && invoiceData.line_items.length > 0) {
                                formattedContent += `**Line Items:**\n`;
                                invoiceData.line_items.forEach((item: any, index: number) => {
                                    formattedContent += `${index + 1}. ${item.description || 'N/A'}\n`;
                                    formattedContent += `   Qty: ${item.quantity || 0} × $${item.unit_price || '0.00'} = $${item.total || '0.00'}\n`;
                                });
                            }
                            
                            if (extractionData.validation_errors && extractionData.validation_errors.length > 0) {
                                formattedContent += `\n**Validation Notes:**\n`;
                                extractionData.validation_errors.forEach((error: any) => {
                                    formattedContent += `⚠️ ${error.message || error}\n`;
                                });
                            }
                        }
                        
                        const extractionMessage: AgentMessageData = {
                            agent: 'Invoice',
                            agent_type: AgentMessageType.AI_AGENT,
                            content: formattedContent,
                            timestamp: planResult.plan.timestamp || new Date().toISOString(),
                            steps: [],
                            next_steps: [],
                            raw_data: ''
                        };
                        
                        setAgentMessages(prev => [...prev, extractionMessage]);
                    }
                }
                if (planResult?.mplan) {
                    setPlanApprovalRequest(planResult.mplan);
                }
                if (planResult?.streaming_message && planResult.streaming_message.trim() !== "") {
                    setStreamingMessageBuffer(planResult.streaming_message);
                    setShowBufferingText(true);
                }
                setPlanData(planResult);
                return planResult;
            } catch (err) {
                console.log("Failed to load plan data:", err);
                setErrorLoading(true);
                setPlanData(null);
                return null;
            } finally {
                setLoading(false);
            }
        },
        [planId, navigate, resetPlanVariables]
    );


    // Handle plan approval
    const handleApprovePlan = useCallback(async () => {
        if (!planApprovalRequest) return;

        setProcessingApproval(true);
        let id = showToast("Submitting Approval", "progress");
        try {
            console.log('🔍 [DEBUG] Approval being sent for plan:', planApprovalRequest.id);
            console.log('🔍 [DEBUG] WebSocket connected:', wsConnected);
            
            await apiService.approvePlan({
                m_plan_id: planApprovalRequest.id,
                plan_id: planData?.plan?.id,
                approved: true,
                feedback: 'Plan approved by user'
            });

            dismissToast(id);
            // Only show spinner if task is not already completed
            if (!taskCompleted) {
                setShowProcessingPlanSpinner(true);
                console.log('🔄 Showing spinner after approval');
            } else {
                console.log('✅ Task already completed, not showing spinner');
            }
            setShowApprovalButtons(false);
            
            console.log('🔍 [DEBUG] Approval sent, waiting for agent messages...');
            console.log('🔍 [DEBUG] Current agent messages:', agentMessages.length);

        } catch (error) {
            dismissToast(id);
            showToast("Failed to submit approval", "error");
            console.error('❌ Failed to approve plan:', error);
        } finally {
            setProcessingApproval(false);
        }
    }, [planApprovalRequest, planData, setProcessingApproval, wsConnected, agentMessages]);

    // Handle plan rejection  
    const handleRejectPlan = useCallback(async () => {
        if (!planApprovalRequest) return;

        setProcessingApproval(true);
        let id = showToast("Submitting cancellation", "progress");
        try {
            await apiService.approvePlan({
                m_plan_id: planApprovalRequest.id,
                plan_id: planData?.plan?.id,
                approved: false,
                feedback: 'Plan rejected by user'
            });

            dismissToast(id);

            navigate('/');

        } catch (error) {
            dismissToast(id);
            showToast("Failed to submit cancellation", "error");
            console.error('❌ Failed to reject plan:', error);
            navigate('/');
        } finally {
            setProcessingApproval(false);
        }
    }, [planApprovalRequest, planData, navigate, setProcessingApproval]);

    // Handle extraction approval
    const handleExtractionApproval = useCallback(async (approved: boolean) => {
        if (!extractionApprovalData) {
            console.error('❌ No extraction approval data available');
            return;
        }

        console.log(`📊 Extraction approval: ${approved}`);
        
        // If approved, validate and parse the edited JSON
        let editedInvoiceData = null;
        if (approved) {
            try {
                editedInvoiceData = JSON.parse(editableInvoiceJson);
                console.log('✅ Parsed edited invoice data:', editedInvoiceData);
                setJsonError('');
            } catch (error) {
                console.error('❌ Invalid JSON:', error);
                setJsonError('Invalid JSON format. Please fix the errors before approving.');
                showToast('Invalid JSON format. Please fix the errors.', 'error');
                return;
            }
        }
        
        // Use planId from URL params as fallback
        const targetPlanId = extractionApprovalData.plan_id || planId;
        
        if (!targetPlanId) {
            console.error('❌ No plan_id available for extraction approval');
            showToast('Error: No plan ID available', 'error');
            return;
        }
        
        try {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const endpoint = `${apiUrl}/api/v3/extraction_approval`;
            
            console.log(`📊 Sending extraction approval to: ${endpoint}`);
            
            const requestBody = {
                plan_id: targetPlanId,
                approved: approved,
                feedback: approved ? '' : 'User rejected extraction',
                edited_data: approved ? editedInvoiceData : null
            };
            
            console.log(`📊 Request body:`, requestBody);
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });
            
            console.log(`📊 Response status: ${response.status}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`❌ Response error: ${errorText}`);
                throw new Error(`Failed to send extraction approval: ${response.status} ${errorText}`);
            }
            
            const responseData = await response.json();
            console.log('✅ Extraction approval sent successfully:', responseData);
            
            // Close dialog
            setShowExtractionApproval(false);
            setExtractionApprovalData(null);
            setEditableInvoiceJson('');
            setJsonError('');
            
            // Show spinner while waiting for completion (only if approved)
            if (approved) {
                setShowProcessingPlanSpinner(true);
            }
            
        } catch (error) {
            console.error('❌ Failed to send extraction approval:', error);
            showToast(`Failed to send approval: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
        }
    }, [extractionApprovalData, showToast, planId, editableInvoiceJson]);

    // Chat submission handler - updated for v3 backend compatibility

    const handleOnchatSubmit = useCallback(
        async (chatInput: string) => {
            if (!chatInput.trim()) {
                showToast("Please enter a clarification", "error");
                return;
            }
            setInput("");

            if (!planData?.plan) return;
            setSubmittingChatDisableInput(true);
            let id = showToast("Submitting clarification", "progress");

            // Create the human message BEFORE submitting to ensure correct timestamp order
            const humanMessageData = {
                agent: 'human',
                agent_type: AgentMessageType.HUMAN_AGENT,
                timestamp: new Date().toISOString(),
                steps: [],   // intentionally always empty
                next_steps: [],  // intentionally always empty
                content: chatInput || '',
                raw_data: chatInput || '',
            } as AgentMessageData;
            
            // Add human message immediately to show in the chat
            setAgentMessages(prev => [...prev, humanMessageData]);
            console.log('✅ Added human message to chat:', chatInput);

            try {
                // Use legacy method for non-v3 backends
                const response = await PlanDataService.submitClarification({
                    request_id: clarificationMessage?.request_id || "",
                    answer: chatInput,
                    plan_id: planData?.plan.id,
                    m_plan_id: planApprovalRequest?.id || ""
                });

                console.log("Clarification submitted successfully:", response);
                setInput("");
                dismissToast(id);
                showToast("Clarification submitted successfully", "success");
                
                // Clear clarification message to hide the UI
                setClarificationMessage(null);
                
                // Keep input disabled while waiting for agent response
                // Only show spinner if task is not already completed
                // Use a callback to check the current taskCompleted state
                setTaskCompleted(currentTaskCompleted => {
                    if (!currentTaskCompleted) {
                        setShowProcessingPlanSpinner(true);
                        console.log('🔄 Showing spinner after clarification submission');
                    } else {
                        console.log('✅ Task already completed, not showing spinner after clarification');
                    }
                    return currentTaskCompleted; // Don't change the value, just read it
                });
                scrollToBottom();

            } catch (error: any) {
                setShowProcessingPlanSpinner(false);
                dismissToast(id);
                setSubmittingChatDisableInput(false);
                showToast(
                    "Failed to submit clarification",
                    "error"
                );

            } finally {
                // Don't re-enable input here - let the agent message handler do it
            }
        },
        [planData?.plan, showToast, dismissToast, loadPlanData, taskCompleted, clarificationMessage, planApprovalRequest]
    );


    // ✅ Handlers for PlanPanelLeft with plan cancellation protection
    const handleNewTaskButton = useCallback(() => {
        handleNavigationWithAlert(() => {
            navigate("/", { state: { focusInput: true } });
        });
    }, [navigate, handleNavigationWithAlert]);


    const resetReload = useCallback(() => {
        setReloadLeftList(false);
    }, []);

    useEffect(() => {
        const initializePlanLoading = async () => {
            if (!planId) {
                resetPlanVariables();
                setErrorLoading(true);
                return;
            }

            try {
                await loadPlanData(false);
            } catch (err) {
                console.error("Failed to initialize plan loading:", err);
            }
        };

        initializePlanLoading();
    }, [planId, loadPlanData, resetPlanVariables, setErrorLoading]);

    if (errorLoading) {
        return (
            <CoralShellColumn>
                <CoralShellRow>
                    <PlanPanelLeft
                        reloadTasks={reloadLeftList}
                        onNewTaskButton={handleNewTaskButton}
                        restReload={resetReload}
                        onTeamSelect={() => { }}
                        onTeamUpload={async () => { }}
                        isHomePage={false}
                        selectedTeam={selectedTeam}
                        onNavigationWithAlert={handleNavigationWithAlert}
                    />
                    <Content>
                        <div className="plan-error-message">
                            <Text size={500}>
                                {"An error occurred while loading the plan"}
                            </Text>
                        </div>
                    </Content>
                </CoralShellRow>
            </CoralShellColumn>
        );
    }

    return (
        <CoralShellColumn>
            <CoralShellRow>
                {/* ✅ RESTORED: PlanPanelLeft for navigation */}
                <PlanPanelLeft
                    reloadTasks={reloadLeftList}
                    onNewTaskButton={handleNewTaskButton}
                    restReload={resetReload}
                    onTeamSelect={() => { }}
                    onTeamUpload={async () => { }}
                    isHomePage={false}
                    selectedTeam={selectedTeam}
                    onNavigationWithAlert={handleNavigationWithAlert}
                />

                <Content>
                    {loading || !planData ? (
                        <>
                            <div className="plan-loading-spinner">
                                <Spinner size="medium" />
                                <Text>Loading plan data...</Text>
                            </div>
                            <LoadingMessage
                                loadingMessage={loadingMessage}
                                iconSrc={Octo}
                            />
                        </>
                    ) : (
                        <>
                            <ContentToolbar
                                panelTitle="Nolij Invoice Management Team"
                            >
                                {/* <PanelRightToggles>
                                    <TaskListSquareLtr />
                                </PanelRightToggles> */}
                            </ContentToolbar>

                            {/* Expert Agents Row */}
                            <div style={{
                                display: 'flex',
                                gap: '12px',
                                padding: '12px 24px',
                                backgroundColor: 'var(--colorNeutralBackground2)',
                                borderBottom: '1px solid var(--colorNeutralStroke2)'
                            }}>
                                <div style={{
                                    padding: '6px 16px',
                                    borderRadius: '16px',
                                    backgroundColor: '#E3F2FD',
                                    color: '#1976D2',
                                    fontSize: '13px',
                                    fontWeight: '600'
                                }}>
                                    Planning Expert
                                </div>
                                <div style={{
                                    padding: '6px 16px',
                                    borderRadius: '16px',
                                    backgroundColor: '#E8F5E9',
                                    color: '#388E3C',
                                    fontSize: '13px',
                                    fontWeight: '600'
                                }}>
                                    Invoice Expert
                                </div>
                                <div style={{
                                    padding: '6px 16px',
                                    borderRadius: '16px',
                                    backgroundColor: '#FFF3E0',
                                    color: '#F57C00',
                                    fontSize: '13px',
                                    fontWeight: '600'
                                }}>
                                    Human Expert
                                </div>
                                <div style={{
                                    padding: '6px 16px',
                                    borderRadius: '16px',
                                    backgroundColor: '#F3E5F5',
                                    color: '#7B1FA2',
                                    fontSize: '13px',
                                    fontWeight: '600'
                                }}>
                                    Invoice Processor
                                </div>
                            </div>

                            <PlanChat
                                planData={planData}
                                OnChatSubmit={handleOnchatSubmit}
                                loading={loading}
                                setInput={setInput}
                                submittingChatDisableInput={submittingChatDisableInput}
                                input={input}
                                streamingMessages={streamingMessages}
                                wsConnected={wsConnected}
                                onPlanApproval={(approved) => setPlanApproved(approved)}
                                planApprovalRequest={planApprovalRequest}
                                waitingForPlan={waitingForPlan}
                                messagesContainerRef={messagesContainerRef}
                                streamingMessageBuffer={streamingMessageBuffer}
                                showBufferingText={showBufferingText}
                                agentMessages={agentMessages}
                                showProcessingPlanSpinner={showProcessingPlanSpinner}
                                showApprovalButtons={showApprovalButtons}
                                processingApproval={processingApproval}
                                handleApprovePlan={handleApprovePlan}
                                handleRejectPlan={handleRejectPlan}
                                clarificationMessage={clarificationMessage}
                                workflowProgress={workflowProgress}
                                workflowError={workflowError}
                                onRestartWorkflow={handleRestartWorkflow}
                            />
                        </>
                    )}
                </Content>

                <PlanPanelRight
                    planData={planData}
                    loading={loading}
                    planApprovalRequest={planApprovalRequest}
                    agentMessages={agentMessages}
                />
            </CoralShellRow>

            {/* Plan Cancellation Confirmation Dialog */}
            <PlanCancellationDialog
                isOpen={showCancellationDialog}
                onConfirm={handleConfirmCancellation}
                onCancel={handleCancelDialog}
                loading={cancellingPlan}
            />

            {/* Extraction Approval Dialog */}
            {showExtractionApproval && extractionApprovalData && (
                <div className="extraction-approval-dialog">
                    <div className="dialog-overlay" onClick={(e) => e.stopPropagation()} />
                    <div className="dialog-content">
                        <h2>📊 Invoice Extraction Approval</h2>
                        
                        <div className="extraction-summary">
                            <p className="extraction-instructions">
                                Review and edit the extracted invoice data below. You can modify any field before approving.
                            </p>
                            
                            {extractionApprovalData.extraction_result?.validation_errors?.length > 0 && (
                                <div className="validation-errors">
                                    <h4>⚠️ Validation Issues:</h4>
                                    <ul>
                                        {extractionApprovalData.extraction_result.validation_errors.map((error: string, idx: number) => (
                                            <li key={idx}>{error}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            
                            <div className="extraction-content-layout">
                                {visualizationUrl && (
                                    <div className="visualization-container">
                                        <h3>📊 Extraction Visualization:</h3>
                                        <iframe
                                            src={visualizationUrl}
                                            className="extraction-visualization-iframe"
                                            title="Invoice Extraction Visualization"
                                            sandbox="allow-same-origin allow-scripts"
                                        />
                                    </div>
                                )}
                                
                                <div className="json-editor-container">
                                    <h3>Invoice Data (Editable JSON):</h3>
                                    <textarea
                                        className={`json-editor ${jsonError ? 'json-error' : ''}`}
                                        value={editableInvoiceJson}
                                        onChange={(e) => {
                                            setEditableInvoiceJson(e.target.value);
                                            // Try to parse to validate
                                            try {
                                                JSON.parse(e.target.value);
                                                setJsonError('');
                                            } catch (error) {
                                                setJsonError('Invalid JSON format');
                                            }
                                        }}
                                        spellCheck={false}
                                        rows={20}
                                    />
                                    {jsonError && (
                                        <div className="json-error-message">
                                            ❌ {jsonError}
                                        </div>
                                    )}
                                </div>
                            </div>
                            
                            <div className="extraction-metadata">
                                <p><small>Model: Nolij AI Accounting Model</small></p>
                                <p><small>Extraction Time: {extractionApprovalData.extraction_result?.extraction_time?.toFixed(2)}s</small></p>
                            </div>
                        </div>
                        
                        <div className="dialog-actions">
                            <button 
                                className="btn-approve"
                                onClick={() => handleExtractionApproval(true)}
                                disabled={!!jsonError}
                            >
                                ✅ Approve & Store
                            </button>
                            <button 
                                className="btn-reject"
                                onClick={() => handleExtractionApproval(false)}
                            >
                                ❌ Reject
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </CoralShellColumn>
    );
};

export default PlanPage;