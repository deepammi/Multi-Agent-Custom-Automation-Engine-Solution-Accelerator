"""
Test suite for Analysis Agent comprehensive data correlation functionality.

This test suite validates the Analysis Agent's ability to:
- Correlate data across email, AP, and CRM systems
- Detect discrepancies between systems
- Identify payment issues
- Generate comprehensive analysis reports

**Feature: multi-agent-invoice-workflow, Property 6: Cross-System Data Integration**
**Validates: Requirements FR2.4, FR4.1, FR4.2**
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

from app.agents.analysis_agent import (
    AnalysisAgent, 
    create_analysis_agent,
    DiscrepancyType,
    PaymentIssueType,
    DataCorrelation,
    Discrepancy,
    PaymentIssue,
    AnalysisResult
)
from app.agents.analysis_agent_node import AnalysisAgentNode, create_analysis_agent_node
from app.agents.state import AgentState, AgentStateManager
from app.services.llm_service import LLMService


class TestAnalysisAgent:
    """Test cases for the core Analysis Agent functionality."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        mock_service = Mock(spec=LLMService)
        mock_service.generate_response = AsyncMock(return_value="Mock analysis summary")
        return mock_service
    
    @pytest.fixture
    def analysis_agent(self, mock_llm_service):
        """Create Analysis Agent instance with mock LLM service."""
        return AnalysisAgent(llm_service=mock_llm_service)
    
    @pytest.fixture
    def sample_email_data(self):
        """Sample email data for testing."""
        return {
            'source': 'email',
            'emails_found': 3,
            'relevant_emails': [
                {
                    'subject': 'Invoice #INV-001 from Acme Marketing',
                    'content': 'Please find attached invoice INV-001 for $5,000.00 due on 2024-01-15'
                }
            ],
            'invoice_numbers': ['INV-001'],
            'amounts': ['5000.00'],
            'dates': ['2024-01-15'],
            'payment_status_mentions': ['due'],
            'vendor_mentions': ['Acme Marketing']  # Added vendor mention
        }
    
    @pytest.fixture
    def sample_ap_data(self):
        """Sample AP data for testing."""
        return {
            'source': 'ap',
            'bills_found': 2,
            'vendor_bills': [
                {
                    'invoice_number': 'INV-001',
                    'amount': 5100.00,  # Slight discrepancy
                    'status': 'unpaid',
                    'due_date': '2024-01-15',
                    'vendor_name': 'Acme Marketing'  # Added vendor name
                }
            ],
            'total_outstanding': 5100.00,
            'invoice_numbers': ['INV-001'],
            'amounts': ['5100.00'],
            'statuses': ['unpaid'],
            'vendors': ['Acme Marketing']  # Added vendor list
        }
    
    @pytest.fixture
    def sample_crm_data(self):
        """Sample CRM data for testing."""
        return {
            'source': 'crm',
            'accounts_found': 1,
            'account_data': [
                {
                    'name': 'Acme Marketing Inc',
                    'status': 'active',
                    'revenue': 50000.00
                }
            ],
            'account_names': ['Acme Marketing Inc'],
            'relationship_status': ['active']
        }
    
    @pytest.mark.asyncio
    async def test_analyze_cross_system_data_success(
        self, 
        analysis_agent, 
        sample_email_data, 
        sample_ap_data, 
        sample_crm_data
    ):
        """Test successful cross-system data analysis."""
        # Execute analysis
        result = await analysis_agent.analyze_cross_system_data(
            email_data=sample_email_data,
            ap_data=sample_ap_data,
            crm_data=sample_crm_data,
            vendor_name="Acme Marketing"
        )
        
        # Verify result structure
        assert isinstance(result, AnalysisResult)
        assert isinstance(result.correlations, list)
        assert isinstance(result.discrepancies, list)
        assert isinstance(result.payment_issues, list)
        assert isinstance(result.recommendations, list)
        assert 0.0 <= result.data_quality_score <= 1.0
        assert result.analysis_summary
        
        # Verify execution metadata
        assert 'execution_time_seconds' in result.execution_metadata
        assert 'vendor_name' in result.execution_metadata
        assert result.execution_metadata['vendor_name'] == "Acme Marketing"
    
    @pytest.mark.asyncio
    async def test_correlate_by_vendor_name(self, analysis_agent, sample_email_data, sample_ap_data):
        """Test vendor name correlation."""
        correlation = analysis_agent._correlate_by_vendor_name(
            sample_email_data,
            sample_ap_data,
            None,
            "Acme Marketing"
        )
        
        assert correlation is not None
        assert isinstance(correlation, DataCorrelation)
        assert correlation.correlation_score > 0
        assert 'vendor_name' in correlation.correlation_keys
        assert correlation.confidence_level in ['high', 'medium', 'low']
    
    @pytest.mark.asyncio
    async def test_correlate_by_invoice_numbers(self, analysis_agent, sample_email_data, sample_ap_data):
        """Test invoice number correlation."""
        correlation = analysis_agent._correlate_by_invoice_numbers(
            sample_email_data,
            sample_ap_data,
            None
        )
        
        assert correlation is not None
        assert isinstance(correlation, DataCorrelation)
        assert correlation.correlation_score > 0
        assert any('invoice_' in key for key in correlation.correlation_keys)
    
    def test_detect_amount_discrepancies(self, analysis_agent):
        """Test amount discrepancy detection."""
        # Create data with amounts that differ by more than 5% tolerance
        email_data = {
            'source': 'email',
            'amounts': ['5000.00'],  # $5000
            'invoice_numbers': ['INV-001']
        }
        
        ap_data = {
            'source': 'ap', 
            'amounts': ['5500.00'],  # $5500 - 10% difference, should trigger discrepancy
            'invoice_numbers': ['INV-001']
        }
        
        normalized_data = {
            'email': email_data,
            'ap': ap_data,
            'crm': None
        }
        
        discrepancies = analysis_agent._detect_amount_discrepancies(normalized_data, [])
        
        assert len(discrepancies) > 0
        amount_discrepancy = discrepancies[0]
        assert amount_discrepancy.discrepancy_type == DiscrepancyType.AMOUNT_MISMATCH
        assert 'Email shows $5,000.00, AP shows $5,500.00' in amount_discrepancy.description
        assert amount_discrepancy.severity in ['critical', 'high', 'medium', 'low']
    
    def test_detect_missing_data(self, analysis_agent):
        """Test missing data detection."""
        normalized_data = {
            'email': {'source': 'email'},
            'ap': None,  # Missing AP data
            'crm': {'source': 'crm'}
        }
        
        discrepancies = analysis_agent._detect_missing_data(normalized_data, "Test Vendor")
        
        assert len(discrepancies) > 0
        missing_data_discrepancy = discrepancies[0]
        assert missing_data_discrepancy.discrepancy_type == DiscrepancyType.MISSING_DATA
        assert 'ap' in missing_data_discrepancy.systems_involved
        assert 'Test Vendor' in missing_data_discrepancy.description
    
    def test_extract_amounts_from_data(self, analysis_agent, sample_ap_data):
        """Test amount extraction from data."""
        amounts = analysis_agent._extract_amounts_from_data(sample_ap_data)
        
        assert len(amounts) > 0
        assert 5100.0 in amounts
    
    def test_amounts_match_within_tolerance(self, analysis_agent):
        """Test amount matching with tolerance."""
        # Should match within 5% tolerance (100/5100 = 1.96% < 5%)
        assert analysis_agent._amounts_match_within_tolerance(5000.0, 5100.0, 0.05) == True
        assert analysis_agent._amounts_match_within_tolerance(5000.0, 5050.0, 0.05) == True
        assert analysis_agent._amounts_match_within_tolerance(5000.0, 5000.0, 0.05) == True
        # Should NOT match if difference is too large (300/5300 = 5.66% > 5%)
        assert analysis_agent._amounts_match_within_tolerance(5000.0, 5300.0, 0.05) == False
    
    def test_determine_confidence_level(self, analysis_agent):
        """Test confidence level determination."""
        assert analysis_agent._determine_confidence_level(0.9) == "high"
        assert analysis_agent._determine_confidence_level(0.7) == "medium"
        assert analysis_agent._determine_confidence_level(0.5) == "low"
    
    def test_calculate_data_quality_score(self, analysis_agent):
        """Test data quality score calculation."""
        normalized_data = {
            'email': {'source': 'email'},
            'ap': {'source': 'ap'},
            'crm': None  # Missing CRM data
        }
        
        correlations = [
            DataCorrelation(
                email_data={'source': 'email'},
                ap_data={'source': 'ap'},
                crm_data=None,
                correlation_score=0.8,
                correlation_keys=['vendor_name'],
                confidence_level='high'
            )
        ]
        
        discrepancies = [
            Discrepancy(
                discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                systems_involved=['email', 'ap'],
                description="Test discrepancy",
                severity="medium",
                affected_data={},
                recommended_action="Test action"
            )
        ]
        
        score = analysis_agent._calculate_data_quality_score(
            normalized_data,
            correlations,
            discrepancies
        )
        
        assert 0.0 <= score <= 1.0
        # Should be penalized for missing CRM data and discrepancy
        assert score < 1.0
    
    def test_generate_recommendations(self, analysis_agent):
        """Test recommendation generation."""
        discrepancies = [
            Discrepancy(
                discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                systems_involved=['email', 'ap'],
                description="Amount mismatch",
                severity="critical",
                affected_data={},
                recommended_action="Reconcile amounts"
            )
        ]
        
        payment_issues = [
            PaymentIssue(
                issue_type=PaymentIssueType.OVERDUE_PAYMENT,
                description="Overdue payment",
                severity="high",
                affected_vendor="Test Vendor",
                affected_amount=5000.0,
                affected_invoice="INV-001",
                recommended_action="Contact vendor",
                urgency_score=0.8
            )
        ]
        
        recommendations = analysis_agent._generate_recommendations(
            discrepancies,
            payment_issues,
            0.6  # Medium data quality score
        )
        
        assert len(recommendations) > 0
        assert any("critical discrepancies" in rec.lower() for rec in recommendations)
        assert any("overdue payments" in rec.lower() for rec in recommendations)
        assert any("data quality" in rec.lower() for rec in recommendations)


class TestAnalysisAgentNode:
    """Test cases for the Analysis Agent Node LangGraph integration."""
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Create mock WebSocket manager."""
        mock_manager = Mock()
        mock_manager.send_message = AsyncMock()
        return mock_manager
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        mock_service = Mock(spec=LLMService)
        mock_service.generate_response = AsyncMock(return_value="Mock analysis summary")
        return mock_service
    
    @pytest.fixture
    def analysis_agent_node(self, mock_llm_service):
        """Create Analysis Agent Node with mock LLM service."""
        return AnalysisAgentNode(llm_service=mock_llm_service)
    
    @pytest.fixture
    def sample_agent_state(self, mock_websocket_manager):
        """Create sample agent state with collected data."""
        return AgentState(
            plan_id="test-plan-123",
            session_id="test-session-456",
            task_description="Analyze invoice data for Acme Marketing and identify any payment issues",
            agent_sequence=["planner", "gmail", "invoice", "salesforce", "analysis"],
            current_step=4,
            total_steps=5,
            current_agent="analysis",
            messages=[],
            collected_data={
                "gmail": {
                    "emails_found": 2,
                    "invoice_numbers": ["INV-001"],
                    "amounts": ["5000.00"]
                },
                "invoice": {
                    "bills_found": 1,
                    "invoice_numbers": ["INV-001"],
                    "amounts": ["5100.00"],
                    "statuses": ["unpaid"]
                },
                "salesforce": {
                    "accounts_found": 1,
                    "account_names": ["Acme Marketing Inc"]
                }
            },
            execution_results=[],
            final_result="",
            websocket_manager=mock_websocket_manager
        )
    
    @pytest.mark.asyncio
    async def test_analysis_agent_node_execution_success(
        self, 
        analysis_agent_node, 
        sample_agent_state
    ):
        """Test successful analysis agent node execution."""
        # Mock the analysis agent's analyze_cross_system_data method
        with patch.object(
            analysis_agent_node.analysis_agent, 
            'analyze_cross_system_data'
        ) as mock_analyze:
            # Setup mock analysis result
            mock_result = AnalysisResult(
                correlations=[
                    DataCorrelation(
                        email_data={'source': 'email'},
                        ap_data={'source': 'ap'},
                        crm_data=None,
                        correlation_score=0.8,
                        correlation_keys=['vendor_name'],
                        confidence_level='high'
                    )
                ],
                discrepancies=[
                    Discrepancy(
                        discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                        systems_involved=['email', 'ap'],
                        description="Amount mismatch detected",
                        severity="medium",
                        affected_data={},
                        recommended_action="Reconcile amounts"
                    )
                ],
                payment_issues=[],
                data_quality_score=0.75,
                analysis_summary="Test analysis summary",
                recommendations=["Test recommendation"],
                execution_metadata={
                    "execution_time_seconds": 2.5,
                    "vendor_name": "Acme Marketing"
                }
            )
            mock_analyze.return_value = mock_result
            
            # Execute the node
            updated_state = await analysis_agent_node(sample_agent_state)
            
            # Verify state updates
            assert updated_state is not None
            assert "analysis" in updated_state.get("collected_data", {})
            
            # Verify execution results
            execution_results = updated_state.get("execution_results", [])
            analysis_result = next(
                (result for result in execution_results if result["agent"] == "analysis"),
                None
            )
            assert analysis_result is not None
            assert analysis_result["result"]["status"] == "success"
            assert "correlations_found" in analysis_result["result"]["data"]
            assert "discrepancies_found" in analysis_result["result"]["data"]
            assert "data_quality_score" in analysis_result["result"]["data"]
            
            # Verify WebSocket messages were sent
            websocket_manager = sample_agent_state["websocket_manager"]
            assert websocket_manager.send_message.call_count >= 2  # Start and end messages
    
    def test_extract_vendor_name(self, analysis_agent_node):
        """Test vendor name extraction from task description."""
        # Test quoted vendor name
        task1 = 'Analyze invoice data for "Acme Marketing" and check payment status'
        vendor1 = analysis_agent_node._extract_vendor_name(task1)
        assert vendor1 == "Acme Marketing"
        
        # Test for/with pattern
        task2 = "Check the status of invoices for Acme Marketing Corp"
        vendor2 = analysis_agent_node._extract_vendor_name(task2)
        assert "Acme Marketing" in vendor2
        
        # Test capitalized company name
        task3 = "Find all communications with TechCorp Solutions"
        vendor3 = analysis_agent_node._extract_vendor_name(task3)
        assert "TechCorp Solutions" in vendor3
    
    def test_extract_enhanced_agent_data(self, analysis_agent_node, sample_agent_state):
        """Test enhanced agent data extraction."""
        enhanced_data = analysis_agent_node._extract_enhanced_agent_data(sample_agent_state)
        
        assert 'email' in enhanced_data
        assert 'ap' in enhanced_data
        assert 'crm' in enhanced_data
        
        # Should map gmail -> email, invoice -> ap, salesforce -> crm
        assert enhanced_data['email'] is not None  # From gmail data
        assert enhanced_data['ap'] is not None     # From invoice data
        assert enhanced_data['crm'] is not None   # From salesforce data
    
    @pytest.mark.asyncio
    async def test_analysis_agent_node_error_handling(
        self, 
        analysis_agent_node, 
        sample_agent_state
    ):
        """Test analysis agent node error handling and fallback."""
        # Mock the analysis agent to raise an exception
        with patch.object(
            analysis_agent_node.analysis_agent, 
            'analyze_cross_system_data'
        ) as mock_analyze:
            mock_analyze.side_effect = Exception("Test analysis error")
            
            # Execute the node
            updated_state = await analysis_agent_node(sample_agent_state)
            
            # Verify fallback behavior
            assert updated_state is not None
            
            # Check execution results for partial success
            execution_results = updated_state.get("execution_results", [])
            analysis_result = next(
                (result for result in execution_results if result["agent"] == "analysis"),
                None
            )
            assert analysis_result is not None
            assert analysis_result["result"]["status"] == "partial_success"
            assert "error" in analysis_result["result"]["data"]
            assert "fallback" in analysis_result["result"]["data"]["analysis_type"]
            
            # Verify WebSocket error message was sent
            websocket_manager = sample_agent_state["websocket_manager"]
            assert websocket_manager.send_message.call_count >= 1


class TestAnalysisAgentIntegration:
    """Integration tests for Analysis Agent with real-like data."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_analysis_workflow(self):
        """Test complete analysis workflow with realistic data."""
        # Create analysis agent
        mock_llm = Mock(spec=LLMService)
        mock_llm.generate_response = AsyncMock(return_value="Comprehensive analysis completed successfully")
        
        analysis_agent = AnalysisAgent(llm_service=mock_llm)
        
        # Realistic test data
        email_data = {
            'source': 'email',
            'emails_found': 5,
            'invoice_numbers': ['INV-2024-001', 'INV-2024-002'],
            'amounts': ['2500.00', '1750.00'],
            'payment_status_mentions': ['paid', 'pending'],
            'vendor_mentions': ['Global Tech Solutions']  # Added vendor mention
        }
        
        ap_data = {
            'source': 'ap',
            'bills_found': 3,
            'invoice_numbers': ['INV-2024-001', 'INV-2024-003'],
            'amounts': ['2500.00', '3200.00'],
            'statuses': ['paid', 'overdue'],
            'vendors': ['Global Tech Solutions']  # Added vendor list
        }
        
        crm_data = {
            'source': 'crm',
            'accounts_found': 1,
            'account_names': ['Global Tech Solutions'],
            'relationship_status': ['active']
        }
        
        # Execute analysis
        result = await analysis_agent.analyze_cross_system_data(
            email_data=email_data,
            ap_data=ap_data,
            crm_data=crm_data,
            vendor_name="Global Tech Solutions"
        )
        
        # Verify comprehensive results
        assert isinstance(result, AnalysisResult)
        # Should find at least some correlations or have reasonable data quality
        assert len(result.correlations) > 0 or result.data_quality_score > 0.5  
        assert result.data_quality_score > 0.5  # Reasonable quality
        assert len(result.recommendations) > 0  # Should have recommendations
        
        # Verify LLM was called for summary generation
        assert mock_llm.generate_response.called


def test_create_analysis_agent():
    """Test analysis agent factory function."""
    agent = create_analysis_agent()
    assert isinstance(agent, AnalysisAgent)
    assert agent.llm_service is not None


def test_create_analysis_agent_node():
    """Test analysis agent node factory function."""
    node = create_analysis_agent_node()
    assert isinstance(node, AnalysisAgentNode)
    assert node.analysis_agent is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])