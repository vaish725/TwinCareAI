from pydantic import BaseModel
from typing import List, Dict, Any, Literal

# --- Agent Input/Output Contracts ---

class AgentInput(BaseModel):
    patient_id: str
    sharp_context: Dict[str, Any]
    # Add other common inputs here

class AgentOutput(BaseModel):
    agent_name: str
    result: Any
    # Add other common outputs here

# --- Inter-Agent Communication Protocol ---

class AgentMessage(BaseModel):
    sender: str
    recipient: str
    message_type: Literal["request", "response", "notification"]
    payload: Dict[str, Any]

# --- Agent Responsibilities ---

class AgentSpec(BaseModel):
    name: str
    description: str
    responsibilities: List[str]
    input_contract: Dict[str, Any] # Pydantic model schema
    output_contract: Dict[str, Any] # Pydantic model schema
    communication_channels: List[str] # e.g., ["queue", "http", "event_bus"]

# Example Agent Definitions (Placeholders for 9 agents)
# In a real scenario, these would be detailed with specific inputs/outputs and responsibilities

def get_agent_specs() -> List[AgentSpec]:
    return [
        AgentSpec(
            name="PatientDataAgent",
            description="Manages retrieval and processing of patient data from FHIR and other sources.",
            responsibilities=[
                "Retrieve FHIR resources for a given patient ID.",
                "Normalize and standardize patient data.",
                "Identify data freshness and completeness issues."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["queue"]
        ),
        AgentSpec(
            name="TwinGenerationAgent",
            description="Generates and updates the patient's digital twin.",
            responsibilities=[
                "Construct a comprehensive PatientTwin from raw data.",
                "Update twin with new information.",
                "Maintain twin consistency."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["queue"]
        ),
        AgentSpec(
            name="InsightGenerationAgent",
            description="Analyzes patient twin data to generate clinical insights and predictions.",
            responsibilities=[
                "Apply clinical algorithms to twin data.",
                "Identify potential health risks.",
                "Generate actionable recommendations."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["queue", "event_bus"]
        ),
        AgentSpec(
            name="InterventionPlanningAgent",
            description="Suggests and evaluates intervention plans based on insights.",
            responsibilities=[
                "Propose intervention strategies.",
                "Assess feasibility and impact of interventions.",
                "Provide rationale for intervention choices."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["queue"]
        ),
        AgentSpec(
            name="CommunicationAgent",
            description="Handles communication with external systems and users.",
            responsibilities=[
                "Format insights for clinician review.",
                "Integrate with EHR for data exchange.",
                "Send notifications and alerts."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["http", "queue"]
        ),
        AgentSpec(
            name="EvaluationAgent",
            description="Monitors the effectiveness of interventions and overall system performance.",
            responsibilities=[
                "Track patient outcomes.",
                "Evaluate agent performance metrics.",
                "Suggest improvements to agent logic."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["queue", "event_bus"]
        ),
        AgentSpec(
            name="SecurityAgent",
            description="Ensures data privacy and system security.",
            responsibilities=[
                "Enforce access control policies.",
                "Monitor for suspicious activities.",
                "Handle data encryption/decryption."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["event_bus"]
        ),
        AgentSpec(
            name="AuditAgent",
            description="Maintains an immutable record of all agent actions and decisions.",
            responsibilities=[
                "Log all agent interactions.",
                "Ensure compliance with regulatory requirements.",
                "Provide auditable trails."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["queue"]
        ),
        AgentSpec(
            name="ConfigurationAgent",
            description="Manages the dynamic configuration and deployment of other agents.",
            responsibilities=[
                "Update agent parameters.",
                "Deploy new agent versions.",
                "Monitor agent health and resource usage."
            ],
            input_contract=AgentInput.model_json_schema(),
            output_contract=AgentOutput.model_json_schema(),
            communication_channels=["http", "queue"]
        ),
    ]

class OrchestrationFlow(BaseModel):
    steps: List[str]
    description: str
    # Further details like decision points, parallel execution, etc., can be added here

def get_orchestration_plan() -> OrchestrationFlow:
    return OrchestrationFlow(
        description="High-level plan for agent orchestration within the TwinCare AI platform.",
        steps=[
            "1. Receive SHARP context and patient ID.",
            "2. PatientDataAgent retrieves and processes relevant patient data.",
            "3. TwinGenerationAgent constructs/updates the PatientTwin.",
            "4. InsightGenerationAgent analyzes the PatientTwin to derive insights.",
            "5. InterventionPlanningAgent suggests interventions based on insights.",
            "6. CommunicationAgent formats and delivers insights/recommendations.",
            "7. EvaluationAgent monitors outcomes and provides feedback.",
            "8. AuditAgent logs all significant actions and decisions.",
            "9. SecurityAgent enforces policies throughout the flow."
        ]
    )