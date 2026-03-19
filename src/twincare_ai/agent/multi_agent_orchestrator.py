import asyncio
import logging
import traceback
from typing import List, Dict, Any, Optional, Literal, Callable, Awaitable
from pydantic import BaseModel, Field
from datetime import datetime

from twincare_ai.agent.specs import AgentSpec, AgentInput, AgentOutput
from twincare_ai.agent.orchestration import RetryStrategy, TimeoutStrategy, TraceLogEntry, OrchestrationStep
from twincare_ai.models.twin_state import TwinState
from twincare_ai.models.scenario_and_risk import Scenario, SimulationResult, RiskProjection
from twincare_ai.context.sharp_context import SHARPContext
from twincare_ai.agent.medication_impact_agent import MedicationImpactAgent
from twincare_ai.agent.guideline_alignment_agent import GuidelineAlignmentAgent
from twincare_ai.agent.context_intake_agent import ContextIntakeAgent
from twincare_ai.agent.twin_state_builder_agent import TwinStateBuilderAgent
from twincare_ai.agent.scenario_generator_agent import ScenarioGeneratorAgent
from twincare_ai.agent.risk_projection_agent import RiskProjectionAgent
from twincare_ai.agent.simulation_engine import SimulationEngine
from twincare_ai.agent.safety_guardrail_agent import SafetyGuardrailAgent, GuardrailOutput
from twincare_ai.agent.explanation_agent import ExplanationAgent, ExplanationSummary
from twincare_ai.agent.consensus_agent import ConsensusAgent, AggregatedOutput, ConsensusResult
from twincare_ai.mcp.mcp_server import MCPServer # Import MCPServer


logger = logging.getLogger(__name__)

class OrchestrationTrace(BaseModel):
    trace_id: str = Field(..., description="Unique identifier for this orchestration run.")
    start_time: str = Field(..., description="Timestamp when the orchestration started.")
    end_time: Optional[str] = Field(None, description="Timestamp when the orchestration ended.")
    status: Literal["running", "completed", "failed", "partial_failure"] = Field(..., description="Overall status of the orchestration.")
    log_entries: List[TraceLogEntry] = Field(default_factory=list, description="Chronological log of events during orchestration.")
    final_output: Optional[Any] = Field(None, description="The final aggregated output of the orchestration.")
    error_message: Optional[str] = Field(None, description="Error message if the orchestration failed.")

class OrchestratorResult(BaseModel):
    trace: OrchestrationTrace
    final_data: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)

class MultiAgentOrchestrator:
    """Orchestrates the execution of multiple specialist agents, managing sequencing, retries, and error handling."""

    def __init__(
        self,
        medication_impact_agent: MedicationImpactAgent,
        guideline_alignment_agent: GuidelineAlignmentAgent,
        context_intake_agent: ContextIntakeAgent,
        twin_state_builder_agent: TwinStateBuilderAgent,
        scenario_generator_agent: ScenarioGeneratorAgent,
        risk_projection_agent: RiskProjectionAgent,
        simulation_engine: SimulationEngine,
        safety_guardrail_agent: SafetyGuardrailAgent,
        explanation_agent: ExplanationAgent,
        consensus_agent: ConsensusAgent,
        mcp_server: Any, # Add MCP server instance
        retry_strategy: Optional[RetryStrategy] = None,
        timeout_strategy: Optional[TimeoutStrategy] = None,
        orchestration_steps: Optional[List[OrchestrationStep]] = None
    ):
        self.mcp_server = mcp_server # Assign mcp_server
        self.agents = {
            "MedicationImpactAgent": medication_impact_agent,
            "GuidelineAlignmentAgent": guideline_alignment_agent,
            "ContextIntakeAgent": context_intake_agent,
            "TwinStateBuilderAgent": twin_state_builder_agent,
            "ScenarioGeneratorAgent": scenario_generator_agent,
            "RiskProjectionAgent": risk_projection_agent,
            "SimulationEngine": simulation_engine,
            "SafetyGuardrailAgent": safety_guardrail_agent,
            "ExplanationAgent": explanation_agent,
            "ConsensusAgent": consensus_agent,
        }
        self.retry_strategy = retry_strategy or RetryStrategy()
        self.timeout_strategy = timeout_strategy or TimeoutStrategy()
        self.orchestration_steps = orchestration_steps or self._default_orchestration_steps()

    def _default_orchestration_steps(self) -> List[OrchestrationStep]:
        # Define a default, ordered sequence of operations for a typical flow
        return [
            OrchestrationStep(agent_name="ContextIntakeAgent", action="process_context", description="Parse initial context and resolve patient ID."),
            # Optional step: Invoke an MCP tool to fetch additional data or perform pre-processing
            OrchestrationStep(agent_name="MCPTool", action="invoke", description="Invoke an MCP tool for additional context or pre-processing.", optional=True, payload={"mcp_tool_name": "fetch_patient_context_bundle", "mcp_tool_input": {"patient_id": "{{resolved_patient_id}}"}}),
            OrchestrationStep(agent_name="TwinStateBuilderAgent", action="build_twin_state", description="Build or update the patient's TwinState."),
            OrchestrationStep(agent_name="ScenarioGeneratorAgent", action="generate_scenarios", description="Generate plausible 'what-if' scenarios, or use provided templates."),
            OrchestrationStep(agent_name="SimulationEngine", action="run_simulations", description="Run simulations for each generated scenario."),
            OrchestrationStep(agent_name="RiskProjectionAgent", action="project_risk_for_scenarios", description="Project risks for each simulation result."),
            OrchestrationStep(agent_name="MedicationImpactAgent", action="assess_medication_impact", description="Assess medication burden, interactions, and adherence."),
            OrchestrationStep(agent_name="GuidelineAlignmentAgent", action="check_alignment", description="Check alignment with clinical guidelines."),
            OrchestrationStep(agent_name="ConsensusAgent", action="form_consensus", description="Aggregate and form consensus from agent outputs."),
            OrchestrationStep(agent_name="SafetyGuardrailAgent", action="apply_guardrails", description="Apply safety guardrails to the consensus output."),
            OrchestrationStep(agent_name="ExplanationAgent", action="generate_explanations", description="Generate explanations for various stakeholders."),
        ]

    async def _execute_agent_step(
        self,
        agent_name: str,
        action: str,
        payload: Dict[str, Any],
        trace: OrchestrationTrace,
    ) -> Any:
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found.")

        method = getattr(agent, action, None)
        if not method or not asyncio.iscoroutinefunction(method):
            raise ValueError(f"Action {action} not found or not an async method for agent {agent_name}.")

        for attempt in range(self.retry_strategy.max_retries):
            try:
                logger.info(f"Executing {agent_name}.{action} (Attempt {attempt + 1})")
                trace.log_entries.append(TraceLogEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    agent_name=agent_name,
                    event_type="execution_start",
                    details={"action": action, "attempt": attempt + 1, "payload_keys": list(payload.keys())}
                ))
                
                result = await asyncio.wait_for(method(**payload), timeout=self.timeout_strategy.timeout_seconds)
                
                trace.log_entries.append(TraceLogEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    agent_name=agent_name,
                    event_type="execution_success",
                    details={"action": action, "result_type": str(type(result))}
                ))
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Timeout executing {agent_name}.{action} (Attempt {attempt + 1})")
                trace.log_entries.append(TraceLogEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    agent_name=agent_name,
                    event_type="execution_timeout",
                    details={"action": action, "attempt": attempt + 1}
                ))
            except Exception as e:
                logger.error(f"Error executing {agent_name}.{action} (Attempt {attempt + 1}): {e}")
                trace.log_entries.append(TraceLogEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    agent_name=agent_name,
                    event_type="execution_failure",
                    details={"action": action, "attempt": attempt + 1, "error": str(e), "traceback": traceback.format_exc()}
                ))
                if attempt == self.retry_strategy.max_retries - 1:
                    raise # Re-raise if all retries fail
                await asyncio.sleep(self.retry_strategy.delay_seconds * (self.retry_strategy.backoff_factor ** attempt))
        return None # Should not be reached

    async def orchestrate(
        self,
        trace_id: str,
        initial_sharp_context: Dict[str, Any],
        raw_prompt_opinion_context: Dict[str, Any],
        fhir_token_data: Dict[str, Any],
        patient_id_override: Optional[str] = None,
        scenario_templates: Optional[List[Scenario]] = None # Pre-defined scenarios for simulation/comparison
    ) -> OrchestratorResult:
        
        orchestration_trace = OrchestrationTrace(
            trace_id=trace_id,
            start_time=datetime.utcnow().isoformat(),
            status="running",
            log_entries=[]
        )
        
        # Data store for outputs from each step, keyed by agent_name_action for dependencies
        current_state: Dict[str, Any] = {
            "raw_sharp_context": initial_sharp_context,
            "raw_prompt_opinion_context": raw_prompt_opinion_context,
            "fhir_token_data": fhir_token_data,
            "patient_id_override": patient_id_override,
            "scenario_templates": scenario_templates
        }

        processed_outputs: Dict[str, Any] = {}
        errors: List[str] = []

        # Map of agent_name.action to actual result
        step_results: Dict[str, Any] = {}

        # Topological sort or simple sequential execution based on defined steps
        # For simplicity, we'll assume a fixed sequence for now.
        # A more robust system would handle dynamic dependencies and parallel execution.

        for step in self.orchestration_steps:
            try:
                # Collect inputs for the current step based on previous step_results or initial_state
                payload = {}

                # Dynamic payload rendering for optional steps
                if step.optional and step.payload:
                    rendered_payload = {}
                    for key, value in step.payload.items():
                        if isinstance(value, str) and "{{" in value and "}}" in value:
                            # Simple jinja-like rendering
                            for state_key, state_value in current_state.items():
                                value = value.replace(f"{{{{{state_key}}}}}", str(state_value))
                            rendered_payload[key] = value
                        else:
                            rendered_payload[key] = value
                    payload = rendered_payload
                else:
                    # Existing payload logic
                    pass # This block will be filled with existing payload logic

                if step.agent_name == "ContextIntakeAgent" and step.action == "process_context":
                    processed_context = await self.agents["ContextIntakeAgent"].process_context(
                        initial_sharp_context=initial_sharp_context,
                        raw_prompt_opinion_context=raw_prompt_opinion_context,
                        fhir_token_data=fhir_token_data,
                        patient_id_override=patient_id_override
                    )

                    step_results["ContextIntakeAgent.process_context"] = processed_context
                    current_state["resolved_patient_id"] = processed_context.resolved_patient_id
                    current_state["sharp_context"] = processed_context.sharp_context
                    current_state["fhir_token"] = processed_context.fhir_token
                    current_state["resource_fetch_plans"] = processed_context.resource_fetch_plans
                    current_state["prompt_opinion_context"] = processed_context.prompt_opinion_context

                elif step.agent_name == "MCPTool" and step.action == "invoke": # New step for MCP tool
                    # This is a placeholder for how an MCP tool might be invoked dynamically
                    # The payload would need to specify which MCP tool to call and with what input
                    mcp_tool_name = payload.get("mcp_tool_name")
                    mcp_tool_input = payload.get("mcp_tool_input", {})
                    if mcp_tool_name:
                        mcp_result = await self.mcp_server.invoke_tool(mcp_tool_name, mcp_tool_input)
                        step_results[f"MCPTool.{mcp_tool_name}"] = mcp_result
                        current_state["mcp_results"] = {**current_state.get("mcp_results", {}), mcp_tool_name: mcp_result}
                    else:
                        raise ValueError("MCP tool name not specified for invocation.")

                elif step.agent_name == "TwinStateBuilderAgent" and step.action == "build_twin_state":
                    patient_id = current_state.get("resolved_patient_id", "")
                    synthetic_fhir_bundle = {"resourceType": "Bundle", "entry": []} # Placeholder
                    
                    twin_state = await self.agents["TwinStateBuilderAgent"].build_twin_state(
                        patient_id=patient_id,
                        fhir_bundle=synthetic_fhir_bundle, # Placeholder
                        sharp_context=current_state.get("sharp_context")
                    )
                    step_results["TwinStateBuilderAgent.build_twin_state"] = twin_state
                    current_state["twin_state"] = twin_state

                elif step.agent_name == "ScenarioGeneratorAgent" and step.action == "generate_scenarios":
                    if current_state.get("scenario_templates"):
                        scenarios = current_state["scenario_templates"]
                        logger.info(f"Using provided scenario templates: {[s.name for s in scenarios]}")
                    else:
                        twin_state = current_state.get("twin_state")
                        scenarios = await self.agents["ScenarioGeneratorAgent"].generate_scenarios(twin_state=twin_state)
                        logger.info(f"Generated scenarios: {[s.name for s in scenarios]}")

                    step_results["ScenarioGeneratorAgent.generate_scenarios"] = scenarios
                    current_state["generated_scenarios"] = scenarios
                    current_state["generated_scenarios_by_id"] = {s.id: s for s in scenarios}

                elif step.agent_name == "SimulationEngine" and step.action == "run_simulations":
                    twin_state = current_state.get("twin_state")
                    scenarios = current_state.get("generated_scenarios", [])
                    simulation_results_map = {}
                    for scenario in scenarios:
                        sim_results = await self.agents["SimulationEngine"].run_simulation(twin_state, scenario)
                        simulation_results_map[scenario.id] = sim_results
                    step_results["SimulationEngine.run_simulations"] = simulation_results_map
                    current_state["simulation_results_map"] = simulation_results_map

                elif step.agent_name == "RiskProjectionAgent" and step.action == "project_risk_for_scenarios":
                    simulation_results_map = current_state.get("simulation_results_map", {})
                    projected_risks: Dict[str, Dict[str, RiskProjection]] = {}
                    generated_scenarios_by_id = current_state.get("generated_scenarios_by_id", {})

                    for scenario_id, sim_results in simulation_results_map.items():
                        projected_risks[scenario_id] = {
                            sr.time_point: await self.agents["RiskProjectionAgent"].project_risk(sr.twin_state_snapshot, generated_scenarios_by_id.get(scenario_id))
                            for sr in sim_results
                        }
                    step_results["RiskProjectionAgent.project_risk_for_scenarios"] = projected_risks
                    current_state["projected_risks"] = projected_risks

                elif step.agent_name == "MedicationImpactAgent" and step.action == "assess_medication_impact":
                    twin_state = current_state.get("twin_state")
                    if twin_state and twin_state.normalized_medications:
                        burden = self.agents["MedicationImpactAgent"].calculate_medication_burden(twin_state.normalized_medications)
                        interactions = self.agents["MedicationImpactAgent"].check_interactions(twin_state.normalized_medications)
                        adherence = self.agents["MedicationImpactAgent"].model_adherence_impact({}, twin_state.normalized_medications) # Placeholder patient_data
                        flags = self.agents["MedicationImpactAgent"].generate_caution_flags({}, twin_state.normalized_medications) # Placeholder patient_data
                        med_impact = {"burden": burden, "interactions": interactions, "adherence": adherence, "flags": flags}
                        step_results["MedicationImpactAgent.assess_medication_impact"] = med_impact
                        current_state["medication_impact"] = med_impact
                
                elif step.agent_name == "GuidelineAlignmentAgent" and step.action == "check_alignment":
                    twin_state = current_state.get("twin_state")
                    scenarios = current_state.get("generated_scenarios", [])
                    guideline_alignments = {}
                    if twin_state and scenarios:
                        for scenario in scenarios:
                            alignment_result = self.agents["GuidelineAlignmentAgent"].check_scenario_guideline_consistency(
                                twin_state, scenario, "ADA_Diabetes_2024"
                            )
                            guideline_alignments[scenario.id] = alignment_result
                    step_results["GuidelineAlignmentAgent.check_alignment"] = guideline_alignments
                    current_state["guideline_alignments"] = guideline_alignments

                elif step.agent_name == "ConsensusAgent" and step.action == "form_consensus":
                    simulation_results_map = current_state.get("simulation_results_map", {})
                    generated_scenarios = current_state.get("generated_scenarios", [])

                    aggregated_outputs: List[AggregatedOutput] = []

                    for scenario_id, sim_results in simulation_results_map.items():
                        for sim_result in sim_results:
                            if sim_result.risk_projection_snapshot:
                                aggregated_outputs.append(AggregatedOutput(
                                    agent_id="RiskProjectionAgent",
                                    output_type="risk_projection",
                                    content=sim_result.risk_projection_snapshot,
                                    confidence=sim_result.risk_projection_snapshot.overall_confidence,
                                    flags=[]
                                ))
                    
                    med_impact = current_state.get("medication_impact")
                    if med_impact:
                        aggregated_outputs.append(AggregatedOutput(
                            agent_id="MedicationImpactAgent",
                            output_type="medication_impact",
                            content=med_impact,
                            confidence=None, # Placeholder
                            flags=[]
                        ))
                    
                    guideline_alignments = current_state.get("guideline_alignments")
                    if guideline_alignments:
                        for scenario_id, alignment in guideline_alignments.items():
                            aggregated_outputs.append(AggregatedOutput(
                                agent_id="GuidelineAlignmentAgent",
                                output_type="guideline_alignment",
                                content=alignment,
                                confidence=alignment.applicability_score if hasattr(alignment, 'applicability_score') else None,
                                flags=[]
                            ))

                    aggregated_results_by_type = self.agents["ConsensusAgent"].aggregate_outputs(aggregated_outputs)
                    
                    ranked_scenarios = self.agents["ConsensusAgent"].rank_scenarios_by_benefit(generated_scenarios, simulation_results_map)

                    disagreements = self.agents["ConsensusAgent"].handle_agent_disagreements(aggregated_results_by_type)

                    # Generate final narrative
                    final_narrative = self.agents["ConsensusAgent"].generate_final_comparison_narrative(ranked_scenarios, disagreements)

                    # Compile overall confidence
                    overall_confidence_bucket = self.agents["ConsensusAgent"].compile_confidence_buckets(aggregated_outputs)

                    consensus_result = ConsensusResult(
                        final_narrative=final_narrative,
                        scenario_comparisons=ranked_scenarios,
                        agent_disagreements=disagreements,
                        overall_confidence_bucket=overall_confidence_bucket
                    )
                    step_results["ConsensusAgent.form_consensus"] = consensus_result
                    current_state["consensus_result"] = consensus_result

                elif step.agent_name == "SafetyGuardrailAgent" and step.action == "apply_guardrails":
                    # Apply guardrails to the final consensus result
                    consensus_result = current_state.get("consensus_result")
                    twin_state = current_state.get("twin_state")
                    scenarios = current_state.get("generated_scenarios", [])
                    simulation_results_map = current_state.get("simulation_results_map", {})
                    risk_projection = next(iter(current_state.get("projected_risks", {}).values()), {}).get("P0Y") # Get one risk projection for guardrail
                    
                    guardrail_output = self.agents["SafetyGuardrailAgent"].apply_guardrails(
                        agent_output=consensus_result,
                        twin_state=twin_state,
                        scenario=scenarios[0] if scenarios else None, # Pass a single scenario for guardrail check
                        risk_projection=risk_projection,
                        simulation_results=list(simulation_results_map.values())[0] if simulation_results_map else None # Pass a single list of sim results
                    )
                    step_results["SafetyGuardrailAgent.apply_guardrails"] = guardrail_output
                    current_state["guarded_consensus_result"] = guardrail_output

                elif step.agent_name == "ExplanationAgent" and step.action == "generate_explanations":
                    twin_state = current_state.get("twin_state")
                    consensus_result = current_state.get("consensus_result")
                    scenarios = current_state.get("generated_scenarios", [])
                    risk_projection = next(iter(current_state.get("projected_risks", {}).values()), {}).get("P0Y") # Get one risk projection

                    clinician_summary = self.agents["ExplanationAgent"].generate_clinician_summary(twin_state, scenarios[0] if scenarios else None, risk_projection)
                    patient_summary = self.agents["ExplanationAgent"].generate_patient_friendly_language(twin_state, scenarios[0] if scenarios else None, risk_projection)
                    assumption_explanations = []
                    if scenarios: assumption_explanations = self.agents["ExplanationAgent"].create_assumption_explanations(scenarios[0])

                    # Placeholder for 'why this changed' - requires initial and final twin states over time
                    # For now, let's just use the summaries
                    explanations = {
                        "clinician": clinician_summary,
                        "patient": patient_summary,
                        "assumptions": assumption_explanations
                    }
                    step_results["ExplanationAgent.generate_explanations"] = explanations
                    current_state["explanations"] = explanations

                processed_outputs[f"{step.agent_name}.{step.action}"] = step_results[f"{step.agent_name}.{step.action}"]

            except Exception as e:
                error_msg = f"Orchestration step failed for {step.agent_name}.{action}: {e}"
                logger.error(error_msg, exc_info=True)
                orchestration_trace.log_entries.append(TraceLogEntry(
                    timestamp=datetime.utcnow().isoformat(),
                    agent_name=step.agent_name,
                    event_type="step_failure",
                    details={"action": step.action, "error": str(e), "traceback": traceback.format_exc()}
                ))
                errors.append(error_msg)
                orchestration_trace.status = "partial_failure"
                # Decide if orchestration should continue or stop on failure
                # For now, we'll try to continue but mark as partial_failure
        
        # Final aggregation of relevant outputs
        final_output = {
            "twin_state": current_state.get("twin_state"),
            "scenarios": current_state.get("generated_scenarios"),
            "simulation_results": current_state.get("simulation_results_map"),
            "risk_projections": current_state.get("projected_risks"),
            "medication_impact": current_state.get("medication_impact"),
            "guideline_alignments": current_state.get("guideline_alignments"),
            "consensus_result": current_state.get("guarded_consensus_result"),
            "explanations": current_state.get("explanations"),
        }

        orchestration_trace.end_time = datetime.utcnow().isoformat()
        if not errors:
            orchestration_trace.status = "completed"
        orchestration_trace.final_output = final_output

        return OrchestratorResult(
            trace=orchestration_trace,
            final_data=final_output,
            errors=errors
        )


# Helper for async execution, if needed elsewhere
async def run_orchestration_example():
    # Instantiate all agents (with dummy dependencies for now)
    med_agent = MedicationImpactAgent()
    guide_agent = GuidelineAlignmentAgent()
    context_agent = ContextIntakeAgent()
    twin_builder = TwinStateBuilderAgent()
    scenario_gen = ScenarioGeneratorAgent()
    risk_proj = RiskProjectionAgent()
    sim_engine = SimulationEngine(risk_projector=risk_proj) # Needs risk projector
    safety_agent = SafetyGuardrailAgent()
    exp_agent = ExplanationAgent()
    cons_agent = ConsensusAgent()

    orchestrator = MultiAgentOrchestrator(
        medication_impact_agent=med_agent,
        guideline_alignment_agent=guide_agent,
        context_intake_agent=context_agent,
        twin_state_builder_agent=twin_builder,
        scenario_generator_agent=scenario_gen,
        risk_projection_agent=risk_proj,
        simulation_engine=sim_engine,
        safety_guardrail_agent=safety_agent,
        explanation_agent=exp_agent,
        consensus_agent=cons_agent,
    )

    # Dummy inputs
    sharp_context_data = {"patient": {"id": "test_pat_1", "gender": "female"}}
    prompt_opinion_context_data = {"patientGuid": "test_pat_1", "userRole": "clinician"}
    fhir_token_data = {"access_token": "dummy_token", "expires_in": 3600, "scope": "patient/*.read"}

    result = await orchestrator.orchestrate(
        trace_id="test_orchestration_001",
        initial_sharp_context=sharp_context_data,
        raw_prompt_opinion_context=prompt_opinion_context_data,
        fhir_token_data=fhir_token_data
    )

    print("\nOrchestration Result Status:", result.trace.status)
    print("Errors:", result.errors)
    # print("Final Data:", result.final_data)
    print("Number of log entries:", len(result.trace.log_entries))

if __name__ == "__main__":
    # Basic logging setup for console output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(run_orchestration_example())
