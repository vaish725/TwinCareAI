from pydantic import BaseModel, Field
from typing import Dict, Any, List, Literal

# --- MCP Tool Interfaces ---

class ToolInputSchema(BaseModel):
    """Base schema for tool inputs."""
    pass

class ToolOutputSchema(BaseModel):
    """Base schema for tool outputs."""
    pass

class ToolInterface(BaseModel):
    name: str = Field(..., description="Unique name of the tool.")
    description: str = Field(..., description="A brief description of what the tool does.")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for the tool's input parameters.")
    output_schema: Dict[str, Any] = Field(..., description="JSON schema for the tool's output.")
    implementation_approach: str = Field(..., description="Planned approach for implementing this tool (e.g., 'API call', 'database query', 'internal function').")

# Example Tool Definitions

class GetPatientFhirDataInput(ToolInputSchema):
    patient_id: str = Field(..., description="The ID of the patient to retrieve FHIR data for.")
    resource_types: List[str] = Field(..., description="List of FHIR resource types to retrieve (e.g., Patient, Condition, Observation).")

class GetPatientFhirDataOutput(ToolOutputSchema):
    fhir_bundle: Dict[str, Any] = Field(..., description="A FHIR Bundle containing the requested patient data.")

class GenerateInsightsInput(ToolInputSchema):
    patient_twin_summary: Dict[str, Any] = Field(..., description="Summary of the patient's digital twin data.")
    insight_type: Literal["risk_assessment", "treatment_recommendation"] = Field(..., description="Type of insight to generate.")

class GenerateInsightsOutput(ToolOutputSchema):
    insights: List[str] = Field(..., description="List of generated insights.")
    confidence_score: float = Field(..., description="Confidence score for the generated insights.")

class SendNotificationInput(ToolInputSchema):
    recipient: str = Field(..., description="The recipient of the notification (e.g., clinician ID, email address).")
    message: str = Field(..., description="The content of the notification message.")
    urgency: Literal["low", "medium", "high"] = Field("medium", description="Urgency level of the notification.")

class SendNotificationOutput(ToolOutputSchema):
    success: bool = Field(..., description="True if the notification was sent successfully, false otherwise.")
    notification_id: str | None = Field(None, description="Optional ID of the sent notification.")

class UpdatePatientTwinInput(ToolInputSchema):
    patient_id: str = Field(..., description="The ID of the patient whose twin is to be updated.")
    updates: Dict[str, Any] = Field(..., description="A dictionary of updates to apply to the patient twin.")

class UpdatePatientTwinOutput(ToolOutputSchema):
    success: bool = Field(..., description="True if the patient twin was updated successfully.")
    message: str = Field(..., description="Status message regarding the update.")

class AuditLogEventInput(ToolInputSchema):
    agent_name: str = Field(..., description="Name of the agent performing the action.")
    event_type: str = Field(..., description="Type of audit event (e.g., 'data_access', 'insight_generation').")
    event_details: Dict[str, Any] = Field(..., description="Details of the audit event.")

class AuditLogEventOutput(ToolOutputSchema):
    log_id: str = Field(..., description="Unique ID for the audit log entry.")

def get_mcp_tool_interfaces() -> List[ToolInterface]:
    """Returns a list of defined MCP tool interfaces."""
    return [
        ToolInterface(
            name="GetPatientFhirData",
            description="Retrieves raw FHIR data for a specified patient and resource types.",
            input_schema=GetPatientFhirDataInput.model_json_schema(),
            output_schema=GetPatientFhirDataOutput.model_json_schema(),
            implementation_approach="API call to FHIR server"
        ),
        ToolInterface(
            name="GenerateInsights",
            description="Generates clinical insights or predictions based on patient twin data.",
            input_schema=GenerateInsightsInput.model_json_schema(),
            output_schema=GenerateInsightsOutput.model_json_schema(),
            implementation_approach="Internal AI model inference"
        ),
        ToolInterface(
            name="SendNotification",
            description="Sends a notification to a specified recipient with a given message and urgency.",
            input_schema=SendNotificationInput.model_json_schema(),
            output_schema=SendNotificationOutput.model_json_schema(),
            implementation_approach="External messaging service API"
        ),
        ToolInterface(
            name="UpdatePatientTwin",
            description="Applies updates to a patient's digital twin in the database.",
            input_schema=UpdatePatientTwinInput.model_json_schema(),
            output_schema=UpdatePatientTwinOutput.model_json_schema(),
            implementation_approach="Database ORM update"
        ),
        ToolInterface(
            name="AuditLogEvent",
            description="Logs an auditable event detailing agent actions and outcomes.",
            input_schema=AuditLogEventInput.model_json_schema(),
            output_schema=AuditLogEventOutput.model_json_schema(),
            implementation_approach="Internal logging service"
        ),
    ]
