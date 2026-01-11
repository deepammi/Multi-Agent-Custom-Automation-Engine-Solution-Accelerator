"""
Integration test for Analysis Agent with existing multi-agent workflow.

This test verifies that the Analysis Agent integrates properly with the existing
multi-agent invoice workflow and can process real agent data.

**Feature: multi-agent-invoice-workflow, Property 6: Cross-System Data Integration**
**Validates: Requirements FR2.4, FR4.1, FR4.2**
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from app.agents.analysis_agent_node import AnalysisAgentNode
from app.agents.state import AgentState, AgentStateManager
from app.services.llm_service import LLMService


class TestAnalysisAgentIntegration:
    """Integration tests for Analysis Agent with real workflow data."""
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Create mock WebSocket manager."""
        mock_manager = Mock()
        mock_manager.send_message = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def realistic_workflow_state(self, mock_websocket_manager):
        """Create realistic workflow state with data from multiple agents."""
        return AgentState(
            plan_id="integration-test-plan",
            session_id="integration-test-session",
            task_description="Analyze invoice data for Acme Marketing and identify any payment issues or discrepancies",
            agent_sequence=["planner", "gmail", "accounts_payable", "salesforce", "analysis"],
            current_step=4,
            total_steps=5,
            current_agent="analysis",
            messages=[
                "AI Planner generated execution plan",
                "Gmail agent found 3 relevant emails",
                "AccountsPayable agent found 2 bills",
                "Salesforce agent found 1 account"
            ],
            collected_data={
                "gmail": {
                    "emails_found": 3,
                    "relevant_emails": [
                        {
                            "subject": "Invoice INV-2024-001 from Acme Marketing",
                            "content": "Please find attached invoice INV-2024-001 for $2,500.00 due on 2024-02-15"
                        },
                        {
                            "subject": "Payment reminder for INV-2024-001",
                            "content": "This is a reminder that invoice INV-2024-001 for $2,500.00 is now overdue"
                        }
                    ],
                    "invoice_numbers": ["INV-2024-001"],
                    "amounts": ["2500.00"],
                    "payment_status_mentions": ["due", "overdue"],
                    "vendor_mentions": ["Acme Marketing"]
                },
                "accounts_payable": {
                    "bills_found": 2,
                    "vendor_bills": [
                        {
                            "invoice_number": "INV-2024-001",
                            "amount": 2600.00,  # Slight discrepancy
                            "status": "overdue",
                            "due_date": "2024-02-15",
                            "vendor_name": "Acme Marketing Corp"
                        }
                    ],
                    "total_outstanding": 2600.00,
                    "invoice_numbers": ["INV-2024-001"],
                    "amounts": ["2600.00"],
                    "statuses": ["overdue"],
                    "vendors": ["Acme Marketing Corp"]
                },
                "salesforce": {
                    "accounts_found": 1,
                    "account_data": [
                        {
                            "name": "Acme Marketing Inc",
                            "status": "active",
                            "revenue": 125000.00,
                            "last_contact": "2024-01-10"
                        }
                    ],
                    "opportunities": [
                        {
                            "name": "Q1 Marketing Campaign",
                            "amount": 15000.00,
                            "stage": "negotiation"
                        }
                    ],
                    "account_names": ["Acme Marketing Inc"],
                    "relationship_status": ["active"]
                }
            },
            execution_results=[],
            final_result="",
            websocket_manager=mock_websocket_manager
        )
    
    @pytest.mark.asyncio
    async def test_analysis_agent_with_realistic_workflow_data(self, realistic_workflow_state):
        """Test Analysis Agent with realistic multi-agent workflow data."""
        # Create analysis agent node with mock LLM
        mock_llm = Mock(spec=LLMService)
        mock_llm.generate_response = AsyncMock(return_value="""
        ## COMPREHENSIVE ANALYSIS REPORT FOR ACME MARKETING
        
        **Executive Summary:**
        Cross-system analysis reveals a $100 discrepancy between email communications ($2,500) 
        and AP system records ($2,600) for invoice INV-2024-001. The invoice is currently 
        overdue with active vendor relationship maintained in CRM.
        
        **Key Findings:**
        - Amount discrepancy detected requiring reconciliation
        - Overdue payment status confirmed across systems
        - Strong vendor relationship with active opportunities
        
        **Recommendations:**
        1. Immediately reconcile the $100 amount discrepancy
        2. Process overdue payment to maintain vendor relationship
        3. Leverage active opportunities for continued partnership
        """)
        
        analysis_node = AnalysisAgentNode(llm_service=mock_llm)
        
        # Execute analysis agent
        updated_state = await analysis_node(realistic_workflow_state)
        
        # Verify analysis was performed
        assert updated_state is not None
        
        # Check that analysis data was added to collected_data
        collected_data = updated_state.get("collected_data", {})
        assert "analysis" in collected_data
        
        # Check execution results
        execution_results = updated_state.get("execution_results", [])
        analysis_execution = next(
            (result for result in execution_results if result["agent"] == "analysis"),
            None
        )
        assert analysis_execution is not None
        
        # Verify analysis result structure
        analysis_result = analysis_execution["result"]
        assert analysis_result["status"] in ["success", "partial_success"]
        assert "data" in analysis_result
        assert "message" in analysis_result
        
        # Verify analysis data contains expected fields
        analysis_data = analysis_result["data"]
        if "analysis_result" in analysis_data:
            # Full analysis completed
            assert "correlations_found" in analysis_data
            assert "discrepancies_found" in analysis_data
            assert "payment_issues_found" in analysis_data
            assert "data_quality_score" in analysis_data
            assert "recommendations" in analysis_data
        
        # Verify WebSocket messages were sent
        websocket_manager = realistic_workflow_state["websocket_manager"]
        assert websocket_manager.send_message.call_count >= 2  # At least start and end messages
        
        # Verify analysis message contains comprehensive content
        analysis_message = analysis_result["message"]
        assert len(analysis_message) > 100  # Should be substantial
        assert "ACME MARKETING" in analysis_message.upper()  # Check for uppercase version
        
        print(f"✅ Analysis Agent Integration Test Results:")
        print(f"   - Status: {analysis_result['status']}")
        print(f"   - Message Length: {len(analysis_message)} characters")
        print(f"   - WebSocket Messages: {websocket_manager.send_message.call_count}")
        print(f"   - Analysis Data Keys: {list(analysis_data.keys())}")
    
    @pytest.mark.asyncio
    async def test_analysis_agent_with_missing_data(self, mock_websocket_manager):
        """Test Analysis Agent handles missing data gracefully."""
        # Create state with only partial data (missing CRM data)
        partial_state = AgentState(
            plan_id="partial-test-plan",
            session_id="partial-test-session", 
            task_description="Analyze invoice data for Test Vendor with limited data",
            agent_sequence=["planner", "gmail", "analysis"],
            current_step=2,
            total_steps=3,
            current_agent="analysis",
            messages=[],
            collected_data={
                "gmail": {
                    "emails_found": 1,
                    "invoice_numbers": ["INV-TEST-001"],
                    "amounts": ["1000.00"],
                    "vendor_mentions": ["Test Vendor"]
                }
                # Missing AP and CRM data
            },
            execution_results=[],
            final_result="",
            websocket_manager=mock_websocket_manager
        )
        
        # Create analysis agent node
        mock_llm = Mock(spec=LLMService)
        mock_llm.generate_response = AsyncMock(return_value="Analysis with limited data completed")
        analysis_node = AnalysisAgentNode(llm_service=mock_llm)
        
        # Execute analysis agent
        updated_state = await analysis_node(partial_state)
        
        # Verify analysis still completes
        assert updated_state is not None
        
        # Check execution results
        execution_results = updated_state.get("execution_results", [])
        analysis_execution = next(
            (result for result in execution_results if result["agent"] == "analysis"),
            None
        )
        assert analysis_execution is not None
        
        # Should complete successfully even with limited data
        analysis_result = analysis_execution["result"]
        assert analysis_result["status"] in ["success", "partial_success"]
        
        print(f"✅ Partial Data Test Results:")
        print(f"   - Status: {analysis_result['status']}")
        print(f"   - Handled missing data gracefully")
    
    @pytest.mark.asyncio
    async def test_analysis_agent_error_recovery(self, realistic_workflow_state):
        """Test Analysis Agent error handling and fallback analysis."""
        # Create analysis agent that will fail
        mock_llm = Mock(spec=LLMService)
        mock_llm.generate_response = AsyncMock(side_effect=Exception("LLM service unavailable"))
        analysis_node = AnalysisAgentNode(llm_service=mock_llm)
        
        # Execute analysis agent (should handle error gracefully)
        updated_state = await analysis_node(realistic_workflow_state)
        
        # Verify fallback analysis was generated
        assert updated_state is not None
        
        # Check execution results
        execution_results = updated_state.get("execution_results", [])
        analysis_execution = next(
            (result for result in execution_results if result["agent"] == "analysis"),
            None
        )
        assert analysis_execution is not None
        
        # Should have success or partial success (both are acceptable for error recovery)
        analysis_result = analysis_execution["result"]
        assert analysis_result["status"] in ["success", "partial_success"]
        
        # Should still provide analysis (either full or fallback)
        analysis_message = analysis_result["message"]
        assert len(analysis_message) > 50  # Should have content
        
        # Check if it's a fallback analysis or successful template-based analysis
        is_fallback = "FALLBACK ANALYSIS" in analysis_message.upper()
        is_template = "template" in analysis_result.get("data", {}).get("analysis_type", "").lower()
        
        # Either fallback or template-based analysis is acceptable
        assert is_fallback or is_template or analysis_result["status"] == "success"
        
        print(f"✅ Error Recovery Test Results:")
        print(f"   - Status: {analysis_result['status']}")
        print(f"   - Analysis generated successfully")
        print(f"   - Error handled gracefully")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])