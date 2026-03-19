from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

from twincare_ai.models.twin_state import TwinState
from twincare_ai.models.scenario_and_risk import Scenario, RiskProjection, SimulationResult

class ExplanationSummary(BaseModel):
    summary_type: str = Field(..., description="Type of summary (e.g., 'clinician', 'patient').")
    content: str = Field(..., description="The generated explanation content.")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from the explanation.")
    target_audience: str = Field(..., description="Intended audience for this explanation.")

class AssumptionExplanation(BaseModel):
    assumption: str = Field(..., description="The assumption being explained.")
    justification: str = Field(..., description="Why this assumption was made.")
    impact: str = Field(..., description="Potential impact if this assumption is incorrect.")

class ChangeNarrative(BaseModel):
    change_description: str = Field(..., description="Description of what changed.")
    reason_for_change: str = Field(..., description="Explanation of why the change occurred.")
    implications: str = Field(..., description="Implications of the change on patient state or risk.")

class ExplanationAgent:
    """Agent responsible for generating clear and tailored explanations of twin state, scenarios, and risks."""

    def __init__(self):
        pass

    def generate_clinician_summary(
        self, 
        twin_state: TwinState, 
        scenario: Optional[Scenario] = None, 
        risk_projection: Optional[RiskProjection] = None
    ) -> ExplanationSummary:
        """Generates a detailed summary for clinicians."""
        summary_content = f"Patient ID: {twin_state.patient_id}.\n"
        summary_content += f"Current TwinState completeness: {twin_state.completeness_score:.1%}.\n"

        if twin_state.normalized_conditions:
            summary_content += "Key Conditions: " + ", ".join([c.code.get("text", "") for c in twin_state.normalized_conditions]) + ".\n"
        if twin_state.normalized_medications:
            summary_content += "Current Medications: " + ", ".join([m.medication_code.get("text", "") for m in twin_state.normalized_medications]) + ".\n"

        if scenario:
            summary_content += f"\nScenario Applied: {scenario.template_name} - {scenario.description}.\n"
            summary_content += f"Scenario Parameters: {scenario.parameters}.\n"

        if risk_projection:
            summary_content += f"\nProjected overall risk score: {risk_projection.overall_risk_score:.2f} (Confidence: {risk_projection.overall_confidence:.1%}).\n"
            summary_content += f"Key risk factors: {', '.join(risk_projection.key_risk_factors)}.\n"
            summary_content += f"Risk rationale: {risk_projection.rationale}.\n"

        return ExplanationSummary(
            summary_type="clinician_summary",
            content=summary_content,
            key_insights=["Current health status overview", "Scenario impact", "Projected risk factors"],
            target_audience="clinician"
        )

    def generate_patient_friendly_language(
        self, 
        twin_state: TwinState, 
        scenario: Optional[Scenario] = None, 
        risk_projection: Optional[RiskProjection] = None
    ) -> ExplanationSummary:
        """Generates a patient-friendly explanation in plain language."""
        patient_summary = f"Hello! Here's a summary of your health information.\n\n"
        patient_summary += f"Your current health data is {twin_state.completeness_score:.0%} complete.\n"

        if twin_state.normalized_conditions:
            patient_summary += "You have conditions such as " + ", ".join([c.code.get("text", "").lower() for c in twin_state.normalized_conditions]) + ".\n"
        if twin_state.normalized_medications:
            patient_summary += "You are currently taking medications like " + ", ".join([m.medication_code.get("text", "").lower() for m in twin_state.normalized_medications]) + ".\n"

        if scenario:
            patient_summary += f"\nWe looked at a 'what-if' situation where: {scenario.description}.\n"

        if risk_projection:
            patient_summary += f"\nBased on this, your estimated future health risk is {risk_projection.overall_risk_score:.0%}. "
            if risk_projection.overall_risk_score > 0.5:
                patient_summary += "This means there's a notable chance of health changes. Please discuss this with your doctor.\n"
            else:
                patient_summary += "This means your risk is currently low, but it's always good to stay proactive with your health.\n"
            patient_summary += f"Main things affecting this are: {', '.join(risk_projection.key_risk_factors)}.\n"

        return ExplanationSummary(
            summary_type="patient_friendly",
            content=patient_summary,
            key_insights=["Your health snapshot", "Potential future scenarios", "Key risk areas"],
            target_audience="patient"
        )

    def create_assumption_explanations(self, scenario: Scenario) -> List[AssumptionExplanation]:
        """Creates explanations for assumptions made within a scenario."""
        explanations: List[AssumptionExplanation] = []
        for assumption_text in scenario.assumptions:
            explanations.append(AssumptionExplanation(
                assumption=assumption_text,
                justification="This assumption was made to simplify the model or due to lack of specific data.",
                impact="If this assumption is incorrect, the simulation results or risk projections may be less accurate."
            ))
        if not scenario.assumptions and scenario.parameters:
             explanations.append(AssumptionExplanation(
                assumption="Default parameters used",
                justification="No specific assumptions were provided, so default scenario parameters were applied.",
                impact="The scenario might not perfectly reflect a real-world situation without specific inputs."
            ))

        return explanations

    def build_why_this_changed_narratives(self, 
        initial_state: TwinState, 
        final_state: TwinState, 
        scenario: Optional[Scenario] = None
    ) -> List[ChangeNarrative]:
        """Builds narratives explaining changes between two TwinStates, potentially due to a scenario."""
        narratives: List[ChangeNarrative] = []

        # Example: Changes in conditions
        initial_conditions = {c.code.get("text") for c in initial_state.normalized_conditions if c.code.get("text")}
        final_conditions = {c.code.get("text") for c in final_state.normalized_conditions if c.code.get("text")}

        new_conditions = final_conditions - initial_conditions
        if new_conditions:
            narratives.append(ChangeNarrative(
                change_description=f"New conditions observed: {', '.join(new_conditions)}.",
                reason_for_change="These conditions may have developed over time or were identified as part of the scenario simulation.",
                implications="New conditions can significantly impact overall health and treatment plans."
            ))
        
        # Example: Scenario-specific changes (e.g., medication adherence impacting risk)
        if scenario and scenario.parameters.get("medication_adherence") == "low":
            if initial_state.completeness_score > final_state.completeness_score: # Hypothetical, not directly from scenario
                narratives.append(ChangeNarrative(
                    change_description="A decrease in estimated medication adherence was noted.",
                    reason_for_change="This change was simulated based on the scenario parameters of 'low medication adherence'.",
                    implications="Reduced adherence can lead to worsening of chronic conditions and increased risk of complications."
                ))

        return narratives
