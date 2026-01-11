"""Prompt templates for specialized agents."""
""" comments revised: Dec 24 after MCP HTTP fix
1. It defined Text Prompts for Invoice Agent, Closing Agent, Audit Agent (not sure if being used??)
2. It defines Text Prompt for Gmail Agent - check to see if it needs improvement ??
3. It includes functions that create structured prompt queries for each type of agent - audit, closing, invoice, gmail
4. It includes funciton to validate the structure of each prompt query
"""

import logging

logger = logging.getLogger(__name__)


# Invoice Agent Prompt Template
INVOICE_AGENT_PROMPT = """You are an expert Invoice Agent specializing in invoice management and analysis.

Your expertise includes:
- Verifying invoice accuracy and completeness
- Checking payment due dates and status
- Reviewing vendor information
- Validating payment terms
- Identifying discrepancies or issues

Task: {task_description}

Please analyze this invoice-related task and provide:
1. A clear assessment of the situation
2. Any issues or concerns identified
3. Recommended actions or next steps
4. Specific details about invoice accuracy, due dates, vendor info, and payment terms

Provide your analysis in a clear, structured format. If the task description lacks specific invoice details, work with the information provided and note what additional information would be helpful."""


# Closing Agent Prompt Template
CLOSING_AGENT_PROMPT = """You are an expert Closing Agent specializing in financial closing process automation.

Your expertise includes:
- Performing account reconciliations
- Drafting journal entries
- Identifying GL anomalies
- Completing variance analysis
- Ensuring closing process accuracy

Task: {task_description}

Please analyze this closing-related task and provide:
1. A clear assessment of the closing requirements
2. Any anomalies or issues identified
3. Recommended reconciliation steps
4. Specific details about account balances, journal entries, and variances

Provide your analysis in a clear, structured format. If the task description lacks specific closing details, work with the information provided and note what additional information would be helpful."""


# Audit Agent Prompt Template
AUDIT_AGENT_PROMPT = """You are an expert Audit Agent specializing in audit automation and compliance.

Your expertise includes:
- Performing continuous monitoring
- Gathering audit evidence
- Detecting exceptions and anomalies
- Preparing audit responses
- Ensuring compliance with standards

Task: {task_description}

Please analyze this audit-related task and provide:
1. A clear assessment of the audit requirements
2. Any exceptions or anomalies identified
3. Recommended audit procedures
4. Specific details about evidence, compliance, and findings

Provide your analysis in a clear, structured format. If the task description lacks specific audit details, work with the information provided and note what additional information would be helpful."""


# Gmail Agent Prompt Template
GMAIL_AGENT_PROMPT = """You are an expert Gmail Agent specializing in email search, analysis, and management.

Your capabilities include:
- Searching Gmail using precise search criteria and Gmail search syntax
- Analyzing email communications and extracting relevant information
- Sending emails with proper formatting
- Retrieving specific emails by ID
- Providing detailed summaries of email content and patterns

Task: {task_description}

IMPORTANT INSTRUCTIONS:
1. When searching emails, use Gmail search syntax (from:sender, subject:keyword, newer_than:1m, etc.)
2. If NO emails are found, respond with "Nothing found - no emails match the specified criteria"
3. If emails ARE found, provide detailed analysis of the actual email content
4. Focus ONLY on emails that directly match the search criteria
5. Do not fabricate or imagine email content - only analyze what is actually retrieved
6. For sending emails, extract recipient, subject, and body from the request
7. For listing emails, determine appropriate number of recent emails to show

Based on this task, analyze what specific action is needed:
- SEARCH: Extract search terms and use Gmail search syntax
- SEND: Extract recipient, subject, and body details  
- GET: Extract message ID for specific email retrieval
- LIST: Determine number of recent emails to show

Provide your response based ONLY on actual email data retrieved, not hypothetical content.
If no emails match the search criteria, clearly state "Nothing found" and explain what was searched for."""


def build_invoice_prompt(task_description: str) -> str:
    """
    Build invoice agent prompt with task details.
    
    Args:
        task_description: The user's task description
        
    Returns:
        str: Formatted prompt ready for LLM
    """
    if not task_description or not task_description.strip():
        logger.warning("Empty task description provided to build_invoice_prompt")
        task_description = "No specific task provided. Please provide general invoice analysis guidance."
    
    prompt = INVOICE_AGENT_PROMPT.format(task_description=task_description.strip())
    logger.debug(f"Built invoice prompt (length: {len(prompt)} chars)")
    return prompt


def build_closing_prompt(task_description: str) -> str:
    """
    Build closing agent prompt with task details.
    
    Args:
        task_description: The user's task description
        
    Returns:
        str: Formatted prompt ready for LLM
    """
    if not task_description or not task_description.strip():
        logger.warning("Empty task description provided to build_closing_prompt")
        task_description = "No specific task provided. Please provide general closing process guidance."
    
    prompt = CLOSING_AGENT_PROMPT.format(task_description=task_description.strip())
    logger.debug(f"Built closing prompt (length: {len(prompt)} chars)")
    return prompt


def build_audit_prompt(task_description: str) -> str:
    """
    Build audit agent prompt with task details.
    
    Args:
        task_description: The user's task description
        
    Returns:
        str: Formatted prompt ready for LLM
    """
    if not task_description or not task_description.strip():
        logger.warning("Empty task description provided to build_audit_prompt")
        task_description = "No specific task provided. Please provide general audit guidance."
    
    prompt = AUDIT_AGENT_PROMPT.format(task_description=task_description.strip())
    logger.debug(f"Built audit prompt (length: {len(prompt)} chars)")
    return prompt


def build_gmail_prompt(task_description: str) -> str:
    """
    Build Gmail agent prompt with task details.
    
    Args:
        task_description: The user's task description
        
    Returns:
        str: Formatted prompt ready for LLM
    """
    if not task_description or not task_description.strip():
        logger.warning("Empty task description provided to build_gmail_prompt")
        task_description = "No specific task provided. Please provide general email analysis guidance."
    
    prompt = GMAIL_AGENT_PROMPT.format(task_description=task_description.strip())
    logger.debug(f"Built Gmail prompt (length: {len(prompt)} chars)")
    return prompt


def validate_prompt_structure(prompt: str, agent_name: str) -> bool:
    """
    Validate that a prompt contains all required sections.
    
    Args:
        prompt: The prompt to validate
        agent_name: Name of the agent (for logging)
        
    Returns:
        bool: True if prompt is valid, False otherwise
    """
    required_elements = [
        ("role/expertise", "expert"),
        ("task description", "Task:"),
        ("output instructions", "provide"),
        ("format guidance", "format")
    ]
    
    missing_elements = []
    for element_name, keyword in required_elements:
        if keyword.lower() not in prompt.lower():
            missing_elements.append(element_name)
    
    if missing_elements:
        logger.error(
            f"Prompt validation failed for {agent_name} agent. "
            f"Missing elements: {', '.join(missing_elements)}"
        )
        return False
    
    logger.debug(f"Prompt validation passed for {agent_name} agent")
    return True

