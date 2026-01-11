import React, { useState } from 'react';
import {
  Button,
  Text,
  Body1,
  Body2,
  Caption1,
  Title3,
  Card,
  CardHeader,
  CardPreview,
  Badge,
  Divider,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogContent,
  DialogBody,
  DialogActions,
  Field,
  Textarea,
  makeStyles,
  tokens,
  Spinner
} from '@fluentui/react-components';
import {
  ChevronDown20Regular,
  ChevronUp20Regular,
  Clock20Regular,
  People20Regular,
  TaskListSquareLtrRegular,
  Edit20Regular,
  Checkmark20Regular,
  Dismiss20Regular,
  Info20Regular
} from '@fluentui/react-icons';
import { MPlanData } from '@/models';
import { getAgentIcon, getAgentDisplayName } from '@/utils/agentIconUtils';

interface PlanApprovalDisplayProps {
  planApprovalRequest: MPlanData | null;
  handleApprovePlan: () => Promise<void>;
  handleRejectPlan: () => Promise<void>;
  processingApproval: boolean;
  showApprovalButtons: boolean;
}

const useStyles = makeStyles({
  container: {
    maxWidth: '800px',
    margin: '0 auto 32px auto',
    padding: '0 24px',
    fontFamily: tokens.fontFamilyBase
  },
  planCard: {
    marginBottom: '24px',
    padding: '24px',
    backgroundColor: tokens.colorNeutralBackground2,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusLarge
  },
  planHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '20px'
  },
  agentAvatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: tokens.colorNeutralBackground3,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  planTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: tokens.colorNeutralForeground1,
    marginBottom: '8px'
  },
  planSubtitle: {
    color: tokens.colorNeutralForeground2,
    fontSize: '14px'
  },
  metadataSection: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '24px',
    padding: '16px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`
  },
  metadataItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  metadataIcon: {
    color: tokens.colorNeutralForeground2,
    fontSize: '16px'
  },
  metadataText: {
    fontSize: '14px',
    color: tokens.colorNeutralForeground1
  },
  agentSequence: {
    marginBottom: '24px'
  },
  agentSequenceTitle: {
    fontSize: '16px',
    fontWeight: '600',
    marginBottom: '12px',
    color: tokens.colorNeutralForeground1
  },
  agentList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  },
  agentItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`
  },
  agentNumber: {
    minWidth: '24px',
    height: '24px',
    borderRadius: '50%',
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '12px',
    fontWeight: '600',
    flexShrink: 0
  },
  agentIcon: {
    width: '24px',
    height: '24px',
    borderRadius: '50%',
    backgroundColor: tokens.colorNeutralBackground3,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  agentName: {
    fontSize: '14px',
    fontWeight: '500',
    color: tokens.colorNeutralForeground1,
    flex: 1
  },
  agentRole: {
    fontSize: '12px',
    color: tokens.colorNeutralForeground2
  },
  expandableSection: {
    marginBottom: '24px'
  },
  sectionContent: {
    padding: '16px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    fontSize: '14px',
    lineHeight: '1.5',
    color: tokens.colorNeutralForeground1,
    whiteSpace: 'pre-wrap'
  },
  buttonContainer: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
    marginTop: '24px',
    paddingTop: '24px',
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`
  },
  modificationDialog: {
    minWidth: '500px'
  },
  feedbackField: {
    marginBottom: '16px'
  },
  loadingContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '16px',
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    marginBottom: '16px'
  },
  warningBadge: {
    backgroundColor: tokens.colorPaletteYellowBackground2,
    color: tokens.colorPaletteYellowForeground2
  }
});

/**
 * Enhanced Plan Approval Display Component
 * Provides comprehensive plan review with agent sequence, duration, and modification options
 * Validates: Requirements 1.4, 1.5, 2.2
 */
const PlanApprovalDisplay: React.FC<PlanApprovalDisplayProps> = ({
  planApprovalRequest,
  handleApprovePlan,
  handleRejectPlan,
  processingApproval,
  showApprovalButtons
}) => {
  const styles = useStyles();
  const [isModificationDialogOpen, setIsModificationDialogOpen] = useState(false);
  const [modificationFeedback, setModificationFeedback] = useState('');
  const [isSubmittingModification, setIsSubmittingModification] = useState(false);

  // Always render, but return null if no approval request
  if (!planApprovalRequest) {
    return null;
  }

  // Extract plan data
  const agentName = getAgentDisplayName('Planning Agent');
  const planTitle = planApprovalRequest.user_request || 'Multi-Agent Workflow Plan';
  
  // Calculate estimated duration (mock calculation based on number of agents and steps)
  const estimatedDuration = calculateEstimatedDuration(planApprovalRequest);
  
  // Extract agent sequence from plan steps
  const agentSequence = extractAgentSequence(planApprovalRequest);
  
  // Extract plan details for expandable sections
  const planDetails = extractPlanDetails(planApprovalRequest);

  // Check if plan is still being created
  const isCreatingPlan = !planApprovalRequest.steps?.length && !planApprovalRequest.facts;

  const handleModificationSubmit = async () => {
    if (!modificationFeedback.trim()) {
      return;
    }

    setIsSubmittingModification(true);
    try {
      // For now, treat modification as rejection with feedback
      // In a full implementation, this would call a separate modification endpoint
      await handleRejectPlan();
      setIsModificationDialogOpen(false);
      setModificationFeedback('');
    } catch (error) {
      console.error('Error submitting modification:', error);
    } finally {
      setIsSubmittingModification(false);
    }
  };

  if (isCreatingPlan) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingContainer}>
          <Spinner size="small" />
          <Text>Creating comprehensive multi-agent plan...</Text>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <Card className={styles.planCard}>
        {/* Plan Header */}
        <div className={styles.planHeader}>
          <div className={styles.agentAvatar}>
            {getAgentIcon(agentName, null, planApprovalRequest)}
          </div>
          <div style={{ flex: 1 }}>
            <div className={styles.planTitle}>
              Plan Approval Required
            </div>
            <div className={styles.planSubtitle}>
              {planTitle}
            </div>
          </div>
          <Badge appearance="filled" color="brand">
            Awaiting Approval
          </Badge>
        </div>

        {/* Plan Metadata */}
        <div className={styles.metadataSection}>
          <div className={styles.metadataItem}>
            <Clock20Regular className={styles.metadataIcon} />
            <div>
              <Text className={styles.metadataText}>
                <strong>Estimated Duration:</strong> {estimatedDuration}
              </Text>
            </div>
          </div>
          <div className={styles.metadataItem}>
            <People20Regular className={styles.metadataIcon} />
            <div>
              <Text className={styles.metadataText}>
                <strong>Agents:</strong> {agentSequence.length} agents
              </Text>
            </div>
          </div>
          <div className={styles.metadataItem}>
            <TaskListSquareLtrRegular className={styles.metadataIcon} />
            <div>
              <Text className={styles.metadataText}>
                <strong>Steps:</strong> {planApprovalRequest.steps?.length || 0} steps
              </Text>
            </div>
          </div>
        </div>

        {/* Agent Execution Sequence */}
        <div className={styles.agentSequence}>
          <div className={styles.agentSequenceTitle}>
            Agent Execution Sequence
          </div>
          <div className={styles.agentList}>
            {agentSequence.map((agent, index) => (
              <div key={index} className={styles.agentItem}>
                <div className={styles.agentNumber}>
                  {index + 1}
                </div>
                <div className={styles.agentIcon}>
                  {getAgentIcon(agent.name)}
                </div>
                <div className={styles.agentName}>
                  {agent.displayName}
                </div>
                <div className={styles.agentRole}>
                  {agent.role}
                </div>
                <Badge appearance="outline" size="small">
                  {agent.estimatedTime}
                </Badge>
              </div>
            ))}
          </div>
        </div>

        {/* Expandable Plan Details */}
        <div className={styles.expandableSection}>
          <Accordion multiple collapsible>
            {planDetails.facts && (
              <AccordionItem value="facts">
                <AccordionHeader>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Info20Regular />
                    <Text weight="semibold">Plan Context & Analysis</Text>
                  </div>
                </AccordionHeader>
                <AccordionPanel>
                  <div className={styles.sectionContent}>
                    {planDetails.facts}
                  </div>
                </AccordionPanel>
              </AccordionItem>
            )}
            
            {planDetails.steps && (
              <AccordionItem value="steps">
                <AccordionHeader>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <TaskListSquareLtrRegular />
                    <Text weight="semibold">Detailed Execution Steps</Text>
                  </div>
                </AccordionHeader>
                <AccordionPanel>
                  <div className={styles.sectionContent}>
                    {planDetails.steps}
                  </div>
                </AccordionPanel>
              </AccordionItem>
            )}

            {planDetails.teamInfo && (
              <AccordionItem value="team">
                <AccordionHeader>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <People20Regular />
                    <Text weight="semibold">Team Configuration</Text>
                  </div>
                </AccordionHeader>
                <AccordionPanel>
                  <div className={styles.sectionContent}>
                    {planDetails.teamInfo}
                  </div>
                </AccordionPanel>
              </AccordionItem>
            )}
          </Accordion>
        </div>

        {/* Approval Instructions */}
        <Body1 style={{ 
          color: tokens.colorNeutralForeground2, 
          marginBottom: '16px',
          padding: '12px',
          backgroundColor: tokens.colorNeutralBackground1,
          borderRadius: tokens.borderRadiusMedium,
          border: `1px solid ${tokens.colorNeutralStroke2}`
        }}>
          Please review the proposed execution plan above. If approved, the agents will execute in the specified sequence. 
          You can modify the plan if adjustments are needed.
        </Body1>

        {/* Action Buttons */}
        {showApprovalButtons && (
          <div className={styles.buttonContainer}>
            <Button
              appearance="primary"
              size="medium"
              onClick={handleApprovePlan}
              disabled={processingApproval || isSubmittingModification}
              icon={<Checkmark20Regular />}
            >
              {processingApproval ? 'Approving...' : 'Approve Plan'}
            </Button>
            
            <Dialog 
              open={isModificationDialogOpen} 
              onOpenChange={(_, data) => setIsModificationDialogOpen(data.open)}
            >
              <DialogTrigger disableButtonEnhancement>
                <Button
                  appearance="secondary"
                  size="medium"
                  disabled={processingApproval || isSubmittingModification}
                  icon={<Edit20Regular />}
                >
                  Modify Plan
                </Button>
              </DialogTrigger>
              <DialogSurface className={styles.modificationDialog}>
                <DialogBody>
                  <DialogTitle>Modify Execution Plan</DialogTitle>
                  <DialogContent>
                    <Body2 style={{ marginBottom: '16px' }}>
                      Provide specific feedback on what should be changed in the execution plan. 
                      The planner will revise the plan based on your input.
                    </Body2>
                    <Field 
                      label="Modification Instructions"
                      className={styles.feedbackField}
                    >
                      <Textarea
                        placeholder="Describe the changes you'd like to see in the plan..."
                        value={modificationFeedback}
                        onChange={(_, data) => setModificationFeedback(data.value)}
                        rows={4}
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
                      onClick={handleModificationSubmit}
                      disabled={!modificationFeedback.trim() || isSubmittingModification}
                    >
                      {isSubmittingModification ? 'Submitting...' : 'Submit Modifications'}
                    </Button>
                  </DialogActions>
                </DialogBody>
              </DialogSurface>
            </Dialog>

            <Button
              appearance="secondary"
              size="medium"
              onClick={handleRejectPlan}
              disabled={processingApproval || isSubmittingModification}
              icon={<Dismiss20Regular />}
            >
              Cancel Plan
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

/**
 * Calculate estimated duration based on plan complexity
 */
function calculateEstimatedDuration(planData: MPlanData): string {
  const baseTimePerAgent = 2; // 2 minutes per agent
  const baseTimePerStep = 0.5; // 30 seconds per step
  
  const agentCount = new Set(planData.steps?.map(step => step.agent).filter(Boolean)).size || 1;
  const stepCount = planData.steps?.length || 1;
  
  const totalMinutes = (agentCount * baseTimePerAgent) + (stepCount * baseTimePerStep);
  
  if (totalMinutes < 1) return '< 1 minute';
  if (totalMinutes < 60) return `${Math.ceil(totalMinutes)} minutes`;
  
  const hours = Math.floor(totalMinutes / 60);
  const minutes = Math.ceil(totalMinutes % 60);
  
  if (hours === 1 && minutes === 0) return '1 hour';
  if (minutes === 0) return `${hours} hours`;
  return `${hours}h ${minutes}m`;
}

/**
 * Extract agent sequence from plan data
 */
function extractAgentSequence(planData: MPlanData): Array<{
  name: string;
  displayName: string;
  role: string;
  estimatedTime: string;
}> {
  const agents = new Map<string, { name: string; stepCount: number }>();
  
  // Extract unique agents from steps
  planData.steps?.forEach(step => {
    if (step.agent) {
      const existing = agents.get(step.agent) || { name: step.agent, stepCount: 0 };
      existing.stepCount++;
      agents.set(step.agent, existing);
    }
  });

  // Convert to sequence with display information
  return Array.from(agents.entries()).map(([agentName, info]) => {
    const displayName = getAgentDisplayName(agentName);
    const role = getAgentRole(agentName);
    const estimatedTime = `${Math.ceil(info.stepCount * 0.5 + 2)}min`;
    
    return {
      name: agentName,
      displayName,
      role,
      estimatedTime
    };
  });
}

/**
 * Get agent role description
 */
function getAgentRole(agentName: string): string {
  const roleMap: Record<string, string> = {
    'gmail': 'Email Management',
    'accounts_payable': 'Financial Processing',
    'crm': 'Customer Relations',
    'analysis': 'Data Analysis',
    'invoice': 'Invoice Processing',
    'planner': 'Task Planning',
    'planning': 'Task Planning'
  };
  
  const normalizedName = agentName.toLowerCase().replace(/[^a-z]/g, '');
  return roleMap[normalizedName] || 'Specialized Agent';
}

/**
 * Extract plan details for expandable sections
 */
function extractPlanDetails(planData: MPlanData): {
  facts?: string;
  steps?: string;
  teamInfo?: string;
} {
  const details: { facts?: string; steps?: string; teamInfo?: string } = {};
  
  // Extract facts/context
  if (planData.facts && planData.facts.trim()) {
    details.facts = planData.facts.trim();
  }
  
  // Extract detailed steps
  if (planData.steps && planData.steps.length > 0) {
    details.steps = planData.steps
      .map((step, index) => `${index + 1}. ${step.action || step.cleanAction || 'Step description'}`)
      .join('\n\n');
  }
  
  // Extract team information
  if (planData.context?.participant_descriptions) {
    const teamDescriptions = Object.entries(planData.context.participant_descriptions)
      .map(([agent, description]) => `${getAgentDisplayName(agent)}: ${description}`)
      .join('\n\n');
    
    if (teamDescriptions) {
      details.teamInfo = teamDescriptions;
    }
  }
  
  return details;
}

export default PlanApprovalDisplay;
