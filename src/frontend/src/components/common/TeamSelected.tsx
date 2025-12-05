import { TeamConfig } from "@/models";
import { Body1, Body2, Caption1, Caption2 } from "@fluentui/react-components";
import styles from '../../styles/TeamSelector.module.css';
export interface TeamSelectedProps {
    selectedTeam?: TeamConfig | null;
}

const TeamSelected: React.FC<TeamSelectedProps> = ({ selectedTeam }) => {
    return (
        <div className={styles.teamSelectorContent}>
            <Caption1 className={styles.currentTeamLabel}>
                &nbsp;&nbsp;Current Team
            </Caption1>
            <Body1 className={styles.currentTeamName}>
                &nbsp;&nbsp;{selectedTeam ? selectedTeam.name : 'No team selected'}
            </Body1>
            {selectedTeam && selectedTeam.description && (
                <Caption2 style={{ padding: '0 8px', color: '#666', marginTop: '4px' }}>
                    {selectedTeam.description}
                </Caption2>
            )}
            {selectedTeam && selectedTeam.agents && selectedTeam.agents.length > 0 && (
                <div style={{ padding: '8px', marginTop: '4px' }}>
                    <Caption2 style={{ fontWeight: 600, marginBottom: '4px' }}>Agents:</Caption2>
                    {selectedTeam.agents.map((agent, index) => (
                        <Caption2 key={index} style={{ display: 'block', color: '#666', marginLeft: '8px' }}>
                            • {agent.name}{agent.role ? ` - ${agent.role}` : ''}
                        </Caption2>
                    ))}
                </div>
            )}
        </div>
    );
}
export default TeamSelected;