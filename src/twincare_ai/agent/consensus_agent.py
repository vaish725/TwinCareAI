from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

from twincare_ai.models.scenario_and_risk import Scenario, RiskProjection, SimulationResult
from twincare_ai.agent.safety_guardrail_agent import GuardrailOutput, SafetyFlag

class AggregatedOutput(BaseModel):
    agent_id: str = Field(..., description="Identifier of the agent producing this output.")
    output_type: str = Field(..., description="Type of output (e.g., 'risk_projection', 'medication_impact').")
    content: Any = Field(..., description="The actual content of the agent's output.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score of the agent's output.")
    flags: List[SafetyFlag] = Field(default_factory=list, description="Safety flags associated with this output.")

class ScenarioComparison(BaseModel):
    scenario_id: str = Field(..., description="ID of the scenario.")
    projected_benefit_score: float = Field(..., description="A score representing the projected benefit or impact of the scenario.")
    key_differences: List[str] = Field(default_factory=list, description="Key differences compared to other scenarios or baseline.")
    overall_risk_score: float = Field(..., description="The final aggregated risk score for this scenario.")
    confidence_bucket: Literal["high", "medium", "low"] = Field(..., description="Categorization of the confidence level.")

class ConsensusResult(BaseModel):
    final_narrative: str = Field(..., description="A narrative summarizing the findings and recommendations.")
    scenario_comparisons: List[ScenarioComparison] = Field(default_factory=list, description="Comparison of all evaluated scenarios.")
    agent_disagreements: List[str] = Field(default_factory=list, description="Identified disagreements or discrepancies between agent outputs.")
    overall_confidence_bucket: Literal["high", "medium", "low"] = Field(..., description="Overall confidence in the consensus result.")

class ConsensusAgent:
    """Agent responsible for aggregating, comparing, and synthesizing outputs from specialist agents."""

    def __init__(self):
        pass

    def aggregate_outputs(self, outputs: List[AggregatedOutput]) -> Dict[str, List[AggregatedOutput]]:
        """Aggregates outputs from various specialist agents."""
        aggregated: Dict[str, List[AggregatedOutput]] = {}
        for output in outputs:
            aggregated.setdefault(output.output_type, []).append(output)
        return aggregated

    def rank_scenarios_by_benefit(
        self, 
        scenarios: List[Scenario],
        simulation_results_map: Dict[str, List[SimulationResult]]
    ) -> List[ScenarioComparison]:
        """Ranks scenarios based on their projected benefit or impact."""
        comparisons: List[ScenarioComparison] = []

        for scenario in scenarios:
            results = simulation_results_map.get(scenario.id, [])
            if not results:
                continue

            # Simple benefit calculation: inverse of final risk score
            final_risk_score = results[-1].risk_projection_snapshot.overall_risk_score
            projected_benefit = 1.0 - final_risk_score # Lower risk = higher benefit

            # Determine confidence bucket based on the final risk projection's confidence
            final_confidence = results[-1].risk_projection_snapshot.overall_confidence
            confidence_bucket: Literal["high", "medium", "low"]
            if final_confidence > 0.75: confidence_bucket = "high"
            elif final_confidence > 0.4: confidence_bucket = "medium"
            else: confidence_bucket = "low"

            comparisons.append(ScenarioComparison(
                scenario_id=scenario.id,
                projected_benefit_score=projected_benefit,
                key_differences=[f"Final risk score: {final_risk_score:.2f}"],
                overall_risk_score=final_risk_score,
                confidence_bucket=confidence_bucket
            ))
        
        # Sort by benefit score (descending)
        return sorted(comparisons, key=lambda x: x.projected_benefit_score, reverse=True)

    def handle_agent_disagreements(self, aggregated_outputs: Dict[str, List[AggregatedOutput]]) -> List[str]:
        """Identifies and reports disagreements between agent outputs."""
        disagreements: List[str] = []
        # Placeholder: More sophisticated logic would compare specific output fields
        if "risk_projection" in aggregated_outputs and len(aggregated_outputs["risk_projection"]) > 1:
            # Example: If risk projections from different agents vary widely
            risk_scores = [o.content.overall_risk_score for o in aggregated_outputs["risk_projection"] if hasattr(o.content, 'overall_risk_score')]
            if risk_scores and (max(risk_scores) - min(risk_scores)) > 0.3: # Arbitrary threshold
                disagreements.append("Significant variation in overall risk scores reported by different agents.")

        return disagreements

    def generate_final_comparison_narrative(
        self, 
        scenario_comparisons: List[ScenarioComparison],
        agent_disagreements: List[str]
    ) -> str:
        """Generates a narrative summarizing scenario comparisons and disagreements."""
        narrative = "Overall analysis of scenarios and agent outputs:\n\n"
        
        if scenario_comparisons:
            narrative += "Scenario Rankings (by projected benefit):\n"
            for comp in scenario_comparisons:
                narrative += f"- Scenario {comp.scenario_id}: Benefit Score {comp.projected_benefit_score:.2f}, Risk {comp.overall_risk_score:.2f}, Confidence: {comp.confidence_bucket}.\n"
        
        if agent_disagreements:
            narrative += "\nNoteworthy agent disagreements/discrepancies:\n"
            for disag in agent_disagreements:
                narrative += f"- {disag}\n"
        else:
            narrative += "\nNo significant disagreements identified among agent outputs."

        return narrative

    def compile_confidence_buckets(self, outputs: List[AggregatedOutput]) -> Literal["high", "medium", "low"]:
        """Compiles an overall confidence bucket based on individual agent outputs and flags."""
        total_confidence = 0.0
        num_outputs = 0
        has_critical_flags = False

        for output in outputs:
            if output.confidence is not None:
                total_confidence += output.confidence
                num_outputs += 1
            if any(f.severity == "critical" for f in output.flags):
                has_critical_flags = True
        
        if has_critical_flags: return "low"

        if num_outputs == 0: return "low" # No confidence if no outputs

        avg_confidence = total_confidence / num_outputs
        if avg_confidence > 0.75: return "high"
        elif avg_confidence > 0.4: return "medium"
        else: return "low"
