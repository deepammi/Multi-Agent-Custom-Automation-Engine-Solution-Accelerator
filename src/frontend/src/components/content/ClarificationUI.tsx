import React, { useState } from 'react';
import {
    Button,
    Text,
    Body1,
    Body2,
    Title3,
    makeStyles,
    tokens,
    Textarea,
    Card,
    CardHeader,
    CardPreview,
    Badge,
    Dialog,
    DialogTrigger,
    DialogSurface,
    DialogTitle,
    DialogContent,
    DialogBody,
    DialogActions,
    Field
} from "@fluentui/react-components";
import {
    CheckmarkCircle20Regular,
    ArrowReply20Regular,
    Save20Regular,
    Share20Regular,
    Dismiss20Regular,
    Warning20Regular
} from "@fluentui/react-icons";

const useStyles = makeStyles({
    container: {
        maxWidth: '800px',
        margin: '0 auto 32px auto',
        padding: '0 24px',
        fontFamily: tokens.fontFamilyBase
    },
    resultsCard: {
        backgroundColor: tokens.colorNeutralBackground2,
        border: `1px solid ${tokens.colorNeutralStroke2}`,
        borderRadius: tokens.borderRadiusLarge,
        padding: '24px',
        marginBottom: '24px'
    },
    resultsHeader: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '16px'
    },
    resultsTitle: {
        fontSize: '18px',
        fontWeight: '600',
        color: tokens.colorNeutralForeground1,
        flex: 1
    },
    statusBadge: {
        marginLeft: 'auto'
    },
    resultContent: {
        fontSize: '14px',
        lineHeight: '1.5',
        color: tokens.colorNeutralForeground1,
        whiteSpace: 'pre-wrap',
        wordWrap: 'break-word',
        padding: '16px',
        backgroundColor: tokens.colorNeutralBackground1,
        borderRadius: tokens.borderRadiusMedium,
        border: `1px solid ${tokens.colorNeutralStroke2}`,
        maxHeight: '400px',
        overflowY: 'auto'
    },
    approvalSection: {
        backgroundColor: tokens.colorNeutralBackground1,
        border: `1px solid ${tokens.colorNeutralStroke2}`,
        borderRadius: tokens.borderRadiusMedium,
        padding: '20px',
        marginBottom: '16px'
    },
    approvalHeader: {
        fontWeight: '600',
        color: tokens.colorNeutralForeground1,
        fontSize: '16px',
        marginBottom: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
    },
    approvalInstructions: {
        color: tokens.colorNeutralForeground2,
        fontSize: '14px',
        lineHeight: '1.5',
        marginBottom: '20px',
        padding: '12px',
        backgroundColor: tokens.colorNeutralBackground2,
        borderRadius: tokens.borderRadiusMedium,
        border: `1px solid ${tokens.colorNeutralStroke2}`
    },
    buttonContainer: {
        display: 'flex',
        gap: '12px',
        alignItems: 'center',
        marginTop: '20px',
        paddingTop: '20px',
        borderTop: `1px solid ${tokens.colorNeutralStroke2}`
    },
    primaryButton: {
        minWidth: '120px'
    },
    secondaryButton: {
        minWidth: '120px'
    },
    exportButton: {
        marginLeft: 'auto'
    },
    feedbackSection: {
        marginTop: '16px'
    },
    feedbackLabel: {
        fontSize: '14px',
        fontWeight: '500',
        color: tokens.colorNeutralForeground1,
        marginBottom: '8px',
        display: 'block'
    },
    restartDialog: {
        minWidth: '500px'
    },
    restartWarning: {
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '16px',
        backgroundColor: tokens.colorPaletteYellowBackground1,
        borderRadius: tokens.borderRadiusMedium,
        border: `1px solid ${tokens.colorPaletteYellowBorder1}`,
        marginBottom: '16px'
    },
    warningIcon: {
        color: tokens.colorPaletteYellowForeground1,
        flexShrink: 0,
        marginTop: '2px'
    },
    warningText: {
        color: tokens.colorNeutralForeground1,
        fontSize: '14px',
        lineHeight: '1.5'
    }
});

interface ClarificationUIProps {
    agentResult: string;
    onApprove: () => void;
    onRetry: (feedback: string) => void;
    isLoading?: boolean;
}

/**
 * Simplified ClarificationUI Component for Final Approval
 * Task 11: Updated for comprehensive results approval with simple "Approve" / "Start New Task" options
 * Removes complex revision targeting UI in favor of restart workflow
 * 
 * **Validates: Requirements 5.1, 5.2, 5.3, 9.1, 9.2**
 */
const ClarificationUI: React.FC<ClarificationUIProps> = ({
    agentResult,
    onApprove,
    onRetry,
    isLoading = false
}) => {
    const styles = useStyles();
    const [feedback, setFeedback] = useState<string>('');
    const [showRestartDialog, setShowRestartDialog] = useState(false);
    const [restartReason, setRestartReason] = useState('');
    const [isExporting, setIsExporting] = useState(false);

    const handleApprove = () => {
        console.log('✅ User approved final results');
        onApprove();
    };

    const handleStartNewTask = () => {
        if (restartReason.trim()) {
            console.log('🔄 User requested workflow restart:', restartReason);
            onRetry(`restart: ${restartReason}`);
            setRestartReason('');
            setShowRestartDialog(false);
        }
    };

    const handleExportResults = async () => {
        setIsExporting(true);
        try {
            // Create a downloadable text file with the results
            const resultsData = {
                timestamp: new Date().toISOString(),
                results: agentResult,
                status: 'completed'
            };
            
            const dataStr = JSON.stringify(resultsData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `workflow-results-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            console.log('💾 Results exported successfully');
        } catch (error) {
            console.error('❌ Failed to export results:', error);
        } finally {
            setIsExporting(false);
        }
    };

    const handleShareResults = async () => {
        try {
            if (navigator.share) {
                await navigator.share({
                    title: 'Workflow Results',
                    text: 'Check out these workflow results',
                    url: window.location.href
                });
            } else {
                // Fallback: copy to clipboard
                await navigator.clipboard.writeText(window.location.href);
                console.log('📋 Results URL copied to clipboard');
            }
        } catch (error) {
            console.error('❌ Failed to share results:', error);
        }
    };

    return (
        <div className={styles.container}>
            {/* Results Display Card */}
            <Card className={styles.resultsCard}>
                <div className={styles.resultsHeader}>
                    <div className={styles.resultsTitle}>
                        🎯 Final Results Ready for Review
                    </div>
                    <Badge 
                        appearance="filled" 
                        color="success"
                        className={styles.statusBadge}
                    >
                        Completed
                    </Badge>
                </div>

                <div className={styles.resultContent}>
                    {agentResult || 'No results available'}
                </div>
            </Card>

            {/* Simplified Approval Section */}
            <div className={styles.approvalSection}>
                <div className={styles.approvalHeader}>
                    <CheckmarkCircle20Regular />
                    Final Approval Required
                </div>

                <div className={styles.approvalInstructions}>
                    <strong>Please review the results above and choose one of the following options:</strong>
                    <br /><br />
                    • <strong>Approve Results:</strong> Accept the current results and complete the workflow
                    <br />
                    • <strong>Start New Task:</strong> Begin a fresh workflow with different parameters or requirements
                    <br />
                    • <strong>Export Results:</strong> Save the current results for future reference
                </div>

                <div className={styles.buttonContainer}>
                    <Button
                        appearance="primary"
                        size="large"
                        onClick={handleApprove}
                        disabled={isLoading}
                        icon={<CheckmarkCircle20Regular />}
                        className={styles.primaryButton}
                    >
                        {isLoading ? 'Approving...' : 'Approve Results'}
                    </Button>

                    <Dialog 
                        open={showRestartDialog} 
                        onOpenChange={(_, data) => setShowRestartDialog(data.open)}
                    >
                        <DialogTrigger disableButtonEnhancement>
                            <Button
                                appearance="secondary"
                                size="large"
                                disabled={isLoading}
                                icon={<ArrowReply20Regular />}
                                className={styles.secondaryButton}
                            >
                                Start New Task
                            </Button>
                        </DialogTrigger>
                        <DialogSurface className={styles.restartDialog}>
                            <DialogBody>
                                <DialogTitle>Start New Task</DialogTitle>
                                <DialogContent>
                                    <div className={styles.restartWarning}>
                                        <Warning20Regular className={styles.warningIcon} />
                                        <div className={styles.warningText}>
                                            <strong>This will end the current workflow.</strong>
                                            <br />
                                            You'll need to submit a new task to begin a fresh workflow. 
                                            The current results will not be saved unless you export them first.
                                        </div>
                                    </div>
                                    
                                    <Field label="Reason for starting new task (optional)">
                                        <Textarea
                                            placeholder="Describe why you want to start a new task or what should be different..."
                                            value={restartReason}
                                            onChange={(_, data) => setRestartReason(data.value)}
                                            rows={3}
                                            resize="vertical"
                                        />
                                    </Field>
                                </DialogContent>
                                <DialogActions>
                                    <DialogTrigger disableButtonEnhancement>
                                        <Button appearance="secondary">Cancel</Button>
                                    </DialogTrigger>
                                    <Button
                                        appearance="primary"
                                        onClick={handleStartNewTask}
                                        disabled={isLoading}
                                    >
                                        {isLoading ? 'Processing...' : 'Start New Task'}
                                    </Button>
                                </DialogActions>
                            </DialogBody>
                        </DialogSurface>
                    </Dialog>

                    <Button
                        appearance="secondary"
                        size="medium"
                        onClick={handleExportResults}
                        disabled={isExporting}
                        icon={<Save20Regular />}
                        className={styles.exportButton}
                    >
                        {isExporting ? 'Exporting...' : 'Export Results'}
                    </Button>

                    <Button
                        appearance="secondary"
                        size="medium"
                        onClick={handleShareResults}
                        disabled={isLoading}
                        icon={<Share20Regular />}
                    >
                        Share
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default ClarificationUI;
