"""LLM service for managing AI model interactions."""
import logging
import os
import asyncio
from typing import Optional
from datetime import datetime
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger(__name__)


def sanitize_for_logging(text: str) -> str:
    """
    Sanitize text for logging by removing API keys and sensitive data.
    
    Args:
        text: Text to sanitize
        
    Returns:
        str: Sanitized text safe for logging
    """
    import re
    
    # Remove OpenAI API keys (sk-...)
    text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[OPENAI_KEY_REDACTED]', text)
    
    # Remove Anthropic API keys (sk-ant-...)
    text = re.sub(r'sk-ant-[a-zA-Z0-9]{20,}', '[ANTHROPIC_KEY_REDACTED]', text)
    
    # Remove generic API keys
    text = re.sub(r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}', 'api_key=[REDACTED]', text, flags=re.IGNORECASE)
    
    return text


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMTimeoutError(LLMError):
    """LLM call timed out."""
    pass


class LLMAuthError(LLMError):
    """LLM authentication failed."""
    pass


class LLMRateLimitError(LLMError):
    """LLM rate limit exceeded."""
    pass


class LLMNetworkError(LLMError):
    """LLM network error."""
    pass


class LLMService:
    """Centralized service for LLM provider configuration and API calls."""
    
    _llm_instance: Optional[BaseChatModel] = None
    _provider: Optional[str] = None
    
    @classmethod
    def get_llm_instance(cls) -> BaseChatModel:
        """
        Get configured LLM instance based on environment variables.
        
        Returns:
            BaseChatModel: Configured LLM instance
            
        Raises:
            ValueError: If provider is not configured or invalid
        """
        # Return cached instance if available
        if cls._llm_instance is not None:
            return cls._llm_instance
        
        # Read configuration from environment
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        cls._provider = provider
        
        logger.info(f"Initializing LLM provider: {provider}")
        
        try:
            if provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")
                
                model = os.getenv("OPENAI_MODEL", "gpt-4o")
                temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
                timeout = int(os.getenv("LLM_TIMEOUT", "60"))
                
                cls._llm_instance = ChatOpenAI(
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    timeout=timeout,
                    max_retries=0  # We handle retries ourselves
                )
                logger.info(f"✅ OpenAI initialized with model: {model}")
                
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic provider")
                
                model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
                temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
                timeout = int(os.getenv("LLM_TIMEOUT", "60"))
                
                cls._llm_instance = ChatAnthropic(
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    timeout=timeout,
                    max_retries=0  # We handle retries ourselves
                )
                logger.info(f"✅ Anthropic initialized with model: {model}")
                
            elif provider == "ollama":
                try:
                    from langchain_ollama import ChatOllama
                except ImportError:
                    raise ValueError(
                        "langchain-ollama package is required for Ollama provider. "
                        "Install with: pip install langchain-ollama"
                    )
                
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                model = os.getenv("OLLAMA_MODEL", "llama3")
                temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
                
                cls._llm_instance = ChatOllama(
                    base_url=base_url,
                    model=model,
                    temperature=temperature
                )
                logger.info(f"✅ Ollama initialized with model: {model} at {base_url}")
                
            else:
                raise ValueError(
                    f"Invalid LLM provider: {provider}. "
                    f"Supported providers: openai, anthropic, ollama"
                )
            
            return cls._llm_instance
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM provider {provider}: {e}")
            raise
    
    @classmethod
    def is_mock_mode(cls) -> bool:
        """
        Check if mock mode is enabled.
        
        Returns:
            bool: True if mock mode is enabled, False otherwise
        """
        use_mock = os.getenv("USE_MOCK_LLM", "false").lower()
        is_mock = use_mock in ("true", "1", "yes")
        
        if is_mock:
            logger.info("🎭 Mock mode is ENABLED - using dummy responses")
        
        return is_mock
    
    @classmethod
    def get_mock_response(cls, agent_name: str, task: str) -> str:
        """
        Return hardcoded mock response for testing.
        
        Args:
            agent_name: Name of the agent (Invoice, Closing, Audit, etc.)
            task: Task description
            
        Returns:
            str: Mock response appropriate for the agent
        """
        logger.info(
            f"🎭 Mock mode: Generating mock response for {agent_name} agent "
            f"(task_length={len(task)} chars)"
        )
        
        mock_responses = {
            "Invoice": (
                f"Invoice Agent here. I've processed your request:\n\n"
                f"✓ Verified invoice accuracy and completeness\n"
                f"✓ Checked payment due dates and status\n"
                f"✓ Reviewed vendor information\n"
                f"✓ Validated payment terms\n\n"
                f"Invoice analysis complete. All checks passed successfully."
            ),
            "Closing": (
                f"Closing Agent here. I've completed the closing process:\n\n"
                f"✓ Performed account reconciliations\n"
                f"✓ Drafted journal entries\n"
                f"✓ Identified GL anomalies\n"
                f"✓ Completed variance analysis\n\n"
                f"Closing process complete. All reconciliations balanced."
            ),
            "Audit": (
                f"Audit Agent here. I've completed the audit review:\n\n"
                f"✓ Performed continuous monitoring\n"
                f"✓ Gathered audit evidence\n"
                f"✓ Detected exceptions and anomalies\n"
                f"✓ Prepared audit responses\n\n"
                f"Audit review complete. No critical issues identified."
            )
        }
        
        return mock_responses.get(agent_name, f"{agent_name} Agent: Task processed successfully.")
    
    @classmethod
    async def call_llm_streaming(
        cls,
        prompt: str,
        plan_id: str,
        websocket_manager,
        agent_name: str = "Invoice"
    ) -> str:
        """
        Call LLM with streaming support, error handling, and retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            plan_id: Plan ID for WebSocket routing
            websocket_manager: WebSocket manager instance for sending messages
            agent_name: Name of the agent making the call
            
        Returns:
            str: Complete response from LLM
            
        Raises:
            LLMTimeoutError: If LLM call exceeds timeout
            LLMAuthError: If authentication fails
            LLMRateLimitError: If rate limit is exceeded after retries
            LLMNetworkError: If network error occurs
            LLMError: For other LLM errors
        """
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry attempt {attempt}/{max_retries} for {agent_name} Agent")
                
                return await cls._call_llm_streaming_internal(
                    prompt, plan_id, websocket_manager, agent_name
                )
                
            except LLMRateLimitError as e:
                if attempt < max_retries:
                    # Exponential backoff: 2s, 4s
                    delay = 2 ** (attempt + 1)
                    logger.warning(
                        f"⏳ Rate limit hit, retrying in {delay}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Rate limit exceeded after {max_retries} retries")
                    raise
            
            except (LLMTimeoutError, LLMAuthError, LLMNetworkError, LLMError) as e:
                # Don't retry these errors
                raise
    
    @classmethod
    async def _call_llm_streaming_internal(
        cls,
        prompt: str,
        plan_id: str,
        websocket_manager,
        agent_name: str
    ) -> str:
        """Internal method for LLM streaming call with error handling."""
        logger.info(
            f"🤖 {agent_name} Agent calling LLM (streaming mode) "
            f"[plan_id={plan_id}]"
        )
        
        # Truncate and sanitize prompt for logging (max 200 chars)
        prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
        prompt_preview = sanitize_for_logging(prompt_preview)
        logger.debug(
            f"Prompt ({len(prompt)} chars) [plan_id={plan_id}, agent={agent_name}]: "
            f"{prompt_preview}"
        )
        
        # Get LLM instance
        try:
            llm = cls.get_llm_instance()
        except ValueError as e:
            error_msg = f"LLM configuration error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise LLMError(error_msg) from e
        
        # Send stream start message
        await websocket_manager.send_message(plan_id, {
            "type": "agent_stream_start",
            "agent": agent_name,
            "plan_id": plan_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            # Collect full response
            full_response = ""
            start_time = asyncio.get_event_loop().time()
            timeout = cls._get_timeout()
            
            # Stream the response with timeout
            async def stream_with_timeout():
                nonlocal full_response
                async for chunk in llm.astream([HumanMessage(content=prompt)]):
                    # Extract content from chunk
                    if hasattr(chunk, 'content'):
                        token = chunk.content
                    else:
                        token = str(chunk)
                    
                    if token:
                        full_response += token
                        
                        # Send token via WebSocket
                        await websocket_manager.send_message(plan_id, {
                            "type": "agent_message_streaming",
                            "agent": agent_name,
                            "content": token,
                            "plan_id": plan_id
                        })
            
            # Execute with timeout
            try:
                await asyncio.wait_for(stream_with_timeout(), timeout=timeout)
            except asyncio.TimeoutError:
                error_msg = f"LLM call timed out after {timeout}s"
                logger.error(
                    f"❌ {error_msg} [plan_id={plan_id}, agent={agent_name}, "
                    f"timeout={timeout}s]"
                )
                
                # Send error via WebSocket
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_stream_end",
                    "agent": agent_name,
                    "plan_id": plan_id,
                    "error": True,
                    "error_message": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                raise LLMTimeoutError(error_msg)
            
            # Calculate completion time
            completion_time = asyncio.get_event_loop().time() - start_time
            
            # Send stream end message
            await websocket_manager.send_message(plan_id, {
                "type": "agent_stream_end",
                "agent": agent_name,
                "plan_id": plan_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(
                f"✅ {agent_name} Agent LLM call completed "
                f"[plan_id={plan_id}, duration={completion_time:.2f}s, "
                f"response_length={len(full_response)} chars]"
            )
            
            return full_response
            
        except LLMTimeoutError:
            # Already handled above
            raise
            
        except Exception as e:
            # Classify the error
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Check for authentication errors
            if "auth" in error_str or "401" in error_str or "api key" in error_str:
                error_msg = "Authentication failed. Please check your API key."
                logger.error(
                    f"❌ {error_msg} [plan_id={plan_id}, agent={agent_name}, "
                    f"error_type={error_type}]"
                )
                
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_stream_end",
                    "agent": agent_name,
                    "plan_id": plan_id,
                    "error": True,
                    "error_message": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                raise LLMAuthError(error_msg) from e
            
            # Check for rate limit errors
            elif "rate limit" in error_str or "429" in error_str or "quota" in error_str:
                error_msg = "Rate limit exceeded. Please try again later."
                logger.error(
                    f"❌ {error_msg} [plan_id={plan_id}, agent={agent_name}, "
                    f"error_type={error_type}]"
                )
                
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_stream_end",
                    "agent": agent_name,
                    "plan_id": plan_id,
                    "error": True,
                    "error_message": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                raise LLMRateLimitError(error_msg) from e
            
            # Check for network errors
            elif "connection" in error_str or "network" in error_str or "timeout" in error_str:
                error_msg = "Network error. Please check your connection."
                logger.error(
                    f"❌ {error_msg} [plan_id={plan_id}, agent={agent_name}, "
                    f"error_type={error_type}]"
                )
                
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_stream_end",
                    "agent": agent_name,
                    "plan_id": plan_id,
                    "error": True,
                    "error_message": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                raise LLMNetworkError(error_msg) from e
            
            # Generic error
            else:
                error_msg = f"LLM call failed: {error_type}"
                error_details = sanitize_for_logging(str(e))
                logger.error(
                    f"❌ {error_msg} [plan_id={plan_id}, agent={agent_name}, "
                    f"error_type={error_type}, details={error_details}]"
                )
                
                await websocket_manager.send_message(plan_id, {
                    "type": "agent_stream_end",
                    "agent": agent_name,
                    "plan_id": plan_id,
                    "error": True,
                    "error_message": "An error occurred while processing your request.",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                raise LLMError(error_msg) from e
    
    @classmethod
    def _get_timeout(cls) -> int:
        """Get configured timeout value."""
        return int(os.getenv("LLM_TIMEOUT", "60"))
    
    @classmethod
    def reset(cls):
        """Reset the LLM instance (useful for testing)."""
        cls._llm_instance = None
        cls._provider = None

