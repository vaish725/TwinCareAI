from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ScenarioDefinition(BaseModel):
    """Defines a specific simulation scenario."""
    scenario_id: str = Field(..., description="Unique identifier for the scenario.")
    name: str = Field(..., description="A human-readable name for the scenario.")
    description: str = Field(..., description="Detailed description of the intervention or changes being simulated.")
    simulation_horizon_days: int = Field(..., description="The duration of the simulation in days.")
    # Additional parameters specific to the scenario, e.g., medication changes, lifestyle interventions
    intervention_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters defining the intervention.")

class ScenarioResult(BaseModel):
    """Represents the outcome of a simulation scenario."""
    scenario_id: str = Field(..., description="Identifier of the scenario this result belongs to.")
    projected_outcome: Dict[str, Any] = Field(..., description="Key metrics and projected states after simulation.")
    relative_risk_movement: Dict[str, float] = Field(default_factory=dict, description="Change in various risk factors.")
    caution_notes: List[str] = Field(default_factory=list, description="Warnings or important considerations for the scenario.")
    uncertainty_estimate: float = Field(..., description="A numerical estimate of the uncertainty in the projection (e.g., 0.0 to 1.0).")
    rationale_chain: List[str] = Field(default_factory=list, description="Step-by-step reasoning for the projection.")

class AgentTrace(BaseModel):
    """Represents a trace of actions and outputs from an agent during a simulation."""
    agent_name: str = Field(..., description="Name of the agent that performed the action.")
    action: str = Field(..., description="Description of the action performed by the agent.")
    timestamp: str = Field(..., description="Timestamp when the action occurred (ISO 8601 format).")
    output: Dict[str, Any] = Field(default_factory=dict, description="Output or result of the agent's action.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the trace entry.")
