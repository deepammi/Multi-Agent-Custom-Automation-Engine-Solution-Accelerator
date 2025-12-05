"""Configurable validation rules for invoice extraction."""
import logging
import os
import json
import re
from typing import List, Dict, Any
from decimal import Decimal
from datetime import date as date_class
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation failures."""
    ERROR = "error"      # Blocks approval
    WARNING = "warning"  # Shows warning but allows approval
    INFO = "info"        # Informational only


class ValidationRule(BaseModel):
    """Configuration for a single validation rule."""
    id: str
    name: str
    description: str
    enabled: bool = True
    severity: ValidationSeverity = ValidationSeverity.ERROR
    
    class Config:
        use_enum_values = True


class ValidationRulesConfig:
    """Configurable validation rules for invoice extraction."""
    
    # Rule definitions with enable/disable flags
    RULES: Dict[str, ValidationRule] = {
        "date_ordering": ValidationRule(
            id="date_ordering",
            name="Date Ordering Check",
            description="Verify that due date is after invoice date",
            enabled=True,
            severity=ValidationSeverity.ERROR
        ),
        "total_calculation": ValidationRule(
            id="total_calculation",
            name="Total Calculation Check",
            description="Verify that total = subtotal + tax",
            enabled=True,
            severity=ValidationSeverity.ERROR
        ),
        "line_items_sum": ValidationRule(
            id="line_items_sum",
            name="Line Items Sum Check",
            description="Verify that line items sum to subtotal",
            enabled=True,
            severity=ValidationSeverity.WARNING
        ),
        "positive_amounts": ValidationRule(
            id="positive_amounts",
            name="Positive Amounts Check",
            description="Verify all amounts are positive",
            enabled=True,
            severity=ValidationSeverity.ERROR
        ),
        "required_fields": ValidationRule(
            id="required_fields",
            name="Required Fields Check",
            description="Verify all required fields are present",
            enabled=True,
            severity=ValidationSeverity.ERROR
        ),
        "invoice_number_format": ValidationRule(
            id="invoice_number_format",
            name="Invoice Number Format Check",
            description="Verify invoice number follows expected format",
            enabled=False,
            severity=ValidationSeverity.WARNING
        ),
        "vendor_name_length": ValidationRule(
            id="vendor_name_length",
            name="Vendor Name Length Check",
            description="Verify vendor name is reasonable length",
            enabled=False,
            severity=ValidationSeverity.INFO
        ),
        "future_date_check": ValidationRule(
            id="future_date_check",
            name="Future Date Check",
            description="Warn if invoice date is in the future",
            enabled=True,
            severity=ValidationSeverity.WARNING
        ),
        "duplicate_line_items": ValidationRule(
            id="duplicate_line_items",
            name="Duplicate Line Items Check",
            description="Check for duplicate line item descriptions",
            enabled=False,
            severity=ValidationSeverity.INFO
        ),
        "tax_rate_reasonableness": ValidationRule(
            id="tax_rate_reasonableness",
            name="Tax Rate Reasonableness Check",
            description="Verify tax rate is within reasonable range (0-30%)",
            enabled=True,
            severity=ValidationSeverity.WARNING
        )
    }
    
    @classmethod
    def get_enabled_rules(cls) -> List[ValidationRule]:
        """Get list of enabled validation rules."""
        return [rule for rule in cls.RULES.values() if rule.enabled]
    
    @classmethod
    def is_rule_enabled(cls, rule_id: str) -> bool:
        """Check if a specific rule is enabled."""
        rule = cls.RULES.get(rule_id)
        return rule.enabled if rule else False
    
    @classmethod
    def enable_rule(cls, rule_id: str):
        """Enable a validation rule."""
        if rule_id in cls.RULES:
            cls.RULES[rule_id].enabled = True
            logger.info(f"Enabled validation rule: {rule_id}")
    
    @classmethod
    def disable_rule(cls, rule_id: str):
        """Disable a validation rule."""
        if rule_id in cls.RULES:
            cls.RULES[rule_id].enabled = False
            logger.info(f"Disabled validation rule: {rule_id}")
    
    @classmethod
    def load_from_env(cls):
        """Load rule configuration from environment variables."""
        for rule_id in cls.RULES.keys():
            env_var = f"VALIDATION_RULE_{rule_id}"
            env_value = os.getenv(env_var)
            
            if env_value is not None:
                enabled = env_value.lower() in ('true', '1', 'yes', 'on')
                cls.RULES[rule_id].enabled = enabled
                logger.info(f"Set {rule_id} to {enabled} from environment")
    
    @classmethod
    def load_from_config_file(cls, config_path: str = "validation_rules.json"):
        """Load rule configuration from JSON file."""
        if not os.path.exists(config_path):
            logger.warning(f"Validation config file not found: {config_path}")
            return
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            for rule_id, rule_config in config.items():
                if rule_id in cls.RULES:
                    if 'enabled' in rule_config:
                        cls.RULES[rule_id].enabled = rule_config['enabled']
                    if 'severity' in rule_config:
                        cls.RULES[rule_id].severity = ValidationSeverity(rule_config['severity'])
            
            logger.info(f"Loaded validation rules from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load validation config: {e}")


class InvoiceValidator:
    """Validator that applies configured rules to invoice data."""
    
    def __init__(self, invoice_data: Any):
        """
        Initialize validator with invoice data.
        
        Args:
            invoice_data: InvoiceData instance to validate
        """
        self.invoice_data = invoice_data
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def validate(self) -> Dict[str, Any]:
        """
        Run all enabled validation rules.
        
        Returns:
            dict with errors, warnings, info messages, and flags
        """
        # Get enabled rules
        enabled_rules = ValidationRulesConfig.get_enabled_rules()
        
        logger.info(f"Running {len(enabled_rules)} enabled validation rules")
        
        # Run each enabled rule
        for rule in enabled_rules:
            try:
                self._run_rule(rule)
            except Exception as e:
                self.errors.append(f"Validation rule '{rule.name}' failed: {str(e)}")
                logger.error(f"Validation rule {rule.id} failed: {e}")
        
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "has_errors": len(self.errors) > 0,
            "has_warnings": len(self.warnings) > 0
        }
    
    def _run_rule(self, rule: ValidationRule):
        """Run a specific validation rule."""
        rule_id = rule.id
        
        # Date ordering check
        if rule_id == "date_ordering":
            if self.invoice_data.due_date and self.invoice_data.invoice_date:
                if self.invoice_data.due_date < self.invoice_data.invoice_date:
                    self._add_issue(rule, "Due date is before invoice date")
        
        # Total calculation check
        elif rule_id == "total_calculation":
            # Calculate expected total: Subtotal + Tax - Discount
            expected_total = self.invoice_data.subtotal
            if self.invoice_data.tax_amount:
                expected_total += self.invoice_data.tax_amount
            if self.invoice_data.discount_amount:
                expected_total -= self.invoice_data.discount_amount
            
            if abs(self.invoice_data.total_amount - expected_total) > Decimal('0.01'):
                # Build detailed message showing the calculation
                calc_parts = [f"subtotal ({self.invoice_data.subtotal})"]
                if self.invoice_data.tax_amount:
                    calc_parts.append(f"+ tax ({self.invoice_data.tax_amount})")
                if self.invoice_data.discount_amount:
                    calc_parts.append(f"- discount ({self.invoice_data.discount_amount})")
                
                self._add_issue(
                    rule,
                    f"Total {self.invoice_data.total_amount} doesn't match "
                    f"{' '.join(calc_parts)} = {expected_total}"
                )
        
        # Line items sum check
        elif rule_id == "line_items_sum":
            if self.invoice_data.line_items:
                line_items_total = sum(item.total for item in self.invoice_data.line_items)
                if abs(line_items_total - self.invoice_data.subtotal) > Decimal('0.01'):
                    self._add_issue(
                        rule,
                        f"Line items sum ({line_items_total}) doesn't match "
                        f"subtotal ({self.invoice_data.subtotal})"
                    )
        
        # Positive amounts check
        elif rule_id == "positive_amounts":
            if self.invoice_data.subtotal <= 0:
                self._add_issue(rule, "Subtotal must be positive")
            if self.invoice_data.total_amount <= 0:
                self._add_issue(rule, "Total amount must be positive")
            if self.invoice_data.tax_amount and self.invoice_data.tax_amount < 0:
                self._add_issue(rule, "Tax amount cannot be negative")
        
        # Required fields check
        elif rule_id == "required_fields":
            if not self.invoice_data.vendor_name:
                self._add_issue(rule, "Vendor name is required")
            if not self.invoice_data.invoice_number:
                self._add_issue(rule, "Invoice number is required")
        
        # Invoice number format check
        elif rule_id == "invoice_number_format":
            # Example: Check if invoice number matches pattern
            if not re.match(r'^[A-Z]{2,4}-\d{3,6}$', self.invoice_data.invoice_number):
                self._add_issue(
                    rule,
                    f"Invoice number '{self.invoice_data.invoice_number}' "
                    f"doesn't match expected format (e.g., INV-12345)"
                )
        
        # Vendor name length check
        elif rule_id == "vendor_name_length":
            if len(self.invoice_data.vendor_name) < 2:
                self._add_issue(rule, "Vendor name is too short")
            elif len(self.invoice_data.vendor_name) > 100:
                self._add_issue(rule, "Vendor name is too long")
        
        # Future date check
        elif rule_id == "future_date_check":
            today = date_class.today()
            if self.invoice_data.invoice_date > today:
                self._add_issue(rule, "Invoice date is in the future")
        
        # Duplicate line items check
        elif rule_id == "duplicate_line_items":
            descriptions = [item.description for item in self.invoice_data.line_items]
            duplicates = [desc for desc in descriptions if descriptions.count(desc) > 1]
            if duplicates:
                self._add_issue(rule, f"Duplicate line items found: {set(duplicates)}")
        
        # Tax rate reasonableness check
        elif rule_id == "tax_rate_reasonableness":
            if self.invoice_data.tax_amount and self.invoice_data.subtotal > 0:
                tax_rate = (self.invoice_data.tax_amount / self.invoice_data.subtotal) * 100
                if tax_rate < 0 or tax_rate > 30:
                    self._add_issue(
                        rule,
                        f"Tax rate ({tax_rate:.1f}%) seems unusual (expected 0-30%)"
                    )
    
    def _add_issue(self, rule: ValidationRule, message: str):
        """Add a validation issue based on severity."""
        full_message = f"[{rule.name}] {message}"
        
        if rule.severity == ValidationSeverity.ERROR:
            self.errors.append(full_message)
        elif rule.severity == ValidationSeverity.WARNING:
            self.warnings.append(full_message)
        else:  # INFO
            self.info.append(full_message)
