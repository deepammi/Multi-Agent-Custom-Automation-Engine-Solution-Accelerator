import React from 'react';
import {
    ProgressBar,
    Text,
    Body1,
    Body2,
    Card,
    Badge,
    makeStyles,
    tokens,
    Spinner
} from '@fluentui/react-components';
import {
    CheckmarkCircle20Filled,
    Circle20Regular,
    Clock20Regular
} from '@fluentui/react-icons';
import { WorkflowProgressUpdate } from '../../models';
import { getAgentIcon, getAgentDisplayName } from '../../utils/agentIconUtils';

const useStyles = makeStyles({
    container: {
        maxWidth: '800px',
        margin: '0 auto 24px auto',
        padding: '0 24px'
    },
    progressCard: {
        backgroundColor: tokens.colorNeutralBackground2,
        border: `1px solid ${tokens.colorNeutralStroke2}`,
        borderRadius: tokens.borderRadiusMedium,
        padding: '20px'
    },
    progressHeader: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '16px'
    },
    stageTitle: {
        fontSize: '16px',
        fontWeight: '600',
        color: tokens.colorNeutralForeground1
    },
    progressPercentage: {
        fontSize: '14px',
        fontWeight: '500',
        color: tokens.colorBrandForeground1
    },
    progressBarContainer: {
        marginBottom: '20px'
    },
    agentsContainer: {
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
    },
    agentRow: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '8px 0'
    },
    agentIcon: {
        width: '24px',
        height: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0
    },
    agentName: {
        flex: 1,
        fontSize: '14px',
        color: tokens.colorNeutralForeground1
    },
    agentStatus: {
        display: 'flex',
        alignItems: 'center',
        gap: '6px'
    },
    statusIcon: {
        fontSize: '16px'
    },
    completedIcon: {
        color: tokens.colorPaletteGreenForeground1
    },
    activeIcon: {
        color: tokens.colorBrandForeground1
    },
    pendingIcon: {
        color: tokens.colorNeutralForeground3
    },
    currentAgentHighlight: {
        backgroundColor: tokens.colorBrandBackground2,
        borderRadius: tokens.borderRadiusSmall,
        padding: '4px 8px',
        border: `1px solid ${tokens.colorBrandStroke1}`
    }
});

interface WorkflowProgressDisplayProps {
    progress: WorkflowProgressUpdate;
    planData?: any;
    planApprovalRequest?: any;
}

const STAGE_DISPLAY_NAMES: Record<string, string> = {
    'plan_creation': 'Creating Plan',
    'plan_approval': 'Awaiting Plan Approval',
    'gmail_execution': 'Processing Gmail Data',
    'ap_execution': 'Processing Accounts Payable',
    'crm_execution': 'Processing CRM Data',
    'analysis_execution': 'Analyzing Results',
    'results_compilation': 'Compiling Final Results',
    'final_approval': 'Awaiting Final Approval',
    'completed': 'Workflow Complete'
};

const WorkflowProgressDisplay: React.FC<WorkflowProgressDisplayProps> = ({
    progress,
    planData,
    planApprovalRequest
}) => {
    const styles = useStyles();

    if (!progress) return null;

    const stageDisplayName = STAGE_DISPLAY_NAMES[progress.current_stage] || progress.current_stage;
    
    // Get all agents from completed + pending + current
    const allAgents = [
        ...progress.completed_agents,
        ...(progress.current_agent ? [progress.current_agent] : []),
        ...progress.pending_agents
    ];

    // Remove duplicates and filter out system agents
    const uniqueAgents = Array.from(new Set(allAgents)).filter(agent => 
        agent && !['Group_Chat_Manager', 'Planner_Agent'].includes(agent)
    );

    const getAgentStatus = (agent: string) => {
        if (progress.completed_agents.includes(agent)) {
            return 'completed';
        } else if (progress.current_agent === agent) {
            return 'active';
        } else {
            return 'pending';
        }
    };

    const renderAgentStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CheckmarkCircle20Filled className={`${styles.statusIcon} ${styles.completedIcon}`} />;
            case 'active':
                return <Spinner size="extra-small" className={styles.activeIcon} />;
            case 'pending':
                return <Circle20Regular className={`${styles.statusIcon} ${styles.pendingIcon}`} />;
            default:
                return <Circle20Regular className={`${styles.statusIcon} ${styles.pendingIcon}`} />;
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed':
                return <Badge appearance="filled" color="success" size="small">Complete</Badge>;
            case 'active':
                return <Badge appearance="filled" color="brand" size="small">In Progress</Badge>;
            case 'pending':
                return <Badge appearance="outline" color="subtle" size="small">Pending</Badge>;
            default:
                return <Badge appearance="outline" color="subtle" size="small">Pending</Badge>;
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.progressCard}>
                {/* Progress Header */}
                <div className={styles.progressHeader}>
                    <Text className={styles.stageTitle}>
                        {stageDisplayName}
                    </Text>
                    <Text className={styles.progressPercentage}>
                        {Math.round(progress.progress_percentage)}%
                    </Text>
                </div>

                {/* Progress Bar */}
                <div className={styles.progressBarContainer}>
                    <ProgressBar 
                        value={progress.progress_percentage / 100}
                        color="brand"
                        thickness="medium"
                    />
                </div>

                {/* Agent Status List */}
                {uniqueAgents.length > 0 && (
                    <div className={styles.agentsContainer}>
                        <Body2 style={{ 
                            color: tokens.colorNeutralForeground2, 
                            marginBottom: '8px',
                            fontWeight: '500'
                        }}>
                            Agent Progress:
                        </Body2>
                        
                        {uniqueAgents.map((agent, index) => {
                            const status = getAgentStatus(agent);
                            const isCurrentAgent = progress.current_agent === agent;
                            
                            return (
                                <div 
                                    key={index} 
                                    className={`${styles.agentRow} ${isCurrentAgent ? styles.currentAgentHighlight : ''}`}
                                >
                                    <div className={styles.agentIcon}>
                                        {getAgentIcon(agent, planData, planApprovalRequest)}
                                    </div>
                                    
                                    <Text className={styles.agentName}>
                                        {getAgentDisplayName(agent)}
                                    </Text>
                                    
                                    <div className={styles.agentStatus}>
                                        {renderAgentStatusIcon(status)}
                                        {getStatusBadge(status)}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </Card>
        </div>
    );
};

export default WorkflowProgressDisplay;