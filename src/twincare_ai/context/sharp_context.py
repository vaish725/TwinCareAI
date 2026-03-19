from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PatientContext(BaseModel):
    patient_id: str
    patient_identifier_system: Optional[str] = None
    fhir_server_url: str
    fhir_access_token: str

class RequestingAgent(BaseModel):
    agent_id: str
    agent_name: Optional[str] = None

class InvocationContext(BaseModel):
    timestamp: str
    request_type: str
    user_role: Optional[str] = None

class SHARPContext(BaseModel):
    sharp_version: str = "1.0"
    session_id: str
    patient_context: PatientContext
    requesting_agent: RequestingAgent
    invocation_context: InvocationContext

# Example of expected SHARP context structure from RESEARCH_FINDINGS.md
# {
#   "sharp_version": "1.0",
#   "session_id": "uuid-v4",
#   "patient_context": {
#     "patient_id": "synthetic-001",
#     "patient_identifier_system": "http://twincare-ai.example.com",
#     "fhir_server_url": "https://fhir.example.com/r4",
#     "fhir_access_token": "bearer-token-here"
#   },
#   "requesting_agent": {
#     "agent_id": "prompt-opinion-coordinator",
#     "agent_name": "Clinical Decision Coordinator"
#   },
#   "invocation_context": {
#     "timestamp": "2026-03-06T10:00:00Z",
#     "request_type": "scenario_simulation",
#     "user_role": "clinician"
#   }
# }
