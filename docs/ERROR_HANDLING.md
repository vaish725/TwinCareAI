# TwinCare AI - Error Handling Strategy

**Version:** 0.1.0  
**Date:** March 6, 2026  
**Status:** Complete

---

## Overview

This document defines a comprehensive error handling strategy for TwinCare AI, covering error classification, handling patterns, user communication, and recovery mechanisms.

---

## Error Classification

### Error Hierarchy

```
AgentError (Base)
├── ValidationError
│   ├── InvalidInputError
│   ├── MissingRequiredFieldError
│   └── SchemaValidationError
├── DataError
│   ├── InsufficientDataError
│   ├── StaleDataError
│   └── DataQualityError
├── ExecutionError
│   ├── TimeoutError
│   ├── AgentFailureError
│   └── OrchestrationError
├── ExternalServiceError
│   ├── FHIRServerError
│   ├── LLMServiceError
│   └── DatabaseError
├── SafetyError
│   ├── SafetyViolationError
│   ├── UnsupportedScenarioError
│   └── ConfidenceTooLowError
└── AuthorizationError
    ├── InvalidTokenError
    ├── ExpiredTokenError
    └── InsufficientPermissionsError
```

---

## Error Code System

### Format: `CATEGORY-COMPONENT-NUMBER`

**Example:** `VAL-INPUT-001`
- **VAL** = Validation Error
- **INPUT** = Input validation component
- **001** = Specific error code

### Error Code Registry

```python
class ErrorCode(str, Enum):
    # Validation Errors (VAL-xxx-xxx)
    VAL_INPUT_001 = "VAL-INPUT-001"  # Missing required field
    VAL_INPUT_002 = "VAL-INPUT-002"  # Invalid field format
    VAL_SHARP_001 = "VAL-SHARP-001"  # Invalid SHARP context
    VAL_SHARP_002 = "VAL-SHARP-002"  # Missing patient ID
    
    # Data Errors (DATA-xxx-xxx)
    DATA_INSUF_001 = "DATA-INSUF-001"  # Insufficient data for simulation
    DATA_INSUF_002 = "DATA-INSUF-002"  # Missing critical lab values
    DATA_STALE_001 = "DATA-STALE-001"  # Data too old
    DATA_QUAL_001 = "DATA-QUAL-001"   # Data quality issue
    
    # Execution Errors (EXEC-xxx-xxx)
    EXEC_TIMEOUT_001 = "EXEC-TIMEOUT-001"  # Agent timeout
    EXEC_AGENT_001 = "EXEC-AGENT-001"      # Agent execution failure
    EXEC_ORCH_001 = "EXEC-ORCH-001"        # Orchestration failure
    
    # External Service Errors (EXT-xxx-xxx)
    EXT_FHIR_001 = "EXT-FHIR-001"    # FHIR server unreachable
    EXT_FHIR_002 = "EXT-FHIR-002"    # FHIR patient not found
    EXT_FHIR_003 = "EXT-FHIR-003"    # FHIR authentication failed
    EXT_LLM_001 = "EXT-LLM-001"      # LLM service error
    EXT_DB_001 = "EXT-DB-001"        # Database error
    
    # Safety Errors (SAFE-xxx-xxx)
    SAFE_VIOLATION_001 = "SAFE-VIOLATION-001"  # Unsafe output detected
    SAFE_UNSUP_001 = "SAFE-UNSUP-001"          # Unsupported scenario
    SAFE_CONF_001 = "SAFE-CONF-001"            # Confidence too low
    
    # Authorization Errors (AUTH-xxx-xxx)
    AUTH_TOKEN_001 = "AUTH-TOKEN-001"  # Invalid token
    AUTH_TOKEN_002 = "AUTH-TOKEN-002"  # Expired token
    AUTH_PERM_001 = "AUTH-PERM-001"    # Insufficient permissions
```

---

## Error Response Format

### Standard Error Response

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ErrorResponse(BaseModel):
    """Standard error response format"""
    
    # Error identification
    error_code: str
    error_message: str
    error_category: str
    
    # Recovery information
    recoverable: bool = False
    retry_possible: bool = False
    suggested_action: Optional[str] = None
    
    # Details
    error_details: Dict[str, Any] = {}
    affected_component: Optional[str] = None
    
    # User-facing information
    user_message: str
    technical_message: str
    
    # Context
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    timestamp: str
    
    # Documentation
    documentation_url: Optional[str] = None
    support_contact: Optional[str] = None
```

### Example Error Responses

#### 1. Insufficient Data Error

```json
{
  "error_code": "DATA-INSUF-001",
  "error_message": "Insufficient data for cardiovascular risk simulation",
  "error_category": "data_error",
  "recoverable": false,
  "retry_possible": false,
  "suggested_action": "Request recent lipid panel and HbA1c from patient's provider",
  "error_details": {
    "missing_fields": ["ldl_cholesterol", "hdl_cholesterol", "hba1c"],
    "required_for": "cardiovascular_risk_projection",
    "last_available": {
      "ldl_cholesterol": "2025-06-15",
      "hba1c": null
    }
  },
  "affected_component": "risk_projection_agent",
  "user_message": "We need more recent lab results to provide accurate risk projections. Please ensure the patient has recent cholesterol and diabetes tests.",
  "technical_message": "Risk Projection Agent requires LDL, HDL, and HbA1c values from the last 6 months. Current data is incomplete or stale.",
  "session_id": "session-abc-123",
  "trace_id": "trace-xyz-789",
  "timestamp": "2026-03-06T10:00:05.234Z",
  "documentation_url": "https://docs.twincare-ai.com/errors/DATA-INSUF-001",
  "support_contact": "support@twincare-ai.com"
}
```

#### 2. FHIR Server Error

```json
{
  "error_code": "EXT-FHIR-001",
  "error_message": "FHIR server unreachable",
  "error_category": "external_service_error",
  "recoverable": true,
  "retry_possible": true,
  "suggested_action": "Retry request after a few seconds",
  "error_details": {
    "fhir_server_url": "https://fhir.example.com/r4",
    "http_status": 503,
    "error_type": "ServiceUnavailable",
    "retry_after_seconds": 30
  },
  "affected_component": "fhir_client_service",
  "user_message": "The healthcare data server is temporarily unavailable. Please try again in a moment.",
  "technical_message": "FHIR server at https://fhir.example.com/r4 returned 503 Service Unavailable. Connection timeout after 5000ms.",
  "session_id": "session-abc-123",
  "trace_id": "trace-xyz-789",
  "timestamp": "2026-03-06T10:00:01.567Z",
  "documentation_url": "https://docs.twincare-ai.com/errors/EXT-FHIR-001",
  "support_contact": "support@twincare-ai.com"
}
```

#### 3. Safety Violation

```json
{
  "error_code": "SAFE-VIOLATION-001",
  "error_message": "Safety guardrail triggered: output contains unsafe treatment directive",
  "error_category": "safety_error",
  "recoverable": false,
  "retry_possible": false,
  "suggested_action": "Review scenario parameters and ensure compliance with safety guidelines",
  "error_details": {
    "violation_type": "definitive_treatment_directive",
    "detected_phrase": "patient should start...",
    "safety_rule_violated": "no_autonomous_prescriptions",
    "confidence_downgraded_to": 0.0
  },
  "affected_component": "safety_guardrail_agent",
  "user_message": "This simulation result was blocked due to safety concerns. The system cannot provide definitive treatment recommendations.",
  "technical_message": "Safety Guardrail Agent detected prohibited language in output. Rule 'no_autonomous_prescriptions' violated. Output blocked.",
  "session_id": "session-abc-123",
  "trace_id": "trace-xyz-789",
  "timestamp": "2026-03-06T10:00:10.123Z",
  "documentation_url": "https://docs.twincare-ai.com/errors/SAFE-VIOLATION-001",
  "support_contact": "support@twincare-ai.com"
}
```

---

## Error Handling Patterns

### Pattern 1: Fail Fast (Non-Recoverable)

```python
async def handle_validation_error(error: ValidationError):
    """
    Validation errors should fail immediately
    No retry, no fallback
    """
    logger.error(f"Validation error: {error.message}")
    
    return ErrorResponse(
        error_code=error.code,
        error_message=error.message,
        error_category="validation_error",
        recoverable=False,
        retry_possible=False,
        user_message="Invalid input provided. Please check your request and try again.",
        technical_message=error.details,
        timestamp=datetime.utcnow().isoformat()
    )
```

### Pattern 2: Retry with Exponential Backoff

```python
async def handle_external_service_error(
    error: ExternalServiceError,
    retry_count: int = 0,
    max_retries: int = 3
):
    """
    External service errors should retry with backoff
    """
    if retry_count >= max_retries:
        logger.error(f"Max retries exceeded for {error.service_name}")
        return ErrorResponse(
            error_code=error.code,
            error_message=f"{error.service_name} failed after {max_retries} attempts",
            error_category="external_service_error",
            recoverable=False,
            retry_possible=False,
            user_message="An external service is currently unavailable. Please try again later.",
            technical_message=f"Service: {error.service_name}, Attempts: {retry_count}",
            timestamp=datetime.utcnow().isoformat()
        )
    
    # Calculate backoff delay
    delay = 2 ** retry_count  # Exponential: 1, 2, 4, 8...
    logger.warning(f"Retrying {error.service_name} in {delay}s (attempt {retry_count + 1})")
    
    await asyncio.sleep(delay)
    
    # Retry operation...
    # (return to caller for retry logic)
```

### Pattern 3: Graceful Degradation

```python
async def handle_insufficient_data(
    error: InsufficientDataError,
    partial_results: Optional[Dict] = None
):
    """
    Insufficient data errors should return partial results with warnings
    """
    if partial_results and error.can_continue_with_partial:
        logger.warning(f"Continuing with partial data: {error.missing_fields}")
        
        return {
            "status": "partial_success",
            "results": partial_results,
            "warnings": [
                {
                    "type": "insufficient_data",
                    "message": error.message,
                    "missing_fields": error.missing_fields,
                    "impact": error.impact_description
                }
            ],
            "confidence_level": "low",
            "recommendation": "Results may be incomplete. Consider requesting additional data."
        }
    else:
        # Cannot continue, return error
        return ErrorResponse(
            error_code="DATA-INSUF-001",
            error_message=error.message,
            error_category="data_error",
            recoverable=False,
            retry_possible=False,
            suggested_action=f"Please provide: {', '.join(error.missing_fields)}",
            user_message="Insufficient data to complete simulation.",
            technical_message=f"Missing: {error.missing_fields}",
            timestamp=datetime.utcnow().isoformat()
        )
```

### Pattern 4: Circuit Breaker

```python
class CircuitBreaker:
    """
    Circuit breaker pattern for external services
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_attempts: int = 1
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_attempts = half_open_attempts
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is open. Last failure: {self.last_failure_time}"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Reset failure count on success"""
        self.failure_count = 0
        if self.state == "half_open":
            self.state = "closed"
    
    def _on_failure(self):
        """Increment failure count"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if timeout period has elapsed"""
        if not self.last_failure_time:
            return False
        
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout_seconds
```

---

## User-Facing Error Messages

### Principles

1. **Be Clear:** Explain what went wrong in simple terms
2. **Be Helpful:** Suggest what the user can do
3. **Be Honest:** Don't hide errors or make false promises
4. **Be Professional:** Maintain clinical safety tone

### Message Templates

```python
USER_ERROR_MESSAGES = {
    "DATA-INSUF-001": {
        "title": "Incomplete Patient Data",
        "message": "We need more information to provide accurate simulations.",
        "action": "Please ensure recent lab results are available in the patient's record.",
        "severity": "warning"
    },
    "EXT-FHIR-001": {
        "title": "Healthcare Data Temporarily Unavailable",
        "message": "The patient data system is temporarily unavailable.",
        "action": "Please try again in a few moments.",
        "severity": "error"
    },
    "SAFE-VIOLATION-001": {
        "title": "Safety Check Failed",
        "message": "This simulation was blocked due to safety guidelines.",
        "action": "Results cannot be displayed. Please review scenario parameters.",
        "severity": "critical"
    },
    "EXEC-TIMEOUT-001": {
        "title": "Simulation Timeout",
        "message": "The simulation took too long to complete.",
        "action": "Please try again. If the problem persists, try a simpler scenario.",
        "severity": "warning"
    }
}
```

---

## Logging Strategy

### Log Levels

```python
# ERROR: System failures requiring immediate attention
logger.error("FHIR server unreachable", extra={
    "error_code": "EXT-FHIR-001",
    "fhir_url": fhir_url,
    "session_id": session_id
})

# WARNING: Recoverable issues or degraded performance
logger.warning("Insufficient data, returning partial results", extra={
    "missing_fields": ["hba1c", "ldl"],
    "session_id": session_id
})

# INFO: Important state changes
logger.info("Agent execution completed", extra={
    "agent": "risk_projection_agent",
    "duration_ms": 2100,
    "status": "success"
})

# DEBUG: Detailed execution information
logger.debug("Risk calculation parameters", extra={
    "baseline_risk": 0.15,
    "intervention_effect": -0.03,
    "confidence": 0.75
})
```

### Structured Logging Format

```json
{
  "timestamp": "2026-03-06T10:00:05.234Z",
  "level": "ERROR",
  "logger": "twincare_ai.agents.risk_projection",
  "message": "Risk calculation failed",
  "error_code": "DATA-INSUF-001",
  "session_id": "session-abc-123",
  "trace_id": "trace-xyz-789",
  "agent_id": "risk_projection_agent",
  "patient_id": "synthetic-001",
  "missing_fields": ["hba1c", "ldl_cholesterol"],
  "stack_trace": "..."
}
```

---

## Error Recovery Mechanisms

### 1. Automatic Retry

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(ExternalServiceError),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def fetch_fhir_data(patient_id: str):
    """Fetch FHIR data with automatic retry"""
    # Implementation...
    pass
```

### 2. Fallback Values

```python
async def get_risk_factor_with_fallback(
    patient_twin: PatientTwin,
    risk_factor: str
) -> float:
    """
    Get risk factor with fallback to default if unavailable
    """
    try:
        return patient_twin.get_risk_factor(risk_factor)
    except KeyError:
        logger.warning(f"Risk factor '{risk_factor}' not available, using default")
        return DEFAULT_RISK_FACTORS.get(risk_factor, 1.0)
```

### 3. Partial Results

```python
async def run_simulation_with_partial_results(
    scenarios: List[ScenarioDefinition]
) -> Dict:
    """
    Run simulations and return partial results if some fail
    """
    results = []
    errors = []
    
    for scenario in scenarios:
        try:
            result = await simulate_scenario(scenario)
            results.append(result)
        except Exception as e:
            logger.error(f"Scenario {scenario.id} failed: {str(e)}")
            errors.append({
                "scenario_id": scenario.id,
                "error": str(e)
            })
    
    return {
        "status": "partial" if errors else "success",
        "results": results,
        "errors": errors,
        "warnings": [
            f"{len(errors)} of {len(scenarios)} scenarios failed"
        ] if errors else []
    }
```

---

## Error Monitoring & Alerting

### Metrics to Track

```python
ERROR_METRICS = {
    "error_count_by_code": Counter("errors_total", ["error_code"]),
    "error_rate": Gauge("error_rate", ["component"]),
    "retry_attempts": Histogram("retry_attempts", ["service"]),
    "recovery_success": Counter("recovery_success_total", ["error_type"])
}
```

### Alert Conditions

```python
ALERT_RULES = {
    "high_error_rate": {
        "condition": "error_rate > 0.10",  # 10% error rate
        "severity": "critical",
        "action": "page_oncall"
    },
    "fhir_service_down": {
        "condition": "consecutive_fhir_errors > 5",
        "severity": "high",
        "action": "notify_team"
    },
    "safety_violations": {
        "condition": "safety_violation_count > 0",
        "severity": "critical",
        "action": "immediate_investigation"
    }
}
```

---

**Document Status:** Complete  
**Next Review:** March 12, 2026
