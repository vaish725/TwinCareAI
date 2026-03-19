import pytest
from typing import Dict, Any, List
from datetime import datetime

from twincare_ai.agent.medication_impact_agent import MedicationImpactAgent
from twincare_ai.agent.guideline_alignment_agent import GuidelineAlignmentAgent
from twincare_ai.agent.context_intake_agent import ContextIntakeAgent
from twincare_ai.models.twin_state import TwinState, NormalizedMedication, NormalizedCondition, NormalizedPatient, NormalizedObservation, NormalizedEncounter
from twincare_ai.models.scenario_and_risk import Scenario, ScenarioTemplate
from twincare_ai.context.sharp_context import SharpContext
from twincare_ai.fhir.fhir_ingestion_service import FhirIngestionService

# --- Fixtures for common test data ---

@pytest.fixture
def mock_fhir_ingestion_service():
    return FhirIngestionService() # Use real service for now, can be mocked later

@pytest.fixture
def medication_impact_agent():
    return MedicationImpactAgent()

@pytest.fixture
def guideline_alignment_agent():
    return GuidelineAlignmentAgent()

@pytest.fixture
def context_intake_agent(mock_fhir_ingestion_service):
    return ContextIntakeAgent(fhir_ingestion_service=mock_fhir_ingestion_service)

@pytest.fixture
def sample_normalized_medications() -> List[NormalizedMedication]:
    return [
        NormalizedMedication(id="med1", medication_code={"text": "Metformin"}, status="active"),
        NormalizedMedication(id="med2", medication_code={"text": "Aspirin"}, status="active"),
    ]

@pytest.fixture
def sample_normalized_conditions() -> List[NormalizedCondition]:
    return [
        NormalizedCondition(id="cond1", code={"text": "Type 2 Diabetes"}, clinical_status={"text": "active"}, recorded_date="2023-01-01"),
        NormalizedCondition(id="cond2", code={"text": "Hypertension"}, clinical_status={"text": "active"}, recorded_date="2022-06-15"),
    ]

@pytest.fixture
def sample_normalized_patient() -> NormalizedPatient:
    return NormalizedPatient(id="pat1", gender="male", birth_date="1970-01-01")

@pytest.fixture
def sample_twin_state(sample_normalized_patient, sample_normalized_conditions, sample_normalized_medications) -> TwinState:
    return TwinState(
        patient_id="pat1",
        last_updated=datetime.utcnow().isoformat(),
        completeness_score=0.8,
        normalized_patient=sample_normalized_patient,
        normalized_conditions=sample_normalized_conditions,
        normalized_medications=sample_normalized_medications,
        normalized_observations=[],
        normalized_encounters=[],
    )

@pytest.fixture
def sample_scenario() -> Scenario:
    template = ScenarioTemplate(
        name="Diabetes Progression with Poor Adherence",
        description="Test scenario",
        parameters={"medication_adherence": "low", "time_horizon_years": 5}
    )
    return Scenario(
        id="scn_test_001",
        patient_id="pat1",
        template_name=template.name,
        description=template.description,
        parameters=template.parameters,
        assumptions=[]
    )

@pytest.fixture
def sample_prompt_opinion_context() -> Dict[str, Any]:
    return {
        "patientGuid": "guid-123",
        "encounterId": "enc-456",
        "userRole": "physician",
        "userPreferences": {"theme": "dark"}
    }

@pytest.fixture
def sample_sharp_context_data() -> Dict[str, Any]:
    return {
        "patient": {"id": "pat1", "gender": "male"},
        "encounter": {"id": "enc-456", "type": "outpatient"},
        "user": {"id": "user1", "role": "physician"}
    }

@pytest.fixture
def sample_fhir_token_data() -> Dict[str, Any]:
    return {
        "access_token": "xyz123abc",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "patient/*.read"
    }

# --- Test Cases ---

def test_medication_impact_agent_integration(medication_impact_agent, sample_normalized_medications, sample_normalized_patient):
    # Test medication burden
    burden = medication_impact_agent.calculate_medication_burden(sample_normalized_medications)
    assert burden.score >= 0

    # Test interactions
    interactions = medication_impact_agent.check_interactions(sample_normalized_medications)
    assert isinstance(interactions, list)

    # Test adherence impact (requires patient_data, using a mock for now)
    patient_data_mock = {"socioeconomic_status": "low"}
    adherence = medication_impact_agent.model_adherence_impact(patient_data_mock, sample_normalized_medications)
    assert adherence.adherence_score <= 0.8 # Due to low socioeconomic status mock

    # Test caution flags
    patient_data_mock_renal = {"renal_function": "impaired"}
    caution_flags = medication_impact_agent.generate_caution_flags(patient_data_mock_renal, sample_normalized_medications)
    assert any(flag.flag_type == "RenalImpairment" for flag in caution_flags)

def test_guideline_alignment_agent_integration(guideline_alignment_agent, sample_twin_state, sample_scenario):
    # Test guideline consistency check
    consistency_result = guideline_alignment_agent.check_scenario_guideline_consistency(
        sample_twin_state, sample_scenario, "ADA_Diabetes_2024"
    )
    assert consistency_result.guideline_id == "ADA_Diabetes_2024"
    assert consistency_result.consistency_status in ["consistent", "inconsistent", "partially_consistent"]

    # Test evidence strength notes
    evidence = guideline_alignment_agent.generate_evidence_strength_notes("HbA1c target for diabetes management")
    assert evidence.strength == "high"

    # Test false certainty claims
    modified_text = guideline_alignment_agent.avoid_false_certainty_claims("This intervention is certain to prevent adverse events.")
    assert "certain" not in modified_text
    assert "likely" in modified_text

def test_context_intake_agent_integration(context_intake_agent, sample_prompt_opinion_context, sample_sharp_context_data, sample_fhir_token_data):
    # Test Prompt Opinion context parsing
    po_context = context_intake_agent.parse_prompt_opinion_context(sample_prompt_opinion_context)
    assert po_context.patient_id == "guid-123"

    # Test SHARP context validation
    sharp_context = context_intake_agent.validate_sharp_context(sample_sharp_context_data)
    assert sharp_context.patient.id == "pat1"

    # Test patient ID resolution
    resolved_id = context_intake_agent.resolve_patient_id("external-pat-id")
    assert resolved_id.resolved_patient_id == "internal_external-pat-id"

    # Test FHIR token handling
    fhir_token = context_intake_agent.handle_fhir_token(sample_fhir_token_data)
    assert fhir_token.access_token == "xyz123abc"

    # Test resource fetch planning
    fetch_plans = context_intake_agent.plan_resource_fetches(po_context.patient_id, po_context)
    assert any(plan.resource_type == "Patient" for plan in fetch_plans)
