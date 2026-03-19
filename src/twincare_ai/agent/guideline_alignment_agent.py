from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

from twincare_ai.models.twin_state import TwinState
from twincare_ai.models.scenario_and_risk import Scenario

class GuidelineRecommendation(BaseModel):
    guideline_id: str = Field(..., description="Identifier for the clinical guideline.")
    recommendation_text: str = Field(..., description="The specific recommendation from the guideline.")
    applicability_score: float = Field(..., ge=0.0, le=1.0, description="How applicable this recommendation is to the current patient/scenario.")
    strength_of_evidence: Literal["strong", "moderate", "weak", "expert_opinion"] = Field(..., description="Strength of evidence supporting the recommendation.")
    source: str = Field(..., description="Source of the guideline (e.g., ADA, ACC/AHA).")

class ConsistencyCheckResult(BaseModel):
    guideline_id: str = Field(..., description="Identifier for the clinical guideline.")
    consistency_status: Literal["consistent", "inconsistent", "partially_consistent", "not_applicable"] = Field(..., description="Status of consistency with the guideline.")
    deviations: List[str] = Field(default_factory=list, description="List of observed deviations from the guideline.")
    rationale: str = Field(..., description="Explanation for the consistency status.")

class EvidenceStrength(BaseModel):
    claim: str = Field(..., description="The clinical claim or statement being evaluated.")
    strength: Literal["high", "moderate", "low", "insufficient"] = Field(..., description="Strength of evidence for the claim.")
    justification: str = Field(..., description="Justification for the assigned strength.")

class GuidelineAlignmentAgent:
    """Agent responsible for aligning patient data and scenarios with clinical guidelines."""

    def __init__(self):
        self._loaded_guidelines = self._load_relevant_guidelines()

    def _load_relevant_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """Loads predefined or external clinical guidelines."""
        # Placeholder: In a real system, this would load from a database, API, or local files.
        # Example: Simplified guideline snippets
        return {
            "ADA_Diabetes_2024": {
                "title": "ADA Standards of Medical Care in Diabetes - 2024",
                "recommendations": [
                    {"id": "ADA.DM.BP.1", "text": "For most adults with diabetes, a blood pressure target of <130/80 mmHg is appropriate.", "evidence": "strong"},
                    {"id": "ADA.DM.HbA1c.1", "text": "An A1C of 7% (53 mmol/mol) is recommended for many nonpregnant adults.", "evidence": "strong"}
                ]
            },
            "ACC_AHA_Hypertension_2017": {
                "title": "2017 ACC/AHA Guideline for the Prevention, Detection, Evaluation, and Management of High Blood Pressure in Adults",
                "recommendations": [
                    {"id": "ACC.HTN.BP.1", "text": "A threshold of 130/80 mmHg for hypertension is recommended.", "evidence": "strong"}
                ]
            }
        }

    def check_scenario_guideline_consistency(self, twin_state: TwinState, scenario: Scenario, guideline_id: str) -> ConsistencyCheckResult:
        """Checks the consistency of a patient's TwinState and a scenario with a specific guideline."""
        guideline = self._loaded_guidelines.get(guideline_id)
        if not guideline:
            return ConsistencyCheckResult(
                guideline_id=guideline_id,
                consistency_status="not_applicable",
                rationale=f"Guideline {guideline_id} not found."
            )

        deviations: List[str] = []
        consistency_status: Literal["consistent", "inconsistent", "partially_consistent", "not_applicable"] = "consistent"
        rationale_parts: List[str] = []

        # Example: Check HbA1c recommendation (ADA.DM.HbA1c.1)
        if guideline_id == "ADA_Diabetes_2024" and twin_state.normalized_patient:
            patient_hba1c_obs = [obs for obs in twin_state.normalized_observations if "HbA1c" in obs.code.get("coding",[{}])[0].get("display","")]
            if patient_hba1c_obs:
                latest_hba1c = patient_hba1c_obs[0].value # Assuming first is latest for simplicity
                if latest_hba1c and latest_hba1c > 7.0:
                    deviations.append(f"Current HbA1c ({latest_hba1c}%) is above recommended target (7%).")
                    consistency_status = "inconsistent" if consistency_status == "consistent" else "partially_consistent"
                    rationale_parts.append("HbA1c above target.")
            else:
                deviations.append("Missing recent HbA1c observation.")
                consistency_status = "partially_consistent"
                rationale_parts.append("Missing HbA1c data.")

        # Example: Check scenario parameters against guidelines
        if scenario.parameters.get("medication_adherence") == "low" and guideline_id == "ADA_Diabetes_2024":
            deviations.append("Scenario assumes low medication adherence, inconsistent with optimal diabetes management guidelines.")
            consistency_status = "inconsistent" if consistency_status == "consistent" else "partially_consistent"
            rationale_parts.append("Low medication adherence in scenario.")

        if not deviations and consistency_status == "consistent":
            rationale_parts.append("Patient data and scenario appear consistent with guideline recommendations.")

        return ConsistencyCheckResult(
            guideline_id=guideline_id,
            consistency_status=consistency_status,
            deviations=deviations,
            rationale=". ".join(rationale_parts)
        )

    def generate_evidence_strength_notes(self, claim: str) -> EvidenceStrength:
        """Generates notes on the strength of evidence for a given clinical claim."""
        # Placeholder: This would typically involve NLP on research papers or structured evidence databases.
        if "HbA1c target" in claim or "blood pressure control" in claim:
            return EvidenceStrength(
                claim=claim,
                strength="high",
                justification="Supported by numerous large-scale clinical trials and meta-analyses."
            )
        elif "novel biomarker" in claim:
            return EvidenceStrength(
                claim=claim,
                strength="low",
                justification="Limited peer-reviewed studies, mostly small cohort or animal studies."
            )
        return EvidenceStrength(
            claim=claim,
            strength="insufficient",
            justification="No direct evidence found or available to evaluate the claim."
        )

    def avoid_false_certainty_claims(self, input_text: str) -> str:
        """Modifies text to avoid conveying false certainty, adding probabilistic language."""
        # Placeholder: Simple text replacement for demonstration
        text = input_text.replace("is certain", "is likely")
        text = text.replace("will cause", "may cause")
        text = text.replace("definitely", "potentially")
        return text
