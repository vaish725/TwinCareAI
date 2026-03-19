from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class NormalizedPatient(BaseModel):
    id: str
    gender: Optional[str]
    birth_date: Optional[str]
    marital_status: Optional[str]
    address: Optional[Dict[str, Any]]
    telecom: List[Dict[str, Any]] = []

class NormalizedCondition(BaseModel):
    id: str
    code: Dict[str, Any]
    clinical_status: Optional[Dict[str, Any]]
    recorded_date: Optional[str]

class NormalizedMedication(BaseModel):
    id: str
    medication_code: Dict[str, Any]
    status: Optional[str]
    authored_on: Optional[str]

class NormalizedObservation(BaseModel):
    id: str
    code: Dict[str, Any]
    value: Optional[Any]
    unit: Optional[str]
    effective_date: Optional[str]

class NormalizedEncounter(BaseModel):
    id: str
    status: Optional[str]
    period: Optional[Dict[str, Any]]
    service_type: Optional[Dict[str, Any]]

class CareGap(BaseModel):
    type: str = Field(..., description="Type of care gap (e.g., 'MissingScreening', 'UncontrolledBP')")
    description: str = Field(..., description="Detailed description of the care gap.")
    severity: str = Field("medium", description="Severity of the care gap (low, medium, high).")
    recommendation: Optional[str] = Field(None, description="Recommendation to address the care gap.")

class MissingDataReport(BaseModel):
    resource_type: str = Field(..., description="FHIR resource type with missing data.")
    missing_fields: List[str] = Field(..., description="List of fields that were expected but not found.")
    impact: str = Field(..., description="Potential impact of the missing data on twin completeness or insights.")

class TwinState(BaseModel):
    patient_id: str
    last_updated: str  # ISO formatted datetime string
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Score indicating the completeness of the digital twin data.")
    normalized_patient: Optional[NormalizedPatient]
    normalized_conditions: List[NormalizedCondition] = []
    normalized_medications: List[NormalizedMedication] = []
    normalized_observations: List[NormalizedObservation] = []
    normalized_encounters: List[NormalizedEncounter] = []
    care_gaps: List[CareGap] = []
    missing_data_report: List[MissingDataReport] = []
    raw_fhir_data_references: Dict[str, Any] = Field(default_factory=dict, description="References to raw FHIR data that contributed to this TwinState.")
