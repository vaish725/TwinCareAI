# TwinCare AI - Agent Communication Protocol

**Version:** 0.1.0  
**Date:** March 6, 2026  
**Status:** Complete

---

## Overview

This document defines the communication protocol between agents in the TwinCare AI multi-agent system, including message formats, error handling, and orchestration patterns.

---

## Communication Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                              │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │   Agent    │  │   Agent    │  │   Agent    │           │
│  │   Router   │  │   Queue    │  │   Logger   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└──────────────────────────────────────────────────────────────┘
           │                │                │
           ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │  Agent 1  │    │  Agent 2  │    │  Agent 3  │
    └───────────┘    └───────────┘    └───────────┘
```

---

## Message Format

### Base Message Structure

```python
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    NOTIFICATION = "notification"

class MessageStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMEOUT = "timeout"
    PENDING = "pending"

class AgentMessage(BaseModel):
    # Identity
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType
    
    # Routing
    sender_agent_id: str
    receiver_agent_id: str
    session_id: str
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    timeout_seconds: Optional[int] = 30
    
    # Payload
    payload: Dict[str, Any]
    
    # Context
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    status: MessageStatus = MessageStatus.PENDING
    
    # Tracing
    trace_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### Example Messages

#### 1. Context Intake Request

```json
{
  "message_id": "msg-001",
  "message_type": "request",
  "sender_agent_id": "orchestrator",
  "receiver_agent_id": "context_intake_agent",
  "session_id": "session-abc-123",
  "timestamp": "2026-03-06T10:00:00.000Z",
  "timeout_seconds": 5,
  "payload": {
    "sharp_context": {
      "patient_id": "synthetic-001",
      "fhir_server_url": "https://fhir.example.com/r4",
      "fhir_access_token": "bearer-token-redacted"
    },
    "request_type": "scenario_simulation"
  },
  "context": {
    "invocation_source": "prompt_opinion",
    "user_role": "clinician"
  },
  "metadata": {},
  "status": "pending",
  "trace_id": "trace-xyz-789",
  "parent_message_id": null
}
```

#### 2. Twin Builder Response

```json
{
  "message_id": "msg-002",
  "message_type": "response",
  "sender_agent_id": "clinical_state_builder_agent",
  "receiver_agent_id": "orchestrator",
  "session_id": "session-abc-123",
  "timestamp": "2026-03-06T10:00:02.567Z",
  "timeout_seconds": null,
  "payload": {
    "patient_twin": {
      "patient_id": "synthetic-001",
      "demographics": {"age": 56, "sex": "male"},
      "active_conditions": [...],
      "active_medications": [...],
      "recent_labs": [...],
      "recent_vitals": [...],
      "completeness_score": 0.85
    },
    "missing_data": ["lipid_panel", "recent_hba1c"]
  },
  "context": {
    "fhir_resources_fetched": 12,
    "processing_time_ms": 1567
  },
  "metadata": {
    "agent_version": "0.1.0",
    "confidence": 0.85
  },
  "status": "success",
  "trace_id": "trace-xyz-789",
  "parent_message_id": "msg-001"
}
```

#### 3. Error Message

```json
{
  "message_id": "msg-003",
  "message_type": "error",
  "sender_agent_id": "risk_projection_agent",
  "receiver_agent_id": "orchestrator",
  "session_id": "session-abc-123",
  "timestamp": "2026-03-06T10:00:05.789Z",
  "timeout_seconds": null,
  "payload": {
    "error_code": "INSUFFICIENT_DATA",
    "error_message": "Missing required lab values for risk calculation",
    "error_details": {
      "missing_fields": ["hba1c", "ldl_cholesterol"],
      "required_for": "cardiovascular_risk_projection"
    },
    "recoverable": false,
    "suggested_action": "Request additional data from FHIR server"
  },
  "context": {},
  "metadata": {
    "exception_type": "InsufficientDataError",
    "stack_trace": "..."
  },
  "status": "failed",
  "trace_id": "trace-xyz-789",
  "parent_message_id": "msg-002"
}
```

---

## Agent Interface

### Base Agent Class

```python
from abc import ABC, abstractmethod
from typing import Optional
import asyncio

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_id: str, timeout_seconds: int = 30):
        self.agent_id = agent_id
        self.timeout_seconds = timeout_seconds
        self.logger = setup_logger(agent_id)
    
    @abstractmethod
    async def process(self, message: AgentMessage) -> AgentMessage:
        """
        Process incoming message and return response
        
        Args:
            message: Incoming agent message
            
        Returns:
            Response message
            
        Raises:
            AgentError: On processing failure
            TimeoutError: On timeout
        """
        pass
    
    async def execute(self, message: AgentMessage) -> AgentMessage:
        """
        Execute agent with timeout and error handling
        """
        try:
            # Apply timeout
            response = await asyncio.wait_for(
                self.process(message),
                timeout=self.timeout_seconds
            )
            
            # Ensure response has correct routing
            response.sender_agent_id = self.agent_id
            response.receiver_agent_id = message.sender_agent_id
            response.session_id = message.session_id
            response.parent_message_id = message.message_id
            response.trace_id = message.trace_id
            
            return response
            
        except asyncio.TimeoutError:
            self.logger.error(f"Agent {self.agent_id} timed out after {self.timeout_seconds}s")
            return self._create_error_message(
                message,
                "TIMEOUT",
                f"Agent execution exceeded {self.timeout_seconds} seconds"
            )
            
        except Exception as e:
            self.logger.exception(f"Agent {self.agent_id} failed: {str(e)}")
            return self._create_error_message(
                message,
                "AGENT_ERROR",
                str(e)
            )
    
    def _create_error_message(
        self, 
        original_message: AgentMessage,
        error_code: str,
        error_message: str
    ) -> AgentMessage:
        """Create standardized error message"""
        return AgentMessage(
            message_type=MessageType.ERROR,
            sender_agent_id=self.agent_id,
            receiver_agent_id=original_message.sender_agent_id,
            session_id=original_message.session_id,
            payload={
                "error_code": error_code,
                "error_message": error_message,
                "recoverable": False
            },
            status=MessageStatus.FAILED,
            trace_id=original_message.trace_id,
            parent_message_id=original_message.message_id
        )
```

### Example Agent Implementation

```python
class RiskProjectionAgent(BaseAgent):
    """Agent for projecting risk outcomes"""
    
    def __init__(self):
        super().__init__(
            agent_id="risk_projection_agent",
            timeout_seconds=15
        )
    
    async def process(self, message: AgentMessage) -> AgentMessage:
        """Process risk projection request"""
        
        # Extract input from payload
        twin_state = message.payload.get("patient_twin")
        scenario = message.payload.get("scenario")
        
        # Validate inputs
        if not twin_state or not scenario:
            raise ValueError("Missing required inputs: patient_twin or scenario")
        
        # Run risk projection logic
        projection = await self._calculate_risk_projection(twin_state, scenario)
        
        # Return response
        return AgentMessage(
            message_type=MessageType.RESPONSE,
            sender_agent_id=self.agent_id,
            receiver_agent_id=message.sender_agent_id,
            session_id=message.session_id,
            payload={
                "risk_projection": projection,
                "confidence": projection["confidence"],
                "rationale": projection["rationale"]
            },
            status=MessageStatus.SUCCESS,
            trace_id=message.trace_id,
            parent_message_id=message.message_id
        )
    
    async def _calculate_risk_projection(self, twin, scenario):
        """Internal risk calculation logic"""
        # Implementation details...
        pass
```

---

## Orchestration Patterns

### 1. Sequential Orchestration

```python
class SequentialOrchestrator:
    """Execute agents in sequence"""
    
    async def orchestrate(
        self,
        agents: List[BaseAgent],
        initial_message: AgentMessage
    ) -> List[AgentMessage]:
        """
        Run agents sequentially, passing output to next input
        """
        responses = []
        current_message = initial_message
        
        for agent in agents:
            # Send message to agent
            response = await agent.execute(current_message)
            responses.append(response)
            
            # Check for errors
            if response.status == MessageStatus.FAILED:
                self.logger.error(f"Agent {agent.agent_id} failed, stopping chain")
                break
            
            # Prepare next message (use response as input for next agent)
            current_message = self._prepare_next_message(response, current_message)
        
        return responses
    
    def _prepare_next_message(
        self, 
        response: AgentMessage,
        original: AgentMessage
    ) -> AgentMessage:
        """Transform response into next agent's input"""
        return AgentMessage(
            message_type=MessageType.REQUEST,
            sender_agent_id="orchestrator",
            receiver_agent_id="next_agent",  # Set appropriately
            session_id=original.session_id,
            payload=response.payload,  # Pass response as next input
            trace_id=original.trace_id
        )
```

### 2. Parallel Orchestration

```python
class ParallelOrchestrator:
    """Execute agents in parallel"""
    
    async def orchestrate(
        self,
        agents: List[BaseAgent],
        messages: List[AgentMessage]
    ) -> List[AgentMessage]:
        """
        Run agents in parallel and collect results
        """
        # Create tasks for all agents
        tasks = [
            agent.execute(message)
            for agent, message in zip(agents, messages)
        ]
        
        # Execute in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # Convert exception to error message
                self.logger.error(f"Agent {agents[i].agent_id} raised exception: {response}")
                results.append(self._create_error_response(agents[i], messages[i], response))
            else:
                results.append(response)
        
        return results
    
    def _create_error_response(
        self,
        agent: BaseAgent,
        message: AgentMessage,
        exception: Exception
    ) -> AgentMessage:
        """Create error message from exception"""
        return AgentMessage(
            message_type=MessageType.ERROR,
            sender_agent_id=agent.agent_id,
            receiver_agent_id=message.sender_agent_id,
            session_id=message.session_id,
            payload={
                "error_code": "EXCEPTION",
                "error_message": str(exception),
                "exception_type": type(exception).__name__
            },
            status=MessageStatus.FAILED,
            trace_id=message.trace_id,
            parent_message_id=message.message_id
        )
```

### 3. Conditional Orchestration

```python
class ConditionalOrchestrator:
    """Execute agents based on conditions"""
    
    async def orchestrate(
        self,
        agents: Dict[str, BaseAgent],
        initial_message: AgentMessage,
        routing_logic: Callable
    ) -> List[AgentMessage]:
        """
        Route messages to agents based on custom logic
        """
        responses = []
        current_message = initial_message
        
        while True:
            # Determine next agent
            next_agent_id = routing_logic(current_message, responses)
            
            if not next_agent_id:
                break  # Orchestration complete
            
            # Execute agent
            agent = agents.get(next_agent_id)
            if not agent:
                self.logger.error(f"Agent {next_agent_id} not found")
                break
            
            response = await agent.execute(current_message)
            responses.append(response)
            
            # Prepare for next iteration
            current_message = self._transform_message(response)
        
        return responses
```

---

## Error Handling Protocol

### Error Categories

```python
class ErrorCategory(str, Enum):
    VALIDATION_ERROR = "validation_error"        # Invalid input
    INSUFFICIENT_DATA = "insufficient_data"      # Missing required data
    TIMEOUT = "timeout"                          # Agent timed out
    AGENT_ERROR = "agent_error"                  # Internal agent failure
    EXTERNAL_SERVICE_ERROR = "external_service_error"  # FHIR/LLM failure
    SAFETY_VIOLATION = "safety_violation"        # Safety check failed
```

### Error Response Format

```python
class AgentError(BaseModel):
    error_code: str
    error_message: str
    error_category: ErrorCategory
    recoverable: bool
    retry_possible: bool
    suggested_action: Optional[str]
    error_details: Dict[str, Any] = Field(default_factory=dict)
```

### Error Handling Strategy

```python
async def handle_agent_error(
    error_message: AgentMessage,
    retry_count: int = 0,
    max_retries: int = 3
) -> Optional[AgentMessage]:
    """
    Handle agent errors with retry logic
    """
    error = error_message.payload
    
    # Check if error is recoverable
    if not error.get("recoverable", False):
        logger.error(f"Non-recoverable error: {error['error_code']}")
        return None
    
    # Check retry limit
    if retry_count >= max_retries:
        logger.error(f"Max retries ({max_retries}) exceeded")
        return None
    
    # Determine retry strategy
    if error.get("error_category") == ErrorCategory.TIMEOUT:
        # Wait before retry
        await asyncio.sleep(2 ** retry_count)  # Exponential backoff
        return error_message  # Retry same message
    
    elif error.get("error_category") == ErrorCategory.INSUFFICIENT_DATA:
        # Try to fetch missing data
        missing_data = error.get("error_details", {}).get("missing_fields", [])
        # ... attempt to fetch missing data ...
        return None  # Cannot automatically recover
    
    else:
        # Default: no retry
        return None
```

---

## Retry and Timeout Configuration

### Agent-Specific Timeouts

```python
AGENT_TIMEOUTS = {
    "context_intake_agent": 5,
    "clinical_state_builder_agent": 10,
    "scenario_generator_agent": 8,
    "risk_projection_agent": 15,
    "medication_impact_agent": 10,
    "guideline_alignment_agent": 10,
    "safety_guardrail_agent": 5,
    "explanation_agent": 8,
    "consensus_agent": 10
}
```

### Retry Configuration

```python
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay_seconds": 2,
    "exponential_backoff": True,
    "retry_on_timeout": True,
    "retry_on_errors": [
        "EXTERNAL_SERVICE_ERROR",
        "TIMEOUT"
    ],
    "no_retry_on_errors": [
        "VALIDATION_ERROR",
        "SAFETY_VIOLATION",
        "INSUFFICIENT_DATA"
    ]
}
```

### Timeout Handler

```python
async def execute_with_timeout_and_retry(
    agent: BaseAgent,
    message: AgentMessage,
    config: dict = RETRY_CONFIG
) -> AgentMessage:
    """
    Execute agent with timeout and retry logic
    """
    retry_count = 0
    last_error = None
    
    while retry_count <= config["max_retries"]:
        try:
            # Execute with timeout
            response = await asyncio.wait_for(
                agent.process(message),
                timeout=AGENT_TIMEOUTS.get(agent.agent_id, 30)
            )
            
            # Success
            return response
            
        except asyncio.TimeoutError as e:
            last_error = e
            if not config["retry_on_timeout"]:
                raise
            
            logger.warning(
                f"Agent {agent.agent_id} timed out (attempt {retry_count + 1})"
            )
            
        except Exception as e:
            last_error = e
            logger.error(f"Agent {agent.agent_id} error: {str(e)}")
            
            # Check if error is retryable
            if not _is_retryable_error(e, config):
                raise
        
        # Increment retry counter
        retry_count += 1
        
        # Wait before retry (exponential backoff)
        if config["exponential_backoff"]:
            delay = config["retry_delay_seconds"] * (2 ** (retry_count - 1))
        else:
            delay = config["retry_delay_seconds"]
        
        await asyncio.sleep(delay)
    
    # Max retries exceeded
    raise RuntimeError(
        f"Agent {agent.agent_id} failed after {config['max_retries']} retries. "
        f"Last error: {str(last_error)}"
    )

def _is_retryable_error(error: Exception, config: dict) -> bool:
    """Check if error should trigger retry"""
    error_type = type(error).__name__
    
    if error_type in config.get("no_retry_on_errors", []):
        return False
    
    if error_type in config.get("retry_on_errors", []):
        return True
    
    return False  # Default: no retry
```

---

## Message Tracing

### Trace Context

```python
class TraceContext:
    """Context for distributed tracing"""
    
    def __init__(self, session_id: str):
        self.trace_id = str(uuid.uuid4())
        self.session_id = session_id
        self.spans: List[TraceSpan] = []
    
    def start_span(self, agent_id: str, message_id: str) -> "TraceSpan":
        """Start new span for agent execution"""
        span = TraceSpan(
            span_id=str(uuid.uuid4()),
            trace_id=self.trace_id,
            agent_id=agent_id,
            message_id=message_id,
            start_time=datetime.utcnow()
        )
        self.spans.append(span)
        return span

class TraceSpan:
    """Individual span in trace"""
    
    def __init__(
        self,
        span_id: str,
        trace_id: str,
        agent_id: str,
        message_id: str,
        start_time: datetime
    ):
        self.span_id = span_id
        self.trace_id = trace_id
        self.agent_id = agent_id
        self.message_id = message_id
        self.start_time = start_time
        self.end_time: Optional[datetime] = None
        self.duration_ms: Optional[int] = None
        self.status: str = "in_progress"
        self.metadata: Dict[str, Any] = {}
    
    def end(self, status: str = "success"):
        """End span"""
        self.end_time = datetime.utcnow()
        self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)
        self.status = status
```

---

## Communication Best Practices

### 1. Message Immutability
- Messages should be immutable once sent
- Create new messages for responses

### 2. Explicit Routing
- Always set sender_agent_id and receiver_agent_id
- Use orchestrator as intermediary when needed

### 3. Timeout Management
- Set appropriate timeouts per agent
- Use exponential backoff for retries

### 4. Error Propagation
- Always return error messages, don't raise exceptions across agent boundaries
- Include actionable error details

### 5. Tracing
- Maintain trace_id across all messages in a session
- Link messages via parent_message_id

### 6. Payload Validation
- Validate payload structure in each agent
- Use Pydantic models for type safety

---

**Document Status:** Complete  
**Next Review:** March 12, 2026
