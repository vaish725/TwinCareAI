from typing import Dict, Any, List, Type
from pydantic import BaseModel, ValidationError

class DataValidationException(Exception):
    """Custom exception for data validation errors."""
    pass

def validate_fhir_resource_has_required_fields(resource: Dict[str, Any], required_fields: List[str]) -> None:
    """Checks if a FHIR resource contains all specified required fields."""
    for field in required_fields:
        if field not in resource:
            raise DataValidationException(f"FHIR resource missing required field: {field}")

def validate_fhir_bundle_structure(bundle: Dict[str, Any]) -> None:
    """Validates the basic structure of a FHIR Bundle."""
    if "resourceType" not in bundle or bundle["resourceType"] != "Bundle":
        raise DataValidationException("Invalid Bundle: 'resourceType' must be 'Bundle'.")
    if "type" not in bundle:
        raise DataValidationException("Invalid Bundle: Missing 'type' field.")
    if "entry" in bundle:
        if not isinstance(bundle["entry"], list):
            raise DataValidationException("Invalid Bundle: 'entry' must be a list.")
        for i, entry in enumerate(bundle["entry"]):
            if "resource" not in entry:
                raise DataValidationException(f"Invalid Bundle Entry {i}: Missing 'resource' field.")
            if "resourceType" not in entry["resource"]:
                raise DataValidationException(f"Invalid Bundle Entry {i}: Resource missing 'resourceType' field.")

def validate_pydantic_model(data: Dict[str, Any], model: Type[BaseModel]) -> BaseModel:
    """Validates data against a Pydantic model and returns an instance of the model."""
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise DataValidationException(f"Pydantic model validation error: {e}") from e

def validate_patient_id(patient_id: str) -> None:
    """Validates a patient ID. For now, simply checks if it's not empty.
    In a real application, this would involve more sophisticated checks (e.g., regex, database lookup).
    """
    if not patient_id or not patient_id.strip():
        raise DataValidationException("Patient ID cannot be empty.")
    # Further validation logic could be added here (e.g., regex, existence check)


# Example Usage (for demonstration/testing)
if __name__ == "__main__":
    # Test validate_fhir_resource_has_required_fields
    print("--- Testing FHIR Resource Required Fields ---")
    valid_patient = {"resourceType": "Patient", "id": "123", "name": "Test"}
    try:
        validate_fhir_resource_has_required_fields(valid_patient, ["id", "name"])
        print("Valid patient resource: OK")
    except DataValidationException as e:
        print(f"Valid patient resource: FAILED - {e}")

    invalid_patient = {"resourceType": "Patient", "id": "123"}
    try:
        validate_fhir_resource_has_required_fields(invalid_patient, ["id", "name"])
        print("Invalid patient resource (missing name): FAILED (should raise exception)")
    except DataValidationException as e:
        print(f"Invalid patient resource (missing name): OK - {e}")

    # Test validate_fhir_bundle_structure
    print("\n--- Testing FHIR Bundle Structure ---")
    valid_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "p1"}},
            {"resource": {"resourceType": "Observation", "id": "o1"}}
        ]
    }
    try:
        validate_fhir_bundle_structure(valid_bundle)
        print("Valid bundle structure: OK")
    except DataValidationException as e:
        print(f"Valid bundle structure: FAILED - {e}")

    invalid_bundle_type = {"resourceType": "Bundle", "entry": []}
    try:
        validate_fhir_bundle_structure(invalid_bundle_type)
        print("Invalid bundle (missing type): FAILED (should raise exception)")
    except DataValidationException as e:
        print(f"Invalid bundle (missing type): OK - {e}")

    invalid_bundle_entry = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "p1"}},
            {"no_resource_key": {}}
        ]
    }
    try:
        validate_fhir_bundle_structure(invalid_bundle_entry)
        print("Invalid bundle (bad entry): FAILED (should raise exception)")
    except DataValidationException as e:
        print(f"Invalid bundle (bad entry): OK - {e}")

    # Test validate_pydantic_model
    print("\n--- Testing Pydantic Model Validation ---")
    from pydantic import BaseModel

    class TestModel(BaseModel):
        name: str
        age: int

    valid_data = {"name": "Alice", "age": 30}
    try:
        model_instance = validate_pydantic_model(valid_data, TestModel)
        print(f"Valid Pydantic data: OK - {model_instance}")
    except DataValidationException as e:
        print(f"Valid Pydantic data: FAILED - {e}")

    invalid_data = {"name": "Bob", "age": "twenty"}
    try:
        model_instance = validate_pydantic_model(invalid_data, TestModel)
        print("Invalid Pydantic data (wrong type): FAILED (should raise exception)")
    except DataValidationException as e:
        print(f"Invalid Pydantic data (wrong type): OK - {e}")
