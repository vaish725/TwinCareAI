from pydantic import BaseModel, Field
from typing import Optional

class PromptOpinionConfig(BaseModel):
    """
    Configuration model for integrating with the Prompt Opinion platform.
    """
    api_endpoint: str = Field(..., description="The base URL for the Prompt Opinion API.")
    agent_id: str = Field(..., description="The unique identifier for the TwinCare AI agent on Prompt Opinion.")
    api_key: Optional[str] = Field(None, description="API key for authentication with Prompt Opinion.")
    # Add other configuration parameters as needed, e.g., webhook_url, tenant_id, etc.

    class Config:
        schema_extra = {
            "example": {
                "api_endpoint": "https://api.promptopinion.com/v1",
                "agent_id": "twincare-ai-agent-123",
                "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            }
        }
