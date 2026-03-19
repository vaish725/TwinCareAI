from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from twincare_ai.models.twin_state import TwinState
from twincare_ai.models.scenario_and_risk import Scenario, RiskProjection, SimulationResult
from twincare_ai.agent.twin_state_builder_agent import TwinStateBuilderAgent
from twincare_ai.agent.risk_projection_agent import RiskProjectionAgent

class SimulationEngine:
    """Core engine for running simulations based on scenarios and projecting risks over time."""

    def __init__(self, twin_state_builder: Optional[TwinStateBuilderAgent] = None, risk_projector: Optional[RiskProjectionAgent] = None):
        self.twin_state_builder = twin_state_builder or TwinStateBuilderAgent()
        self.risk_projector = risk_projector or RiskProjectionAgent()

    def _apply_scenario_parameters(self, twin_state: TwinState, scenario: Scenario, current_time: datetime) -> TwinState:
        """Applies scenario parameters to evolve the TwinState over a time step."""
        # This is a highly simplified placeholder. In a real system, this would involve:
        # 1. Modifying specific attributes of the twin_state based on scenario.parameters
        # 2. Potentially simulating physiological changes or external events.
        # For now, let's assume some parameters directly affect the TwinState.

        # Example: if medication adherence is low, a hypothetical health metric might worsen
        if scenario.parameters.get("medication_adherence") == "low":
            # This is illustrative; actual logic would be more complex
            if twin_state.completeness_score > 0.1: # Prevent negative score
                twin_state.completeness_score -= 0.01 # Simulate slight worsening

        # Update last_updated time to reflect the simulated time point
        twin_state.last_updated = current_time.isoformat()

        return twin_state

    def run_simulation(self, initial_twin_state: TwinState, scenario: Scenario, time_horizon_years: int = 5) -> List[SimulationResult]:
        """Runs a simulation for a given TwinState and scenario over a specified time horizon."""
        simulation_results: List[SimulationResult] = []
        current_twin_state = initial_twin_state.model_copy(deep=True) # Create a deep copy to avoid modifying original
        start_date = datetime.now()

        for year in range(time_horizon_years + 1):
            current_time = start_date + timedelta(days=year * 365)
            time_point_str = f"P{year}Y"

            # Apply scenario parameters for the current time step
            current_twin_state = self._apply_scenario_parameters(current_twin_state, scenario, current_time)

            # Project risk for the current state under the scenario
            current_risk_projection = self.risk_projector.project_risk(current_twin_state, scenario)

            # Capture snapshot
            simulation_results.append(SimulationResult(
                scenario_id=scenario.id,
                time_point=time_point_str,
                patient_id=current_twin_state.patient_id,
                twin_state_snapshot=current_twin_state.model_dump(),
                risk_projection_snapshot=current_risk_projection,
                events_occurred=[] # Placeholder for simulated events
            ))

        return simulation_results
