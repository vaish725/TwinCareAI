from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from twincare_ai.context.sharp_context import SHARPContext
from twincare_ai.fhir.fhir_ingestion_service import FhirIngestionService
from twincare_ai.mcp.prompt_opinion_config import PromptOpinionConfig
from twincare_ai.models.api_models import FhirToken # Import FhirToken from api_models

class PromptOpinionContext(BaseModel):
    patient_id: str = Field(..., description="ID of the patient from Prompt Opinion context.")
    encounter_id: Optional[str] = Field(None, description="ID of the current encounter.")
    user_role: str = Field(..., description="Role of the user accessing the context (e.g., physician, nurse).")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User-specific preferences or settings.")

class PatientResolution(BaseModel):
    resolved_patient_id: str = Field(..., description="The internal, resolved patient ID.")
    source_system: str = Field(..., description="The system from which the patient ID was resolved (e.g., EHR, Prompt Opinion).")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level of the patient ID resolution.")

class ResourceFetchPlan(BaseModel):
    resource_type: str = Field(..., description="FHIR resource type to fetch.")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters to apply when fetching resources.")
    priority: int = Field(0, description="Priority of fetching this resource (higher is more urgent).")

class ProcessedContext(BaseModel):
    sharp_context: SHARPContext
    prompt_opinion_context: PromptOpinionContext
    fhir_token: FhirToken
    resolved_patient_id: str
    resource_fetch_plans: List[ResourceFetchPlan]

class ContextIntakeAgent:
    """Agent responsible for parsing external contexts (e.g., Prompt Opinion, SHARP) and preparing for FHIR data access."""

    def __init__(self, fhir_ingestion_service: Optional[FhirIngestionService] = None, prompt_opinion_config: Optional[PromptOpinionConfig] = None):
        self.fhir_ingestion_service = fhir_ingestion_service or FhirIngestionService()
        self.prompt_opinion_config = prompt_opinion_config

    def parse_prompt_opinion_context(self, raw_context: Dict[str, Any]) -> PromptOpinionContext:
        """Parses a raw context dictionary from Prompt Opinion into a structured model."""
        # Placeholder for actual parsing logic, which would extract specific fields
        return PromptOpinionContext(
            patient_id=raw_context.get("patientGuid", "unknown_patient"),
            encounter_id=raw_context.get("encounterId"),
            user_role=raw_context.get("userRole", "unspecified"),
            preferences=raw_context.get("userPreferences", {})
        )

    def validate_sharp_context(self, sharp_context_data: Dict[str, Any]) -> SHARPContext:
        """Validates SHARP context data against the defined schema."""
        # The SharpContext Pydantic model handles the validation upon instantiation
        return SHARPContext(**sharp_context_data)

    def resolve_patient_id(self, external_patient_id: str, source_system: str = "PromptOpinion") -> PatientResolution:
        """Resolves an external patient ID to an internal patient ID."""
        # Placeholder: In a real system, this would involve a master patient index (MPI) lookup.
        # For now, we assume a direct mapping or simple transformation.
        resolved_id = f"internal_{external_patient_id}"
        return PatientResolution(
            resolved_patient_id=resolved_id,
            source_system=source_system,
            confidence=0.95 # High confidence for direct resolution
        )

    def handle_fhir_token(self, token_data: Dict[str, Any]) -> FhirToken:
        """Handles and validates FHIR access token data."""
        return FhirToken(
            access_token=token_data.get("access_token", ""),
            expires_in=token_data.get("expires_in", 3600),
            scope=token_data.get("scope", "")
        )

    def plan_resource_fetches(self, patient_id: str, context: PromptOpinionContext) -> List[ResourceFetchPlan]:
        """Plans which FHIR resources to fetch based on patient context and user needs."""
        plans: List[ResourceFetchPlan] = []

        plans.append(ResourceFetchPlan(resource_type="Patient", filters={"_id": patient_id}, priority=10))
        plans.append(ResourceFetchPlan(resource_type="Condition", filters={"patient": patient_id}, priority=8))
        plans.append(ResourceFetchPlan(resource_type="Observation", filters={"patient": patient_id, "category": "laboratory"}, priority=7))
        plans.append(ResourceFetchPlan(resource_type="MedicationRequest", filters={"patient": patient_id}, priority=6))
        plans.append(ResourceFetchPlan(resource_type="Encounter", filters={"patient": patient_id}, priority=5))

        # Add more sophisticated logic based on context.preferences or other agent inputs
        if context.user_role == "physician":
            plans.append(ResourceFetchPlan(resource_type="DiagnosticReport", filters={"patient": patient_id}, priority=9))

        return plans

    def process_context(
        self,
        initial_sharp_context: Dict[str, Any],
        raw_prompt_opinion_context: Dict[str, Any],
        fhir_token_data: Dict[str, Any],
        patient_id_override: Optional[str] = None
    ) -> ProcessedContext:
        """
        Processes all incoming context data to produce a unified, validated context
        for subsequent agent operations.
        """
        if not initial_sharp_context:
            raise ValueError("Initial SHARP context cannot be empty.")
        # 1. Validate SHARP Context
        sharp_context = self.validate_sharp_context(initial_sharp_context)

        # 2. Parse Prompt Opinion Context
        prompt_opinion_context = self.parse_prompt_opinion_context(raw_prompt_opinion_context)

        # 3. Handle FHIR Token
        fhir_token = self.handle_fhir_token(fhir_token_data)

        # 4. Determine Resolved Patient ID
        if patient_id_override:
            resolved_patient_id = patient_id_override
            source_system = "Override"
        else:
            patient_resolution = self.resolve_patient_id(prompt_opinion_context.patient_id)
            resolved_patient_id = patient_resolution.resolved_patient_id
            source_system = patient_resolution.source_system
        
        # 5. Plan Resource Fetches
        resource_fetch_plans = self.plan_resource_fetches(resolved_patient_id, prompt_opinion_context)

        return ProcessedContext(
            sharp_context=sharp_context,
            prompt_opinion_context=prompt_opinion_context,
            fhir_token=fhir_token,
            resolved_patient_id=resolved_patient_id,
            resource_fetch_plans=resource_fetch_plans
        )