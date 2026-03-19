from typing import List, Dict, Any, Literal, Optional
from pydantic import BaseModel
from datetime import datetime

from twincare_ai.models.twin_state import TwinState
from twincare_ai.models.scenario_and_risk import RiskProjection, UncertaintyEstimate, Rationale, Scenario

class RiskProjectionAgent:
    """Agent responsible for projecting risks based on TwinState and scenarios."""

    def __init__(self):
        pass

    def _apply_deterministic_transforms(self, twin_state: TwinState, scenario: Scenario) -> Dict[str, Any]:
        """Applies deterministic transformations based on the scenario parameters (Tier 1)."""
        # Placeholder: This would involve direct calculations based on current twin state and scenario parameters
        # For example, if medication adherence is low, deterministically increase a risk factor.
        transformed_state = twin_state.model_dump()
        if scenario.parameters.get("medication_adherence") == "low":
            transformed_state["risk_factors"] = transformed_state.get("risk_factors", {}) # type: ignore
            transformed_state["risk_factors"]["adherence_impact"] = "negative" # type: ignore
        return transformed_state

    def _apply_guideline_heuristics(self, transformed_state: Dict[str, Any]) -> Dict[str, Any]:
        """Applies guideline-informed heuristics (Tier 2)."""
        # Placeholder: This would involve rules based on clinical guidelines
        # E.g., if HbA1c > 7% and no medication, flag for intervention.
        if transformed_state.get("risk_factors", {}).get("adherence_impact") == "negative" and \
           any("diabetes" in cond.code.get("text", "").lower() for cond in transformed_state.get("normalized_conditions", [])) and \
           not transformed_state.get("normalized_medications"): # type: ignore
            transformed_state["heuristic_flags"] = transformed_state.get("heuristic_flags", []) # type: ignore
            transformed_state["heuristic_flags"].append("unmanaged_diabetes_risk") # type: ignore
        return transformed_state

    def _apply_llm_reasoning(self, final_state: Dict[str, Any], scenario: Scenario) -> Dict[str, Any]:
        """Applies LLM-based generative reasoning for complex patterns (Tier 3)."""
        # Placeholder: In a real system, this would call an LLM to generate insights or refine risks
        # based on the aggregated data and scenario context.
        # For now, we'll simulate some LLM output.
        llm_insights = {"llm_summary": f"Based on scenario '{scenario.description}', the patient's condition is projected to {'worsen' if final_state.get('heuristic_flags') else 'remain stable'}."}
        return {**final_state, **llm_insights}

    def _calculate_directional_risk(self, initial_twin_state: TwinState, final_state: Dict[str, Any]) -> float:
        """Calculates a directional risk score (0.0 to 1.0) and its change."""
        # Placeholder: More sophisticated models would be here
        # Simple example: if any heuristic flag, risk is higher.
        initial_risk = 0.3 # Baseline
        projected_risk = initial_risk

        if final_state.get("heuristic_flags"):
            projected_risk += 0.4 # Increase risk if flagged

        return min(max(projected_risk, 0.0), 1.0) # Clamp between 0 and 1

    def _generate_uncertainty_estimates(self, risk_score: float, method: str = "heuristic_range") -> UncertaintyEstimate:
        """Generates uncertainty estimates for the risk projection."""
        # Placeholder: This would be based on model confidence, data quality, etc.
        if method == "heuristic_range":
            return UncertaintyEstimate(
                metric="risk_score",
                lower_bound=max(0.0, risk_score - 0.15),
                upper_bound=min(1.0, risk_score + 0.15),
                confidence_level=0.80, # Example: 80% confidence interval
                method=method
            )
        return UncertaintyEstimate(
            metric="risk_score", lower_bound=risk_score, upper_bound=risk_score, confidence_level=1.0, method="none"
        )

    def _generate_rationale(self, initial_twin_state: TwinState, final_state: Dict[str, Any], risk_score: float) -> List[Rationale]:
        """Generates rationales for the risk projection."""
        rationales: List[Rationale] = []

        rationales.append(Rationale(
            step="Deterministic Transforms",
            reasoning="Applied scenario parameters to modify patient state.",
            evidence=["Scenario parameters: medication_adherence=low"]
        ))
        if final_state.get("heuristic_flags"):
            rationales.append(Rationale(
                step="Guideline Heuristics",
                reasoning="Identified unmanaged diabetes risk based on clinical guidelines (HbA1c > 7%, no medication).",
                evidence=final_state.get("heuristic_flags", []) # type: ignore
            ))
        if final_state.get("llm_summary"):
            rationales.append(Rationale(
                step="LLM Reasoning",
                reasoning=final_state.get("llm_summary"), # type: ignore
                evidence=[]
            ))
        rationales.append(Rationale(
            step="Final Risk Calculation",
            reasoning=f"Projected risk score of {risk_score:.2f} based on aggregated factors.",
            evidence=[]
        ))

        return rationales

    def project_risk(self, initial_twin_state: TwinState, scenario: Scenario) -> RiskProjection:
        """Generates a risk projection for a given TwinState under a specific scenario."""
        # Tier 1: Deterministic Transforms
        transformed_state = self._apply_deterministic_transforms(initial_twin_state, scenario)

        # Tier 2: Guideline-informed Heuristics
        heuristic_state = self._apply_guideline_heuristics(transformed_state)

        # Tier 3: LLM-based Generative Reasoning
        final_state = self._apply_llm_reasoning(heuristic_state, scenario)

        # Calculate directional risk
        risk_score = self._calculate_directional_risk(initial_twin_state, final_state)
        directional_change: Literal["increasing", "decreasing", "stable"] = "stable"
        # Simple logic: if risk increased, then increasing
        if risk_score > 0.35: # Assuming 0.35 is a threshold for increased risk in this example
            directional_change = "increasing"

        # Generate uncertainty estimates
        uncertainty = self._generate_uncertainty_estimates(risk_score)

        # Generate rationales
        rationales = self._generate_rationale(initial_twin_state, final_state, risk_score)

        return RiskProjection(
            scenario_id=scenario.id,
            projected_outcome=final_state.get("llm_summary", "No specific LLM summary."), # type: ignore
            risk_score=risk_score,
            directional_change=directional_change,
            uncertainty=uncertainty,
            rationales=rationales,
            projected_at=datetime.utcnow().isoformat()
        )
