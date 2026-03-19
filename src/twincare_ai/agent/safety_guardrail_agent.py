from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

from twincare_ai.models.scenario_and_risk import Scenario, SimulationResult, RiskProjection
from twincare_ai.models.twin_state import TwinState

class SafetyFlag(BaseModel):
    flag_type: Literal["warning", "blocking", "info"] = Field(..., description="Type of safety flag.")
    message: str = Field(..., description="Detailed message about the safety concern.")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Severity of the safety flag.")
    rule_id: str = Field(..., description="Identifier of the safety rule triggered.")
    action_taken: Optional[str] = Field(None, description="Action taken by the guardrail (e.g., 'blocked_scenario', 'injected_disclaimer').")

class GuardrailOutput(BaseModel):
    original_output: Any = Field(..., description="The original output before guardrail application.")
    modified_output: Any = Field(..., description="The output after guardrail application (e.g., with disclaimers, sanitized).")
    safety_flags: List[SafetyFlag] = Field(default_factory=list, description="List of safety flags raised.")
    is_safe: bool = Field(..., description="True if the output is considered safe after guardrails, False otherwise.")

class SafetyGuardrailAgent:
    """Agent responsible for enforcing safety rules and ensuring responsible AI output."""

    def __init__(self):
        self.safety_rules = self._load_safety_rules()

    def _load_safety_rules(self) -> List[Dict[str, Any]]:
        """Loads predefined safety rules."""
        return [
            {"id": "SG001", "type": "no_definitive_advice", "pattern": "^You should.*$", "action": "disclaimer"},
            {"id": "SG002", "type": "missing_data", "threshold": 0.5, "action": "flag_and_downgrade"},
            {"id": "SG003", "type": "unsafe_scenario", "condition": "extreme_risk_increase", "action": "block"},
            {"id": "SG004", "type": "output_sanitization", "keywords": ["cure", "guarantee"], "action": "sanitize"},
        ]

    def apply_guardrails(
        self, 
        agent_output: Any, 
        twin_state: TwinState,
        scenario: Optional[Scenario] = None,
        risk_projection: Optional[RiskProjection] = None,
        simulation_results: Optional[List[SimulationResult]] = None,
    ) -> GuardrailOutput:
        """Applies various safety guardrails to the agent's output."""
        modified_output = agent_output # Start with original, modify as needed
        safety_flags: List[SafetyFlag] = []
        is_safe = True

        # Rule SG001: No definitive advice
        if isinstance(modified_output, str) and "you should" in modified_output.lower():
            modified_output = self._inject_disclaimer(modified_output)
            safety_flags.append(SafetyFlag(
                flag_type="warning",
                message="Output contained definitive advice. A disclaimer has been injected.",
                severity="medium",
                rule_id="SG001",
                action_taken="injected_disclaimer"
            ))

        # Rule SG002: Missing data flag enforcement and confidence downgrade
        if twin_state.completeness_score < 0.6: # Example threshold
            is_safe = False
            safety_flags.append(SafetyFlag(
                flag_type="blocking",
                message=f"Significant missing data detected (completeness: {twin_state.completeness_score}). Output confidence downgraded.",
                severity="high",
                rule_id="SG002",
                action_taken="confidence_downgraded"
            ))
            # Example: Modify risk_projection confidence if available
            if risk_projection:
                risk_projection.overall_confidence = max(0.1, risk_projection.overall_confidence * 0.5) # Drastically reduce

        # Rule SG003: Unsafe scenario blocking (placeholder logic)
        if scenario and simulation_results:
            # Hypothetical: check if a scenario leads to a critical health event with high probability
            # For demonstration, assume any scenario is 'unsafe' if it significantly worsens a metric
            if any(sr.risk_projection_snapshot.overall_risk_score > (risk_projection.overall_risk_score * 2) 
                   for sr in simulation_results if risk_projection): # If risk doubles
                is_safe = False
                safety_flags.append(SafetyFlag(
                    flag_type="blocking",
                    message=f"Scenario '{scenario.template_name}' deemed unsafe as it leads to significantly increased risk.",
                    severity="critical",
                    rule_id="SG003",
                    action_taken="blocked_scenario"
                ))

        # Rule SG004: Output sanitization
        if isinstance(modified_output, str):
            modified_output = self._sanitize_output(modified_output)
            if "cure" in agent_output.lower() or "guarantee" in agent_output.lower():
                safety_flags.append(SafetyFlag(
                    flag_type="warning",
                    message="Output contained potentially misleading or overly optimistic terms. Sanitized.",
                    severity="medium",
                    rule_id="SG004",
                    action_taken="sanitized_output"
                ))

        return GuardrailOutput(
            original_output=agent_output,
            modified_output=modified_output,
            safety_flags=safety_flags,
            is_safe=is_safe
        )

    def _inject_disclaimer(self, text: str) -> str:
        """Injects a disclaimer into the output text."""
        disclaimer = "\n\n[Disclaimer: This information is for informational purposes only and does not constitute medical advice. Consult with a qualified healthcare professional for diagnosis and treatment.]"
        return text + disclaimer

    def _sanitize_output(self, text: str) -> str:
        """Removes or replaces unsafe keywords."""
        text = text.replace("cure", "manage")
        text = text.replace("guarantee", "aim to")
        return text
