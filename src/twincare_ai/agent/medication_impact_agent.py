from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal

from twincare_ai.models.twin_state import NormalizedMedication

class MedicationBurden(BaseModel):
    score: float = Field(..., description="A calculated score representing the overall medication burden.")
    details: str = Field(..., description="Details about factors contributing to the burden (e.g., polypharmacy).")

class DrugInteraction(BaseModel):
    medication_a: str = Field(..., description="Name or code of the first medication.")
    medication_b: str = Field(..., description="Name or code of the second medication.")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Severity of the interaction.")
    description: str = Field(..., description="Description of the potential interaction and its effects.")
    recommendation: Optional[str] = Field(None, description="Recommendation to manage the interaction.")

class AdherenceImpact(BaseModel):
    adherence_score: float = Field(..., ge=0.0, le=1.0, description="Estimated medication adherence score.")
    risk_factors: List[str] = Field(default_factory=list, description="Factors contributing to potential non-adherence.")
    impact_statement: str = Field(..., description="Statement on the impact of adherence on patient outcomes.")

class CautionFlag(BaseModel):
    flag_type: str = Field(..., description="Type of caution (e.g., 'RenalImpairment', 'LiverDisease').")
    description: str = Field(..., description="Description of the caution flag.")
    relevant_medications: List[str] = Field(default_factory=list, description="Medications affected by this caution.")

class MedicationImpactAgent:
    """Agent responsible for analyzing medication-related impacts."""

    def __init__(self):
        pass

    def calculate_medication_burden(self, medications: List[NormalizedMedication]) -> MedicationBurden:
        """Calculates medication burden based on the list of medications."""
        num_meds = len(medications)
        burden_score = min(num_meds * 0.1, 1.0) # Simple linear scale, capped at 1.0
        details = f"Patient is on {num_meds} medications. Polypharmacy risk increases with number of medications."
        return MedicationBurden(score=burden_score, details=details)

    def check_interactions(self, medications: List[NormalizedMedication]) -> List[DrugInteraction]:
        """Performs basic drug interaction checking."""
        interactions: List[DrugInteraction] = []
        # Placeholder: In a real system, this would integrate with a drug-interaction database.
        # Example: a hypothetical interaction
        if any("metformin" in m.medication_code.get("text", "").lower() for m in medications) and \
           any("contrast" in m.medication_code.get("text", "").lower() for m in medications):
            interactions.append(DrugInteraction(
                medication_a="Metformin",
                medication_b="Iodinated Contrast",
                severity="high",
                description="Risk of lactic acidosis with concurrent use in patients with renal impairment.",
                recommendation="Hold Metformin 48 hours before and after contrast administration."
            ))
        return interactions

    def model_adherence_impact(self, patient_data: Dict[str, Any], medications: List[NormalizedMedication]) -> AdherenceImpact:
        """Models the impact of medication adherence."""
        # Placeholder: This would use patient data (e.g., past refill history, social determinants)
        # to estimate adherence and its impact.
        adherence_score = 0.8 # Assume good adherence by default
        risk_factors: List[str] = []

        if patient_data.get("socioeconomic_status") == "low":
            adherence_score -= 0.1
            risk_factors.append("Socioeconomic factors")

        impact_statement = f"Estimated adherence score of {adherence_score:.2f}. "
        if adherence_score < 0.7:
            impact_statement += "Poor adherence significantly impacts treatment effectiveness."
        else:
            impact_statement += "Good adherence supports optimal treatment outcomes."

        return AdherenceImpact(
            adherence_score=adherence_score,
            risk_factors=risk_factors,
            impact_statement=impact_statement
        )

    def generate_caution_flags(self, patient_data: Dict[str, Any], medications: List[NormalizedMedication]) -> List[CautionFlag]:
        """Generates caution flags based on patient conditions and medications."""
        flags: List[CautionFlag] = []

        # Example: Renal impairment flag
        if patient_data.get("renal_function") == "impaired": # Hypothetical field
            flags.append(CautionFlag(
                flag_type="RenalImpairment",
                description="Patient has impaired renal function, requiring dose adjustments for renally-cleared drugs.",
                relevant_medications=["Metformin", "Lisinopril"] # Example drugs
            ))
        return flags
