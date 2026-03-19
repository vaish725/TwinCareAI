from enum import Enum

class FhirResourceScope(Enum):
    PATIENT = "Patient"
    CONDITION = "Condition"
    MEDICATION_REQUEST = "MedicationRequest"
    OBSERVATION = "Observation"
    ENCOUNTER = "Encounter"
    # Additional resources mentioned in PRD, but not yet explicitly used:
    # CARE_PLAN = "CarePlan"
    # ALLERGY_INTOLERANCE = "AllergyIntolerance"
    # PROCEDURE = "Procedure"
    # SERVICE_REQUEST = "ServiceRequest"

# A list of the string values for easy iteration
FHIR_RESOURCE_TYPES_IN_SCOPE = [
    FhirResourceScope.PATIENT.value,
    FhirResourceScope.CONDITION.value,
    FhirResourceScope.MEDICATION_REQUEST.value,
    FhirResourceScope.OBSERVATION.value,
    FhirResourceScope.ENCOUNTER.value,
]
