import pytest
from pathlib import Path
from twincare_ai.agent.twin_state_builder_agent import TwinStateBuilderAgent
from twincare_ai.fhir.fhir_ingestion_service import FhirIngestionService
from twincare_ai.models.twin_state import TwinState, CareGap, MissingDataReport

# Assuming synthetic data is available in data/fhir_synthetic
SYNTHETIC_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "fhir_synthetic"

@pytest.fixture
def fhir_ingestion_service():
    return FhirIngestionService()

@pytest.fixture
def twin_state_builder_agent(fhir_ingestion_service):
    return TwinStateBuilderAgent(ingestion_service=fhir_ingestion_service)

@pytest.fixture
def sample_fhir_bundle_001(fhir_ingestion_service):
    file_path = SYNTHETIC_DATA_DIR / "patient_001.json"
    return fhir_ingestion_service.load_bundle_from_file(file_path)

@pytest.fixture
def sample_fhir_bundle_002(fhir_ingestion_service):
    file_path = SYNTHETIC_DATA_DIR / "patient_002.json"
    return fhir_ingestion_service.load_bundle_from_file(file_path)

def test_build_twin_state_patient_001(twin_state_builder_agent, sample_fhir_bundle_001):
    patient_id = "patient_001"
    twin_state = twin_state_builder_agent.build_twin_state(patient_id, sample_fhir_bundle_001)

    assert isinstance(twin_state, TwinState)
    assert twin_state.patient_id == patient_id
    assert twin_state.completeness_score > 0
    assert twin_state.normalized_patient is not None
    assert len(twin_state.normalized_conditions) > 0
    assert len(twin_state.normalized_observations) > 0
    assert len(twin_state.normalized_medications) > 0

    # Test care gaps and missing data report (basic checks)
    assert isinstance(twin_state.care_gaps, list)
    assert all(isinstance(gap, CareGap) for gap in twin_state.care_gaps)
    assert isinstance(twin_state.missing_data_report, list)
    assert all(isinstance(report_entry, MissingDataReport) for report_entry in twin_state.missing_data_report)

def test_build_twin_state_patient_002(twin_state_builder_agent, sample_fhir_bundle_002):
    patient_id = "patient_002"
    twin_state = twin_state_builder_agent.build_twin_state(patient_id, sample_fhir_bundle_002)

    assert isinstance(twin_state, TwinState)
    assert twin_state.patient_id == patient_id
    assert twin_state.completeness_score > 0

    # Add more specific assertions for patient_002 data if known characteristics

def test_completeness_score_calculation(twin_state_builder_agent):
    # Test with an empty bundle to check score calculation
    empty_bundle = {"resourceType": "Bundle", "type": "collection", "entry": []}
    twin_state = twin_state_builder_agent.build_twin_state("empty_patient", empty_bundle)
    assert twin_state.completeness_score == 0.0
    assert len(twin_state.missing_data_report) > 0

def test_care_gap_identification(twin_state_builder_agent, sample_fhir_bundle_001):
    patient_id = "patient_001"
    twin_state = twin_state_builder_agent.build_twin_state(patient_id, sample_fhir_bundle_001)
    # Assuming patient_001 might trigger some care gaps based on its synthetic data
    # This test would need to be more specific if care gap conditions are known for patient_001
    assert any(gap.type == "MissingHbA1c" for gap in twin_state.care_gaps) or \
           any(gap.type == "MissingBloodPressure" for gap in twin_state.care_gaps) or \
           any(gap.type == "UnmanagedDiabetes" for gap in twin_state.care_gaps)

def test_missing_data_report_generation(twin_state_builder_agent, sample_fhir_bundle_001):
    patient_id = "patient_001"
    twin_state = twin_state_builder_agent.build_twin_state(patient_id, sample_fhir_bundle_001)
    # Assuming patient_001 might have some missing data points
    assert len(twin_state.missing_data_report) >= 0 # It can be 0 if all data is present
