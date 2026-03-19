from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Demographics(BaseModel):
    gender: str
    birth_date: str
    # Add more demographic fields as needed

class ConditionSummary(BaseModel):
    code: str
    display: str
    onset_date: Optional[str] = None
    # Add more condition-related fields as needed

class MedicationSummary(BaseModel):
    code: str
    display: str
    authored_on: Optional[str] = None
    # Add more medication-related fields as needed

class ObservationSummary(BaseModel):
    code: str
    display: str
    value: Any
    unit: Optional[str] = None
    effective_date: Optional[str] = None
    # Add more observation-related fields as needed

class EncounterSummary(BaseModel):
    class_code: str
    display: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None

class PatientTwin(BaseModel):
    """Represents the digital twin state of a patient."""
    patient_id: str = Field(..., description="Unique identifier for the patient.")
    demographics: Demographics
    active_conditions: List[ConditionSummary] = Field(default_factory=list)
    active_medications: List[MedicationSummary] = Field(default_factory=list)
    recent_labs: List[ObservationSummary] = Field(default_factory=list)
    recent_vitals: List[ObservationSummary] = Field(default_factory=list)
    encounter_history_summary: List[EncounterSummary] = Field(default_factory=list)
    risk_factor_vector: Dict[str, float] = Field(default_factory=dict, description="Key-value pairs for various risk factors.")
    adherence_assumptions: Dict[str, Any] = Field(default_factory=dict, description="Assumptions about patient adherence to treatments.")
    care_gap_flags: List[str] = Field(default_factory=list, description="Flags indicating potential care gaps.")
    confidence_profile: Dict[str, float] = Field(default_factory=dict, description="Confidence levels for different aspects of the twin's data.")

    # Example of how a PatientTwin could be created (for demonstration/testing)
    @classmethod
    def from_fhir_resources(cls, patient_id: str, scoped_resources: Dict[str, List[Dict[str, Any]]]) -> 'PatientTwin':
        """Constructs a PatientTwin from extracted FHIR resources."""
        patient_resource = next(iter(scoped_resources.get("Patient", [])), None)
        if not patient_resource:
            raise ValueError(f"Patient resource not found for patient_id: {patient_id}")

        demographics = Demographics(
            gender=patient_resource.get("gender"),
            birth_date=patient_resource.get("birthDate")
        )

        active_conditions = [
            ConditionSummary(
                code=cond.get("code", {}).get("coding", [{}])[0].get("code"),
                display=cond.get("code", {}).get("text", cond.get("code", {}).get("coding", [{}])[0].get("display")),
                onset_date=cond.get("onsetDateTime")
            )
            for cond in scoped_resources.get("Condition", [])
        ]

        active_medications = [
            MedicationSummary(
                code=med.get("medicationCodeableConcept", {}).get("coding", [{}])[0].get("code"),
                display=med.get("medicationCodeableConcept", {}).get("text", med.get("medicationCodeableConcept", {}).get("coding", [{}])[0].get("display")),
                authored_on=med.get("authoredOn")
            )
            for med in scoped_resources.get("MedicationRequest", [])
        ]

        recent_labs = [
            ObservationSummary(
                code=obs.get("code", {}).get("coding", [{}])[0].get("code"),
                display=obs.get("code", {}).get("text", obs.get("code", {}).get("coding", [{}])[0].get("display")),
                value=obs.get("valueQuantity", {}).get("value"),
                unit=obs.get("valueQuantity", {}).get("unit"),
                effective_date=obs.get("effectiveDateTime")
            )
            for obs in scoped_resources.get("Observation", [])
        ]

        encounter_history_summary = [
            EncounterSummary(
                class_code=enc.get("class", {}).get("code"),
                display=enc.get("class", {}).get("display"),
                period_start=enc.get("period", {}).get("start"),
                period_end=enc.get("period", {}).get("end")
            )
            for enc in scoped_resources.get("Encounter", [])
        ]

        return cls(
            patient_id=patient_id,
            demographics=demographics,
            active_conditions=active_conditions,
            active_medications=active_medications,
            recent_labs=recent_labs,
            encounter_history_summary=encounter_history_summary,
            # For now, risk_factor_vector, adherence_assumptions, care_gap_flags, confidence_profile are empty/defaults
        )
