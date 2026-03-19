import pytest
from typing import Dict, Any, List
from datetime import datetime

from twincare_ai.agent.safety_guardrail_agent import SafetyGuardrailAgent
from twincare_ai.agent.explanation_agent import ExplanationAgent
from twincare_ai.agent.consensus_agent import ConsensusAgent, AggregatedOutput, ScenarioComparison
from twincare_ai.models.twin_state import TwinState, NormalizedPatient, NormalizedCondition, NormalizedMedication
from twincare_ai.models.scenario_and_risk import Scenario, RiskProjection, SimulationResult

# --- Fixtures for common test data ---

@pytest.fixture
def safety_guardrail_agent():
    return SafetyGuardrailAgent()

@pytest.fixture
def explanation_agent():
    return ExplanationAgent()

@pytest.fixture
def consensus_agent():
    return ConsensusAgent()

@pytest.fixture
def sample_normalized_patient() -> NormalizedPatient:
    return NormalizedPatient(id="pat1", gender="male", birth_date="1970-01-01")

@pytest.fixture
def sample_normalized_conditions() -> List[NormalizedCondition]:
    return [
        NormalizedCondition(id="cond1", code={"text": "Type 2 Diabetes"}, clinical_status={"text": "active"}, recorded_date="2023-01-01"),
    ]

@pytest.fixture
def sample_normalized_medications() -> List[NormalizedMedication]:
    return [
        NormalizedMedication(id="med1", medication_code={"text": "Metformin"}, status="active"),
    ]

@pytest.fixture
def sample_twin_state(sample_normalized_patient, sample_normalized_conditions, sample_normalized_medications) -> TwinState:
    return TwinState(
        patient_id="pat1",
        last_updated=datetime.utcnow().isoformat(),
        completeness_score=0.8,
        normalized_patient=sample_normalized_patient,
        normalized_conditions=sample_normalized_conditions,
        normalized_medications=sample_normalized_medications,
        normalized_observations=[],
        normalized_encounters=[],
    )

@pytest.fixture
def sample_low_completeness_twin_state(sample_normalized_patient) -> TwinState:
    return TwinState(
        patient_id="pat1",
        last_updated=datetime.utcnow().isoformat(),
        completeness_score=0.4, # Low completeness
        normalized_patient=sample_normalized_patient,
        normalized_conditions=[],
        normalized_medications=[],
        normalized_observations=[],
        normalized_encounters=[],
    )

@pytest.fixture
def sample_scenario() -> Scenario:
    return Scenario(
        id="scn_test_001",
        patient_id="pat1",
        template_name="Test Scenario",
        description="A test scenario description.",
        parameters={"param1": "value1"},
        assumptions=["Assumption A", "Assumption B"]
    )

@pytest.fixture
def sample_risk_projection() -> RiskProjection:
    return RiskProjection(
        scenario_id="scn_test_001",
        overall_risk_score=0.6,
        overall_confidence=0.7,
        key_risk_factors=["Diabetes Progression"],
        risk_breakdown={},
        rationale="Sample risk rationale.",
        uncertainty_estimate=0.1
    )

@pytest.fixture
def sample_simulation_results(sample_risk_projection) -> List[SimulationResult]:
    return [
        SimulationResult(
            scenario_id="scn_test_001",
            time_point="P0Y",
            patient_id="pat1",
            twin_state_snapshot={}, # Simplified
            risk_projection_snapshot=sample_risk_projection,
            events_occurred=[]
        ),
        SimulationResult(
            scenario_id="scn_test_001",
            time_point="P1Y",
            patient_id="pat1",
            twin_state_snapshot={}, # Simplified
            risk_projection_snapshot=RiskProjection(
                scenario_id="scn_test_001",
                overall_risk_score=0.7,
                overall_confidence=0.6,
                key_risk_factors=["Diabetes Progression"],
                risk_breakdown={},
                rationale="Sample risk rationale at 1 year.",
                uncertainty_estimate=0.15
            ),
            events_occurred=[]
        )
    ]


# --- Test Cases ---

def test_safety_guardrail_agent_integration(
    safety_guardrail_agent,
    sample_twin_state,
    sample_low_completeness_twin_state,
    sample_scenario,
    sample_risk_projection,
    sample_simulation_results
):
    # Test: No definitive advice & disclaimer injection
    output_with_advice = "You should take this medication."
    guardrail_output = safety_guardrail_agent.apply_guardrails(
        agent_output=output_with_advice,
        twin_state=sample_twin_state
    )
    assert "Disclaimer" in guardrail_output.modified_output
    assert any(flag.rule_id == "SG001" for flag in guardrail_output.safety_flags)

    # Test: Missing data flag enforcement
    guardrail_output_missing_data = safety_guardrail_agent.apply_guardrails(
        agent_output="Some output",
        twin_state=sample_low_completeness_twin_state,
        risk_projection=sample_risk_projection # Pass risk_projection to test confidence downgrade
    )
    assert not guardrail_output_missing_data.is_safe
    assert any(flag.rule_id == "SG002" for flag in guardrail_output_missing_data.safety_flags)
    assert guardrail_output_missing_data.original_output == "Some output"

    # Test: Unsafe scenario blocking (simplified: if risk doubles over time)
    # Create a scenario where risk appears to double
    unsafe_simulation_results = [
        sample_simulation_results[0],
        SimulationResult(
            scenario_id="scn_test_001",
            time_point="P1Y",
            patient_id="pat1",
            twin_state_snapshot={}, 
            risk_projection_snapshot=RiskProjection(
                scenario_id="scn_test_001",
                overall_risk_score=sample_risk_projection.overall_risk_score * 2.5, # More than double
                overall_confidence=0.5,
                key_risk_factors=["Rapid Decline"],
                risk_breakdown={},
                rationale="Risk doubled.",
                uncertainty_estimate=0.2
            ),
            events_occurred=[]
        )
    ]

    guardrail_output_unsafe_scenario = safety_guardrail_agent.apply_guardrails(
        agent_output="Scenario results",
        twin_state=sample_twin_state,
        scenario=sample_scenario,
        risk_projection=sample_risk_projection,
        simulation_results=unsafe_simulation_results
    )
    assert not guardrail_output_unsafe_scenario.is_safe
    assert any(flag.rule_id == "SG003" for flag in guardrail_output_unsafe_scenario.safety_flags)

    # Test: Output sanitization
    output_with_unsafe_terms = "This treatment will cure your diabetes and guarantee health."
    guardrail_output_sanitized = safety_guardrail_agent.apply_guardrails(
        agent_output=output_with_unsafe_terms,
        twin_state=sample_twin_state
    )
    assert "cure" not in guardrail_output_sanitized.modified_output.lower()
    assert "guarantee" not in guardrail_output_sanitized.modified_output.lower()
    assert any(flag.rule_id == "SG004" for flag in guardrail_output_sanitized.safety_flags)

def test_explanation_agent_integration(
    explanation_agent,
    sample_twin_state,
    sample_scenario,
    sample_risk_projection,
    sample_simulation_results
):
    # Test: Clinician-facing summary
    clinician_summary = explanation_agent.generate_clinician_summary(
        twin_state=sample_twin_state,
        scenario=sample_scenario,
        risk_projection=sample_risk_projection
    )
    assert "Patient ID: pat1" in clinician_summary.content
    assert "Scenario Applied: Test Scenario" in clinician_summary.content
    assert clinician_summary.target_audience == "clinician"

    # Test: Patient-friendly plain language
    patient_summary = explanation_agent.generate_patient_friendly_language(
        twin_state=sample_twin_state,
        scenario=sample_scenario,
        risk_projection=sample_risk_projection
    )
    assert "Hello! Here's a summary of your health information." in patient_summary.content
    assert "conditions such as type 2 diabetes" in patient_summary.content.lower()
    assert patient_summary.target_audience == "patient"

    # Test: Assumption explanations
    assumption_explanations = explanation_agent.create_assumption_explanations(sample_scenario)
    assert len(assumption_explanations) == 2
    assert assumption_explanations[0].assumption == "Assumption A"

    # Test: Why this changed narratives
    # Simulate a change in conditions for demonstration
    initial_twin_state_for_change = sample_twin_state.model_copy(deep=True)
    final_twin_state_for_change = sample_twin_state.model_copy(deep=True)
    final_twin_state_for_change.normalized_conditions.append(
        NormalizedCondition(id="cond3", code={"text": "Cardiovascular Disease"}, clinical_status={"text": "active"}, recorded_date="2024-01-01")
    )

    change_narratives = explanation_agent.build_why_this_changed_narratives(
        initial_state=initial_twin_state_for_change,
        final_state=final_twin_state_for_change
    )
    assert len(change_narratives) > 0
    assert any("New conditions observed: Cardiovascular Disease" in n.change_description for n in change_narratives)

def test_consensus_agent_integration(
    consensus_agent,
    sample_scenario,
    sample_risk_projection,
    sample_simulation_results
):
    # Create some mock aggregated outputs from different agents
    mock_aggregated_outputs = [
        AggregatedOutput(
            agent_id="risk_agent_1",
            output_type="risk_projection",
            content=sample_risk_projection,
            confidence=0.7,
            flags=[]
        ),
        AggregatedOutput(
            agent_id="risk_agent_2",
            output_type="risk_projection",
            content=RiskProjection(
                scenario_id="scn_test_001",
                overall_risk_score=0.65,
                overall_confidence=0.6,
                key_risk_factors=["Hypertension Progression"],
                risk_breakdown={},
                rationale="Another risk rationale.",
                uncertainty_estimate=0.12
            ),
            confidence=0.6,
            flags=[]
        ),
        AggregatedOutput(
            agent_id="medication_agent",
            output_type="medication_impact",
            content={"burden_score": 0.5},
            confidence=0.8,
            flags=[]
        )
    ]

    # Test: Aggregate outputs
    aggregated_results = consensus_agent.aggregate_outputs(mock_aggregated_outputs)
    assert "risk_projection" in aggregated_results
    assert "medication_impact" in aggregated_results
    assert len(aggregated_results["risk_projection"]) == 2

    # Test: Rank scenarios by benefit
    scenario_b_risk_projection = sample_risk_projection.model_copy(update={"overall_risk_score": 0.4, "overall_confidence": 0.8})
    scenario_b_simulation_results = [
        SimulationResult(
            scenario_id="scn_test_002",
            time_point="P0Y",
            patient_id="pat1",
            twin_state_snapshot={},
            risk_projection_snapshot=scenario_b_risk_projection,
            events_occurred=[]
        )
    ]
    mock_scenarios = [
        sample_scenario,
        Scenario(
            id="scn_test_002",
            patient_id="pat1",
            template_name="Better Outcome Scenario",
            description="A scenario with better outcome.",
            parameters={},
            assumptions=[]
        )
    ]
    simulation_results_map = {
        sample_scenario.id: sample_simulation_results,
        "scn_test_002": scenario_b_simulation_results
    }
    ranked_scenarios = consensus_agent.rank_scenarios_by_benefit(mock_scenarios, simulation_results_map)
    assert len(ranked_scenarios) == 2
    assert ranked_scenarios[0].scenario_id == "scn_test_002" # Should have higher benefit (lower risk)

    # Test: Handle agent disagreements
    disagreements = consensus_agent.handle_agent_disagreements(aggregated_results)
    assert len(disagreements) > 0 # Should detect variation in risk scores

    # Test: Generate final comparison narrative
    final_narrative = consensus_agent.generate_final_comparison_narrative(ranked_scenarios, disagreements)
    assert "Overall analysis of scenarios" in final_narrative
    assert "Noteworthy agent disagreements" in final_narrative

    # Test: Compile confidence buckets
    overall_confidence = consensus_agent.compile_confidence_buckets(mock_aggregated_outputs)
    assert overall_confidence in ["high", "medium", "low"]

    # Test with critical flag
    mock_outputs_with_critical = mock_aggregated_outputs + [
        AggregatedOutput(
            agent_id="safety_agent",
            output_type="guardrail_output",
            content={"message": "Critical issue"},
            confidence=0.1,
            flags=[{"flag_type": "blocking", "message": "Critical blocking issue", "severity": "critical", "rule_id": "SG00X"}]
        )
    ]
    overall_confidence_critical = consensus_agent.compile_confidence_buckets(mock_outputs_with_critical)
    assert overall_confidence_critical == "low"
