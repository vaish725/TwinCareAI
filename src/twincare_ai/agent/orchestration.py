from pydantic import BaseModel
from typing import List, Dict, Any, Literal

# --- Multi-agent Orchestration Design ---

class OrchestrationStep(BaseModel):
    agent_name: str
    action: str
    description: str
    dependencies: List[str] = []

class RetryStrategy(BaseModel):
    max_retries: int = 3
    delay_seconds: int = 5
    backoff_factor: float = 2.0

class TimeoutStrategy(BaseModel):
    timeout_seconds: int = 60

class ConflictResolutionStrategy(BaseModel):
    strategy_type: Literal["manual", "last_write_wins", "priority_based"]
    description: str

class TraceLogEntry(BaseModel):
    timestamp: str # Using string for simplicity, datetime in real impl
    agent_name: str
    event_type: str
    details: Dict[str, Any]

class AgentOrchestrationDesign(BaseModel):
    execution_sequence: List[OrchestrationStep]
    retry_strategy: RetryStrategy
    timeout_strategy: TimeoutStrategy
    conflict_resolution: ConflictResolutionStrategy
    trace_logging_mechanism: str

def get_orchestration_design() -> AgentOrchestrationDesign:
    """Provides a conceptual design for multi-agent orchestration."""
    return AgentOrchestrationDesign(
        execution_sequence=[
            OrchestrationStep(
                agent_name="PatientDataAgent",
                action="retrieve_data",
                description="Retrieves and processes patient's raw data from various sources (e.g., FHIR).",
                dependencies=[]
            ),
            OrchestrationStep(
                agent_name="TwinGenerationAgent",
                action="update_twin",
                description="Creates or updates the patient's digital twin based on processed data.",
                dependencies=["PatientDataAgent"]
            ),
            OrchestrationStep(
                agent_name="InsightGenerationAgent",
                action="generate_insights",
                description="Analyzes the digital twin to produce health insights and predictions.",
                dependencies=["TwinGenerationAgent"]
            ),
            OrchestrationStep(
                agent_name="InterventionPlanningAgent",
                action="plan_interventions",
                description="Develops potential intervention plans based on generated insights.",
                dependencies=["InsightGenerationAgent"]
            ),
            OrchestrationStep(
                agent_name="CommunicationAgent",
                action="deliver_information",
                description="Communicates relevant information (insights, plans) to clinicians/systems.",
                dependencies=["InsightGenerationAgent", "InterventionPlanningAgent"]
            ),
            OrchestrationStep(
                agent_name="EvaluationAgent",
                action="monitor_outcomes",
                description="Monitors the effectiveness of interventions and system performance.",
                dependencies=["CommunicationAgent"]
            ),
            OrchestrationStep(
                agent_name="AuditAgent",
                action="log_event",
                description="Records all significant actions and decisions for auditing purposes.",
                dependencies=["PatientDataAgent", "TwinGenerationAgent", "InsightGenerationAgent", "InterventionPlanningAgent", "CommunicationAgent", "EvaluationAgent"]
            ),
            OrchestrationStep(
                agent_name="SecurityAgent",
                action="enforce_policies",
                description="Ensures data security and access control throughout the orchestration.",
                dependencies=[]
            ),
            OrchestrationStep(
                agent_name="ConfigurationAgent",
                action="manage_agents",
                description="Manages the lifecycle and configuration of other agents.",
                dependencies=[]
            ),
        ],
        retry_strategy=RetryStrategy(
            max_retries=5,
            delay_seconds=10,
            backoff_factor=2.5
        ),
        timeout_strategy=TimeoutStrategy(
            timeout_seconds=120
        ),
        conflict_resolution=ConflictResolutionStrategy(
            strategy_type="priority_based",
            description="Conflicts resolved based on predefined agent priorities or manual clinician override."
        ),
        trace_logging_mechanism="Centralized structured logging with correlation IDs for each request."
    )
