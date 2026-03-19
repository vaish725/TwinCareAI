from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import json
import asyncio

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

# Local imports
from twincare_ai.context.sharp_context import SHARPContext
from twincare_ai.agent.multi_agent_orchestrator import MultiAgentOrchestrator, OrchestratorResult, OrchestrationTrace
from twincare_ai.agent.medication_impact_agent import MedicationImpactAgent
from twincare_ai.agent.guideline_alignment_agent import GuidelineAlignmentAgent
from twincare_ai.agent.context_intake_agent import ContextIntakeAgent
from twincare_ai.agent.twin_state_builder_agent import TwinStateBuilderAgent
from twincare_ai.agent.scenario_generator_agent import ScenarioGeneratorAgent
from twincare_ai.agent.risk_projection_agent import RiskProjectionAgent
from twincare_ai.agent.simulation_engine import SimulationEngine
from twincare_ai.agent.safety_guardrail_agent import SafetyGuardrailAgent
from twincare_ai.agent.explanation_agent import ExplanationAgent
from twincare_ai.agent.consensus_agent import ConsensusAgent
from twincare_ai.models.scenario_and_risk import Scenario
from twincare_ai.models.api_models import SessionCreate, SessionUpdate, SessionResponse, InvokeRequest, SimulateRequest, CompareRequest
from twincare_ai.database.crud import create_session, get_session, update_session, get_all_sessions
from twincare_ai.database.database import SessionLocal, engine, Base
from twincare_ai.agent.orchestration import RetryStrategy, TimeoutStrategy

from twincare_ai.mcp.prompt_opinion_config import PromptOpinionConfig

from twincare_ai.fhir.fhir_ingestion_service import FhirIngestionService
from twincare_ai.mcp.mcp_server import mcp_server # Import the mcp_server instance

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TwinCare AI API",
    description="API for orchestrating AI agents to generate digital twin insights.",
    version="0.0.1",
)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Placeholder for Prompt Opinion Configuration
prompt_opinion_config_instance = PromptOpinionConfig(
    api_endpoint="https://mock.promptopinion.com/api",
    agent_id="twincare-ai-mock-agent"
)

# Placeholder for FHIR Server URL (should be configured externally)
FHIR_BASE_URL = "http://localhost:8080/fhir" # Example FHIR server URL

# Initialize agents (these would ideally be configured via dependency injection or a factory)
context_intake_agent = ContextIntakeAgent(prompt_opinion_config=prompt_opinion_config_instance)

fhir_ingestion_service = FhirIngestionService(fhir_base_url=FHIR_BASE_URL)
twin_state_builder_agent = TwinStateBuilderAgent(ingestion_service=fhir_ingestion_service)
scenario_generator_agent = ScenarioGeneratorAgent()
risk_projection_agent = RiskProjectionAgent()
simulation_engine = SimulationEngine()
medication_impact_agent = MedicationImpactAgent()
guideline_alignment_agent = GuidelineAlignmentAgent()
safety_guardrail_agent = SafetyGuardrailAgent()
explanation_agent = ExplanationAgent()
consensus_agent = ConsensusAgent()

# Initialize the orchestrator
orchestrator = MultiAgentOrchestrator(
    context_intake_agent=context_intake_agent,
    twin_state_builder_agent=twin_state_builder_agent,
    scenario_generator_agent=scenario_generator_agent,
    risk_projection_agent=risk_projection_agent,
    simulation_engine=simulation_engine,
    medication_impact_agent=medication_impact_agent,
    guideline_alignment_agent=guideline_alignment_agent,
    safety_guardrail_agent=safety_guardrail_agent,
    explanation_agent=explanation_agent,
    consensus_agent=consensus_agent,
    mcp_server=mcp_server, # Add this line
    retry_strategy=RetryStrategy(max_attempts=3, delay_seconds=1, backoff_factor=2),
    timeout_strategy=TimeoutStrategy(timeout_seconds=600) # 10 minutes timeout
)

@app.get("/health", response_model=Dict[str, str])
async def health_check():
    return {"status": "ok", "message": "TwinCare AI API is running"}

@app.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_new_session(session_create: SessionCreate, db: Session = Depends(get_db)):
    db_session = create_session(db=db, session_id=str(uuid.uuid4()), patient_id=session_create.patient_id, initial_context=session_create.initial_context)
    session_data = {
        "id": db_session.id,
        "patient_id": db_session.patient_id,
        "created_at": db_session.created_at,
        "last_updated": db_session.last_updated,
        "status": db_session.status,
        "initial_context": json.loads(db_session.initial_context) if db_session.initial_context else {},
        "results": json.loads(db_session.results) if db_session.results else None,
        "trace": json.loads(db_session.trace) if db_session.trace else None,
        "errors": json.loads(db_session.errors) if db_session.errors else None,
    }
    return SessionResponse.model_validate(session_data)

@app.get("/sessions/{session_id}", response_model=SessionResponse)
def get_existing_session(session_id: str, db: Session = Depends(get_db)):
    db_session = get_session(db=db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session_data = {
        "id": db_session.id,
        "patient_id": db_session.patient_id,
        "created_at": db_session.created_at,
        "last_updated": db_session.last_updated,
        "status": db_session.status,
        "initial_context": json.loads(db_session.initial_context) if db_session.initial_context else {},
        "results": json.loads(db_session.results) if db_session.results else None,
        "trace": json.loads(db_session.trace) if db_session.trace else None,
        "errors": json.loads(db_session.errors) if db_session.errors else None,
    }
    return SessionResponse.model_validate(session_data)

async def _run_orchestration_task(session_id: str, initial_sharp_context: Dict[str, Any], raw_prompt_opinion_context: Dict[str, Any], fhir_token_data: Dict[str, Any], patient_id_override: Optional[str], scenario_templates: Optional[List[Scenario]] = None):
    db = None
    try:
        db = SessionLocal()
        # Update session status to in_progress
        update_session(db=db, session_id=session_id, session_update=SessionUpdate(status="in_progress"))

        orchestrator_result: OrchestratorResult = await orchestrator.orchestrate(
            trace_id=session_id, # Using session_id as trace_id
            initial_sharp_context=initial_sharp_context,
            raw_prompt_opinion_context=raw_prompt_opinion_context,
            fhir_token_data=fhir_token_data,
            patient_id_override=patient_id_override,
            scenario_templates=scenario_templates
        )

        # Update session with results and trace
        session_update = SessionUpdate(
            status=orchestrator_result.trace.status,
            results=orchestrator_result.final_output.model_dump() if orchestrator_result.final_output else None,
            trace=orchestrator_result.trace.model_dump(),
            errors=[orchestrator_result.trace.error_message] if orchestrator_result.trace.error_message else None,
            last_updated=datetime.now()
        )
        update_session(db=db, session_id=session_id, session_update=session_update)

    except Exception as e:
        error_message = f"Orchestration failed: {str(e)}"
        session_update = SessionUpdate(
            status="failed",
            errors=[error_message],
            last_updated=datetime.now()
        )
        update_session(db=db, session_id=session_id, session_update=session_update)
        print(f"Error during orchestration for session {session_id}: {e}") # Log the error
    finally:
        if db:
            db.close()
@app.post("/invoke", response_model=SessionResponse, status_code=status.HTTP_202_ACCEPTED)
async def invoke_orchestration(
    request: InvokeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session = get_session(db=db, session_id=request.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Start the orchestration in a background task
    background_tasks.add_task(
        _run_orchestration_task,
        session.id,
        request.sharp_context,
        request.raw_prompt_opinion_context,
        request.fhir_token_data,
        request.patient_id_override,
        None # No scenario templates for invoke
    )

    # Update session status immediately to indicate processing has started
    updated_session = update_session(db=db, session_id=session.id, session_update=SessionUpdate(status="accepted", last_updated=datetime.now()))
    updated_session_data = {
        "id": updated_session.id,
        "patient_id": updated_session.patient_id,
        "created_at": updated_session.created_at,
        "last_updated": updated_session.last_updated,
        "status": updated_session.status,
        "initial_context": json.loads(updated_session.initial_context) if updated_session.initial_context else {},
        "results": json.loads(updated_session.results) if updated_session.results else None,
        "trace": json.loads(updated_session.trace) if updated_session.trace else None,
        "errors": json.loads(updated_session.errors) if updated_session.errors else None,
    }
    return SessionResponse.model_validate(updated_session_data)

@app.post("/mcp/invoke-tool")
async def invoke_mcp_tool(tool_name: str, input_data: Dict[str, Any]):
    """
    Invokes a registered MCP tool.
    """
    try:
        result = await mcp_server.invoke_tool(tool_name, input_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error invoking MCP tool: {e}")


@app.get("/sessions/{session_id}/trace", response_model=OrchestratorResult)
def get_session_trace(session_id: str, db: Session = Depends(get_db)):
    session_data = get_session(db=db, session_id=session_id)
    if session_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if not session_data.trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found for this session.")
    
    # Reconstruct OrchestratorResult from stored session data
    orchestration_trace = OrchestrationTrace.model_validate(session_data.trace)
    final_output = None
    if session_data.results:
        # Assuming results stored are directly consumable or can be converted to a specific model if needed
        final_output = session_data.results # This might need further parsing if it's a complex Pydantic model

    # For now, let's create a placeholder OrchestratorResult.
    # In a real scenario, you'd deserialize the stored 'results' into the appropriate Pydantic model
    # that OrchestratorResult expects as its 'final_data'.
    # For simplicity, we'll return a dict representation.
    return OrchestratorResult(
        trace=orchestration_trace,
        final_data=final_output if final_output else {},
        errors=session_data.errors if session_data.errors else []
    )

@app.post("/simulate", response_model=SessionResponse, status_code=status.HTTP_202_ACCEPTED)
async def simulate_scenario(
    request: SimulateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session = get_session(db=db, session_id=request.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    background_tasks.add_task(
        _run_orchestration_task, 
        session.id,
        request.sharp_context,
        request.raw_prompt_opinion_context,
        request.fhir_token_data,
        request.patient_id_override,
        [request.scenario_template] # Pass the scenario template as a list
    )

    updated_session = update_session(db=db, session_id=session.id, session_update=SessionUpdate(status="accepted", last_updated=datetime.now()))
    return SessionResponse.model_validate(updated_session)

@app.post("/compare", response_model=SessionResponse, status_code=status.HTTP_202_ACCEPTED)
async def compare_scenarios(
    request: CompareRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    session = get_session(db=db, session_id=request.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    background_tasks.add_task(
        _run_orchestration_task, 
        session.id,
        request.sharp_context,
        request.raw_prompt_opinion_context,
        request.fhir_token_data,
        request.patient_id_override,
        request.scenario_templates # Pass multiple scenario templates
    )

    updated_session = update_session(db=db, session_id=session.id, session_update=SessionUpdate(status="accepted", last_updated=datetime.now()))
    return SessionResponse.model_validate(updated_session)