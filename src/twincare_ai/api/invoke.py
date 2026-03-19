from typing import Dict, Any, Optional
from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import ValidationError

from twincare_ai.context.sharp_context import SHARPContext, PatientContext, RequestingAgent, InvocationContext
from twincare_ai.utils.validation import DataValidationException, validate_pydantic_model

router = APIRouter()

@router.post("/invoke", tags=["A2A Agent"])
async def invoke_agent(
    request_body: Dict[str, Any],
    authorization: str = Header(..., description="Bearer token for authentication"),
    x_fhir_server_url: Optional[str] = Header(None, alias="X-FHIR-Server-URL", description="FHIR Server URL from SHARP context"),
    x_fhir_access_token: Optional[str] = Header(None, alias="X-FHIR-Access-Token", description="FHIR Access Token from SHARP context"),
    x_patient_id: Optional[str] = Header(None, alias="X-Patient-ID", description="Patient ID from SHARP context"),
):
    """Main agent invocation endpoint, extracts and validates SHARP context.

    This endpoint receives A2A agent requests, including SHARP context in headers and body.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        # Attempt to construct SHARPContext from request_body
        sharp_context_data = request_body.get("sharp_context", {})
        if not sharp_context_data:
             # If not in body, try to construct from headers (minimal SHARP context)
            if not all([x_fhir_server_url, x_fhir_access_token, x_patient_id]):
                raise HTTPException(status_code=400, detail="SHARP context missing in body and insufficient headers.")

            sharp_context_data = {
                "sharp_version": "1.0", # Defaulting as per spec
                "session_id": request_body.get("session_id", "default-session-id"), # Placeholder for now
                "patient_context": {
                    "patient_id": x_patient_id,
                    "fhir_server_url": x_fhir_server_url,
                    "fhir_access_token": x_fhir_access_token,
                },
                "requesting_agent": {
                    "agent_id": "unknown-agent", # Placeholder for now
                    "agent_name": "Unknown Agent",
                },
                "invocation_context": {
                    "timestamp": "", # To be filled, maybe current time
                    "request_type": "unknown",
                }
            }
        
        # Validate and parse the SHARP context using the Pydantic model
        sharp_context = validate_pydantic_model(sharp_context_data, SHARPContext)
        
        # Add patient ID validation
        validate_patient_id(sharp_context.patient_context.patient_id)

        # TODO: Use the extracted sharp_context for further processing and agent orchestration
        # For now, just return a success message and the parsed context
        return {
            "status": "received",
            "message": "Invocation request received and SHARP context extracted.",
            "sharp_context": sharp_context.model_dump()
        }

    except (ValidationError, DataValidationException) as e:
        raise HTTPException(status_code=400, detail=f"Invalid SHARP context: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during SHARP context processing: {e}")