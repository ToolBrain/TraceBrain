"""
TraceBrain Tracing SDK - Client

This module provides a robust client for interacting with the TraceBrain Tracing API.
It includes automatic retries, connection pooling, and fail-safe error handling.

Usage:
    from tracebrain import TraceClient
    
    # Initialize client
    client = TraceClient(base_url="http://localhost:8000")
    
    # Send a trace
    trace_data = {
        "trace_id": "abc123",
        "attributes": {"system_prompt": "You are helpful"},
        "spans": [...]
    }
    success = client.log_trace(trace_data)
    
    # Check health
    if client.health_check():
        print("TraceStore is reachable")
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from tracebrain.core.schema import TraceBrainAttributes, SpanType

# Configure logger for this module
logger = logging.getLogger(__name__)


class TraceClient:
    """
    Robust HTTP client for TraceBrain Tracing API.
    
    Features:
    - Connection pooling via requests.Session
    - Automatic retries on network errors and 5xx status codes
    - Fail-safe design: errors are logged but don't crash the application
    - Optional API key authentication
    
    Attributes:
        base_url (str): Base URL of the TraceStore API
        api_key (Optional[str]): Optional API key for authentication
        session (requests.Session): Persistent HTTP session with retry logic
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_on_post: bool = True
    ):
        """
        Initialize the TraceClient with retry strategy and session pooling.
        
        Args:
            base_url: Base URL of the TraceStore API (default: http://localhost:8000)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
        
        Example:
            client = TraceClient(
                base_url="http://tracestore.company.com",
                api_key="secret-key-123",
                timeout=60,
                max_retries=5
            )
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # Initialize requests session for connection pooling
        self.session = requests.Session()
        
        # Configure retry strategy
        # Retry on:
        # - Connection errors (network issues)
        # - 500, 502, 503, 504 (server errors)
        # - 429 (rate limiting - with backoff)
        allowed_methods = ["HEAD", "GET", "PUT", "DELETE", "OPTIONS"]
        if retry_on_post:
            allowed_methods.append("POST")

        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(allowed_methods),
            backoff_factor=1,  # Wait 1s, 2s, 4s between retries
            raise_on_status=False,  # Don't raise exceptions, we handle them manually
            respect_retry_after_header=True
        )
        
        # Mount retry adapter for both HTTP and HTTPS
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "TraceBrain-Tracing-SDK/1.0.0"
        })
        
        # Add API key if provided
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
        
        logger.info(f"TraceClient initialized for {self.base_url}")
    
    def _make_url(self, path: str) -> str:
        """
        Construct full URL from base URL and path.
        
        Args:
            path: API endpoint path (e.g., "/api/v1/traces")
        
        Returns:
            str: Full URL
        """
        return urljoin(self.base_url + '/', path.lstrip('/'))
    
    def log_trace(self, trace_data: Dict[str, Any]) -> bool:
        """
        Send a trace to the TraceStore API.
        
        This method implements a fail-safe design: if the trace cannot be sent,
        it logs the error but returns False instead of raising an exception.
        This ensures that observability failures don't crash the main application.
        
        Args:
            trace_data: Dictionary containing the trace data conforming to
                       TraceBrain Standard OTLP Trace Schema
        
        Returns:
            bool: True if trace was successfully logged, False otherwise
        
        Example:
            trace_data = {
                "trace_id": "a1b2c3d4e5f6a7b8",
                "attributes": {
                    "system_prompt": "You are a helpful assistant.",
                    "tracebrain.episode.id": "episode_123"
                },
                "spans": [
                    {
                        "span_id": "00f067aa0ba902b7",
                        "parent_id": None,
                        "name": "LLM Inference",
                        "start_time": "2025-10-27T10:30:01.123Z",
                        "end_time": "2025-10-27T10:30:02.234Z",
                        "attributes": {
                            "tracebrain.span.type": "llm_inference",
                            "tracebrain.llm.thought": "I need to calculate this"
                        }
                    }
                ]
            }
            
            success = client.log_trace(trace_data)
            if not success:
                print("Failed to log trace, but application continues")
        """
        url = self._make_url("/api/v1/traces")
        
        try:
            headers = {}
            if trace_data.get("trace_id"):
                headers["Idempotency-Key"] = trace_data["trace_id"]

            response = self.session.post(
                url,
                json=trace_data,
                timeout=self.timeout,
                headers=headers or None
            )
            
            # Check if request was successful
            if response.status_code in (200, 201):
                logger.debug(f"Trace logged successfully: {trace_data.get('trace_id', 'unknown')}")
                return True
            if response.status_code == 409:
                logger.info("Trace already exists (idempotent): %s", trace_data.get("trace_id", "unknown"))
                return True
            else:
                # Log the error but don't crash
                logger.warning(
                    f"Failed to log trace. Status: {response.status_code}, "
                    f"Response: {response.text[:200]}"
                )
                return False
                
        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout while logging trace to {url}. "
                f"The TraceStore may be slow or unreachable."
            )
            return False
            
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Connection error while logging trace to {url}. "
                f"Is the TraceStore running? Error: {str(e)}"
            )
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Unexpected error while logging trace: {str(e)}"
            )
            return False
            
        except Exception as e:
            # Catch-all for any other errors (JSON serialization, etc.)
            logger.error(
                f"Critical error in log_trace: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            return False
    
    def health_check(self) -> bool:
        """
        Check if the TraceStore API is reachable and healthy.
        
        This method attempts to connect to the API's health endpoint
        and verify that it responds successfully.
        
        Returns:
            bool: True if the API is healthy and reachable, False otherwise
        
        Example:
            client = TraceClient()
            
            if client.health_check():
                print("TraceStore is ready")
            else:
                print("TraceStore is not reachable")
        """
        # Try multiple health check endpoints
        endpoints = [
            "/api/v1/health",
            "/healthz",
            "/"
        ]
        
        for endpoint in endpoints:
            url = self._make_url(endpoint)
            
            try:
                response = self.session.get(url, timeout=5)
                
                if response.status_code == 200:
                    logger.info(f"TraceStore is healthy at {self.base_url}")
                    return True
                    
            except requests.exceptions.RequestException:
                # Try next endpoint
                continue
        
        logger.warning(f"TraceStore health check failed at {self.base_url}")
        return False
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a trace by its ID.
        
        Args:
            trace_id: The unique identifier of the trace
        
        Returns:
            Optional[Dict]: Trace data if found, None otherwise
        
        Example:
            trace = client.get_trace("a1b2c3d4e5f6a7b8")
            if trace:
                print(f"Found trace with {len(trace['spans'])} spans")
        """
        url = self._make_url(f"/api/v1/traces/{trace_id}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Trace {trace_id} not found")
                return None
            else:
                logger.error(f"Failed to get trace {trace_id}: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting trace {trace_id}: {str(e)}")
            return None
    
    def list_traces(self, skip: int = 0, limit: int = 20) -> Optional[Dict[str, Any]]:
        """
        List traces with pagination.
        
        Args:
            skip: Number of traces to skip (default: 0)
            limit: Maximum number of traces to return (default: 20)
        
        Returns:
            Optional[Dict]: Response containing traces list and metadata, or None on error
        
        Example:
            result = client.list_traces(skip=0, limit=10)
            if result:
                print(f"Found {result['total']} traces")
                for trace in result['traces']:
                    print(f"  - {trace['trace_id']}")
        """
        url = self._make_url(f"/api/v1/traces?skip={skip}&limit={limit}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to list traces: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing traces: {str(e)}")
            return None
    
    def add_feedback(
        self,
        trace_id: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add feedback to a trace.
        
        Args:
            trace_id: The unique identifier of the trace
            rating: Rating from 1-5 (optional)
            comment: Text feedback (optional)
            tags: List of tags (optional)
            metadata: Additional metadata (optional)
        
        Returns:
            bool: True if feedback was added successfully, False otherwise
        
        Example:
            success = client.add_feedback(
                trace_id="abc123",
                rating=5,
                comment="Excellent reasoning!",
                tags=["high-quality", "approved"]
            )
        """
        url = self._make_url(f"/api/v1/traces/{trace_id}/feedback")
        
        feedback_data = {}
        if rating is not None:
            feedback_data["rating"] = rating
        if comment is not None:
            feedback_data["comment"] = comment
        if tags is not None:
            feedback_data["tags"] = tags
        if metadata is not None:
            feedback_data["metadata"] = metadata
        
        try:
            response = self.session.post(
                url,
                json=feedback_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Feedback added to trace {trace_id}")
                return True
            else:
                logger.error(f"Failed to add feedback: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding feedback: {str(e)}")
            return False

    def export_traces(
        self,
        min_rating: int = 4,
        limit: int = 100,
        as_jsonl: bool = False,
    ) -> Optional[Any]:
        """Export high-quality traces from the API."""
        url = self._make_url("/api/v1/export/traces")
        params = {"min_rating": min_rating, "limit": limit}
        if as_jsonl:
            params["format"] = "jsonl"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            if response.status_code != 200:
                logger.error(f"Failed to export traces: {response.status_code}")
                return None
            return response.text if as_jsonl else response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exporting traces: {str(e)}")
            return None
    
    def close(self):
        """
        Close the HTTP session and release resources.
        
        Call this when you're done using the client to clean up connections.
        
        Example:
            client = TraceClient()
            try:
                client.log_trace(trace_data)
            finally:
                client.close()
        """
        self.session.close()
        logger.info("TraceClient session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically closes session."""
        self.close()
        return False
    
    def __repr__(self) -> str:
        """String representation of the client."""
        return f"TraceClient(base_url='{self.base_url}')"

    @staticmethod
    def _parse_iso(timestamp: Optional[str]) -> Optional[datetime]:
        if not timestamp:
            return None
        try:
            if timestamp.endswith("Z"):
                timestamp = timestamp.replace("Z", "+00:00")
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return None

    @staticmethod
    def _normalize_messages(raw) -> List[Dict[str, str]]:
        if raw is None:
            return []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                return []
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list):
            return []

        messages: List[Dict[str, str]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role and content:
                messages.append({"role": str(role), "content": str(content)})
        return messages

    @staticmethod
    def to_messages(trace_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Reconstruct ChatML messages from a raw OTLP trace."""
        messages: List[Dict[str, str]] = []
        attributes = trace_data.get("attributes") or {}
        system_prompt = attributes.get(TraceBrainAttributes.SYSTEM_PROMPT) or attributes.get("system_prompt")
        if system_prompt:
            messages.append({"role": "system", "content": str(system_prompt)})

        spans = trace_data.get("spans") or []
        spans_sorted = sorted(
            spans,
            key=lambda span: TraceClient._parse_iso(span.get("start_time")) or datetime.min,
        )
        for span in spans_sorted:
            attrs = span.get("attributes") or {}
            if attrs.get(TraceBrainAttributes.SPAN_TYPE) != SpanType.LLM_INFERENCE:
                continue
            new_content = attrs.get(TraceBrainAttributes.LLM_NEW_CONTENT)
            messages.extend(TraceClient._normalize_messages(new_content))

        return messages

    @staticmethod
    def to_turns(trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Reconstruct TraceBrain turns from a raw OTLP trace."""
        turns: List[Dict[str, Any]] = []
        messages: List[Dict[str, str]] = []

        attributes = trace_data.get("attributes") or {}
        system_prompt = attributes.get(TraceBrainAttributes.SYSTEM_PROMPT) or attributes.get("system_prompt")
        if system_prompt:
            messages.append({"role": "system", "content": str(system_prompt)})

        spans = trace_data.get("spans") or []
        spans_sorted = sorted(
            spans,
            key=lambda span: TraceClient._parse_iso(span.get("start_time")) or datetime.min,
        )

        tool_outputs: Dict[str, Any] = {}
        for span in spans_sorted:
            attrs = span.get("attributes") or {}
            if attrs.get(TraceBrainAttributes.SPAN_TYPE) == SpanType.TOOL_EXECUTION:
                parent_id = span.get("parent_id")
                if parent_id:
                    tool_outputs[parent_id] = attrs.get(TraceBrainAttributes.TOOL_OUTPUT)

        for span in spans_sorted:
            attrs = span.get("attributes") or {}
            if attrs.get(TraceBrainAttributes.SPAN_TYPE) != SpanType.LLM_INFERENCE:
                continue

            new_content = attrs.get(TraceBrainAttributes.LLM_NEW_CONTENT)
            new_messages = TraceClient._normalize_messages(new_content)
            if new_messages:
                messages.extend(new_messages)

            turn = {
                "prompt_for_model": [dict(item) for item in messages],
                "model_completion": attrs.get(TraceBrainAttributes.LLM_COMPLETION),
                "thought": attrs.get(TraceBrainAttributes.LLM_THOUGHT),
                "tool_code": attrs.get(TraceBrainAttributes.LLM_TOOL_CODE),
                "tool_output": tool_outputs.get(span.get("span_id")),
            }
            turns.append(turn)

        return turns

    @staticmethod
    def to_tracebrain_turns(trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format turns for TraceBrain 1.0 compatibility."""
        turns = TraceClient.to_turns(trace_data)
        formatted = []
        for turn in turns:
            formatted.append(
                {
                    "prompt_for_model": turn.get("prompt_for_model"),
                    "model_completion": turn.get("model_completion"),
                    "thought": turn.get("thought"),
                    "tool_code": turn.get("tool_code"),
                    "tool_output": turn.get("tool_output"),
                    "prompt": turn.get("prompt_for_model"),
                    "completion": turn.get("model_completion"),
                }
            )
        return formatted
