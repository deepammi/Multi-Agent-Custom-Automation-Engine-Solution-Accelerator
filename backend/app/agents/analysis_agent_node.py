"""
Analysis Agent Node for LangGraph Workflows

This module provides the LangGraph node implementation for the Analysis Agent,
enabling comprehensive cross-system data correlation within multi-agent workflows.

Enhanced for Task 6.2 with:
- Integration with LangGraph state management
- WebSocket progress reporting for analysis steps
- Enhanced data passing from previous agents
- Comprehensive error handling and fallback analysis

**Feature: multi-agent-invoice-workflow, Property 6: Cross-System Data Integration**
**Validates: Requirements FR2.4, FR4.1, FR4.2**
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.agents.state import AgentState, AgentStateManager
from app.agents.analysis_agent import AnalysisAgent, create_analysis_agent
from app.services.llm_service import LLMService
from app.services.websocket_service import WebSocketManager

logger = logging.getLogger(__name__)


class AnalysisAgentNode:
    """
    LangGraph node for comprehensive cross-system data analysis.
    
    This node performs the final analysis step in the multi-agent workflow,
    correlating data from email, accounts payable, and CRM agents to generate
    comprehensive insights and identify payment issues.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the Analysis Agent Node.
        
        Args:
            llm_service: Optional LLM service for generating analysis
        """
        self.analysis_agent = create_analysis_agent(llm_service)
        self.llm_service = llm_service or LLMService()
        
    async def __call__(self, state: AgentState) -> AgentState:
        """
        Execute analysis agent within LangGraph workflow.
        
        Args:
            state: Current agent state with collected data from previous agents
            
        Returns:
            Updated agent state with analysis results
        """
        plan_id = state.get("plan_id", "unknown")
        task_description = state.get("task_description", "")
        websocket_manager = state.get("websocket_manager")
        
        logger.info(
            f"Analysis agent starting for plan {plan_id}",
            extra={
                "plan_id": plan_id,
                "task_description": task_description[:100] + "..." if len(task_description) > 100 else task_description
            }
        )
        
        # Send start message via WebSocket
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "agent_stream_start",
                "data": {
                    "agent": "analysis",
                    "agent_type": "analysis",
                    "message": "🔍 Starting comprehensive cross-system data analysis...",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }
            })
        
        try:
            # Extract vendor name from task description
            vendor_name = self._extract_vendor_name(task_description)
            
            # Collect data from previous agents
            collected_data = state.get("collected_data", {})
            enhanced_data = self._extract_enhanced_agent_data(state)
            
            # Send progress update
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message_streaming",
                    "data": {
                        "agent": "analysis",
                        "content": f"📊 Analyzing data from {len(enhanced_data)} systems for vendor: {vendor_name}\n",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            
            # Perform comprehensive analysis
            analysis_result = await self.analysis_agent.analyze_cross_system_data(
                email_data=enhanced_data.get('email'),
                ap_data=enhanced_data.get('ap'),
                crm_data=enhanced_data.get('crm'),
                vendor_name=vendor_name
            )
            
            # Generate detailed analysis report
            analysis_report = await self._generate_detailed_report(
                analysis_result,
                vendor_name,
                websocket_manager,
                plan_id
            )
            
            # Update state with analysis results
            agent_result = {
                "status": "success",
                "agent": "analysis",
                "message": analysis_report,
                "data": {
                    "analysis_result": analysis_result,
                    "vendor_name": vendor_name,
                    "correlations_found": len(analysis_result.correlations),
                    "discrepancies_found": len(analysis_result.discrepancies),
                    "payment_issues_found": len(analysis_result.payment_issues),
                    "data_quality_score": analysis_result.data_quality_score,
                    "recommendations": analysis_result.recommendations
                },
                "execution_time": analysis_result.execution_metadata.get("execution_time_seconds", 0.0)
            }
            
            # Add agent result to state
            updated_state = AgentStateManager.add_agent_result(state, "analysis", agent_result)
            
            # Send completion message
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_stream_end",
                    "data": {
                        "agent": "analysis",
                        "agent_type": "analysis",
                        "message": f"✅ Analysis completed: {len(analysis_result.correlations)} correlations, {len(analysis_result.discrepancies)} discrepancies, {len(analysis_result.payment_issues)} issues identified",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            
            logger.info(
                f"Analysis agent completed successfully for plan {plan_id}",
                extra={
                    "plan_id": plan_id,
                    "vendor_name": vendor_name,
                    "correlations_found": len(analysis_result.correlations),
                    "discrepancies_found": len(analysis_result.discrepancies),
                    "payment_issues_found": len(analysis_result.payment_issues),
                    "data_quality_score": analysis_result.data_quality_score,
                    "execution_time": analysis_result.execution_metadata.get("execution_time_seconds", 0.0)
                }
            )
            
            return updated_state
            
        except Exception as e:
            logger.error(
                f"Analysis agent failed for plan {plan_id}: {e}",
                extra={
                    "plan_id": plan_id,
                    "error": str(e),
                    "task_description": task_description
                },
                exc_info=True
            )
            
            # Generate fallback analysis
            fallback_analysis = await self._generate_fallback_analysis(
                state,
                vendor_name,
                str(e),
                websocket_manager,
                plan_id
            )
            
            # Update state with fallback result
            agent_result = {
                "status": "partial_success",
                "agent": "analysis",
                "message": fallback_analysis,
                "data": {
                    "analysis_type": "fallback",
                    "error": str(e),
                    "vendor_name": vendor_name
                },
                "execution_time": 0.0
            }
            
            updated_state = AgentStateManager.add_agent_result(state, "analysis", agent_result)
            
            # Send error message
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_stream_end",
                    "data": {
                        "agent": "analysis",
                        "agent_type": "analysis",
                        "message": f"⚠️ Analysis completed with limitations due to error: {str(e)[:100]}",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            
            return updated_state
    
    def _extract_vendor_name(self, task_description: str) -> Optional[str]:
        """
        Extract vendor name from task description.
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Extracted vendor name or None
        """
        # Look for common vendor name patterns
        import re
        
        # Pattern 1: "vendor_name" in quotes
        quoted_pattern = r'["\']([^"\']+)["\']'
        quoted_matches = re.findall(quoted_pattern, task_description)
        
        # Pattern 2: "for [vendor_name]" or "with [vendor_name]"
        for_with_pattern = r'(?:for|with|from)\s+([A-Z][a-zA-Z\s&]+?)(?:\s+and|$|\.|,)'
        for_with_matches = re.findall(for_with_pattern, task_description)
        
        # Pattern 3: Look for capitalized company names
        company_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b'
        company_matches = re.findall(company_pattern, task_description)
        
        # Filter out common words that aren't vendor names
        common_words = {
            'Check', 'Find', 'Analyze', 'Status', 'Invoice', 'Payment', 'Bill',
            'Account', 'System', 'Data', 'Information', 'Report', 'Summary'
        }
        
        # Prioritize quoted matches
        if quoted_matches:
            return quoted_matches[0].strip()
        
        # Then for/with pattern matches
        if for_with_matches:
            candidate = for_with_matches[0].strip()
            if candidate not in common_words:
                return candidate
        
        # Finally, look for company-like patterns
        for match in company_matches:
            if match not in common_words and len(match) > 3:
                return match
        
        # Default fallback
        return "Unknown Vendor"
    
    def _extract_enhanced_agent_data(self, state: AgentState) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Extract and organize data from previous agents with enhanced structure.
        
        Args:
            state: Current agent state
            
        Returns:
            Dictionary with organized data from each agent type
        """
        collected_data = state.get("collected_data", {})
        enhanced_data = {
            'email': None,
            'ap': None,
            'crm': None
        }
        
        # Map agent names to data types
        agent_mapping = {
            'gmail': 'email',
            'email': 'email',
            'invoice': 'ap',
            'accounts_payable': 'ap',
            'salesforce': 'crm',
            'crm': 'crm'
        }
        
        # Extract data from collected_data
        for agent_name, agent_data in collected_data.items():
            data_type = agent_mapping.get(agent_name)
            if data_type and agent_data:
                enhanced_data[data_type] = agent_data
        
        # Also check enhanced data from orchestrator
        for agent_name in agent_mapping.keys():
            enhanced_key = f"{agent_name}_enhanced_data"
            if enhanced_key in state:
                enhanced_agent_data = state[enhanced_key]
                data_type = agent_mapping[agent_name]
                
                # Merge with existing data or replace if better
                if enhanced_data[data_type] is None:
                    enhanced_data[data_type] = enhanced_agent_data.get('data', {})
                elif isinstance(enhanced_agent_data, dict) and 'data' in enhanced_agent_data:
                    # Merge the data
                    existing_data = enhanced_data[data_type] or {}
                    new_data = enhanced_agent_data['data'] or {}
                    enhanced_data[data_type] = {**existing_data, **new_data}
        
        return enhanced_data
    
    async def _generate_detailed_report(
        self,
        analysis_result,
        vendor_name: Optional[str],
        websocket_manager: Optional[WebSocketManager],
        plan_id: str
    ) -> str:
        """
        Generate detailed analysis report with streaming updates.
        
        Args:
            analysis_result: Analysis result from analysis agent
            vendor_name: Target vendor name
            websocket_manager: WebSocket manager for streaming
            plan_id: Plan ID for WebSocket messages
            
        Returns:
            Formatted analysis report
        """
        report_sections = []
        
        # Executive Summary
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message_streaming",
                "data": {
                    "agent": "analysis",
                    "content": "📋 **EXECUTIVE SUMMARY**\n",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }
            })
        
        executive_summary = f"""
**CROSS-SYSTEM ANALYSIS REPORT FOR {vendor_name.upper()}**

Data Quality Score: {analysis_result.data_quality_score:.1%}
Correlations Found: {len(analysis_result.correlations)}
Discrepancies Detected: {len(analysis_result.discrepancies)}
Payment Issues Identified: {len(analysis_result.payment_issues)}

{analysis_result.analysis_summary}
"""
        report_sections.append(executive_summary)
        
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message_streaming",
                "data": {
                    "agent": "analysis",
                    "content": executive_summary + "\n",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }
            })
        
        # Correlations Section
        if analysis_result.correlations:
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message_streaming",
                    "data": {
                        "agent": "analysis",
                        "content": "🔗 **DATA CORRELATIONS**\n",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            
            correlations_section = "\n**DATA CORRELATIONS FOUND:**\n"
            for i, correlation in enumerate(analysis_result.correlations, 1):
                systems = []
                if correlation.email_data:
                    systems.append("Email")
                if correlation.ap_data:
                    systems.append("AP")
                if correlation.crm_data:
                    systems.append("CRM")
                
                correlation_text = (
                    f"{i}. {' ↔ '.join(systems)} Correlation\n"
                    f"   Score: {correlation.correlation_score:.2f} ({correlation.confidence_level} confidence)\n"
                    f"   Keys: {', '.join(correlation.correlation_keys)}\n"
                )
                correlations_section += correlation_text
                
                if websocket_manager:
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message_streaming",
                        "data": {
                            "agent": "analysis",
                            "content": correlation_text,
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                        }
                    })
            
            report_sections.append(correlations_section)
        
        # Discrepancies Section
        if analysis_result.discrepancies:
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message_streaming",
                    "data": {
                        "agent": "analysis",
                        "content": "\n⚠️ **DISCREPANCIES DETECTED**\n",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            
            discrepancies_section = "\n**DISCREPANCIES DETECTED:**\n"
            for i, discrepancy in enumerate(analysis_result.discrepancies, 1):
                severity_icon = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "⚡",
                    "low": "ℹ️"
                }.get(discrepancy.severity, "•")
                
                discrepancy_text = (
                    f"{i}. {severity_icon} {discrepancy.discrepancy_type.value.replace('_', ' ').title()} "
                    f"({discrepancy.severity.upper()})\n"
                    f"   {discrepancy.description}\n"
                    f"   Action: {discrepancy.recommended_action}\n"
                )
                discrepancies_section += discrepancy_text
                
                if websocket_manager:
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message_streaming",
                        "data": {
                            "agent": "analysis",
                            "content": discrepancy_text,
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                        }
                    })
            
            report_sections.append(discrepancies_section)
        
        # Payment Issues Section
        if analysis_result.payment_issues:
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message_streaming",
                    "data": {
                        "agent": "analysis",
                        "content": "\n💰 **PAYMENT ISSUES**\n",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            
            payment_issues_section = "\n**PAYMENT ISSUES IDENTIFIED:**\n"
            for i, issue in enumerate(analysis_result.payment_issues, 1):
                severity_icon = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "⚡",
                    "low": "ℹ️"
                }.get(issue.severity, "•")
                
                amount_text = f" (${issue.affected_amount:,.2f})" if issue.affected_amount else ""
                
                issue_text = (
                    f"{i}. {severity_icon} {issue.issue_type.value.replace('_', ' ').title()} "
                    f"({issue.severity.upper()}){amount_text}\n"
                    f"   {issue.description}\n"
                    f"   Action: {issue.recommended_action}\n"
                    f"   Urgency: {issue.urgency_score:.1%}\n"
                )
                payment_issues_section += issue_text
                
                if websocket_manager:
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message_streaming",
                        "data": {
                            "agent": "analysis",
                            "content": issue_text,
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                        }
                    })
            
            report_sections.append(payment_issues_section)
        
        # Recommendations Section
        if analysis_result.recommendations:
            if websocket_manager:
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_message_streaming",
                    "data": {
                        "agent": "analysis",
                        "content": "\n💡 **RECOMMENDATIONS**\n",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    }
                })
            
            recommendations_section = "\n**KEY RECOMMENDATIONS:**\n"
            for i, recommendation in enumerate(analysis_result.recommendations, 1):
                recommendation_text = f"{i}. {recommendation}\n"
                recommendations_section += recommendation_text
                
                if websocket_manager:
                    await websocket_manager.send_message(plan_id, {
                        "type": "agent_message_streaming",
                        "data": {
                            "agent": "analysis",
                            "content": recommendation_text,
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                        }
                    })
            
            report_sections.append(recommendations_section)
        
        # Execution Metadata
        metadata = analysis_result.execution_metadata
        metadata_section = f"""
**ANALYSIS METADATA:**
- Execution Time: {metadata.get('execution_time_seconds', 0):.2f} seconds
- Data Sources Analyzed: {metadata.get('data_sources_analyzed', 0)}
- Analysis Completed: {metadata.get('analysis_end_time', 'Unknown')}
"""
        report_sections.append(metadata_section)
        
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message_streaming",
                "data": {
                    "agent": "analysis",
                    "content": metadata_section,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }
            })
        
        return "\n".join(report_sections)
    
    async def _generate_fallback_analysis(
        self,
        state: AgentState,
        vendor_name: Optional[str],
        error_message: str,
        websocket_manager: Optional[WebSocketManager],
        plan_id: str
    ) -> str:
        """
        Generate fallback analysis when main analysis fails.
        
        Args:
            state: Current agent state
            vendor_name: Target vendor name
            error_message: Error that caused fallback
            websocket_manager: WebSocket manager for streaming
            plan_id: Plan ID for WebSocket messages
            
        Returns:
            Fallback analysis report
        """
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message_streaming",
                "data": {
                    "agent": "analysis",
                    "content": "⚠️ Generating fallback analysis due to processing error...\n",
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }
            })
        
        # Collect basic information from state
        collected_data = state.get("collected_data", {})
        execution_results = state.get("execution_results", [])
        
        # Count available data sources
        available_agents = [agent for agent, data in collected_data.items() if data]
        
        fallback_report = f"""
**FALLBACK ANALYSIS REPORT FOR {vendor_name}**

⚠️ **ANALYSIS LIMITATION NOTICE**
The comprehensive analysis engine encountered an error: {error_message[:200]}

**BASIC DATA SUMMARY:**
- Vendor: {vendor_name}
- Data Sources Available: {len(available_agents)} ({', '.join(available_agents) if available_agents else 'None'})
- Agents Executed: {len(execution_results)}

**AVAILABLE DATA OVERVIEW:**
"""
        
        # Summarize available data
        for agent_name, agent_data in collected_data.items():
            if agent_data:
                data_summary = f"✅ {agent_name.title()}: Data available"
                if isinstance(agent_data, dict):
                    if 'message' in agent_data:
                        message_length = len(str(agent_data['message']))
                        data_summary += f" ({message_length} characters)"
                fallback_report += f"- {data_summary}\n"
        
        if not available_agents:
            fallback_report += "- No agent data available for analysis\n"
        
        fallback_report += f"""
**BASIC RECOMMENDATIONS:**
1. Review individual agent results for {vendor_name}
2. Manually verify data consistency across systems
3. Contact technical support if analysis errors persist
4. Consider re-running the workflow with updated parameters

**NEXT STEPS:**
- Check system logs for detailed error information
- Verify data connectivity to all required systems
- Ensure all required services are operational

*This fallback analysis provides basic information only. For comprehensive cross-system correlation, please resolve the technical issue and re-run the analysis.*
"""
        
        if websocket_manager:
            await websocket_manager.send_message(plan_id, {
                "type": "agent_message_streaming",
                "data": {
                    "agent": "analysis",
                    "content": fallback_report,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                }
            })
        
        return fallback_report


# Factory function for creating analysis agent node
def create_analysis_agent_node(llm_service: Optional[LLMService] = None) -> AnalysisAgentNode:
    """
    Create and configure an Analysis Agent Node for LangGraph workflows.
    
    Args:
        llm_service: Optional LLM service instance
        
    Returns:
        Configured AnalysisAgentNode instance
    """
    return AnalysisAgentNode(llm_service=llm_service)