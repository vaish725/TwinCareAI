import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from twincare_ai.models.twin_state import (
    TwinState, NormalizedPatient, NormalizedCondition, NormalizedMedication,
    NormalizedObservation, NormalizedEncounter, CareGap, MissingDataReport
)
from twincare_ai.fhir.fhir_ingestion_service import FhirIngestionService

class TwinStateBuilderAgent:
    """Agent responsible for building and updating the TwinState from FHIR data."""

    def __init__(self, ingestion_service: Optional[FhirIngestionService] = None):
        self.ingestion_service = ingestion_service or FhirIngestionService()

    def _calculate_completeness_score(self, processed_fhir_data: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculates a completeness score based on the presence of key FHIR resources."""
        total_expected_types = 5 # Patient, Condition, Medication, Observation, Encounter
        present_types = 0

        if processed_fhir_data.get("Patient"): present_types += 1
        if processed_fhir_data.get("Condition"): present_types += 1
        if processed_fhir_data.get("MedicationRequest") or processed_fhir_data.get("MedicationStatement"): present_types += 1
        if processed_fhir_data.get("Observation"): present_types += 1
        if processed_fhir_data.get("Encounter"): present_types += 1

        if total_expected_types == 0: return 0.0 # Avoid division by zero
        return present_types / total_expected_types

    def _identify_care_gaps(self, twin_state: TwinState) -> List[CareGap]:
        """Identifies potential care gaps based on the TwinState data."""
        gaps: List[CareGap] = []

        # Example: Check for missing key observations for diabetes management
        has_hba1c = any("HbA1c" in obs.code.get("coding",[{}])[0].get("display","") for obs in twin_state.normalized_observations)
        has_blood_pressure = any("Blood pressure" in obs.code.get("coding",[{}])[0].get("display","") for obs in twin_state.normalized_observations)

        if not has_hba1c:
            gaps.append(CareGap(
                type="MissingHbA1c",
                description="Missing recent HbA1c observation for diabetes management.",
                severity="high",
                recommendation="Order HbA1c test."
            ))
        if not has_blood_pressure:
            gaps.append(CareGap(
                type="MissingBloodPressure",
                description="Missing recent blood pressure observation.",
                severity="medium",
                recommendation="Record blood pressure at next visit."
            ))

        # Example: Check for patient with diabetes but no active medication
        has_diabetes = any("diabetes" in cond.code.get("text", "").lower() for cond in twin_state.normalized_conditions)
        has_medication = bool(twin_state.normalized_medications)

        if has_diabetes and not has_medication:
            gaps.append(CareGap(
                type="UnmanagedDiabetes",
                description="Patient has diabetes but no active medication recorded.",
                severity="high",
                recommendation="Review diabetes management plan and consider medication."
            ))

        return gaps

    def _generate_missing_data_report(self, processed_fhir_data: Dict[str, List[Dict[str, Any]]]) -> List[MissingDataReport]:
        """Generates a report on missing expected data points."""
        report: List[MissingDataReport] = []

        expected_patient_fields = ["gender", "birth_date"]
        if not processed_fhir_data.get("Patient"):
            report.append(MissingDataReport(
                resource_type="Patient",
                missing_fields=expected_patient_fields, # Assuming all are missing if no patient resource
                impact="Cannot build basic patient profile."
            ))
        else:
            patient_data = processed_fhir_data["Patient"][0]
            missing = [f for f in expected_patient_fields if not patient_data.get(f)]
            if missing:
                report.append(MissingDataReport(
                    resource_type="Patient",
                    missing_fields=missing,
                    impact="Incomplete patient demographic information."
                ))

        # Add more checks for other resource types and critical fields as needed
        if not processed_fhir_data.get("Condition"):
            report.append(MissingDataReport(
                resource_type="Condition",
                missing_fields=["code", "clinical_status"],
                impact="Cannot identify patient's health conditions."
            ))
        if not processed_fhir_data.get("Observation"):
            report.append(MissingDataReport(
                resource_type="Observation",
                missing_fields=["code", "value"],
                impact="Missing vital signs and lab results."
            ))

        return report

    def build_twin_state(self, patient_id: str, raw_fhir_bundle: Dict[str, Any], observation_filter_codes: Optional[List[str]] = None) -> TwinState:
        """Builds a TwinState object from raw FHIR bundle data."""
        processed_data = self.ingestion_service.ingest_and_process_fhir_bundle(raw_fhir_bundle, observation_filter_codes)

        # Extract normalized data for TwinState construction
        normalized_patient = processed_data.get("Patient", [None])[0]
        normalized_conditions = [NormalizedCondition(**c) for c in processed_data.get("Condition", [])]
        normalized_medications = [
            NormalizedMedication(**m) for m in 
            processed_data.get("MedicationRequest", []) + processed_data.get("MedicationStatement", [])
        ]
        normalized_observations = [NormalizedObservation(**o) for o in processed_data.get("Observation", [])]
        normalized_encounters = [NormalizedEncounter(**e) for e in processed_data.get("Encounter", [])]

        completeness_score = self._calculate_completeness_score(processed_data)

        # Create an initial TwinState to pass to care gap and missing data functions
        temp_twin_state = TwinState(
            patient_id=patient_id,
            last_updated=datetime.utcnow().isoformat(),
            completeness_score=completeness_score,
            normalized_patient=NormalizedPatient(**normalized_patient) if normalized_patient else None,
            normalized_conditions=normalized_conditions,
            normalized_medications=normalized_medications,
            normalized_observations=normalized_observations,
            normalized_encounters=normalized_encounters,
        )

        care_gaps = self._identify_care_gaps(temp_twin_state)
        missing_data_report = self._generate_missing_data_report(processed_data)

        # Final TwinState object
        twin_state = TwinState(
            patient_id=patient_id,
            last_updated=datetime.utcnow().isoformat(),
            completeness_score=completeness_score,
            normalized_patient=NormalizedPatient(**normalized_patient) if normalized_patient else None,
            normalized_conditions=normalized_conditions,
            normalized_medications=normalized_medications,
            normalized_observations=normalized_observations,
            normalized_encounters=normalized_encounters,
            care_gaps=care_gaps,
            missing_data_report=missing_data_report,
            # raw_fhir_data_references can be populated if needed, e.g., with bundle ID
        )

        return twin_state
