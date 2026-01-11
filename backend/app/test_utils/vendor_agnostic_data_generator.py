#!/usr/bin/env python3
"""
Vendor-Agnostic Test Data Generator

This module provides configurable test data generation for multi-agent invoice analysis workflows.
It replaces hardcoded vendor names with configurable placeholders, allowing tests to run with
any vendor name while maintaining realistic mock data structure.

Key Features:
- Configurable vendor name injection via [VENDOR_NAME] placeholders
- Realistic mock data generation for email, accounts payable, and CRM systems
- Template-based approach for consistent data structure
- Support for multiple test scenarios with different vendor names
"""

import json
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class VendorTestConfig:
    """Configuration for vendor-specific test data generation."""
    vendor_name: str
    industry: str = "Technology"
    annual_revenue: float = 1000000.0
    invoice_amount_range: tuple = (5000.0, 50000.0)
    email_domain: str = None
    
    def __post_init__(self):
        """Set default email domain based on vendor name."""
        if self.email_domain is None:
            # Convert vendor name to email domain format
            domain_name = self.vendor_name.lower().replace(" ", "").replace("&", "and")
            self.email_domain = f"{domain_name}.com"


class VendorAgnosticDataGenerator:
    """
    Generates realistic test data for any vendor name, replacing hardcoded references
    with configurable vendor information.
    """
    
    def __init__(self, vendor_config: VendorTestConfig):
        """
        Initialize generator with vendor configuration.
        
        Args:
            vendor_config: Configuration object containing vendor details
        """
        self.config = vendor_config
        self.vendor_name = vendor_config.vendor_name
        
        # Generate consistent test data based on vendor name
        random.seed(hash(self.vendor_name))
        
    @classmethod
    def create_default_config(cls, vendor_name: str) -> VendorTestConfig:
        """Create default configuration for a vendor name."""
        return VendorTestConfig(
            vendor_name=vendor_name,
            industry=cls._generate_industry(),
            annual_revenue=random.uniform(500000, 5000000),
            invoice_amount_range=(random.uniform(1000, 5000), random.uniform(10000, 100000))
        )
    
    @staticmethod
    def _generate_industry() -> str:
        """Generate a random industry for the vendor."""
        industries = [
            "Technology", "Marketing", "Consulting", "Manufacturing", 
            "Healthcare", "Finance", "Retail", "Education", "Construction"
        ]
        return random.choice(industries)
    
    def generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """
        Generate test scenarios with vendor-specific data.
        
        Returns:
            List of test scenario dictionaries with vendor name injected
        """
        return [
            {
                "name": f"{self.vendor_name} Invoice Status Analysis",
                "description": f"Check status of invoices with {self.vendor_name} keyword and analyze payment issues",
                "user_query": f"Check the status of invoices received with keyword {self.vendor_name} and analyze any issues with their payment",
                "expected_agents": ["gmail", "accounts_payable", "crm", "analysis"],
                "search_keywords": [self.vendor_name, "invoice", "payment"],
                "expected_data_sources": ["email", "accounts_payable", "crm"],
                "vendor_config": self.config
            },
            {
                "name": f"{self.vendor_name} Communication Cross-Reference",
                "description": f"Find all {self.vendor_name} communications and cross-reference with billing system",
                "user_query": f"Find all {self.vendor_name} communications and cross-reference with our billing system",
                "expected_agents": ["gmail", "accounts_payable", "crm"],
                "search_keywords": [self.vendor_name],
                "expected_data_sources": ["email", "accounts_payable", "crm"],
                "vendor_config": self.config
            }
        ]
    
    def generate_mock_email_data(self, num_emails: int = 3) -> str:
        """
        Generate realistic mock email data for the vendor.
        
        Args:
            num_emails: Number of mock emails to generate
            
        Returns:
            Formatted string containing mock email search results
        """
        emails = []
        base_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        for i in range(num_emails):
            email_date = base_date + timedelta(days=i * 7)
            invoice_num = f"{self.vendor_name.upper().replace(' ', '')}-2024-{i+1:03d}"
            amount = random.uniform(*self.config.invoice_amount_range)
            
            if i == 0:  # Initial invoice
                emails.append({
                    "from": f"billing@{self.config.email_domain}",
                    "to": "accounts@ourcompany.com",
                    "subject": f"Invoice #{invoice_num} - {self.config.industry} Services Q4",
                    "date": email_date.strftime("%Y-%m-%d"),
                    "content": f"Please find attached invoice {invoice_num} for ${amount:,.2f} for Q4 {self.config.industry.lower()} services. Payment due within 30 days."
                })
            elif i == 1:  # Payment reminder
                emails.append({
                    "from": f"finance@{self.config.email_domain}",
                    "to": "ap@ourcompany.com",
                    "subject": f"Payment Reminder - Invoice {invoice_num}",
                    "date": email_date.strftime("%Y-%m-%d"),
                    "content": f"This is a friendly reminder that invoice {invoice_num} for ${amount:,.2f} is due on {(email_date + timedelta(days=14)).strftime('%B %d, %Y')}. Please process payment at your earliest convenience."
                })
            else:  # Payment confirmation
                emails.append({
                    "from": "accounts@ourcompany.com",
                    "to": f"billing@{self.config.email_domain}",
                    "subject": f"RE: Invoice #{invoice_num} - Payment Processing",
                    "date": email_date.strftime("%Y-%m-%d"),
                    "content": f"We have received your invoice {invoice_num}. Payment is being processed and should be completed by {(email_date + timedelta(days=7)).strftime('%B %d, %Y')}."
                })
        
        # Format as search results
        result = f"""
📧 **Gmail Search Results for {self.vendor_name}**

**Search Query:** "{self.vendor_name}" (invoices OR payments)
**Results Found:** {len(emails)} emails

"""
        
        for i, email in enumerate(emails, 1):
            result += f"""**Email {i}:**
- **From:** {email['from']}
- **To:** {email['to']}
- **Subject:** {email['subject']}
- **Date:** {email['date']}
- **Content:** {email['content']}

"""
        
        result += f"""**Summary:**
- Found {len(emails)} relevant emails about {self.vendor_name} invoices
- Invoice numbers identified: {', '.join([f"{self.vendor_name.upper().replace(' ', '')}-2024-{i+1:03d}" for i in range(len(emails))])}
- Payment status: In process as of {datetime.now().strftime('%B %d, %Y')}
"""
        
        return result
    
    def generate_mock_ap_data(self, num_bills: int = 2) -> str:
        """
        Generate realistic mock accounts payable data for the vendor.
        
        Args:
            num_bills: Number of mock bills to generate
            
        Returns:
            Formatted string containing mock AP search results
        """
        bills = []
        base_date = datetime.now(timezone.utc) - timedelta(days=45)
        
        for i in range(num_bills):
            bill_date = base_date + timedelta(days=i * 15)
            invoice_num = f"{self.vendor_name.upper().replace(' ', '')}-2024-{i+1:03d}"
            amount = random.uniform(*self.config.invoice_amount_range)
            status = "Open" if i == 0 else "Paid"
            
            bills.append({
                "id": f"bill_{i+1:03d}",
                "vendor_name": self.vendor_name,
                "invoice_number": invoice_num,
                "amount": amount,
                "due_date": (bill_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                "status": status,
                "created_date": bill_date.strftime("%Y-%m-%d")
            })
        
        # Format as Bill.com search results
        result = f"""
💰 **Bill.com Search Results for {self.vendor_name}**

**Vendor Search:** "{self.vendor_name}"
**Bills Found:** {len(bills)}

"""
        
        total_amount = 0
        outstanding_amount = 0
        
        for i, bill in enumerate(bills, 1):
            result += f"""**Bill {i}:**
- **Vendor:** {bill['vendor_name']}
- **Invoice #:** {bill['invoice_number']}
- **Amount:** ${bill['amount']:,.2f}
- **Due Date:** {bill['due_date']}
- **Status:** {bill['status']}
- **Created:** {bill['created_date']}

"""
            total_amount += bill['amount']
            if bill['status'] == "Open":
                outstanding_amount += bill['amount']
        
        result += f"""**Summary:**
- Total Bills: {len(bills)}
- Total Amount: ${total_amount:,.2f}
- Outstanding Amount: ${outstanding_amount:,.2f}
- Vendor Status: Active
"""
        
        return result
    
    def generate_mock_crm_data(self, include_opportunities: bool = True) -> str:
        """
        Generate realistic mock CRM data for the vendor.
        
        Args:
            include_opportunities: Whether to include opportunity data
            
        Returns:
            Formatted string containing mock CRM search results
        """
        # Account data
        account = {
            "id": f"acc_{hash(self.vendor_name) % 10000:04d}",
            "name": self.vendor_name,
            "industry": self.config.industry,
            "annual_revenue": self.config.annual_revenue,
            "employees": random.randint(50, 1000),
            "website": f"https://www.{self.config.email_domain}",
            "status": "Active"
        }
        
        # Opportunity data
        opportunities = []
        if include_opportunities:
            for i in range(random.randint(1, 3)):
                opp_amount = random.uniform(10000, 200000)
                opportunities.append({
                    "id": f"opp_{i+1:03d}",
                    "name": f"{self.vendor_name} - {random.choice(['Q1', 'Q2', 'Q3', 'Q4'])} {random.choice(['Services', 'Partnership', 'Contract'])}",
                    "amount": opp_amount,
                    "stage": random.choice(["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won"]),
                    "close_date": (datetime.now() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
                    "probability": random.randint(25, 90)
                })
        
        # Format as Salesforce search results
        result = f"""
🏢 **CRM Search Results for {self.vendor_name}**

**Account Search:** "{self.vendor_name}"
**Accounts Found:** 1

**Account Details:**
- **Name:** {account['name']}
- **Industry:** {account['industry']}
- **Annual Revenue:** ${account['annual_revenue']:,.2f}
- **Employees:** {account['employees']}
- **Website:** {account['website']}
- **Status:** {account['status']}

"""
        
        if opportunities:
            result += f"""**Opportunities for {self.vendor_name}:** {len(opportunities)}

"""
            for i, opp in enumerate(opportunities, 1):
                result += f"""**Opportunity {i}:**
- **Name:** {opp['name']}
- **Amount:** ${opp['amount']:,.2f}
- **Stage:** {opp['stage']}
- **Close Date:** {opp['close_date']}
- **Probability:** {opp['probability']}%

"""
        
        result += f"""**Summary:**
- Customer Relationship: Active
- Account Type: {self.config.industry} Partner
- Revenue Potential: High
- Payment History: Good
"""
        
        return result
    
    def generate_mock_analysis_template(self, gmail_data: str, ap_data: str, crm_data: str) -> str:
        """
        Generate a mock analysis template with vendor-specific content.
        
        Args:
            gmail_data: Mock email data
            ap_data: Mock AP data  
            crm_data: Mock CRM data
            
        Returns:
            Formatted analysis report with vendor name injected
        """
        return f"""
# {self.vendor_name} Invoice Status Analysis

## Executive Summary
This analysis examined {self.vendor_name} invoices across email communications, accounts payable systems, and CRM data to identify payment status and potential issues.

## Email Communications Analysis
**Status**: {'✅ Data Retrieved' if len(gmail_data) > 100 else '❌ Limited Data'}
- Searched for {self.vendor_name} communications
- Focused on invoice and payment related emails
- Found correspondence regarding invoice processing and payment status

## Billing System Analysis  
**Status**: {'✅ Data Retrieved' if len(ap_data) > 100 else '❌ Limited Data'}
- Searched Bill.com for {self.vendor_name} vendor records
- Analyzed payment status and outstanding amounts
- Identified active vendor relationship with current billing

## Customer Relationship Analysis
**Status**: {'✅ Data Retrieved' if len(crm_data) > 100 else '❌ Limited Data'}
- Searched Salesforce for {self.vendor_name} account data
- Reviewed customer history and opportunities
- Confirmed active {self.config.industry} partnership

## Payment Issues Identification
- **Outstanding Invoices**: Analysis of unpaid bills from {self.vendor_name}
- **Payment Delays**: Identification of overdue payments
- **Communication Gaps**: Missing follow-up on payment requests
- **System Discrepancies**: Differences between email and AP data

## Data Correlation
Cross-system analysis shows:
- Email communications align with AP system records
- {self.vendor_name} maintains active CRM relationship
- Payment processing appears to be on schedule
- No significant discrepancies identified

## Recommendations
1. **Immediate Actions**: Continue regular payment processing for {self.vendor_name}
2. **Process Improvements**: Maintain current invoice tracking between systems
3. **Follow-up Protocol**: Continue established payment status reviews
4. **Relationship Management**: Leverage strong CRM relationship for future opportunities

## System Status
- Gmail Agent: ✅ Operational
- AccountsPayable Agent: ✅ Operational  
- CRM Agent: ✅ Operational
- Data Correlation: ✅ Completed

**Vendor Focus**: {self.vendor_name} ({self.config.industry})
**Analysis Quality**: High - All systems provided relevant data
        """
    
    def replace_vendor_placeholders(self, template: str) -> str:
        """
        Replace [VENDOR_NAME] placeholders in template strings with actual vendor name.
        
        Args:
            template: Template string containing [VENDOR_NAME] placeholders
            
        Returns:
            String with placeholders replaced with actual vendor name
        """
        return template.replace("[VENDOR_NAME]", self.vendor_name)
    
    def get_vendor_test_queries(self) -> List[str]:
        """
        Get list of test queries with vendor name injected.
        
        Returns:
            List of test query strings for the vendor
        """
        return [
            f"Check the status of invoices received with keyword {self.vendor_name} and analyze any issues with their payment",
            f"Find all {self.vendor_name} communications and cross-reference with our billing system",
            f"Analyze payment history for {self.vendor_name} and identify any outstanding issues",
            f"Search for {self.vendor_name} in all systems and provide comprehensive status report"
        ]


# Predefined vendor configurations for common test scenarios
PREDEFINED_VENDORS = {
    "acme_marketing": VendorTestConfig(
        vendor_name="Acme Marketing",
        industry="Marketing",
        annual_revenue=2500000.0,
        invoice_amount_range=(10000.0, 50000.0)
    ),
    "tech_solutions": VendorTestConfig(
        vendor_name="Tech Solutions Inc",
        industry="Technology",
        annual_revenue=5000000.0,
        invoice_amount_range=(15000.0, 75000.0)
    ),
    "global_consulting": VendorTestConfig(
        vendor_name="Global Consulting Group",
        industry="Consulting",
        annual_revenue=10000000.0,
        invoice_amount_range=(25000.0, 100000.0)
    ),
    "creative_designs": VendorTestConfig(
        vendor_name="Creative Designs LLC",
        industry="Design",
        annual_revenue=1200000.0,
        invoice_amount_range=(5000.0, 30000.0)
    )
}


def get_vendor_generator(vendor_name: str = "Acme Marketing") -> VendorAgnosticDataGenerator:
    """
    Get a vendor data generator for the specified vendor name.
    
    Args:
        vendor_name: Name of the vendor to generate data for
        
    Returns:
        VendorAgnosticDataGenerator instance configured for the vendor
    """
    # Check if we have a predefined configuration
    vendor_key = vendor_name.lower().replace(" ", "_").replace(".", "").replace(",", "")
    
    if vendor_key in PREDEFINED_VENDORS:
        config = PREDEFINED_VENDORS[vendor_key]
    else:
        # Create default configuration for new vendor
        config = VendorAgnosticDataGenerator.create_default_config(vendor_name)
    
    return VendorAgnosticDataGenerator(config)


# Example usage and testing
if __name__ == "__main__":
    # Test with different vendors
    test_vendors = ["Acme Marketing", "Tech Solutions Inc", "Global Consulting Group"]
    
    for vendor in test_vendors:
        print(f"\n{'='*60}")
        print(f"Testing Vendor: {vendor}")
        print(f"{'='*60}")
        
        generator = get_vendor_generator(vendor)
        
        # Generate test scenarios
        scenarios = generator.generate_test_scenarios()
        print(f"\nGenerated {len(scenarios)} test scenarios:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario['name']}")
        
        # Generate mock data samples
        print(f"\nSample Email Data:")
        email_data = generator.generate_mock_email_data(2)
        print(email_data[:300] + "...")
        
        print(f"\nSample AP Data:")
        ap_data = generator.generate_mock_ap_data(1)
        print(ap_data[:300] + "...")
        
        print(f"\nSample CRM Data:")
        crm_data = generator.generate_mock_crm_data()
        print(crm_data[:300] + "...")