import React, { useState } from 'react';
import {
    Button,
    Text,
    Body1,
    makeStyles,
    tokens,
    Input,
    Textarea
} from "@fluentui/react-components";
import {
    CheckmarkCircle20Regular,
    ArrowReply20Regular
} from "@fluentui/react-icons";

const useStyles = makeStyles({
    container: {
        maxWidth: '800px',
        margin: '0 auto 32px auto',
        padding: '0 24px',
        fontFamily: tokens.fontFamilyBase
    },
    resultSection: {
        backgroundColor: 'var(--colorNeutralBackground2)',
        border: '1px solid var(--colorNeutralStroke2)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '16px'
    },
    resultHeader: {
        fontWeight: '600',
        color: 'var(--colorNeutralForeground1)',
        fontSize: '14px',
        lineHeight: '20px',
        marginBottom: '12px'
    },
    resultContent: {
        fontSize: '14px',
        lineHeight: '1.5',
        color: 'var(--colorNeutralForeground1)',
        whiteSpace: 'pre-wrap',
        wordWrap: 'break-word'
    },
    clarificationSection: {
        backgroundColor: 'var(--colorNeutralBackground1)',
        border: '1px solid var(--colorNeutralStroke2)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '16px'
    },
    clarificationHeader: {
        fontWeight: '600',
        color: 'var(--colorNeutralForeground1)',
        fontSize: '14px',
        lineHeight: '20px',
        marginBottom: '12px'
    },
    inputContainer: {
        marginBottom: '16px'
    },
    inputLabel: {
        fontSize: '13px',
        fontWeight: '500',
        color: 'var(--colorNeutralForeground1)',
        marginBottom: '8px',
        display: 'block'
    },
    textarea: {
        width: '100%',
        minHeight: '100px',
        padding: '12px',
        fontSize: '14px',
        fontFamily: tokens.fontFamilyBase,
        border: '1px solid var(--colorNeutralStroke2)',
        borderRadius: '6px',
        backgroundColor: 'var(--colorNeutralBackground1)',
        color: 'var(--colorNeutralForeground1)',
        resize: 'vertical'
    },
    buttonContainer: {
        display: 'flex',
        gap: '12px',
        justifyContent: 'flex-end'
    },
    approveButton: {
        backgroundColor: 'var(--colorBrandBackground)',
        color: 'white',
        border: 'none',
        borderRadius: '6px',
        padding: '10px 20px',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        '&:hover': {
            backgroundColor: 'var(--colorBrandBackgroundHover)'
        }
    },
    retryButton: {
        backgroundColor: 'var(--colorNeutralBackground3)',
        color: 'var(--colorNeutralForeground1)',
        border: '1px solid var(--colorNeutralStroke2)',
        borderRadius: '6px',
        padding: '10px 20px',
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        '&:hover': {
            backgroundColor: 'var(--colorNeutralBackground4)'
        }
    },
    loadingState: {
        opacity: 0.6,
        cursor: 'not-allowed'
    }
});

interface ClarificationUIProps {
    agentResult: string;
    onApprove: () => void;
    onRetry: (feedback: string) => void;
    isLoading?: boolean;
}

/**
 * ClarificationUI Component
 * Displays agent result and allows user to approve or provide revision
 * 
 * **Feature: multi-agent-hitl-loop, Property 1: HITL Routing**
 * **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
 */
const ClarificationUI: React.FC<ClarificationUIProps> = ({
    agentResult,
    onApprove,
    onRetry,
    isLoading = false
}) => {
    const styles = useStyles();
    const [feedback, setFeedback] = useState<string>('');

    const handleApprove = () => {
        onApprove();
    };

    const handleRetry = () => {
        if (feedback.trim()) {
            onRetry(feedback);
            setFeedback('');
        }
    };

    const isRetryDisabled = !feedback.trim() || isLoading;

    return (
        <div className={styles.container}>
            {/* Clarification Section */}
            <div className={styles.clarificationSection}>
                <div className={styles.clarificationHeader}>
                    Please review the agent's result above
                </div>

                <div className={styles.inputContainer}>
                    <label className={styles.inputLabel}>
                        Your feedback (type "OK" to approve, or provide revision details):
                    </label>
                    <textarea
                        className={styles.textarea}
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        placeholder="Type 'OK' to approve, or describe what needs to be revised..."
                        disabled={isLoading}
                    />
                </div>

                <div className={styles.buttonContainer}>
                    <button
                        className={styles.approveButton}
                        onClick={handleApprove}
                        disabled={isLoading}
                        style={isLoading ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                    >
                        <CheckmarkCircle20Regular />
                        Approve
                    </button>
                    <button
                        className={styles.retryButton}
                        onClick={handleRetry}
                        disabled={isRetryDisabled}
                        style={isRetryDisabled ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                    >
                        <ArrowReply20Regular />
                        Retry
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ClarificationUI;
