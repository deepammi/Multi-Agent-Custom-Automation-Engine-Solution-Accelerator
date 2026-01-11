"""
Comprehensive Results Compiler Service

This service formats and delivers comprehensive results from multi-agent workflows,
specifically extracting and formatting the Analysis Agent's comprehensive analysis
into the structure expected by the frontend.

The service acts as a lightweight formatter/transformer rather than performing
additional analysis, since the Analysis Agent already provides comprehensive
cross-system correlation, discrepancy detection, and executive summaries.

Requirements covered:
- 4.1: Compile comprehensive results from all agents
- 4.2: Display detailed output from each source system
- 4.3: Show data correlations and cross-references
- 4.4: Present final analysis with executive summary
- 4.5: Include metadata about quality and execution metrics
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.agents.state import AgentState
from app.agents.analysis_agent import AnalysisResult

logger = logging.getLogger(__name__)


class ResultsCompilerService:
    """
    Service for compiling and formatting comprehensive results from multi-agent workflows.
    
    This service extracts results from all agents, with special focus on the Analysis Agent's
    comprehensive analysis, and formats them into the structure expected by the frontend.
    """
    
    def __init__(self):
        """Initialize the Results Compiler Service."""
        pass
    
    async def compile_comprehensive_results(
        self,
        plan_id: str,
        agent_state: AgentState
    ) -> Dict[str, Any]:
        """
        Compile comprehensive results from all agents in the workflow.
        
        This method extracts results from all executed agents and formats them
        into the ComprehensiveResultsMessage structure expected by the frontend.
        
        Args:
            plan_id: Plan identifier
            agent_state: Current agent state with all execution results
            
        Returns:
            Formatted comprehensive results matching ComprehensiveResultsMessage interface
            
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
        """
        try:
            logger.info(f"Compiling comprehensive results for plan {plan_id}")
            
            # Extract agent results from state
            execution_results = agent_state.get("execution_results", [])
            collected_data = agent_state.get("collected_data", {})
            
            # Format individual agent results
            agent_results = self._format_agent_results(execution_results)
            
            # Extract Analysis Agent's comprehensive analysis
            analysis_result = self._extract_analysis_result(execution_results)
            
            # Format correlations data
            correlations = self._format_correlations(analysis_result)
            
            # Extract executive summary and recommendations
            executive_summary = self._extract_executive_summary(analysis_result)
            recommendations = self._extract_recommendations(analysis_result)
            
            # Compile final comprehensive results
            comprehensive_results = {
                "plan_id": plan_id,
                "results": agent_results,
                "correlations": correlations,
                "executive_summary": executive_summary,
                "recommendations": recommendations,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }
            
            logger.info(
                f"Successfully compiled comprehensive results for plan {plan_id}",
                extra={
                    "plan_id": plan_id,
                    "agents_included": list(agent_results.keys()),
                    "correlations_count": correlations.get("cross_references", 0),
                    "recommendations_count": len(recommendations),
                    "quality_score": correlations.get("quality_score", 0.0)
                }
            )
            
            return comprehensive_results
            
        except Exception as e:
            logger.error(
                f"Failed to compile comprehensive results for plan {plan_id}: {e}",
                extra={"plan_id": plan_id, "error": str(e)},
                exc_info=True
            )
            
            # Return fallback results structure
            return self._create_fallback_results(plan_id, str(e))
    
    def _format_agent_results(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Format individual agent results into the structure expected by frontend.
        
        Args:
            execution_results: List of agent execution results
            
        Returns:
            Dictionary mapping agent names to their formatted results
        """
        formatted_results = {}
        
        for result in execution_results:
            agent_name = result.get("agent", "unknown")
            
            # Map agent names to frontend expected names
            frontend_agent_name = self._map_agent_name(agent_name)
            
            formatted_results[frontend_agent_name] = {
                "agent": agent_name,
                "status": result.get("status", "unknown"),
                "message": result.get("message", ""),
                "data": result.get("data", {}),
                "execution_time": result.get("execution_time", 0.0),
                "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat() + "Z")
            }
        
        return formatted_results
    
    def _extract_analysis_result(self, execution_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Extract the Analysis Agent's comprehensive analysis result.
        
        Args:
            execution_results: List of agent execution results
            
        Returns:
            Analysis Agent's result data or None if not found
        """
        for result in execution_results:
            if result.get("agent") == "analysis":
                return result.get("data", {})
        
        return None
    
    def _format_correlations(self, analysis_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format correlation data from Analysis Agent into frontend structure.
        
        Args:
            analysis_result: Analysis Agent's result data
            
        Returns:
            Formatted correlations data
        """
        if not analysis_result:
            return {
                "cross_references": 0,
                "data_consistency": 0.0,
                "vendor_mentions": 0,
                "quality_score": 0.0
            }
        
        # Extract correlation metrics from Analysis Agent
        correlations_found = analysis_result.get("correlations_found", 0)
        data_quality_score = analysis_result.get("data_quality_score", 0.0)
        
        # Calculate additional metrics if available
        analysis_data = analysis_result.get("analysis_result", {})
        if isinstance(analysis_data, dict):
            # If we have detailed analysis result, extract more metrics
            vendor_mentions = self._count_vendor_mentions(analysis_data)
            data_consistency = self._calculate_data_consistency(analysis_data)
        else:
            vendor_mentions = 1  # Default assumption
            data_consistency = data_quality_score
        
        return {
            "cross_references": correlations_found,
            "data_consistency": data_consistency,
            "vendor_mentions": vendor_mentions,
            "quality_score": data_quality_score
        }
    
    def _extract_executive_summary(self, analysis_result: Optional[Dict[str, Any]]) -> str:
        """
        Extract executive summary from Analysis Agent result.
        
        Args:
            analysis_result: Analysis Agent's result data
            
        Returns:
            Executive summary text
        """
        if not analysis_result:
            return "No comprehensive analysis available."
        
        # Try to extract from analysis_result field
        analysis_data = analysis_result.get("analysis_result", {})
        if isinstance(analysis_data, dict):
            summary = analysis_data.get("analysis_summary", "")
            if summary:
                return summary
        
        # Fallback to general message
        return analysis_result.get("message", "Analysis completed successfully.")
    
    def _extract_recommendations(self, analysis_result: Optional[Dict[str, Any]]) -> List[str]:
        """
        Extract recommendations from Analysis Agent result.
        
        Args:
            analysis_result: Analysis Agent's result data
            
        Returns:
            List of recommendation strings
        """
        if not analysis_result:
            return ["No specific recommendations available."]
        
        # Try to extract from analysis_result field
        analysis_data = analysis_result.get("analysis_result", {})
        if isinstance(analysis_data, dict):
            recommendations = analysis_data.get("recommendations", [])
            if recommendations and isinstance(recommendations, list):
                return recommendations
        
        # Try to extract from direct recommendations field
        direct_recommendations = analysis_result.get("recommendations", [])
        if direct_recommendations and isinstance(direct_recommendations, list):
            return direct_recommendations
        
        # Fallback recommendation
        return ["Review the analysis results and take appropriate action based on findings."]
    
    def _map_agent_name(self, agent_name: str) -> str:
        """
        Map internal agent names to frontend expected names.
        
        Args:
            agent_name: Internal agent name
            
        Returns:
            Frontend expected agent name
        """
        name_mapping = {
            "gmail": "gmail",
            "email": "gmail",
            "accounts_payable": "accounts_payable",
            "invoice": "accounts_payable",
            "ap": "accounts_payable",
            "salesforce": "crm",
            "crm": "crm",
            "analysis": "analysis"
        }
        
        return name_mapping.get(agent_name.lower(), agent_name)
    
    def _count_vendor_mentions(self, analysis_data: Dict[str, Any]) -> int:
        """
        Count vendor mentions in analysis data.
        
        Args:
            analysis_data: Analysis result data
            
        Returns:
            Number of vendor mentions found
        """
        # Simple heuristic - count unique vendor references
        vendor_count = 0
        
        # Check for correlations
        correlations = analysis_data.get("correlations", [])
        if isinstance(correlations, list):
            vendor_count += len(correlations)
        
        # Check for discrepancies
        discrepancies = analysis_data.get("discrepancies", [])
        if isinstance(discrepancies, list):
            vendor_count += len(discrepancies)
        
        # Ensure at least 1 if we have any data
        return max(vendor_count, 1) if analysis_data else 0
    
    def _calculate_data_consistency(self, analysis_data: Dict[str, Any]) -> float:
        """
        Calculate data consistency score from analysis data.
        
        Args:
            analysis_data: Analysis result data
            
        Returns:
            Data consistency score (0.0 to 1.0)
        """
        # Use data quality score if available
        quality_score = analysis_data.get("data_quality_score", 0.0)
        if quality_score > 0:
            return quality_score
        
        # Calculate based on discrepancies
        discrepancies = analysis_data.get("discrepancies", [])
        if isinstance(discrepancies, list):
            # Fewer discrepancies = higher consistency
            if len(discrepancies) == 0:
                return 1.0
            elif len(discrepancies) <= 2:
                return 0.8
            elif len(discrepancies) <= 5:
                return 0.6
            else:
                return 0.4
        
        return 0.7  # Default moderate consistency
    
    def _create_fallback_results(self, plan_id: str, error_message: str) -> Dict[str, Any]:
        """
        Create fallback results structure when compilation fails.
        
        Args:
            plan_id: Plan identifier
            error_message: Error message
            
        Returns:
            Fallback comprehensive results structure
        """
        return {
            "plan_id": plan_id,
            "results": {},
            "correlations": {
                "cross_references": 0,
                "data_consistency": 0.0,
                "vendor_mentions": 0,
                "quality_score": 0.0
            },
            "executive_summary": f"Unable to compile comprehensive results: {error_message}",
            "recommendations": [
                "Review individual agent results for available information.",
                "Consider re-running the analysis if needed."
            ],
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }


# Global service instance
_results_compiler_service: Optional[ResultsCompilerService] = None


def get_results_compiler_service() -> ResultsCompilerService:
    """
    Get or create the global Results Compiler Service instance.
    
    Returns:
        ResultsCompilerService instance
    """
    global _results_compiler_service
    if _results_compiler_service is None:
        _results_compiler_service = ResultsCompilerService()
    return _results_compiler_service


def reset_results_compiler_service() -> None:
    """Reset the global Results Compiler Service (useful for testing)."""
    global _results_compiler_service
    _results_compiler_service = None