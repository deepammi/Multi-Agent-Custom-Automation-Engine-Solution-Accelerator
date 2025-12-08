import React, { useState } from 'react';
import {
  Title2,
  Title3,
  Body1,
  Dropdown,
  Option,
  Card,
  Button,
  makeStyles,
  tokens,
  shorthands,
} from '@fluentui/react-components';
import { Dismiss24Regular, PlugConnected20Regular } from '@fluentui/react-icons';
import { useNavigate } from 'react-router-dom';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.overflow('hidden'),
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...shorthands.padding('24px', '32px'),
    ...shorthands.borderBottom('1px', 'solid', tokens.colorNeutralStroke2),
    backgroundColor: tokens.colorNeutralBackground1,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    ...shorthands.gap('12px'),
  },
  content: {
    flex: 1,
    ...shorthands.padding('32px'),
    ...shorthands.overflow('auto'),
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
    ...shorthands.gap('24px'),
    maxWidth: '1400px',
    marginLeft: 'auto',
    marginRight: 'auto',
  },
  card: {
    ...shorthands.padding('24px'),
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('16px'),
  },
  cardHeader: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('8px'),
  },
  dropdown: {
    minWidth: '100%',
  },
  statusBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    ...shorthands.padding('4px', '12px'),
    ...shorthands.borderRadius('12px'),
    backgroundColor: tokens.colorNeutralBackground3,
    fontSize: '12px',
    fontWeight: 600,
    color: tokens.colorNeutralForeground2,
  },
  connectedBadge: {
    backgroundColor: tokens.colorPaletteGreenBackground2,
    color: tokens.colorPaletteGreenForeground2,
  },
});

interface IntegrationCategory {
  id: string;
  title: string;
  description: string;
  icon: string;
  options: string[];
  connectedTo?: string;
}

const IntegrationsPage: React.FC = () => {
  const styles = useStyles();
  const navigate = useNavigate();

  const [integrations, setIntegrations] = useState<IntegrationCategory[]>([
    {
      id: 'erp',
      title: 'ERP Systems',
      description: 'Connect to enterprise resource planning systems for financial data, inventory, and operations',
      icon: '💼',
      options: ['Select ERP System', 'Zoho Books', 'Oracle NetSuite', 'SAP S/4HANA', 'Microsoft Dynamics 365', 'Sage Intacct', 'Acumatica'],
      connectedTo: 'Zoho Books',
    },
    {
      id: 'crm',
      title: 'CRM Systems',
      description: 'Integrate with customer relationship management platforms for sales, contacts, and opportunities',
      icon: '👥',
      options: ['Select CRM System', 'Salesforce', 'HubSpot', 'Microsoft Dynamics CRM', 'Zoho CRM', 'Pipedrive', 'Freshsales'],
      connectedTo: 'Salesforce',
    },
    {
      id: 'email',
      title: 'Email & Marketing',
      description: 'Connect email and marketing automation platforms for campaigns and communications',
      icon: '📧',
      options: ['Select Email Platform', 'Mailchimp', 'SendGrid', 'Constant Contact', 'Campaign Monitor', 'ActiveCampaign', 'Brevo (Sendinblue)'],
    },
    {
      id: 'accounting',
      title: 'Accounting Systems',
      description: 'Integrate with accounting and bookkeeping platforms for financial management and reporting',
      icon: '📊',
      options: ['Select Accounting System', 'QuickBooks Online', 'Xero', 'FreshBooks', 'Wave', 'Sage Business Cloud', 'Zoho Books', 'NetSuite'],
    },
    {
      id: 'hr',
      title: 'HR & Payroll',
      description: 'Connect to human resources and payroll systems for employee management and benefits',
      icon: '🧑‍💼',
      options: ['Select HR System', 'Workday', 'ADP Workforce Now', 'BambooHR', 'Gusto', 'Rippling', 'Zenefits', 'Paychex Flex'],
    },
    {
      id: 'ai',
      title: 'AI Models',
      description: 'Configure AI and machine learning model providers for intelligent automation and insights',
      icon: '🤖',
      options: ['Select AI Provider', 'OpenAI (GPT-4)', 'Amazon Bedrock', 'Meta Llama', 'Google Gemini', 'Anthropic Claude', 'Azure OpenAI', 'Cohere'],
      connectedTo: 'OpenAI (GPT-4)',
    },
  ]);

  const handleSelectionChange = (categoryId: string, value: string) => {
    setIntegrations(prev =>
      prev.map(integration =>
        integration.id === categoryId
          ? { ...integration, connectedTo: value === integration.options[0] ? undefined : value }
          : integration
      )
    );
  };

  const handleClose = () => {
    navigate(-1);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <PlugConnected20Regular style={{ fontSize: '24px' }} />
          <Title2>Enterprise Integrations</Title2>
        </div>
        <Button
          appearance="subtle"
          icon={<Dismiss24Regular />}
          onClick={handleClose}
          aria-label="Close integrations"
        />
      </div>

      <div className={styles.content}>
        <div className={styles.grid}>
          {integrations.map((integration) => (
            <Card key={integration.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '24px' }}>{integration.icon}</span>
                    <Title3>{integration.title}</Title3>
                  </div>
                  {integration.connectedTo && (
                    <span className={`${styles.statusBadge} ${styles.connectedBadge}`}>
                      Connected
                    </span>
                  )}
                </div>
                <Body1 style={{ color: tokens.colorNeutralForeground2 }}>
                  {integration.description}
                </Body1>
              </div>

              <Dropdown
                className={styles.dropdown}
                placeholder="Select a system"
                value={integration.connectedTo || integration.options[0]}
                onOptionSelect={(_, data) => {
                  if (data.optionValue) {
                    handleSelectionChange(integration.id, data.optionValue);
                  }
                }}
              >
                {integration.options.map((option) => (
                  <Option key={option} value={option}>
                    {option}
                  </Option>
                ))}
              </Dropdown>

              {integration.connectedTo && (
                <Body1 style={{ fontSize: '12px', color: tokens.colorNeutralForeground3 }}>
                  Currently connected to <strong>{integration.connectedTo}</strong>
                </Body1>
              )}
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default IntegrationsPage;
