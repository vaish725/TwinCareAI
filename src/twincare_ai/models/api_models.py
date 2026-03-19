from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from twincare_ai.models.scenario_and_risk import Scenario

# --- Session Management Models ---
class SessionCreate(BaseModel):
    patient_id: str
    initial_context: Dict[str, Any]

class SessionUpdate(BaseModel):
    status: Optional[str] = None
    last_updated: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    trace: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

class SessionResponse(BaseModel):
    id: str
    patient_id: str
    created_at: datetime
    last_updated: datetime
    status: str
    initial_context: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    trace: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None

class FhirToken(BaseModel):
    access_token: str = Field(..., description="OAuth2 access token for FHIR API access.")
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Time in seconds until the token expires.")
    scope: str = Field(..., description="Scopes granted by the token.")

# --- API Request Models ---
class InvokeRequest(BaseModel):
    session_id: str
    sharp_context: Dict[str, Any]
    raw_prompt_opinion_context: Dict[str, Any]
    fhir_token_data: Dict[str, Any]
    patient_id_override: Optional[str] = None

class SimulateRequest(BaseModel):
    session_id: str
    sharp_context: Dict[str, Any]
    raw_prompt_opinion_context: Dict[str, Any]
    fhir_token_data: Dict[str, Any]
    scenario_template: Scenario # Or a simplified model for scenario creation
    patient_id_override: Optional[str] = None

class CompareRequest(BaseModel):
    session_id: str
    sharp_context: Dict[str, Any]
    raw_prompt_opinion_context: Dict[str, Any]
    fhir_token_data: Dict[str, Any]
    scenario_templates: List[Scenario] # List of scenarios to compare
    patient_id_override: Optional[str] = None
