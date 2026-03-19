from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class ScenarioTemplate(BaseModel):
    name: str = Field(..., description="Unique name of the scenario template.")
    description: str = Field(..., description="Description of what this scenario entails.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters for the scenario.")
    validation_rules: List[str] = Field(default_factory=list, description="Rules for validating scenario plausibility.")
    constraints: List[str] = Field(default_factory=list, description="Data-driven constraints for the scenario.")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions made for this scenario.")

class Scenario(BaseModel):
    id: str = Field(..., description="Unique identifier for the generated scenario.")
    patient_id: str = Field(..., description="The ID of the patient this scenario applies to.")
    template_name: str = Field(..., description="Name of the template used to generate this scenario.")
    description: str = Field(..., description="A detailed description of the specific scenario.")
    parameters: Dict[str, Any] = Field(..., description="Specific parameters applied to this scenario instance.")
    assumptions: List[str] = Field(..., description="Specific assumptions for this scenario instance.")
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp of scenario generation.")

class UncertaintyEstimate(BaseModel):
    metric: str = Field(..., description="The metric for which uncertainty is estimated (e.g., 'risk_score').")
    lower_bound: float = Field(..., description="Lower bound of the confidence interval.")
    upper_bound: float = Field(..., description="Upper bound of the confidence interval.")
    confidence_level: float = Field(0.95, description="Confidence level of the interval (e.g., 0.95 for 95%).")
    method: str = Field(..., description="Method used to calculate the uncertainty estimate.")

class Rationale(BaseModel):
    step: str = Field(..., description="The step or decision for which rationale is provided.")
    reasoning: str = Field(..., description="Explanation of the reasoning behind the step/decision.")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence or data points.")

class RiskProjection(BaseModel):
    scenario_id: str = Field(..., description="The ID of the scenario this risk projection applies to.")
    projected_outcome: str = Field(..., description="Description of the projected outcome.")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="A numerical score representing the projected risk.")
    directional_change: Literal["increasing", "decreasing", "stable"] = Field(..., description="Indicates if risk is increasing, decreasing, or stable.")
    uncertainty: Optional[UncertaintyEstimate] = Field(None, description="Estimate of uncertainty for the risk projection.")
    rationales: List[Rationale] = Field(default_factory=list, description="Detailed rationales for the projection.")
    projected_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp of risk projection.")

class SimulationResult(BaseModel):
    scenario_id: str
    time_point: str # e.g., "P1Y" for 1 year, "2024-12-31"
    patient_id: str
    twin_state_snapshot: Dict[str, Any] # A snapshot of the TwinState at this time point
    risk_projection_snapshot: Optional[RiskProjection]
    events_occurred: List[str]

