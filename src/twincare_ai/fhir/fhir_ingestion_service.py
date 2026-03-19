import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx # For making async HTTP requests

from twincare_ai.fhir.resource_scope import FHIR_RESOURCE_TYPES_IN_SCOPE
from twincare_ai.models.api_models import FhirToken # Import FhirToken

class FhirIngestionService:
    """Service to ingest and extract FHIR resources from bundles and interact with FHIR servers."""

    def __init__(
        self, 
        fhir_base_url: Optional[str] = None,
        fhir_token: Optional[FhirToken] = None
    ):
        self.fhir_base_url = fhir_base_url
        self.fhir_token = fhir_token
        self.http_client = httpx.AsyncClient()

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Generates authentication headers from the FHIR token."""
        if self.fhir_token:
            return {"Authorization": f"{self.fhir_token.token_type} {self.fhir_token.access_token}"}
        return {}

    async def fetch_fhir_resource(self, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches a single FHIR resource from the configured FHIR server.
        Requires fhir_base_url and fhir_token to be set.
        """
        if not self.fhir_base_url:
            print("Error: FHIR base URL not configured for fetching.")
            return None
        
        url = f"{self.fhir_base_url}/{resource_type}/{resource_id}"
        headers = await self._get_auth_headers()
        
        try:
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status() # Raises an exception for 4xx/5xx responses
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error fetching {resource_type}/{resource_id}: {e}")
        except httpx.RequestError as e:
            print(f"Request error fetching {resource_type}/{resource_id}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred fetching {resource_type}/{resource_id}: {e}")
        return None

    async def search_fhir_resources(self, resource_type: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Searches for FHIR resources from the configured FHIR server based on type and filters.
        Requires fhir_base_url and fhir_token to be set.
        """
        if not self.fhir_base_url:
            print("Error: FHIR base URL not configured for searching.")
            return []

        url = f"{self.fhir_base_url}/{resource_type}"
        headers = await self._get_auth_headers()
        
        try:
            response = await self.http_client.get(url, headers=headers, params=filters)
            response.raise_for_status() # Raises an exception for 4xx/5xx responses
            bundle = response.json()
            return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error searching {resource_type} with filters {filters}: {e}")
        except httpx.RequestError as e:
            print(f"Request error searching {resource_type} with filters {filters}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred searching {resource_type} with filters {filters}: {e}")
        return []

    def update_fhir_token(self, fhir_token: Optional[FhirToken]):
        """Updates the FHIR token used for authenticated requests."""
        self.fhir_token = fhir_token

    def load_bundle_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Loads a FHIR bundle from a JSON file."""
        if not file_path.exists():
            raise FileNotFoundError(f"FHIR bundle file not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_resources_by_type(self, bundle: Dict[str, Any], resource_type: str) -> List[Dict[str, Any]]:
        """Extracts all resources of a specific type from a FHIR bundle."""
        extracted_resources = []
        if "entry" in bundle:
            for entry in bundle["entry"]:
                if "resource" in entry and entry["resource"].get("resourceType") == resource_type:
                    extracted_resources.append(entry["resource"])
        return extracted_resources

    def extract_all_scoped_resources(self, bundle: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Extracts all resources within the defined FHIR_RESOURCE_TYPES_IN_SCOPE from a bundle."""
        all_scoped_resources: Dict[str, List[Dict[str, Any]]] = {
            res_type: [] for res_type in FHIR_RESOURCE_TYPES_IN_SCOPE
        }
        if "entry" in bundle:
            for entry in bundle["entry"]:
                if "resource" in entry:
                    resource = entry["resource"]
                    resource_type = resource.get("resourceType")
                    if resource_type in FHIR_RESOURCE_TYPES_IN_SCOPE:
                        all_scoped_resources[resource_type].append(resource)
        return all_scoped_resources

    def _get_resource_id(self, resource: Dict[str, Any]) -> Optional[str]:
        """Helper to get a resource's logical ID."""
        return resource.get("id")

    def _normalize_patient(self, patient_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes patient demographic data."""
        normalized = {
            "id": self._get_resource_id(patient_resource),
            "gender": patient_resource.get("gender"),
            "birth_date": patient_resource.get("birthDate"),
            "marital_status": patient_resource.get("maritalStatus", {}).get("coding", [{}])[0].get("display"),
            "address": patient_resource.get("address", [None])[0], # Taking first address if available
            "telecom": patient_resource.get("telecom", [])
        }
        return {k: v for k, v in normalized.items() if v is not None}

    def _normalize_condition(self, condition_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes condition data."""
        normalized = {
            "id": self._get_resource_id(condition_resource),
            "code": condition_resource.get("code"),
            "clinical_status": condition_resource.get("clinicalStatus"),
            "recorded_date": condition_resource.get("recordedDate")
        }
        return {k: v for k, v in normalized.items() if v is not None}

    def _normalize_medication(self, medication_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes medication request/statement data."""
        normalized = {
            "id": self._get_resource_id(medication_resource),
            "medication_code": medication_resource.get("medicationCodeableConcept"),
            "status": medication_resource.get("status"),
            "authored_on": medication_resource.get("authoredOn") or medication_resource.get("dateAsserted")
        }
        return {k: v for k, v in normalized.items() if v is not None}

    def _normalize_observation(self, observation_resource: Dict[str, Any], filter_codes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Normalizes observation data and optionally filters by code."""
        code = observation_resource.get("code", {})
        coding = code.get("coding", [{}])
        code_system = coding[0].get("system")
        code_value = coding[0].get("code")

        if filter_codes and f"{code_system}|{code_value}" not in filter_codes and code_value not in filter_codes:
            return None # Filtered out

        value_concept = observation_resource.get("valueCodeableConcept", {})
        value_quantity = observation_resource.get("valueQuantity", {})

        value = None
        unit = None

        if value_quantity:
            value = value_quantity.get("value")
            unit = value_quantity.get("unit")
        elif value_concept:
            value = value_concept.get("coding", [{}])[0].get("display")

        normalized = {
            "id": self._get_resource_id(observation_resource),
            "code": code,
            "value": value,
            "unit": unit,
            "effective_date": observation_resource.get("effectiveDateTime") or observation_resource.get("effectivePeriod", {}).get("start")
        }
        return {k: v for k, v in normalized.items() if v is not None}

    def _normalize_encounter(self, encounter_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes encounter data."""
        normalized = {
            "id": self._get_resource_id(encounter_resource),
            "status": encounter_resource.get("status"),
            "period": encounter_resource.get("period"),
            "service_type": encounter_resource.get("serviceType")
        }
        return {k: v for k, v in normalized.items() if v is not None}

    def deduplicate_bundle(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Removes duplicate resources from a FHIR bundle based on resourceType and ID."""
        if "entry" not in bundle:
            return bundle

        seen_resources = set()
        deduplicated_entries = []

        for entry in bundle["entry"]:
            resource = entry.get("resource")
            if resource:
                resource_type = resource.get("resourceType")
                resource_id = self._get_resource_id(resource)
                if resource_type and resource_id:
                    identifier = f"{resource_type}/{resource_id}"
                    if identifier not in seen_resources:
                        deduplicated_entries.append(entry)
                        seen_resources.add(identifier)
                else:
                    # Include resources without a clear ID for now, or handle as needed
                    deduplicated_entries.append(entry)
            else:
                deduplicated_entries.append(entry) # Include non-resource entries

        bundle["entry"] = deduplicated_entries
        return bundle

    def ingest_and_process_fhir_bundle(self, raw_bundle: Dict[str, Any], observation_filter_codes: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Ingests a raw FHIR bundle, deduplicates, extracts, and normalizes resources.
        Handles missing/stale data by returning only successfully processed resources.
        """
        processed_data: Dict[str, List[Dict[str, Any]]] = {
            "Patient": [], "Condition": [], "MedicationRequest": [], "MedicationStatement": [],
            "Observation": [], "Encounter": []
        }
        deduplicated_bundle = self.deduplicate_bundle(raw_bundle)
        scoped_resources = self.extract_all_scoped_resources(deduplicated_bundle)

        for res_type, resources in scoped_resources.items():
            for resource in resources:
                normalized_resource = None
                try:
                    if res_type == "Patient":
                        normalized_resource = self._normalize_patient(resource)
                    elif res_type == "Condition":
                        normalized_resource = self._normalize_condition(resource)
                    elif res_type == "MedicationRequest" or res_type == "MedicationStatement":
                        normalized_resource = self._normalize_medication(resource)
                    elif res_type == "Observation":
                        normalized_resource = self._normalize_observation(resource, observation_filter_codes)
                    elif res_type == "Encounter":
                        normalized_resource = self._normalize_encounter(resource)

                    if normalized_resource:
                        processed_data[res_type].append(normalized_resource)
                except Exception as e:
                    print(f"Error normalizing {res_type} resource {self._get_resource_id(resource)}: {e}")
                    # Gracefully handle by skipping this resource

        return processed_data

if __name__ == "__main__":
    # Example Usage:
    ingestion_service = FhirIngestionService()
    synthetic_data_dir = Path(__file__).parent.parent.parent.parent / "data" / "fhir_synthetic"

    print(f"\n--- Processing {synthetic_data_dir.name} ---")

    for patient_file in synthetic_data_dir.glob("patient_*.json"):
        print(f"\nLoading and processing: {patient_file.name}")
        try:
            bundle = ingestion_service.load_bundle_from_file(patient_file)
            print(f"Bundle loaded. Contains {len(bundle.get('entry', []))} entries.")

            # Ingest and process the FHIR bundle
            processed_data = ingestion_service.ingest_and_process_fhir_bundle(bundle)

            print("\nProcessed Data:")
            for res_type, resources in processed_data.items():
                print(f"  {res_type}: {len(resources)} resources")
                if resources and res_type == "Patient":
                    print(f"    Patient ID: {resources[0].get('id')}, Gender: {resources[0].get('gender')}")


        except FileNotFoundError as e:
            print(e)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {patient_file.name}")
