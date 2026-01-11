import {
    Body1Strong,
    Button,
    Caption1,
    Title2,
    Text,
} from "@fluentui/react-components";

import React, { useRef, useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import "./../../styles/Chat.css";
import "../../styles/prism-material-oceanic.css";
import "./../../styles/HomeInput.css";

import { HomeInputProps, iconMap, QuickTask } from "../../models/homeInput";
import { TaskService } from "../../services/TaskService";
import { NewTaskService } from "../../services/NewTaskService";
import { RAIErrorCard, RAIErrorData } from "../errors";

import ChatInput from "@/coral/modules/ChatInput";
import InlineToaster, { useInlineToaster } from "../toast/InlineToaster";
import PromptCard from "@/coral/components/PromptCard";
import { Send } from "@/coral/imports/bundleicons";
import { Clipboard20Regular, Attach20Regular } from "@fluentui/react-icons";
import FileUploadZone from "../common/FileUploadZone";

// Icon mapping function to convert string icons to FluentUI icons
const getIconFromString = (iconString: string | React.ReactNode): React.ReactNode => {
    // If it's already a React node, return it
    if (typeof iconString !== 'string') {
        return iconString;
    }

    return iconMap[iconString] || iconMap['default'] || <Clipboard20Regular />;
};

const truncateDescription = (description: string, maxLength: number = 180): string => {
    if (!description) return '';

    if (description.length <= maxLength) {
        return description;
    }


    const truncated = description.substring(0, maxLength);
    const lastSpaceIndex = truncated.lastIndexOf(' ');

    const cutPoint = lastSpaceIndex > maxLength - 20 ? lastSpaceIndex : maxLength;

    return description.substring(0, cutPoint) + '...';
};

// Extended QuickTask interface to store both truncated and full descriptions
interface ExtendedQuickTask extends QuickTask {
    fullDescription: string; // Store the full, untruncated description
}

const HomeInput: React.FC<HomeInputProps> = ({
    selectedTeam,
    comprehensiveTestingMode = false,
    onWorkflowProgress,
    validateQuery,
    workflowConfig,
}) => {
    const [submitting, setSubmitting] = useState<boolean>(false);
    const [input, setInput] = useState<string>("");
    const [raiError, setRAIError] = useState<RAIErrorData | null>(null);
    const [isUploadingFile, setIsUploadingFile] = useState<boolean>(false);
    const [validationError, setValidationError] = useState<string>("");

    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();
    const location = useLocation(); // ✅ location.state used to control focus
    const { showToast, dismissToast } = useInlineToaster();

    useEffect(() => {
        if (location.state?.focusInput) {
            textareaRef.current?.focus();
        }
    }, [location]);

    const resetTextarea = () => {
        setInput("");
        setRAIError(null); // Clear any RAI errors
        setValidationError(""); // Clear validation errors
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.focus();
        }
    };

    useEffect(() => {
        const cleanup = NewTaskService.addResetListener(resetTextarea);
        return cleanup;
    }, []);

    const handleSubmit = async () => {
        if (!input.trim()) {
            setValidationError("Please enter a query");
            return;
        }

        // Validate query for multi-agent workflows
        if (validateQuery) {
            const validation = validateQuery(input.trim());
            if (!validation.isValid) {
                setValidationError(validation.message || "Invalid query");
                showToast(validation.message || "Invalid query", "error");
                return;
            }
        }

        setSubmitting(true);
        setRAIError(null); // Clear any previous RAI errors
        setValidationError(""); // Clear validation errors
        
        // Report workflow initiation
        if (onWorkflowProgress) {
            if (comprehensiveTestingMode) {
                onWorkflowProgress("Initiating comprehensive multi-agent workflow...", true);
            } else {
                onWorkflowProgress("Creating plan...", true);
            }
        }

        let id = showToast(
            comprehensiveTestingMode 
                ? "Initiating comprehensive workflow with multi-agent coordination" 
                : "Creating a plan", 
            "progress"
        );

        try {
            const response = await TaskService.createPlan(
                input.trim(),
                selectedTeam?.team_id,
                comprehensiveTestingMode ? {
                    mode: workflowConfig?.mode || 'comprehensive',
                    requiresPlanApproval: workflowConfig?.requiresPlanApproval || true,
                    requiresFinalApproval: workflowConfig?.requiresFinalApproval || true,
                    expectedAgents: workflowConfig?.expectedAgents || []
                } : undefined
            );
            
            console.log("Plan created:", response);
            setInput("");

            if (textareaRef.current) {
                textareaRef.current.style.height = "auto";
            }

            if (response.plan_id && response.plan_id !== null) {
                const successMessage = comprehensiveTestingMode 
                    ? "Comprehensive workflow initiated! Proceeding to plan approval..." 
                    : "Plan created!";
                
                showToast(successMessage, "success");
                dismissToast(id);

                // Report workflow progress
                if (onWorkflowProgress) {
                    if (comprehensiveTestingMode) {
                        onWorkflowProgress("Plan created - awaiting approval", true);
                    } else {
                        onWorkflowProgress("", false);
                    }
                }

                navigate(`/plan/${response.plan_id}`);
            } else {
                showToast("Failed to create plan", "error");
                dismissToast(id);
                if (onWorkflowProgress) {
                    onWorkflowProgress("", false);
                }
            }
        } catch (error: any) {
            console.log("Error creating plan:", error);
            let errorMessage = "Unable to create plan. Please try again.";
            dismissToast(id);
            
            // Check if this is an RAI validation error
            try {
                errorMessage = error?.message || errorMessage;
            } catch (parseError) {
                console.error("Error parsing error detail:", parseError);
            }

            showToast(errorMessage, "error");
            if (onWorkflowProgress) {
                onWorkflowProgress("", false);
            }
        } finally {
            setInput("");
            setSubmitting(false);
        }
    };

    const handleQuickTaskClick = (task: ExtendedQuickTask) => {
        setInput(task.fullDescription);
        setRAIError(null); // Clear any RAI errors when selecting a quick task
        setValidationError(""); // Clear validation errors
        if (textareaRef.current) {
            textareaRef.current.focus();
        }
    };

    const handleFileContentExtracted = (content: string, filename: string) => {
        setInput(content);
        setRAIError(null);
        setValidationError("");
        setIsUploadingFile(false);
        showToast(`File "${filename}" uploaded successfully`, "success");
        if (textareaRef.current) {
            textareaRef.current.focus();
        }
    };

    const handleFileUploadError = (error: string) => {
        setIsUploadingFile(false);
        showToast(error, "error");
    };

    const handleAttachClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        // Validate file type
        const allowedTypes = ['.txt', '.doc', '.docx'];
        const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
        if (!allowedTypes.includes(fileExtension)) {
            showToast(`Unsupported file type. Please upload ${allowedTypes.join(', ')} files`, "error");
            event.target.value = ''; // Reset input
            return;
        }

        // Validate file size (10MB)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            showToast('File size exceeds 10MB limit', "error");
            event.target.value = ''; // Reset input
            return;
        }

        setIsUploadingFile(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/v3/upload_file`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to upload file');
            }

            const result = await response.json();
            handleFileContentExtracted(result.content, result.filename);
        } catch (err: any) {
            handleFileUploadError(err.message || 'Failed to upload file');
        } finally {
            event.target.value = ''; // Reset input for next upload
        }
    };

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [input]);

    // Convert team starting_tasks to ExtendedQuickTask format
    const tasksToDisplay: ExtendedQuickTask[] = selectedTeam && selectedTeam.starting_tasks ?
        selectedTeam.starting_tasks.map((task, index) => {
            // Handle both string tasks and StartingTask objects
            if (typeof task === 'string') {
                return {
                    id: `team-task-${index}`,
                    title: task,
                    description: truncateDescription(task),
                    fullDescription: task, // Store the full description
                    icon: getIconFromString("📋")
                };
            } else {
                // Handle StartingTask objects
                const startingTask = task as any; // Type assertion for now
                const taskDescription = startingTask.prompt || startingTask.name || 'Task description';
                return {
                    id: startingTask.id || `team-task-${index}`,
                    title: startingTask.name || startingTask.prompt || 'Task',
                    description: truncateDescription(taskDescription),
                    fullDescription: taskDescription, // Store the full description
                    icon: getIconFromString(startingTask.logo || "📋")
                };
            }
        }) : [];

    return (
        <div className="home-input-container">
            <div className="home-input-content">
                <div className="home-input-center-content">
                    <div className="home-input-title-wrapper">
                        <Title2>How can I help?</Title2>
                        {comprehensiveTestingMode && selectedTeam && (
                            <div style={{ 
                                marginTop: '8px', 
                                padding: '12px', 
                                backgroundColor: '#f3f2f1', 
                                borderRadius: '4px',
                                border: '1px solid #e1dfdd'
                            }}>
                                <Text size={200} style={{ fontWeight: 600, color: '#323130' }}>
                                    Comprehensive Testing Mode Active
                                </Text>
                                <br />
                                <Text size={100} style={{ color: '#605e5c' }}>
                                    Team: {selectedTeam.name} ({selectedTeam.agents?.length || 0} agents)
                                </Text>
                                <br />
                                <Text size={100} style={{ color: '#605e5c' }}>
                                    Workflow: Plan Approval → Multi-Agent Execution → Final Approval
                                </Text>
                            </div>
                        )}
                        {validationError && (
                            <div style={{ 
                                marginTop: '8px', 
                                padding: '8px 12px', 
                                backgroundColor: '#fef7f1', 
                                borderRadius: '4px',
                                border: '1px solid #f7630c'
                            }}>
                                <Text size={200} style={{ color: '#d13438' }}>
                                    {validationError}
                                </Text>
                            </div>
                        )}
                    </div>

                    {/* Show RAI error if present */}
                    {/* {raiError && (
                        <RAIErrorCard
                            error={raiError}
                            onRetry={() => {
                                setRAIError(null);
                                if (textareaRef.current) {
                                    textareaRef.current.focus();
                                }
                            }}
                            onDismiss={() => setRAIError(null)}
                        />
                    )} */}

                    <FileUploadZone
                        onFileContentExtracted={handleFileContentExtracted}
                        onError={handleFileUploadError}
                        disabled={submitting}
                    />

                    <ChatInput
                        ref={textareaRef} // forwarding
                        value={input}
                        placeholder="Tell us what needs planning, building, or connecting—we'll handle the rest."
                        onChange={setInput}
                        onEnter={handleSubmit}
                        disabledChat={submitting || isUploadingFile}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".txt,.doc,.docx"
                            style={{ display: 'none' }}
                            onChange={handleFileSelect}
                        />
                        <Button
                            appearance="subtle"
                            className="home-input-attach-button"
                            onClick={handleAttachClick}
                            disabled={submitting || isUploadingFile}
                            icon={<Attach20Regular />}
                            title="Attach file (.txt, .doc, .docx)"
                        />
                        <Button
                            appearance="subtle"
                            className="home-input-send-button"
                            onClick={handleSubmit}
                            disabled={submitting || isUploadingFile}
                            icon={<Send />}
                        />
                    </ChatInput>

                    <InlineToaster />

                    <div className="home-input-quick-tasks-section">
                        {tasksToDisplay.length > 0 && (
                            <>
                                <div className="home-input-quick-tasks-header">
                                    <Body1Strong>Quick tasks</Body1Strong>
                                </div>

                                <div className="home-input-quick-tasks">
                                    <div>
                                        {tasksToDisplay.map((task) => (
                                            <PromptCard
                                                key={task.id}
                                                title={task.title}
                                                icon={task.icon}
                                                description={task.description}
                                                onClick={() => handleQuickTaskClick(task)}
                                                disabled={submitting}

                                            />
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                        {tasksToDisplay.length === 0 && selectedTeam && (
                            <div style={{
                                textAlign: 'center',
                                padding: '32px 16px',
                                color: '#666'
                            }}>
                                <Caption1>No starting tasks available for this team</Caption1>
                            </div>
                        )}
                        {!selectedTeam && (
                            <div style={{
                                textAlign: 'center',
                                padding: '32px 16px',
                                color: '#666'
                            }}>
                                <Caption1>Select a team to see available tasks</Caption1>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HomeInput;