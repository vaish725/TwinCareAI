import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from twincare_ai.database.database import Base
from twincare_ai.api.main import app, get_db as override_get_db
from twincare_ai.models.api_models import SessionCreate, InvokeRequest, SimulateRequest, CompareRequest
from twincare_ai.models.scenario_and_risk import Scenario, ScenarioTemplate
from twincare_ai.agent.multi_agent_orchestrator import OrchestratorResult, OrchestrationTrace
from datetime import datetime, timedelta
import asyncio
import json

# Setup a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest_asyncio.fixture(name="db_session")
def db_session_fixture():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest_asyncio.fixture(name="client")
async def client_fixture(db_session):
    def get_db_override():
        yield db_session

    app.dependency_overrides[override_get_db] = get_db_override
    async with AsyncClient(base_url="http://test", transport=ASGITransport(app=app)) as client:
        yield client
    app.dependency_overrides = {} # Clean up overrides

# Mock data for requests
MOCK_SHARP_CONTEXT = {"patient": {"id": "patient123", "name": "John Doe"}}
MOCK_PROMPT_OPINION_CONTEXT = {"some_key": "some_value", "patient_id": "patient123"}
MOCK_FHIR_TOKEN_DATA = {"access_token": "mock_token"}
MOCK_SCENARIO_TEMPLATE = Scenario(
    id="scenario_1",
    patient_id="patient123",
    template_name="Test Scenario Template",
    description="A test scenario for simulation",
    parameters={"param1": "value1"},
    context_tags=["diabetes"],
    time_horizon_days=30,
    assumptions=["No new medication changes"]
)

@pytest.mark.asyncio
async def test_create_and_get_session(client: AsyncClient):
    # Test create session
    session_create_data = SessionCreate(patient_id="test_patient_001", initial_context={"source": "test"})
    response = await client.post("/sessions", json=session_create_data.model_dump())
    assert response.status_code == 201
    session_data = response.json()
    assert session_data["patient_id"] == "test_patient_001"
    assert "id" in session_data
    session_id = session_data["id"]

    # Test get session
    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    retrieved_session = response.json()
    assert retrieved_session["id"] == session_id
    assert retrieved_session["patient_id"] == "test_patient_001"
    assert retrieved_session["status"] == "pending"

@pytest.mark.asyncio
async def test_invoke_orchestration(client: AsyncClient):
    # Create a session first
    session_create_data = SessionCreate(patient_id="invoke_patient_001", initial_context={"source": "invoke_test"})
    response = await client.post("/sessions", json=session_create_data.model_dump())
    session_id = response.json()["id"]

    # Invoke orchestration
    invoke_request_data = InvokeRequest(
        session_id=session_id,
        sharp_context=MOCK_SHARP_CONTEXT,
        raw_prompt_opinion_context=MOCK_PROMPT_OPINION_CONTEXT,
        fhir_token_data=MOCK_FHIR_TOKEN_DATA,
        patient_id_override="invoke_patient_001_override"
    )
    response = await client.post("/invoke", json=invoke_request_data.model_dump())
    assert response.status_code == 202 # Accepted
    
    # Check session status immediately after invoke (should be accepted)
    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    session_status_initial = response.json()
    assert session_status_initial["status"] == "accepted"

    # Wait for the background task to complete and check the final status
    # In a real test, you might poll or use a more sophisticated mechanism
    # For now, a simple sleep will do, but note this is not ideal for complex orchestrations
    # Adjust sleep time based on expected orchestration duration
    await asyncio.sleep(5) # Give the background task some time to run

    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    session_status_final = response.json()
    assert session_status_final["status"] in ["completed", "partial_failure", "failed"] # Can be any of these
    assert "trace" in session_status_final
    assert session_status_final["trace"] is not None
    assert "final_output" in session_status_final["results"] or session_status_final["errors"]

@pytest.mark.asyncio
async def test_simulate_scenario(client: AsyncClient):
    # Create a session first
    session_create_data = SessionCreate(patient_id="simulate_patient_001", initial_context={"source": "simulate_test"})
    response = await client.post("/sessions", json=session_create_data.model_dump())
    session_id = response.json()["id"]

    # Simulate scenario
    simulate_request_data = SimulateRequest(
        session_id=session_id,
        sharp_context=MOCK_SHARP_CONTEXT,
        raw_prompt_opinion_context=MOCK_PROMPT_OPINION_CONTEXT,
        fhir_token_data=MOCK_FHIR_TOKEN_DATA,
        scenario_template=MOCK_SCENARIO_TEMPLATE,
        patient_id_override="simulate_patient_001_override"
    )
    response = await client.post("/simulate", json=simulate_request_data.model_dump())
    assert response.status_code == 202

    await asyncio.sleep(5) # Wait for the background task

    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    session_status_final = response.json()
    assert session_status_final["status"] in ["completed", "partial_failure", "failed"]
    assert "trace" in session_status_final
    assert session_status_final["trace"] is not None
    assert "final_output" in session_status_final["results"] or session_status_final["errors"]

@pytest.mark.asyncio
async def test_compare_scenarios(client: AsyncClient):
    # Create a session first
    session_create_data = SessionCreate(patient_id="compare_patient_001", initial_context={"source": "compare_test"})
    response = await client.post("/sessions", json=session_create_data.model_dump())
    session_id = response.json()["id"]

    # Compare scenarios
    compare_request_data = CompareRequest(
        session_id=session_id,
        sharp_context=MOCK_SHARP_CONTEXT,
        raw_prompt_opinion_context=MOCK_PROMPT_OPINION_CONTEXT,
        fhir_token_data=MOCK_FHIR_TOKEN_DATA,
        scenario_templates=[MOCK_SCENARIO_TEMPLATE, MOCK_SCENARIO_TEMPLATE], # Sending two identical for simplicity
        patient_id_override="compare_patient_001_override"
    )
    response = await client.post("/compare", json=compare_request_data.model_dump())
    assert response.status_code == 202

    await asyncio.sleep(5) # Wait for the background task

    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    session_status_final = response.json()
    assert session_status_final["status"] in ["completed", "partial_failure", "failed"]
    assert "trace" in session_status_final
    assert session_status_final["trace"] is not None
    assert "final_output" in session_status_final["results"] or session_status_final["errors"]

@pytest.mark.asyncio
async def test_get_session_trace(client: AsyncClient):
    # Create a session and invoke orchestration first
    session_create_data = SessionCreate(patient_id="trace_patient_001", initial_context={"source": "trace_test"})
    response = await client.post("/sessions", json=session_create_data.model_dump())
    session_id = response.json()["id"]

    invoke_request_data = InvokeRequest(
        session_id=session_id,
        sharp_context=MOCK_SHARP_CONTEXT,
        raw_prompt_opinion_context=MOCK_PROMPT_OPINION_CONTEXT,
        fhir_token_data=MOCK_FHIR_TOKEN_DATA,
        patient_id_override="trace_patient_001_override"
    )
    await client.post("/invoke", json=invoke_request_data.model_dump())

    await asyncio.sleep(5) # Wait for orchestration to complete

    response = await client.get(f"/sessions/{session_id}/trace")
    assert response.status_code == 200
    trace_data = response.json()
    assert "trace" in trace_data
    assert "final_data" in trace_data
    assert trace_data["trace"]["trace_id"] == session_id
    assert trace_data["trace"]["status"] in ["completed", "partial_failure", "failed"]
    assert len(trace_data["trace"]["log_entries"]) > 0

    # Test for non-existent session
    response = await client.get("/sessions/non_existent_id/trace")
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]

    # Test for session with no trace (though current logic ensures a trace is always started)
    # This scenario is less likely now due to how _run_orchestration_task is structured.
    # To properly test this, one might need to explicitly create a session without running orchestration.
    session_create_no_trace = SessionCreate(patient_id="no_trace_patient", initial_context={})
    response = await client.post("/sessions", json=session_create_no_trace.model_dump())
    session_id_no_trace = response.json()["id"]
    response = await client.get(f"/sessions/{session_id_no_trace}/trace")
    assert response.status_code == 404
    assert "Trace not found for this session." in response.json()["detail"]


# New mock data for specific SHARP context tests
MOCK_SHARP_CONTEXT_PATIENT_ID = {"patient": {"id": "sharp_patient_456", "name": "Jane Doe"}}
MOCK_SHARP_CONTEXT_FHIR_TOKEN = {"access_token": "sharp_mock_token_456", "expires_in": 3600, "token_type": "Bearer", "scope": "patient/*.read"}
MOCK_SHARP_CONTEXT_MISSING_PATIENT = {"encounter": {"id": "enc-789"}} # Missing patient ID


@pytest.mark.asyncio
async def test_sharp_context_patient_id_passing(client: AsyncClient):
    session_create_data = SessionCreate(patient_id="sharp_patient_id_test", initial_context={})
    response = await client.post("/sessions", json=session_create_data.model_dump())
    session_id = response.json()["id"]

    invoke_request_data = InvokeRequest(
        session_id=session_id,
        sharp_context=MOCK_SHARP_CONTEXT_PATIENT_ID,
        raw_prompt_opinion_context={},
        fhir_token_data={},
        patient_id_override=None # Ensure patient_id_override is not set to test SHARP context passing
    )
    await client.post("/invoke", json=invoke_request_data.model_dump())
    await asyncio.sleep(5)

    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    session_status = response.json()
    # Assuming the orchestrator uses the SHARP context patient ID if patient_id_override is None
    # This assertion might need adjustment based on the actual orchestrator logic for patient ID resolution
    assert session_status["patient_id"] == MOCK_SHARP_CONTEXT_PATIENT_ID["patient"]["id"]


@pytest.mark.asyncio
async def test_sharp_context_fhir_token_propagation(client: AsyncClient):
    session_create_data = SessionCreate(patient_id="sharp_fhir_token_test", initial_context={})
    response = await client.post("/sessions", json=session_create_data.model_dump())
    session_id = response.json()["id"]

    invoke_request_data = InvokeRequest(
        session_id=session_id,
        sharp_context=MOCK_SHARP_CONTEXT,
        raw_prompt_opinion_context={},
        fhir_token_data=MOCK_SHARP_CONTEXT_FHIR_TOKEN,
        patient_id_override=None
    )
    await client.post("/invoke", json=invoke_request_data.model_dump())
    await asyncio.sleep(5)

    response = await client.get(f"/sessions/{session_id}/trace")
    assert response.status_code == 200
    trace_data = response.json()
    # Assert that fhir_token_data was processed/propagated, e.g., appears in trace or agent inputs
    # This assertion will depend on how fhir_token_data is used and logged within the orchestration trace
    assert any(
        "sharp_mock_token_456" in str(entry)
        for entry in trace_data.get("trace", {}).get("log_entries", [])
    ) or any(
        "sharp_mock_token_456" in str(agent_output)
        for step in trace_data.get("trace", {}).get("agent_steps", [])
        for agent_output in [step.get("agent_output")]
    )


@pytest.mark.asyncio
async def test_sharp_context_missing_context_error_scenario(client: AsyncClient):
    session_create_data = SessionCreate(patient_id="sharp_error_test", initial_context={})
    response = await client.post("/sessions", json=session_create_data.model_dump())
    session_id = response.json()["id"]

    invoke_request_data = InvokeRequest(
        session_id=session_id,
        sharp_context=MOCK_SHARP_CONTEXT_MISSING_PATIENT, # This context is missing patient.id
        raw_prompt_opinion_context={},
        fhir_token_data={},
        patient_id_override=None
    )
    await client.post("/invoke", json=invoke_request_data.model_dump())
    await asyncio.sleep(5)

    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    session_status = response.json()
    # Expecting a failure or partial failure due to invalid SHARP context
    assert session_status["status"] in ["failed", "partial_failure"]
    assert "errors" in session_status
    assert any("patient ID" in error_msg for error_msg in session_status["errors"]) # Adjust error message based on actual validation logic
