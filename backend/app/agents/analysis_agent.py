"""
Analysis Agent for Comprehensive Cross-System Data Correlation

This agent implements comprehensive data correlation capabilities for the multi-agent
invoice analysis workflow. It correlates data from email, accounts payable, and CRM
systems to identify discrepancies, payment issues, and generate actionable insights.

Enhanced for Task 6.2 with:
- Cross-system data correlation and validation
- Discrepancy detection between email, AP, and CRM data
- Payment issue identification logic
- Comprehensive analysis report generation

**Feature: multi-agent-invoice-workflow, Property 6: Cross-System Data Integration**
**Validates: Requirements FR2.4, FR4.1, FR4.2**
"""

import logging
import json
import re
from typing import Dict, Any, Optional, List, Tuple, Set
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class DiscrepancyType(Enum):
    """Types of discrepancies that can be detected between systems."""
    AMOUNT_MISMATCH = "amount_mismatch"
    DATE_MISMATCH = "date_mismatch"
    STATUS_CONFLICT = "status_conflict"
    MISSING_DATA = "missing_data"
    DUPLICATE_RECORDS = "duplicate_records"
    VENDOR_NAME_VARIATION = "vendor_name_variation"
    INVOICE_NUMBER_MISMATCH = "invoice_number_mismatch"


class PaymentIssueType(Enum):
    """Types of payment issues that can be identified."""
    OVERDUE_PAYMENT = "overdue_payment"
    DUPLICATE_PAYMENT = "duplicate_payment"
    AMOUNT_DISCREPANCY = "amount_discrepancy"
    MISSING_INVOICE = "missing_invoice"
    PAYMENT_STATUS_UNCLEAR = "payment_status_unclear"
    VENDOR_COMMUNICATION_GAP = "vendor_communication_gap"
    APPROVAL_DELAY = "approval_delay"


@dataclass
class DataCorrelation:
    """Represents a correlation between data from different systems."""
    email_data: Optional[Dict[str, Any]]
    ap_data: Optional[Dict[str, Any]]
    crm_data: Optional[Dict[str, Any]]
    correlation_score: float  # 0.0 to 1.0
    correlation_keys: List[str]  # Keys used for correlation
    confidence_level: str  # "high", "medium", "low"


@dataclass
class Discrepancy:
    """Represents a discrepancy found between systems."""
    discrepancy_type: DiscrepancyType
    systems_involved: List[str]
    description: str
    severity: str  # "critical", "high", "medium", "low"
    affected_data: Dict[str, Any]
    recommended_action: str


@dataclass
class PaymentIssue:
    """Represents a payment issue identified during analysis."""
    issue_type: PaymentIssueType
    description: str
    severity: str  # "critical", "high", "medium", "low"
    affected_vendor: str
    affected_amount: Optional[float]
    affected_invoice: Optional[str]
    recommended_action: str
    urgency_score: float  # 0.0 to 1.0


@dataclass
class AnalysisResult:
    """Comprehensive analysis result with correlations, discrepancies, and issues."""
    correlations: List[DataCorrelation]
    discrepancies: List[Discrepancy]
    payment_issues: List[PaymentIssue]
    data_quality_score: float  # 0.0 to 1.0
    analysis_summary: str
    recommendations: List[str]
    execution_metadata: Dict[str, Any]


class AnalysisAgent:
    """
    Analysis Agent for comprehensive cross-system data correlation.
    
    This agent performs sophisticated analysis of data collected from email,
    accounts payable, and CRM systems to identify patterns, discrepancies,
    and payment issues that require attention.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the Analysis Agent.
        
        Args:
            llm_service: LLM service for generating natural language analysis
        """
        self.llm_service = llm_service or LLMService()
        
        # Correlation thresholds and weights
        self.correlation_config = {
            'vendor_name_weight': 0.4,
            'invoice_number_weight': 0.3,
            'amount_weight': 0.2,
            'date_weight': 0.1,
            'minimum_correlation_score': 0.6,
            'high_confidence_threshold': 0.8,
            'medium_confidence_threshold': 0.6
        }
        
        # Discrepancy detection thresholds
        self.discrepancy_config = {
            'amount_tolerance_percentage': 0.05,  # 5% tolerance for amount differences
            'date_tolerance_days': 7,  # 7 days tolerance for date differences
            'vendor_name_similarity_threshold': 0.8,
            'critical_amount_threshold': 10000.0,  # Amounts above this are critical
            'high_severity_amount_threshold': 1000.0
        }
        
        # Payment issue detection rules
        self.payment_issue_config = {
            'overdue_days_threshold': 30,
            'critical_overdue_days': 60,
            'duplicate_amount_tolerance': 0.01,  # 1% tolerance for duplicate detection
            'communication_gap_days': 14,
            'approval_delay_days': 10
        }
    
    async def analyze_cross_system_data(
        self,
        email_data: Optional[Dict[str, Any]] = None,
        ap_data: Optional[Dict[str, Any]] = None,
        crm_data: Optional[Dict[str, Any]] = None,
        vendor_name: Optional[str] = None
    ) -> AnalysisResult:
        """
        Perform comprehensive cross-system data analysis.
        
        Args:
            email_data: Data from email agent
            ap_data: Data from accounts payable agent
            crm_data: Data from CRM agent
            vendor_name: Target vendor name for analysis
            
        Returns:
            AnalysisResult: Comprehensive analysis with correlations and issues
        """
        logger.info(
            f"Starting cross-system data analysis for vendor: {vendor_name}",
            extra={
                "vendor_name": vendor_name,
                "has_email_data": email_data is not None,
                "has_ap_data": ap_data is not None,
                "has_crm_data": crm_data is not None
            }
        )
        
        analysis_start_time = datetime.now(timezone.utc)
        
        # Step 1: Normalize and extract structured data
        normalized_data = self._normalize_agent_data(email_data, ap_data, crm_data)
        
        # Step 2: Perform data correlation
        correlations = await self._correlate_cross_system_data(
            normalized_data['email'],
            normalized_data['ap'],
            normalized_data['crm'],
            vendor_name
        )
        
        # Step 3: Detect discrepancies
        discrepancies = await self._detect_discrepancies(
            normalized_data,
            correlations,
            vendor_name
        )
        
        # Step 4: Identify payment issues
        payment_issues = await self._identify_payment_issues(
            normalized_data,
            correlations,
            discrepancies,
            vendor_name
        )
        
        # Step 5: Calculate data quality score
        data_quality_score = self._calculate_data_quality_score(
            normalized_data,
            correlations,
            discrepancies
        )
        
        # Step 6: Generate comprehensive analysis summary
        analysis_summary = await self._generate_analysis_summary(
            normalized_data,
            correlations,
            discrepancies,
            payment_issues,
            vendor_name
        )
        
        # Step 7: Generate actionable recommendations
        recommendations = self._generate_recommendations(
            discrepancies,
            payment_issues,
            data_quality_score
        )
        
        analysis_end_time = datetime.now(timezone.utc)
        execution_time = (analysis_end_time - analysis_start_time).total_seconds()
        
        result = AnalysisResult(
            correlations=correlations,
            discrepancies=discrepancies,
            payment_issues=payment_issues,
            data_quality_score=data_quality_score,
            analysis_summary=analysis_summary,
            recommendations=recommendations,
            execution_metadata={
                "analysis_start_time": analysis_start_time.isoformat(),
                "analysis_end_time": analysis_end_time.isoformat(),
                "execution_time_seconds": execution_time,
                "vendor_name": vendor_name,
                "data_sources_analyzed": len([d for d in normalized_data.values() if d]),
                "correlations_found": len(correlations),
                "discrepancies_found": len(discrepancies),
                "payment_issues_found": len(payment_issues)
            }
        )
        
        logger.info(
            f"Cross-system analysis completed for vendor: {vendor_name}",
            extra={
                "vendor_name": vendor_name,
                "execution_time": execution_time,
                "correlations_found": len(correlations),
                "discrepancies_found": len(discrepancies),
                "payment_issues_found": len(payment_issues),
                "data_quality_score": data_quality_score
            }
        )
        
        return result
    
    def _normalize_agent_data(
        self,
        email_data: Optional[Dict[str, Any]],
        ap_data: Optional[Dict[str, Any]],
        crm_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Normalize data from different agents into consistent structure.
        
        Args:
            email_data: Raw email agent data
            ap_data: Raw AP agent data
            crm_data: Raw CRM agent data
            
        Returns:
            Dict with normalized data for each system
        """
        normalized = {
            'email': None,
            'ap': None,
            'crm': None
        }
        
        # Normalize email data
        if email_data:
            normalized['email'] = self._normalize_email_data(email_data)
        
        # Normalize AP data
        if ap_data:
            normalized['ap'] = self._normalize_ap_data(ap_data)
        
        # Normalize CRM data
        if crm_data:
            normalized['crm'] = self._normalize_crm_data(crm_data)
        
        return normalized
    
    def _normalize_email_data(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize email data into standard structure."""
        normalized = {
            'source': 'email',
            'emails': [],
            'invoice_numbers': [],
            'amounts': [],
            'dates': [],
            'vendor_mentions': [],
            'payment_status_mentions': []
        }
        
        # Extract structured data from email content
        if isinstance(email_data, dict):
            # Handle different email data formats
            if 'emails_found' in email_data:
                normalized['emails_count'] = email_data.get('emails_found', 0)
            
            if 'relevant_emails' in email_data:
                normalized['emails'] = email_data['relevant_emails']
            
            if 'invoice_numbers' in email_data:
                normalized['invoice_numbers'] = email_data['invoice_numbers']
            
            # Extract from raw email content if available
            email_content = email_data.get('gmail_result', '') or email_data.get('email_result', '')
            if email_content:
                normalized.update(self._extract_email_patterns(email_content))
        
        return normalized
    
    def _normalize_ap_data(self, ap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize accounts payable data into standard structure."""
        normalized = {
            'source': 'ap',
            'bills': [],
            'vendors': [],
            'amounts': [],
            'due_dates': [],
            'payment_dates': [],
            'statuses': [],
            'invoice_numbers': []
        }
        
        if isinstance(ap_data, dict):
            # Handle different AP data formats
            if 'bills_found' in ap_data:
                normalized['bills_count'] = ap_data.get('bills_found', 0)
            
            if 'vendor_bills' in ap_data:
                normalized['bills'] = ap_data['vendor_bills']
            
            if 'outstanding_amount' in ap_data:
                normalized['total_outstanding'] = ap_data['outstanding_amount']
            
            # Extract from raw AP content if available
            ap_content = ap_data.get('ap_result', '') or ap_data.get('bill_result', '')
            if ap_content:
                normalized.update(self._extract_ap_patterns(ap_content))
        
        return normalized
    
    def _normalize_crm_data(self, crm_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize CRM data into standard structure."""
        normalized = {
            'source': 'crm',
            'accounts': [],
            'opportunities': [],
            'contacts': [],
            'account_names': [],
            'revenue_data': [],
            'relationship_status': []
        }
        
        if isinstance(crm_data, dict):
            # Handle different CRM data formats
            if 'accounts_found' in crm_data:
                normalized['accounts_count'] = crm_data.get('accounts_found', 0)
            
            if 'account_data' in crm_data:
                normalized['accounts'] = crm_data['account_data']
            
            if 'opportunities' in crm_data:
                normalized['opportunities'] = crm_data['opportunities']
            
            # Extract from raw CRM content if available
            crm_content = crm_data.get('crm_result', '') or crm_data.get('salesforce_result', '')
            if crm_content:
                normalized.update(self._extract_crm_patterns(crm_content))
        
        return normalized
    
    def _extract_email_patterns(self, email_content: str) -> Dict[str, List[str]]:
        """Extract structured patterns from email content."""
        patterns = {
            'invoice_numbers': [],
            'amounts': [],
            'dates': [],
            'vendor_mentions': [],
            'payment_status_mentions': []
        }
        
        # Extract invoice numbers (various formats)
        invoice_patterns = [
            r'invoice\s*#?\s*(\w+[-_]?\w*)',
            r'inv\s*#?\s*(\w+[-_]?\w*)',
            r'bill\s*#?\s*(\w+[-_]?\w*)',
            r'reference\s*#?\s*(\w+[-_]?\w*)'
        ]
        
        for pattern in invoice_patterns:
            matches = re.findall(pattern, email_content, re.IGNORECASE)
            patterns['invoice_numbers'].extend(matches)
        
        # Extract amounts (various currency formats)
        amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|dollars?)',
            r'amount:?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, email_content, re.IGNORECASE)
            patterns['amounts'].extend(matches)
        
        # Extract dates
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, email_content, re.IGNORECASE)
            patterns['dates'].extend(matches)
        
        # Extract payment status mentions
        payment_status_keywords = [
            'paid', 'unpaid', 'overdue', 'pending', 'processed', 'approved',
            'rejected', 'cancelled', 'refunded', 'disputed'
        ]
        
        for keyword in payment_status_keywords:
            if re.search(rf'\b{keyword}\b', email_content, re.IGNORECASE):
                patterns['payment_status_mentions'].append(keyword)
        
        return patterns
    
    def _extract_ap_patterns(self, ap_content: str) -> Dict[str, List[str]]:
        """Extract structured patterns from AP system content."""
        patterns = {
            'invoice_numbers': [],
            'amounts': [],
            'due_dates': [],
            'payment_dates': [],
            'statuses': [],
            'vendors': []
        }
        
        # Similar pattern extraction logic for AP data
        # This would be customized based on the specific AP system format
        
        return patterns
    
    def _extract_crm_patterns(self, crm_content: str) -> Dict[str, List[str]]:
        """Extract structured patterns from CRM system content."""
        patterns = {
            'account_names': [],
            'revenue_data': [],
            'contact_info': [],
            'opportunity_amounts': [],
            'relationship_status': []
        }
        
        # Similar pattern extraction logic for CRM data
        # This would be customized based on the specific CRM system format
        
        return patterns
    
    async def _correlate_cross_system_data(
        self,
        email_data: Optional[Dict[str, Any]],
        ap_data: Optional[Dict[str, Any]],
        crm_data: Optional[Dict[str, Any]],
        vendor_name: Optional[str]
    ) -> List[DataCorrelation]:
        """
        Correlate data across systems to find matching records.
        
        Args:
            email_data: Normalized email data
            ap_data: Normalized AP data
            crm_data: Normalized CRM data
            vendor_name: Target vendor name
            
        Returns:
            List of data correlations found
        """
        correlations = []
        
        if not any([email_data, ap_data, crm_data]):
            return correlations
        
        # Correlation strategy 1: Vendor name matching
        if vendor_name:
            correlation = self._correlate_by_vendor_name(
                email_data, ap_data, crm_data, vendor_name
            )
            if correlation:
                correlations.append(correlation)
        
        # Correlation strategy 2: Invoice number matching
        invoice_correlation = self._correlate_by_invoice_numbers(
            email_data, ap_data, crm_data
        )
        if invoice_correlation:
            correlations.append(invoice_correlation)
        
        # Correlation strategy 3: Amount matching
        amount_correlation = self._correlate_by_amounts(
            email_data, ap_data, crm_data
        )
        if amount_correlation:
            correlations.append(amount_correlation)
        
        # Correlation strategy 4: Date proximity matching
        date_correlation = self._correlate_by_dates(
            email_data, ap_data, crm_data
        )
        if date_correlation:
            correlations.append(date_correlation)
        
        return correlations
    
    def _correlate_by_vendor_name(
        self,
        email_data: Optional[Dict[str, Any]],
        ap_data: Optional[Dict[str, Any]],
        crm_data: Optional[Dict[str, Any]],
        vendor_name: str
    ) -> Optional[DataCorrelation]:
        """Correlate data based on vendor name matching."""
        correlation_keys = ['vendor_name']
        correlation_score = 0.0
        
        # Check vendor name presence in each system
        email_match = False
        ap_match = False
        crm_match = False
        
        if email_data:
            email_str = str(email_data).lower()
            if vendor_name.lower() in email_str:
                email_match = True
        
        if ap_data:
            ap_str = str(ap_data).lower()
            if vendor_name.lower() in ap_str:
                ap_match = True
        
        if crm_data:
            crm_str = str(crm_data).lower()
            if vendor_name.lower() in crm_str:
                crm_match = True
        
        # Require at least 2 systems to have vendor match for correlation
        matches = sum([email_match, ap_match, crm_match])
        if matches < 2:
            return None
        
        # Adjust correlation score based on number of matches
        if matches == 3:
            correlation_score = 0.9  # High score for all three systems
        elif matches == 2:
            correlation_score = 0.7  # Medium score for two systems
        
        confidence_level = self._determine_confidence_level(correlation_score)
        
        return DataCorrelation(
            email_data=email_data if email_match else None,
            ap_data=ap_data if ap_match else None,
            crm_data=crm_data if crm_match else None,
            correlation_score=correlation_score,
            correlation_keys=correlation_keys,
            confidence_level=confidence_level
        )
    
    def _correlate_by_invoice_numbers(
        self,
        email_data: Optional[Dict[str, Any]],
        ap_data: Optional[Dict[str, Any]],
        crm_data: Optional[Dict[str, Any]]
    ) -> Optional[DataCorrelation]:
        """Correlate data based on invoice number matching."""
        # Extract invoice numbers from each system
        email_invoices = set()
        ap_invoices = set()
        crm_invoices = set()
        
        if email_data and 'invoice_numbers' in email_data:
            email_invoices = set(email_data['invoice_numbers'])
        
        if ap_data and 'invoice_numbers' in ap_data:
            ap_invoices = set(ap_data['invoice_numbers'])
        
        if crm_data and 'invoice_numbers' in crm_data:
            crm_invoices = set(crm_data['invoice_numbers'])
        
        # Find common invoice numbers
        all_invoices = email_invoices | ap_invoices | crm_invoices
        if not all_invoices:
            return None
        
        # Calculate correlation score based on overlap
        correlation_score = 0.0
        correlation_keys = []
        
        for invoice in all_invoices:
            systems_with_invoice = []
            if invoice in email_invoices:
                systems_with_invoice.append('email')
            if invoice in ap_invoices:
                systems_with_invoice.append('ap')
            if invoice in crm_invoices:
                systems_with_invoice.append('crm')
            
            if len(systems_with_invoice) >= 2:
                correlation_score += self.correlation_config['invoice_number_weight']
                correlation_keys.append(f'invoice_{invoice}')
        
        if correlation_score == 0:  # Changed from minimum threshold check
            return None
        
        confidence_level = self._determine_confidence_level(correlation_score)
        
        return DataCorrelation(
            email_data=email_data,
            ap_data=ap_data,
            crm_data=crm_data,
            correlation_score=correlation_score,
            correlation_keys=correlation_keys,
            confidence_level=confidence_level
        )
    
    def _correlate_by_amounts(
        self,
        email_data: Optional[Dict[str, Any]],
        ap_data: Optional[Dict[str, Any]],
        crm_data: Optional[Dict[str, Any]]
    ) -> Optional[DataCorrelation]:
        """Correlate data based on amount matching."""
        # Extract amounts from each system
        email_amounts = self._extract_amounts_from_data(email_data)
        ap_amounts = self._extract_amounts_from_data(ap_data)
        crm_amounts = self._extract_amounts_from_data(crm_data)
        
        # Find matching amounts within tolerance
        correlation_score = 0.0
        correlation_keys = []
        tolerance = self.discrepancy_config['amount_tolerance_percentage']
        
        for email_amount in email_amounts:
            for ap_amount in ap_amounts:
                if self._amounts_match_within_tolerance(email_amount, ap_amount, tolerance):
                    correlation_score += self.correlation_config['amount_weight']
                    correlation_keys.append(f'amount_{email_amount}')
        
        if correlation_score == 0:  # Changed from minimum threshold check
            return None
        
        confidence_level = self._determine_confidence_level(correlation_score)
        
        return DataCorrelation(
            email_data=email_data,
            ap_data=ap_data,
            crm_data=crm_data,
            correlation_score=correlation_score,
            correlation_keys=correlation_keys,
            confidence_level=confidence_level
        )
    
    def _correlate_by_dates(
        self,
        email_data: Optional[Dict[str, Any]],
        ap_data: Optional[Dict[str, Any]],
        crm_data: Optional[Dict[str, Any]]
    ) -> Optional[DataCorrelation]:
        """Correlate data based on date proximity."""
        # This would implement date-based correlation logic
        # For now, return None as it's complex and optional
        return None
    
    def _extract_amounts_from_data(self, data: Optional[Dict[str, Any]]) -> List[float]:
        """Extract numeric amounts from data."""
        amounts = []
        
        if not data:
            return amounts
        
        # Extract from amounts field
        if 'amounts' in data:
            for amount_str in data['amounts']:
                try:
                    # Clean and convert amount string to float
                    clean_amount = re.sub(r'[,$]', '', str(amount_str))
                    amount = float(clean_amount)
                    amounts.append(amount)
                except (ValueError, TypeError):
                    continue
        
        # Extract from other numeric fields
        numeric_fields = ['total_outstanding', 'outstanding_amount', 'revenue_data']
        for field in numeric_fields:
            if field in data and isinstance(data[field], (int, float)):
                amounts.append(float(data[field]))
        
        return amounts
    
    def _amounts_match_within_tolerance(
        self, 
        amount1: float, 
        amount2: float, 
        tolerance: float
    ) -> bool:
        """Check if two amounts match within tolerance percentage."""
        if amount1 == 0 and amount2 == 0:
            return True
        
        if amount1 == 0 or amount2 == 0:
            return False
        
        difference = abs(amount1 - amount2)
        larger_amount = max(amount1, amount2)
        percentage_difference = difference / larger_amount
        
        return percentage_difference <= tolerance
    
    def _determine_confidence_level(self, correlation_score: float) -> str:
        """Determine confidence level based on correlation score."""
        if correlation_score >= self.correlation_config['high_confidence_threshold']:
            return "high"
        elif correlation_score >= self.correlation_config['medium_confidence_threshold']:
            return "medium"
        else:
            return "low"
    
    async def _detect_discrepancies(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        correlations: List[DataCorrelation],
        vendor_name: Optional[str]
    ) -> List[Discrepancy]:
        """
        Detect discrepancies between systems.
        
        Args:
            normalized_data: Normalized data from all systems
            correlations: Found correlations between systems
            vendor_name: Target vendor name
            
        Returns:
            List of detected discrepancies
        """
        discrepancies = []
        
        # Detect amount mismatches
        amount_discrepancies = self._detect_amount_discrepancies(normalized_data, correlations)
        discrepancies.extend(amount_discrepancies)
        
        # Detect missing data
        missing_data_discrepancies = self._detect_missing_data(normalized_data, vendor_name)
        discrepancies.extend(missing_data_discrepancies)
        
        # Detect status conflicts
        status_discrepancies = self._detect_status_conflicts(normalized_data, correlations)
        discrepancies.extend(status_discrepancies)
        
        # Detect vendor name variations
        vendor_discrepancies = self._detect_vendor_name_variations(normalized_data, vendor_name)
        discrepancies.extend(vendor_discrepancies)
        
        return discrepancies
    
    def _detect_amount_discrepancies(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        correlations: List[DataCorrelation]
    ) -> List[Discrepancy]:
        """Detect amount mismatches between systems."""
        discrepancies = []
        
        email_data = normalized_data.get('email')
        ap_data = normalized_data.get('ap')
        
        if not email_data or not ap_data:
            return discrepancies
        
        email_amounts = self._extract_amounts_from_data(email_data)
        ap_amounts = self._extract_amounts_from_data(ap_data)
        
        # Check for significant amount differences
        for email_amount in email_amounts:
            for ap_amount in ap_amounts:
                if not self._amounts_match_within_tolerance(
                    email_amount, 
                    ap_amount, 
                    self.discrepancy_config['amount_tolerance_percentage']
                ):
                    difference = abs(email_amount - ap_amount)
                    severity = self._determine_amount_discrepancy_severity(difference)
                    
                    discrepancy = Discrepancy(
                        discrepancy_type=DiscrepancyType.AMOUNT_MISMATCH,
                        systems_involved=['email', 'ap'],
                        description=f"Amount mismatch: Email shows ${email_amount:,.2f}, AP shows ${ap_amount:,.2f} (difference: ${difference:,.2f})",
                        severity=severity,
                        affected_data={
                            'email_amount': email_amount,
                            'ap_amount': ap_amount,
                            'difference': difference
                        },
                        recommended_action=f"Verify invoice amounts and reconcile {severity} discrepancy of ${difference:,.2f}"
                    )
                    discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _detect_missing_data(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        vendor_name: Optional[str]
    ) -> List[Discrepancy]:
        """Detect missing data across systems."""
        discrepancies = []
        
        systems_with_data = [
            system for system, data in normalized_data.items() 
            if data is not None
        ]
        
        systems_without_data = [
            system for system, data in normalized_data.items() 
            if data is None
        ]
        
        if len(systems_without_data) > 0 and len(systems_with_data) > 0:
            discrepancy = Discrepancy(
                discrepancy_type=DiscrepancyType.MISSING_DATA,
                systems_involved=systems_without_data,
                description=f"Missing data from {', '.join(systems_without_data)} systems for vendor {vendor_name}",
                severity="medium" if len(systems_without_data) == 1 else "high",
                affected_data={
                    'missing_systems': systems_without_data,
                    'available_systems': systems_with_data,
                    'vendor_name': vendor_name
                },
                recommended_action=f"Investigate why {', '.join(systems_without_data)} systems have no data for {vendor_name}"
            )
            discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _detect_status_conflicts(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        correlations: List[DataCorrelation]
    ) -> List[Discrepancy]:
        """Detect conflicting status information between systems."""
        discrepancies = []
        
        # Extract payment status from different systems
        email_statuses = self._extract_payment_statuses(normalized_data.get('email'))
        ap_statuses = self._extract_payment_statuses(normalized_data.get('ap'))
        
        # Check for conflicts
        conflicting_statuses = []
        for email_status in email_statuses:
            for ap_status in ap_statuses:
                if self._statuses_conflict(email_status, ap_status):
                    conflicting_statuses.append((email_status, ap_status))
        
        if conflicting_statuses:
            discrepancy = Discrepancy(
                discrepancy_type=DiscrepancyType.STATUS_CONFLICT,
                systems_involved=['email', 'ap'],
                description=f"Conflicting payment statuses detected: {conflicting_statuses}",
                severity="high",
                affected_data={'conflicting_statuses': conflicting_statuses},
                recommended_action="Reconcile payment status differences between email communications and AP system"
            )
            discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _detect_vendor_name_variations(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        vendor_name: Optional[str]
    ) -> List[Discrepancy]:
        """Detect vendor name variations across systems."""
        discrepancies = []
        
        if not vendor_name:
            return discrepancies
        
        # Extract vendor names from each system
        vendor_variations = {}
        
        for system, data in normalized_data.items():
            if data:
                variations = self._extract_vendor_names(data, vendor_name)
                if variations:
                    vendor_variations[system] = variations
        
        # Check for significant variations
        all_variations = set()
        for variations in vendor_variations.values():
            all_variations.update(variations)
        
        if len(all_variations) > 1:
            discrepancy = Discrepancy(
                discrepancy_type=DiscrepancyType.VENDOR_NAME_VARIATION,
                systems_involved=list(vendor_variations.keys()),
                description=f"Vendor name variations detected: {list(all_variations)}",
                severity="low",
                affected_data={
                    'target_vendor': vendor_name,
                    'variations': list(all_variations),
                    'systems': vendor_variations
                },
                recommended_action="Standardize vendor name across all systems to improve data correlation"
            )
            discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _determine_amount_discrepancy_severity(self, difference: float) -> str:
        """Determine severity of amount discrepancy."""
        if difference >= self.discrepancy_config['critical_amount_threshold']:
            return "critical"
        elif difference >= self.discrepancy_config['high_severity_amount_threshold']:
            return "high"
        else:
            return "medium"
    
    def _extract_payment_statuses(self, data: Optional[Dict[str, Any]]) -> List[str]:
        """Extract payment status information from data."""
        statuses = []
        
        if not data:
            return statuses
        
        # Extract from payment_status_mentions
        if 'payment_status_mentions' in data:
            statuses.extend(data['payment_status_mentions'])
        
        # Extract from statuses field
        if 'statuses' in data:
            statuses.extend(data['statuses'])
        
        return statuses
    
    def _statuses_conflict(self, status1: str, status2: str) -> bool:
        """Check if two payment statuses conflict."""
        # Define conflicting status pairs
        conflicts = [
            ('paid', 'unpaid'),
            ('paid', 'overdue'),
            ('processed', 'pending'),
            ('approved', 'rejected')
        ]
        
        status1_lower = status1.lower()
        status2_lower = status2.lower()
        
        for conflict_pair in conflicts:
            if (status1_lower in conflict_pair and status2_lower in conflict_pair and 
                status1_lower != status2_lower):
                return True
        
        return False
    
    def _extract_vendor_names(self, data: Dict[str, Any], target_vendor: str) -> List[str]:
        """Extract vendor name variations from data."""
        variations = []
        
        # Look for vendor mentions in various fields
        text_fields = ['vendor_mentions', 'account_names', 'vendors']
        
        for field in text_fields:
            if field in data:
                field_data = data[field]
                if isinstance(field_data, list):
                    for item in field_data:
                        if isinstance(item, str) and self._is_vendor_variation(item, target_vendor):
                            variations.append(item)
                elif isinstance(field_data, str) and self._is_vendor_variation(field_data, target_vendor):
                    variations.append(field_data)
        
        return variations
    
    def _is_vendor_variation(self, candidate: str, target_vendor: str) -> bool:
        """Check if candidate string is a variation of target vendor name."""
        # Simple similarity check - could be enhanced with fuzzy matching
        candidate_lower = candidate.lower()
        target_lower = target_vendor.lower()
        
        # Check if candidate contains significant portion of target
        target_words = target_lower.split()
        candidate_words = candidate_lower.split()
        
        matching_words = sum(1 for word in target_words if word in candidate_words)
        similarity = matching_words / len(target_words) if target_words else 0
        
        return similarity >= self.discrepancy_config['vendor_name_similarity_threshold']
    
    async def _identify_payment_issues(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        correlations: List[DataCorrelation],
        discrepancies: List[Discrepancy],
        vendor_name: Optional[str]
    ) -> List[PaymentIssue]:
        """
        Identify payment issues based on analysis.
        
        Args:
            normalized_data: Normalized data from all systems
            correlations: Found correlations
            discrepancies: Detected discrepancies
            vendor_name: Target vendor name
            
        Returns:
            List of identified payment issues
        """
        payment_issues = []
        
        # Identify overdue payments
        overdue_issues = self._identify_overdue_payments(normalized_data)
        payment_issues.extend(overdue_issues)
        
        # Identify amount discrepancies as payment issues
        amount_issues = self._identify_amount_payment_issues(discrepancies)
        payment_issues.extend(amount_issues)
        
        # Identify communication gaps
        communication_issues = self._identify_communication_gaps(normalized_data, vendor_name)
        payment_issues.extend(communication_issues)
        
        # Identify unclear payment status
        status_issues = self._identify_unclear_payment_status(normalized_data, discrepancies)
        payment_issues.extend(status_issues)
        
        return payment_issues
    
    def _identify_overdue_payments(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]]
    ) -> List[PaymentIssue]:
        """Identify overdue payment issues."""
        issues = []
        
        ap_data = normalized_data.get('ap')
        if not ap_data:
            return issues
        
        # Check for overdue indicators in AP data
        current_date = datetime.now(timezone.utc)
        
        # Look for due dates and payment status
        due_dates = ap_data.get('due_dates', [])
        statuses = ap_data.get('statuses', [])
        amounts = self._extract_amounts_from_data(ap_data)
        
        for i, due_date_str in enumerate(due_dates):
            try:
                # Parse due date (this would need proper date parsing)
                # For now, assume overdue if status indicates it
                if any(status in ['overdue', 'unpaid', 'outstanding'] for status in statuses):
                    amount = amounts[i] if i < len(amounts) else 0.0
                    severity = "critical" if amount > self.payment_issue_config['critical_overdue_days'] else "high"
                    
                    issue = PaymentIssue(
                        issue_type=PaymentIssueType.OVERDUE_PAYMENT,
                        description=f"Overdue payment detected: ${amount:,.2f} past due date {due_date_str}",
                        severity=severity,
                        affected_vendor="Unknown",  # Would extract from data
                        affected_amount=amount,
                        affected_invoice=None,
                        recommended_action=f"Contact vendor immediately to resolve overdue payment of ${amount:,.2f}",
                        urgency_score=0.9 if severity == "critical" else 0.7
                    )
                    issues.append(issue)
            except Exception as e:
                logger.warning(f"Error parsing due date {due_date_str}: {e}")
        
        return issues
    
    def _identify_amount_payment_issues(
        self,
        discrepancies: List[Discrepancy]
    ) -> List[PaymentIssue]:
        """Convert amount discrepancies to payment issues."""
        issues = []
        
        for discrepancy in discrepancies:
            if discrepancy.discrepancy_type == DiscrepancyType.AMOUNT_MISMATCH:
                affected_data = discrepancy.affected_data
                difference = affected_data.get('difference', 0.0)
                
                issue = PaymentIssue(
                    issue_type=PaymentIssueType.AMOUNT_DISCREPANCY,
                    description=f"Payment amount discrepancy: {discrepancy.description}",
                    severity=discrepancy.severity,
                    affected_vendor="Unknown",
                    affected_amount=difference,
                    affected_invoice=None,
                    recommended_action=discrepancy.recommended_action,
                    urgency_score=0.8 if discrepancy.severity == "critical" else 0.6
                )
                issues.append(issue)
        
        return issues
    
    def _identify_communication_gaps(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        vendor_name: Optional[str]
    ) -> List[PaymentIssue]:
        """Identify communication gaps with vendors."""
        issues = []
        
        email_data = normalized_data.get('email')
        ap_data = normalized_data.get('ap')
        
        # If we have AP data but no email data, there might be a communication gap
        if ap_data and not email_data and vendor_name:
            issue = PaymentIssue(
                issue_type=PaymentIssueType.VENDOR_COMMUNICATION_GAP,
                description=f"No recent email communications found with {vendor_name} despite active AP records",
                severity="medium",
                affected_vendor=vendor_name,
                affected_amount=None,
                affected_invoice=None,
                recommended_action=f"Reach out to {vendor_name} to ensure communication channels are open",
                urgency_score=0.4
            )
            issues.append(issue)
        
        return issues
    
    def _identify_unclear_payment_status(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        discrepancies: List[Discrepancy]
    ) -> List[PaymentIssue]:
        """Identify unclear payment status issues."""
        issues = []
        
        # Check for status conflicts in discrepancies
        for discrepancy in discrepancies:
            if discrepancy.discrepancy_type == DiscrepancyType.STATUS_CONFLICT:
                issue = PaymentIssue(
                    issue_type=PaymentIssueType.PAYMENT_STATUS_UNCLEAR,
                    description=f"Payment status unclear due to conflicting information: {discrepancy.description}",
                    severity="high",
                    affected_vendor="Unknown",
                    affected_amount=None,
                    affected_invoice=None,
                    recommended_action="Clarify payment status by reconciling information between systems",
                    urgency_score=0.7
                )
                issues.append(issue)
        
        return issues
    
    def _calculate_data_quality_score(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        correlations: List[DataCorrelation],
        discrepancies: List[Discrepancy]
    ) -> float:
        """
        Calculate overall data quality score.
        
        Args:
            normalized_data: Normalized data from all systems
            correlations: Found correlations
            discrepancies: Detected discrepancies
            
        Returns:
            Data quality score from 0.0 to 1.0
        """
        score = 1.0
        
        # Penalize for missing data
        systems_with_data = sum(1 for data in normalized_data.values() if data is not None)
        total_systems = len(normalized_data)
        data_completeness = systems_with_data / total_systems
        score *= data_completeness
        
        # Penalize for discrepancies
        critical_discrepancies = sum(1 for d in discrepancies if d.severity == "critical")
        high_discrepancies = sum(1 for d in discrepancies if d.severity == "high")
        medium_discrepancies = sum(1 for d in discrepancies if d.severity == "medium")
        
        discrepancy_penalty = (
            critical_discrepancies * 0.3 +
            high_discrepancies * 0.2 +
            medium_discrepancies * 0.1
        )
        score = max(0.0, score - discrepancy_penalty)
        
        # Bonus for high-quality correlations
        high_confidence_correlations = sum(1 for c in correlations if c.confidence_level == "high")
        correlation_bonus = min(0.2, high_confidence_correlations * 0.05)
        score = min(1.0, score + correlation_bonus)
        
        return round(score, 3)
    
    async def _generate_analysis_summary(
        self,
        normalized_data: Dict[str, Optional[Dict[str, Any]]],
        correlations: List[DataCorrelation],
        discrepancies: List[Discrepancy],
        payment_issues: List[PaymentIssue],
        vendor_name: Optional[str]
    ) -> str:
        """
        Generate comprehensive analysis summary using LLM.
        
        Args:
            normalized_data: Normalized data from all systems
            correlations: Found correlations
            discrepancies: Detected discrepancies
            payment_issues: Identified payment issues
            vendor_name: Target vendor name
            
        Returns:
            Natural language analysis summary
        """
        # Prepare analysis context for LLM
        analysis_context = {
            "vendor_name": vendor_name,
            "data_sources": {
                system: "available" if data else "unavailable"
                for system, data in normalized_data.items()
            },
            "correlations_found": len(correlations),
            "high_confidence_correlations": sum(1 for c in correlations if c.confidence_level == "high"),
            "discrepancies_found": len(discrepancies),
            "critical_discrepancies": sum(1 for d in discrepancies if d.severity == "critical"),
            "payment_issues_found": len(payment_issues),
            "critical_payment_issues": sum(1 for p in payment_issues if p.severity == "critical")
        }
        
        # Create detailed summary prompt
        prompt = f"""
        Analyze the following cross-system data correlation results for vendor "{vendor_name}":

        DATA AVAILABILITY:
        - Email System: {analysis_context['data_sources']['email']}
        - Accounts Payable System: {analysis_context['data_sources']['ap']}
        - CRM System: {analysis_context['data_sources']['crm']}

        CORRELATION ANALYSIS:
        - Total correlations found: {analysis_context['correlations_found']}
        - High confidence correlations: {analysis_context['high_confidence_correlations']}

        DISCREPANCY ANALYSIS:
        - Total discrepancies detected: {analysis_context['discrepancies_found']}
        - Critical discrepancies: {analysis_context['critical_discrepancies']}

        PAYMENT ISSUE ANALYSIS:
        - Total payment issues identified: {analysis_context['payment_issues_found']}
        - Critical payment issues: {analysis_context['critical_payment_issues']}

        DETAILED FINDINGS:
        
        Correlations:
        {self._format_correlations_for_llm(correlations)}
        
        Discrepancies:
        {self._format_discrepancies_for_llm(discrepancies)}
        
        Payment Issues:
        {self._format_payment_issues_for_llm(payment_issues)}

        Please provide a comprehensive analysis summary that includes:
        1. Executive summary of findings
        2. Key insights about data quality and correlation
        3. Critical issues requiring immediate attention
        4. Overall assessment of vendor relationship and payment status
        5. Business impact assessment

        Format the response as a professional business analysis report.
        """
        
        try:
            # Generate analysis using LLM
            analysis_summary = await self.llm_service.generate_response(
                prompt,
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more factual analysis
            )
            
            return analysis_summary
            
        except Exception as e:
            logger.error(f"Failed to generate LLM analysis summary: {e}")
            
            # Fallback to template-based summary
            return self._generate_template_analysis_summary(
                analysis_context,
                correlations,
                discrepancies,
                payment_issues,
                vendor_name
            )
    
    def _format_correlations_for_llm(self, correlations: List[DataCorrelation]) -> str:
        """Format correlations for LLM prompt."""
        if not correlations:
            return "No correlations found between systems."
        
        formatted = []
        for i, correlation in enumerate(correlations, 1):
            systems = []
            if correlation.email_data:
                systems.append("Email")
            if correlation.ap_data:
                systems.append("AP")
            if correlation.crm_data:
                systems.append("CRM")
            
            formatted.append(
                f"{i}. {' ↔ '.join(systems)} correlation "
                f"(Score: {correlation.correlation_score:.2f}, "
                f"Confidence: {correlation.confidence_level}, "
                f"Keys: {', '.join(correlation.correlation_keys)})"
            )
        
        return "\n".join(formatted)
    
    def _format_discrepancies_for_llm(self, discrepancies: List[Discrepancy]) -> str:
        """Format discrepancies for LLM prompt."""
        if not discrepancies:
            return "No discrepancies detected between systems."
        
        formatted = []
        for i, discrepancy in enumerate(discrepancies, 1):
            formatted.append(
                f"{i}. {discrepancy.discrepancy_type.value.replace('_', ' ').title()} "
                f"({discrepancy.severity.upper()}): {discrepancy.description}"
            )
        
        return "\n".join(formatted)
    
    def _format_payment_issues_for_llm(self, payment_issues: List[PaymentIssue]) -> str:
        """Format payment issues for LLM prompt."""
        if not payment_issues:
            return "No payment issues identified."
        
        formatted = []
        for i, issue in enumerate(payment_issues, 1):
            amount_str = f" (${issue.affected_amount:,.2f})" if issue.affected_amount else ""
            formatted.append(
                f"{i}. {issue.issue_type.value.replace('_', ' ').title()} "
                f"({issue.severity.upper()}){amount_str}: {issue.description}"
            )
        
        return "\n".join(formatted)
    
    def _generate_template_analysis_summary(
        self,
        analysis_context: Dict[str, Any],
        correlations: List[DataCorrelation],
        discrepancies: List[Discrepancy],
        payment_issues: List[PaymentIssue],
        vendor_name: Optional[str]
    ) -> str:
        """Generate template-based analysis summary as fallback."""
        summary_parts = []
        
        # Executive Summary
        summary_parts.append("## EXECUTIVE SUMMARY")
        summary_parts.append(
            f"Cross-system analysis completed for vendor '{vendor_name}'. "
            f"Found {len(correlations)} data correlations, {len(discrepancies)} discrepancies, "
            f"and {len(payment_issues)} payment issues across available systems."
        )
        
        # Data Quality Assessment
        summary_parts.append("\n## DATA QUALITY ASSESSMENT")
        available_systems = [
            system for system, status in analysis_context['data_sources'].items()
            if status == "available"
        ]
        summary_parts.append(f"Data available from: {', '.join(available_systems)}")
        
        if len(available_systems) < 3:
            summary_parts.append("⚠️ Limited data availability may impact analysis completeness.")
        
        # Critical Issues
        critical_discrepancies = [d for d in discrepancies if d.severity == "critical"]
        critical_issues = [p for p in payment_issues if p.severity == "critical"]
        
        if critical_discrepancies or critical_issues:
            summary_parts.append("\n## CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION")
            
            for discrepancy in critical_discrepancies:
                summary_parts.append(f"🚨 {discrepancy.description}")
            
            for issue in critical_issues:
                summary_parts.append(f"🚨 {issue.description}")
        
        # Recommendations
        summary_parts.append("\n## KEY RECOMMENDATIONS")
        if not correlations:
            summary_parts.append("• Improve data standardization across systems for better correlation")
        
        if discrepancies:
            summary_parts.append("• Reconcile identified discrepancies to ensure data accuracy")
        
        if payment_issues:
            summary_parts.append("• Address payment issues to maintain vendor relationships")
        
        return "\n".join(summary_parts)
    
    def _generate_recommendations(
        self,
        discrepancies: List[Discrepancy],
        payment_issues: List[PaymentIssue],
        data_quality_score: float
    ) -> List[str]:
        """
        Generate actionable recommendations based on analysis.
        
        Args:
            discrepancies: Detected discrepancies
            payment_issues: Identified payment issues
            data_quality_score: Overall data quality score
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Data quality recommendations
        if data_quality_score < 0.7:
            recommendations.append(
                "Improve data quality by addressing missing data and system discrepancies"
            )
        
        # Discrepancy-based recommendations
        critical_discrepancies = [d for d in discrepancies if d.severity == "critical"]
        if critical_discrepancies:
            recommendations.append(
                f"Immediately investigate and resolve {len(critical_discrepancies)} critical discrepancies"
            )
        
        amount_discrepancies = [
            d for d in discrepancies 
            if d.discrepancy_type == DiscrepancyType.AMOUNT_MISMATCH
        ]
        if amount_discrepancies:
            recommendations.append(
                "Reconcile amount differences between email communications and AP system records"
            )
        
        # Payment issue recommendations
        overdue_issues = [
            p for p in payment_issues 
            if p.issue_type == PaymentIssueType.OVERDUE_PAYMENT
        ]
        if overdue_issues:
            recommendations.append(
                f"Contact vendor immediately to resolve {len(overdue_issues)} overdue payments"
            )
        
        communication_issues = [
            p for p in payment_issues 
            if p.issue_type == PaymentIssueType.VENDOR_COMMUNICATION_GAP
        ]
        if communication_issues:
            recommendations.append(
                "Establish regular communication channels with vendor to prevent future issues"
            )
        
        # System integration recommendations
        if len([d for d in discrepancies if d.discrepancy_type == DiscrepancyType.MISSING_DATA]) > 0:
            recommendations.append(
                "Investigate system integration issues causing missing data"
            )
        
        # Preventive recommendations
        if not recommendations:
            recommendations.append(
                "Continue monitoring vendor relationship - no critical issues detected"
            )
        
        return recommendations


# Factory function for creating analysis agent instances
def create_analysis_agent(llm_service: Optional[LLMService] = None) -> AnalysisAgent:
    """
    Create and configure an Analysis Agent instance.
    
    Args:
        llm_service: Optional LLM service instance
        
    Returns:
        Configured AnalysisAgent instance
    """
    return AnalysisAgent(llm_service=llm_service)