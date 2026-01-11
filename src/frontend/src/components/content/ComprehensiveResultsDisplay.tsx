import React, { useState, useMemo } from 'react';
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
  Tab,
  TabList,
  SelectTabData,
  SelectTabEvent,
  TabValue,
  makeStyles,
  tokens,
  Spinner,
  ProgressBar,
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
  Textarea
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
  Info20Regular,
  DataTrending20Regular,
  Database20Regular,
  Mail20Regular,
  Building20Regular,
  DocumentData20Regular,
  Eye20Regular,
  Save20Regular,
  Share20Regular,
  Warning20Regular,
  CheckmarkCircle20Regular,
  ErrorCircle20Regular
} from '@fluentui/react-icons';
import { getAgentIcon, getAgentDisplayName } from '@/utils/agentIconUtils';
import { ComprehensiveResultsMessage, AgentResult } from '../../models';

// Data models based on design document - now imported from models

interface ComprehensiveResultsDisplayProps {
  comprehensiveResults: ComprehensiveResultsMessage | null;
  handleApproveResults: () => Promise<void>;
  handleRequestRevision: (revisionType: string, targetAgents: string[], feedback: string) => Promise<void>;
  processingApproval: boolean;
  showApprovalButtons: boolean;
}

const useStyles = makeStyles({
  container: {
    maxWidth: '1200px',
    margin: '0 auto 32px auto',
    padding: '0 24px',
    fontFamily: tokens.fontFamilyBase
  },
  resultsCard: {
    marginBottom: '24px',
    padding: '24px',
    backgroundColor: tokens.colorNeutralBackground2,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusLarge
  },
  resultsHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '20px'
  },
  headerIcon: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: tokens.colorBrandBackground,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  resultsTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: tokens.colorNeutralForeground1,
    marginBottom: '8px'
  },
  resultsSubtitle: {
    color: tokens.colorNeutralForeground2,
    fontSize: '14px'
  },
  tabContainer: {
    marginBottom: '24px'
  },
  tabContent: {
    padding: '20px 0'
  },
  agentResultCard: {
    padding: '20px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    marginBottom: '16px'
  },
  agentHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px'
  },
  agentIcon: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: tokens.colorNeutralBackground3,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0
  },
  agentName: {
    fontSize: '16px',
    fontWeight: '600',
    color: tokens.colorNeutralForeground1,
    flex: 1
  },
  statusBadge: {
    marginLeft: 'auto'
  },
  metadataGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '12px',
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium
  },
  metadataItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },
  metadataLabel: {
    fontSize: '12px',
    color: tokens.colorNeutralForeground2,
    fontWeight: '600'
  },
  metadataValue: {
    fontSize: '14px',
    color: tokens.colorNeutralForeground1
  },
  resultContent: {
    padding: '16px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    fontSize: '14px',
    lineHeight: '1.5',
    color: tokens.colorNeutralForeground1,
    whiteSpace: 'pre-wrap',
    maxHeight: '300px',
    overflowY: 'auto'
  },
  correlationSection: {
    marginBottom: '24px'
  },
  correlationGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '16px'
  },
  correlationCard: {
    padding: '16px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    textAlign: 'center'
  },
  correlationValue: {
    fontSize: '24px',
    fontWeight: '700',
    color: tokens.colorBrandForeground1,
    marginBottom: '4px'
  },
  correlationLabel: {
    fontSize: '12px',
    color: tokens.colorNeutralForeground2,
    fontWeight: '600'
  },
  summarySection: {
    marginBottom: '24px'
  },
  summaryContent: {
    padding: '20px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    fontSize: '14px',
    lineHeight: '1.6',
    color: tokens.colorNeutralForeground1
  },
  recommendationsList: {
    listStyle: 'none',
    padding: 0,
    margin: 0
  },
  recommendationItem: {
    padding: '12px 16px',
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    marginBottom: '8px',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px'
  },
  recommendationIcon: {
    color: tokens.colorBrandForeground1,
    marginTop: '2px',
    flexShrink: 0
  },
  recommendationText: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: tokens.colorNeutralForeground1
  },
  buttonContainer: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
    marginTop: '24px',
    paddingTop: '24px',
    borderTop: `1px solid ${tokens.colorNeutralStroke2}`
  },
  revisionDialog: {
    minWidth: '600px'
  },
  revisionOptions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    marginBottom: '16px'
  },
  revisionOption: {
    padding: '12px',
    border: `1px solid ${tokens.colorNeutralStroke2}`,
    borderRadius: tokens.borderRadiusMedium,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    '&:hover': {
      backgroundColor: tokens.colorNeutralBackground2
    }
  },
  selectedRevisionOption: {
    backgroundColor: tokens.colorBrandBackground2,
    borderTopColor: tokens.colorBrandStroke1,
    borderRightColor: tokens.colorBrandStroke1,
    borderBottomColor: tokens.colorBrandStroke1,
    borderLeftColor: tokens.colorBrandStroke1
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
  qualityIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px'
  }
});

/**
 * Comprehensive Results Display Component - Simplified for Task 11
 * Provides tabbed interface for agent results, data correlation visualization,
 * executive summary, and recommendations with metadata about data quality and sources
 * 
 * Task 11 Updates:
 * - Simplified revision UI to "Start New Workflow" instead of complex targeting
 * - Added export/save results functionality
 * - Removed complex revision targeting in favor of restart workflow
 * 
 * Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 9.1, 9.2
 */
const ComprehensiveResultsDisplay: React.FC<ComprehensiveResultsDisplayProps> = ({
  comprehensiveResults,
  handleApproveResults,
  handleRequestRevision,
  processingApproval,
  showApprovalButtons
}) => {
  const styles = useStyles();
  const [selectedTab, setSelectedTab] = useState<TabValue>('overview');
  const [isRevisionDialogOpen, setIsRevisionDialogOpen] = useState(false);
  const [revisionFeedback, setRevisionFeedback] = useState('');
  const [isSubmittingRevision, setIsSubmittingRevision] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  // Always render, but return null if no results
  if (!comprehensiveResults) {
    return null;
  }

  const onTabSelect = (event: SelectTabEvent, data: SelectTabData) => {
    setSelectedTab(data.value);
  };

  // Calculate overall completion status
  const completedAgents = Object.values(comprehensiveResults.results).filter(
    result => result?.status === 'completed'
  ).length;
  const totalAgents = Object.keys(comprehensiveResults.results).length;
  const hasErrors = Object.values(comprehensiveResults.results).some(
    result => result?.status === 'error'
  );

  // Get quality score color
  const getQualityColor = (score: number): string => {
    if (score >= 0.8) return tokens.colorPaletteGreenForeground1;
    if (score >= 0.6) return tokens.colorPaletteYellowForeground1;
    return tokens.colorPaletteRedForeground1;
  };

  // Get quality badge
  const getQualityBadge = (quality: 'high' | 'medium' | 'low') => {
    const config = {
      high: { color: 'success', icon: CheckmarkCircle20Regular },
      medium: { color: 'warning', icon: Warning20Regular },
      low: { color: 'danger', icon: ErrorCircle20Regular }
    };
    
    const { color, icon: Icon } = config[quality];
    return (
      <div className={styles.qualityIndicator}>
        <Icon style={{ fontSize: '14px' }} />
        <Text style={{ fontSize: '12px', textTransform: 'capitalize' }}>{quality}</Text>
      </div>
    );
  };

  // Handle export functionality
  const handleExportResults = async () => {
    setIsExporting(true);
    try {
      // Create comprehensive export data
      const exportData = {
        timestamp: new Date().toISOString(),
        comprehensive_results: comprehensiveResults,
        export_metadata: {
          total_agents: Object.keys(comprehensiveResults.results).length,
          completed_agents: Object.values(comprehensiveResults.results).filter(r => r?.status === 'completed').length,
          export_date: new Date().toLocaleDateString(),
          export_time: new Date().toLocaleTimeString()
        }
      };
      
      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `comprehensive-results-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      console.log('💾 Comprehensive results exported successfully');
    } catch (error) {
      console.error('❌ Failed to export comprehensive results:', error);
    } finally {
      setIsExporting(false);
    }
  };

  // Handle revision submission - simplified to restart workflow - simplified to restart workflow
  const handleRevisionSubmit = async () => {
    if (!revisionFeedback.trim()) {
      return;
    }

    setIsSubmittingRevision(true);
    try {
      // Simplified: all revision requests become restart requests
      console.log('🔄 User requested workflow restart from comprehensive results');
      await handleRequestRevision('restart', [], `restart: ${revisionFeedback}`);
      setIsRevisionDialogOpen(false);
      setRevisionFeedback('');
    } catch (error) {
      console.error('Error submitting restart request:', error);
    } finally {
      setIsSubmittingRevision(false);
    }
  };

  // Render agent result card
  const renderAgentResult = (agentKey: string, result: AgentResult) => {
    const agentDisplayName = getAgentDisplayName(agentKey);
    const isCompleted = result.status === 'completed';
    
    return (
      <div key={agentKey} className={styles.agentResultCard}>
        <div className={styles.agentHeader}>
          <div className={styles.agentIcon}>
            {getAgentIcon(agentKey)}
          </div>
          <div className={styles.agentName}>
            {agentDisplayName}
          </div>
          <Badge 
            appearance="filled" 
            color={isCompleted ? 'success' : 'danger'}
            className={styles.statusBadge}
          >
            {isCompleted ? 'Completed' : 'Error'}
          </Badge>
        </div>

        <div className={styles.metadataGrid}>
          <div className={styles.metadataItem}>
            <div className={styles.metadataLabel}>Service Used</div>
            <div className={styles.metadataValue}>{result.metadata.service_used}</div>
          </div>
          <div className={styles.metadataItem}>
            <div className={styles.metadataLabel}>Data Quality</div>
            <div className={styles.metadataValue}>
              {getQualityBadge(result.metadata.data_quality)}
            </div>
          </div>
          <div className={styles.metadataItem}>
            <div className={styles.metadataLabel}>Execution Time</div>
            <div className={styles.metadataValue}>{result.metadata.execution_time}s</div>
          </div>
        </div>

        <div className={styles.resultContent}>
          {typeof result.result === 'string' 
            ? result.result 
            : JSON.stringify(result.result, null, 2)
          }
        </div>
      </div>
    );
  };

  return (
    <div className={styles.container}>
      <Card className={styles.resultsCard}>
        {/* Results Header */}
        <div className={styles.resultsHeader}>
          <div className={styles.headerIcon}>
            <DataTrending20Regular style={{ color: tokens.colorNeutralForegroundOnBrand, fontSize: '20px' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div className={styles.resultsTitle}>
              Comprehensive Analysis Results
            </div>
            <div className={styles.resultsSubtitle}>
              {completedAgents}/{totalAgents} agents completed • Generated {new Date(comprehensiveResults.timestamp).toLocaleString()}
            </div>
          </div>
          <Badge appearance="filled" color={hasErrors ? 'warning' : 'success'}>
            {hasErrors ? 'Completed with Issues' : 'All Completed'}
          </Badge>
        </div>

        {/* Tab Navigation */}
        <div className={styles.tabContainer}>
          <TabList selectedValue={selectedTab} onTabSelect={onTabSelect}>
            <Tab value="overview">Overview</Tab>
            <Tab value="gmail">Email Results</Tab>
            <Tab value="accounts_payable">AP Results</Tab>
            <Tab value="crm">CRM Results</Tab>
            <Tab value="analysis">Analysis</Tab>
            <Tab value="correlations">Data Correlations</Tab>
          </TabList>
        </div>

        {/* Tab Content */}
        <div className={styles.tabContent}>
          {selectedTab === 'overview' && (
            <div>
              {/* Executive Summary */}
              <div className={styles.summarySection}>
                <Title3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Info20Regular />
                  Executive Summary
                </Title3>
                <div className={styles.summaryContent}>
                  {comprehensiveResults.executive_summary}
                </div>
              </div>

              {/* Recommendations */}
              <div className={styles.summarySection}>
                <Title3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <TaskListSquareLtrRegular />
                  Recommendations
                </Title3>
                <ul className={styles.recommendationsList}>
                  {comprehensiveResults.recommendations.map((recommendation, index) => (
                    <li key={index} className={styles.recommendationItem}>
                      <Checkmark20Regular className={styles.recommendationIcon} />
                      <div className={styles.recommendationText}>{recommendation}</div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {selectedTab === 'gmail' && comprehensiveResults.results.gmail && (
            renderAgentResult('gmail', comprehensiveResults.results.gmail)
          )}

          {selectedTab === 'accounts_payable' && comprehensiveResults.results.accounts_payable && (
            renderAgentResult('accounts_payable', comprehensiveResults.results.accounts_payable)
          )}

          {selectedTab === 'crm' && comprehensiveResults.results.crm && (
            renderAgentResult('crm', comprehensiveResults.results.crm)
          )}

          {selectedTab === 'analysis' && comprehensiveResults.results.analysis && (
            renderAgentResult('analysis', comprehensiveResults.results.analysis)
          )}

          {selectedTab === 'correlations' && (
            <div className={styles.correlationSection}>
              <Title3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <DataTrending20Regular />
                Data Correlation Analysis
              </Title3>
              
              <div className={styles.correlationGrid}>
                <div className={styles.correlationCard}>
                  <div className={styles.correlationValue}>
                    {comprehensiveResults.correlations.cross_references}
                  </div>
                  <div className={styles.correlationLabel}>Cross References</div>
                </div>
                
                <div className={styles.correlationCard}>
                  <div className={styles.correlationValue}>
                    {Math.round(comprehensiveResults.correlations.data_consistency * 100)}%
                  </div>
                  <div className={styles.correlationLabel}>Data Consistency</div>
                </div>
                
                <div className={styles.correlationCard}>
                  <div className={styles.correlationValue}>
                    {comprehensiveResults.correlations.vendor_mentions}
                  </div>
                  <div className={styles.correlationLabel}>Vendor Mentions</div>
                </div>
                
                <div className={styles.correlationCard}>
                  <div 
                    className={styles.correlationValue}
                    style={{ color: getQualityColor(comprehensiveResults.correlations.quality_score) }}
                  >
                    {Math.round(comprehensiveResults.correlations.quality_score * 100)}%
                  </div>
                  <div className={styles.correlationLabel}>Overall Quality Score</div>
                </div>
              </div>

              <Body1 style={{ 
                color: tokens.colorNeutralForeground2,
                padding: '16px',
                backgroundColor: tokens.colorNeutralBackground1,
                borderRadius: tokens.borderRadiusMedium,
                border: `1px solid ${tokens.colorNeutralStroke2}`
              }}>
                The correlation analysis shows how well data from different sources aligns and cross-references. 
                Higher scores indicate better data quality and consistency across systems.
              </Body1>
            </div>
          )}
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
          Please review the comprehensive analysis results above. You can approve the results to complete the workflow, 
          or request revisions to specific agents or the entire analysis.
        </Body1>

        {/* Action Buttons */}
        {showApprovalButtons && (
          <div className={styles.buttonContainer}>
            <Button
              appearance="primary"
              size="medium"
              onClick={handleApproveResults}
              disabled={processingApproval || isSubmittingRevision}
              icon={<Checkmark20Regular />}
            >
              {processingApproval ? 'Approving...' : 'Approve Results'}
            </Button>
            
            <Dialog 
              open={isRevisionDialogOpen} 
              onOpenChange={(_, data) => setIsRevisionDialogOpen(data.open)}
            >
              <DialogTrigger disableButtonEnhancement>
                <Button
                  appearance="secondary"
                  size="medium"
                  disabled={processingApproval || isSubmittingRevision}
                  icon={<Edit20Regular />}
                >
                  Start New Workflow
                </Button>
              </DialogTrigger>
              <DialogSurface className={styles.revisionDialog}>
                <DialogBody>
                  <DialogTitle>Start New Workflow</DialogTitle>
                  <DialogContent>
                    <Body2 style={{ marginBottom: '16px' }}>
                      If you're not satisfied with the current results, you can start a new workflow with different parameters or requirements.
                    </Body2>
                    
                    <div style={{
                      padding: '16px',
                      backgroundColor: tokens.colorPaletteYellowBackground1,
                      borderRadius: tokens.borderRadiusMedium,
                      border: `1px solid ${tokens.colorPaletteYellowBorder1}`,
                      marginBottom: '16px',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px'
                    }}>
                      <Warning20Regular style={{ 
                        color: tokens.colorPaletteYellowForeground1,
                        flexShrink: 0,
                        marginTop: '2px'
                      }} />
                      <div style={{ 
                        color: tokens.colorNeutralForeground1,
                        fontSize: '14px',
                        lineHeight: '1.5'
                      }}>
                        <strong>This will end the current workflow.</strong>
                        <br />
                        You'll need to submit a new task to begin a fresh workflow. 
                        Consider exporting the current results first if you want to keep them.
                      </div>
                    </div>

                    <Field label="Reason for starting new workflow (optional)">
                      <Textarea
                        placeholder="Describe what should be different in the new workflow..."
                        value={revisionFeedback}
                        onChange={(_, data) => setRevisionFeedback(data.value)}
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
                      onClick={handleRevisionSubmit}
                      disabled={!revisionFeedback.trim() || isSubmittingRevision}
                    >
                      {isSubmittingRevision ? 'Starting New Workflow...' : 'Start New Workflow'}
                    </Button>
                  </DialogActions>
                </DialogBody>
              </DialogSurface>
            </Dialog>

            <Button
              appearance="secondary"
              size="medium"
              disabled={processingApproval || isSubmittingRevision || isExporting}
              icon={<Save20Regular />}
              onClick={handleExportResults}
            >
              {isExporting ? 'Exporting...' : 'Export Results'}
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default ComprehensiveResultsDisplay;