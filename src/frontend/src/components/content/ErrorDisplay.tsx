import React from 'react';
import {
    Card,
    Text,
    Button,
    makeStyles,
    tokens
} from '@fluentui/react-components';
import {
    ErrorCircle24Regular,
    ArrowReset24Regular
} from '@fluentui/react-icons';

const useStyles = makeStyles({
    container: {
        maxWidth: '800px',
        margin: '0 auto 24px auto',
        padding: '0 24px'
    },
    errorCard: {
        backgroundColor: tokens.colorPaletteRedBackground1,
        border: `1px solid ${tokens.colorPaletteRedBorder1}`,
        borderRadius: tokens.borderRadiusMedium,
        padding: '24px',
        textAlign: 'center'
    },
    errorIcon: {
        color: tokens.colorPaletteRedForeground1,
        marginBottom: '16px'
    },
    errorTitle: {
        fontSize: '18px',
        fontWeight: '600',
        color: tokens.colorPaletteRedForeground1,
        marginBottom: '12px'
    },
    errorMessage: {
        fontSize: '14px',
        color: tokens.colorNeutralForeground1,
        marginBottom: '20px',
        lineHeight: '1.4'
    },
    restartButton: {
        backgroundColor: tokens.colorBrandBackground,
        color: tokens.colorNeutralForegroundOnBrand,
        '&:hover': {
            backgroundColor: tokens.colorBrandBackgroundHover
        }
    }
});

interface ErrorDisplayProps {
    title?: string;
    message: string;
    onRestart: () => void;
    isLoading?: boolean;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
    title = "Workflow Error",
    message,
    onRestart,
    isLoading = false
}) => {
    const styles = useStyles();

    return (
        <div className={styles.container}>
            <Card className={styles.errorCard}>
                <ErrorCircle24Regular className={styles.errorIcon} />
                
                <Text className={styles.errorTitle}>
                    {title}
                </Text>
                
                <Text className={styles.errorMessage}>
                    {message}
                </Text>
                
                <Button
                    appearance="primary"
                    className={styles.restartButton}
                    icon={<ArrowReset24Regular />}
                    onClick={onRestart}
                    disabled={isLoading}
                >
                    Start New Task
                </Button>
            </Card>
        </div>
    );
};

export default ErrorDisplay;