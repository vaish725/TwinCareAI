from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from twincare_ai.models.twin_state import TwinState
from twincare_ai.models.scenario_and_risk import ScenarioTemplate, Scenario

class ScenarioGeneratorAgent:
    """Agent responsible for generating plausible clinical scenarios based on a patient's TwinState."""

    def __init__(self, scenario_templates: Optional[List[ScenarioTemplate]] = None):
        self.scenario_templates = scenario_templates if scenario_templates is not None else self._load_default_templates()

    def _load_default_templates(self) -> List[ScenarioTemplate]:
        # In a real system, these would be loaded from a database or configuration files.
        # For this example, we define a few simple, hardcoded templates.
        return [
            ScenarioTemplate(
                id="template_exercise_increase",
                name="Increased Physical Activity",
                description="Patient starts moderate intensity exercise 3 times a week.",
                type="lifestyle_change",
                risk_factors_affected=["physical_activity", "weight"],
                expected_outcomes=["improved_glucose_control", "weight_loss"],
                required_twin_state_attributes=["current_activity_level", "bmi"],
                default_parameters={
                    "exercise_frequency": "3_times_week",
                    "intensity": "moderate",
                    "duration_minutes": 30
                }
            ),
            ScenarioTemplate(
                id="template_medication_adjustment",
                name="Medication Dose Adjustment",
                description="Adjusting a diabetes medication (e.g., Metformin) dose.",
                type="medication_change",
                risk_factors_affected=["medication_adherence", "glucose_levels"],
                expected_outcomes=["optimized_glucose_control", "reduced_side_effects"],
                required_twin_state_attributes=["current_medications", "hba1c"],
                default_parameters={
                    "medication_name": "Metformin",
                    "new_dose_mg": 1000,
                    "frequency": "daily"
                }
            ),
            ScenarioTemplate(
                id="template_dietary_intervention",
                name="Dietary Intervention",
                description="Patient adopts a low-carb diet plan.",
                type="lifestyle_change",
                risk_factors_affected=["diet", "glucose_levels", "weight"],
                expected_outcomes=["improved_glucose_control", "weight_loss", "reduced_carb_intake"],
                required_twin_state_attributes=["current_dietary_habits", "hba1c"],
                default_parameters={
                    "diet_type": "low_carb",
                    "carb_limit_grams": 50
                }
            ),
        ]

    def _check_plausibility(self, twin_state: TwinState, scenario_template: ScenarioTemplate) -> bool:
        """Checks if a scenario is plausible given the patient's current TwinState."""
        # Placeholder: In a real system, this would involve complex logic
        # checking against the patient's medical history, current conditions,
        # and the required_twin_state_attributes of the scenario.
        # For now, we'll assume plausibility if required attributes are conceptually present.
        print(f"Checking plausibility for {scenario_template.name} against TwinState...")
        # Example: if a medication scenario requires current_medications, ensure it exists.
        # This is a very simplified check.
        for attr in scenario_template.required_twin_state_attributes:
            if not hasattr(twin_state, attr) or getattr(twin_state, attr) is None:
                # In a real system, you'd check deeper, e.g., if current_medications contains the specific med.
                # For now, we'll just check for existence of the attribute.
                return False
        return True

    def generate_scenario(self, patient_id: str, twin_state: TwinState, template_name: str, overrides: Optional[Dict[str, Any]] = None) -> Optional[Scenario]:
        """Generates a specific Scenario instance from a template and patient TwinState."""
        matching_templates = [t for t in self.scenario_templates if t.name == template_name]
        if not matching_templates:
            print(f"Error: Scenario template '{template_name}' not found.")
            return None
        
        template = matching_templates[0]

        if not self._check_plausibility(twin_state, template):
            print(f"Scenario '{template_name}' is not plausible for patient {patient_id}.")
            return None

        # Merge default parameters with any provided overrides
        parameters = template.default_parameters.copy()
        if overrides:
            parameters.update(overrides)

        # Create a Scenario instance
        scenario = Scenario(
            id=f"{patient_id}_{template.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=template.name,
            description=template.description,
            type=template.type,
            patient_id=patient_id,
            parameters=parameters,
            time_horizon_days=template.default_parameters.get("time_horizon_days", 90), # Default or override
            expected_outcomes=template.expected_outcomes,
            risk_factors_affected=template.risk_factors_affected,
            clinical_guideline_refs=template.clinical_guideline_refs,
            created_at=datetime.now()
        )
        print(f"Generated scenario '{scenario.name}' for patient {patient_id}.")
        return scenario
