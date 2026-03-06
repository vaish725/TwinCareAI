# Prompt Opinion Platform - Integration Notes

**Purpose:** Study notes and integration planning for Prompt Opinion A2A agent development  
**Date:** March 6, 2026

---

## Overview

Prompt Opinion is the hosting platform for A2A (Agent-to-Agent) healthcare workflows. TwinCare AI will be deployed as an A2A agent within this platform.

---

## Key Concepts

### A2A (Agent-to-Agent Communication)
- Enables agents to collaborate on complex tasks
- Standard protocol for agent orchestration
- Supported natively by Prompt Opinion
- Required for hackathon submission

### SHARP (Standardized Healthcare Agent Remote Protocol)
- Extension of MCP for healthcare context
- Enables FHIR-linked context propagation
- Passes patient identifiers and FHIR tokens between agents
- Key for interoperable healthcare agents

### MCP (Model Context Protocol)
- Optional "superpower" servers
- Reusable tool endpoints
- Can enhance A2A agents
- Not required but recommended for bonus points

---

## Platform Requirements

### Must Have ✅
1. ✅ Integrate into Prompt Opinion
2. ✅ Publish to Prompt Opinion Marketplace
3. ✅ Be discoverable and invokable in the platform
4. ✅ Function exactly as shown in demo video
5. ✅ Use only synthetic or de-identified data

### Integration Checklist
- [ ] Create Prompt Opinion account
- [ ] Register as agent developer
- [ ] Configure A2A agent manifest
- [ ] Test invocation in sandbox
- [ ] Validate SHARP context handling
- [ ] Configure agent endpoints
- [ ] Test Marketplace publishing flow
- [ ] Verify discoverability

---

## Agent Registration Process

### 1. Agent Manifest
Create agent configuration file defining:
- Agent ID and name
- Description and capabilities
- Input/output schemas
- Endpoint URLs
- SHARP context requirements

### 2. Endpoint Configuration
- Base URL for agent backend
- Authentication method
- Health check endpoint
- Invocation endpoint

### 3. Marketplace Listing
- Title and one-line description
- Detailed description
- Screenshots
- Demo video
- Usage instructions
- Supported use cases
- Safety disclaimers

---

## SHARP Context Schema

### Expected Context from Prompt Opinion

```json
{
  "sharp_version": "1.0",
  "session_id": "uuid-v4",
  "patient_context": {
    "patient_id": "synthetic-001",
    "patient_identifier_system": "http://twincare-ai.example.com",
    "fhir_server_url": "https://fhir.example.com/r4",
    "fhir_access_token": "bearer-token-here"
  },
  "requesting_agent": {
    "agent_id": "prompt-opinion-coordinator",
    "agent_name": "Clinical Decision Coordinator"
  },
  "invocation_context": {
    "timestamp": "2026-03-06T10:00:00Z",
    "request_type": "scenario_simulation",
    "user_role": "clinician"
  }
}
```

### TwinCare AI Response Format

```json
{
  "agent_id": "twincare-ai",
  "session_id": "uuid-v4",
  "status": "success",
  "results": {
    "twin_state": { ... },
    "scenarios": [ ... ],
    "ranked_results": [ ... ],
    "trace": [ ... ]
  },
  "metadata": {
    "execution_time_ms": 12450,
    "agents_invoked": 9,
    "confidence_level": "moderate",
    "synthetic_data_flag": true,
    "disclaimer": "For simulation purposes only..."
  }
}
```

---

## Testing Strategy

### Phase 1: Local Testing
1. Mock SHARP context locally
2. Test agent orchestration without Prompt Opinion
3. Validate outputs match expected schema
4. Test edge cases (missing context, expired tokens)

### Phase 2: Sandbox Testing
1. Register test agent on Prompt Opinion sandbox
2. Test invocation from platform
3. Validate context propagation
4. Test error handling

### Phase 3: Production Testing
1. Register production agent
2. Test with synthetic patients
3. Validate Marketplace discoverability
4. Record demo video
5. Submit for review

---

## API Integration Points

### Incoming (from Prompt Opinion)
- `POST /invoke` - Main agent invocation
  - Headers: Authorization, SHARP-Context
  - Body: SHARP context + user request
  - Response: Scenario results + trace

### Outgoing (to FHIR/other services)
- FHIR server queries (using token from SHARP context)
- LLM APIs (OpenAI/Anthropic)
- Internal agent-to-agent calls

---

## Marketplace Optimization

### Discoverability
- Clear, searchable title: "TwinCare AI - Digital Twin Healthcare Simulator"
- Keywords: digital twin, scenario simulation, diabetes, treatment planning
- Category: Healthcare AI, Clinical Decision Support
- Tags: FHIR, A2A, SHARP, multi-agent

### Listing Content
- Compelling one-liner
- Problem statement
- Key features (bullet points)
- Demo video (under 3 minutes)
- Screenshots of all 6 screens
- Usage instructions
- Safety disclaimers
- Supported conditions (Type 2 diabetes + cardiovascular)

---

## Common Integration Patterns

### Pattern 1: Simple Request-Response
```
User → Prompt Opinion → TwinCare AI → Response
```

### Pattern 2: Multi-Agent Orchestration
```
User → Prompt Opinion → TwinCare Orchestrator →
  [Agent 1, Agent 2, Agent 3] → Consensus → Response
```

### Pattern 3: FHIR Context Flow
```
Prompt Opinion (SHARP context with FHIR token) →
  TwinCare Context Intake →
    FHIR Server (fetch bundle) →
      Twin Builder → Simulation → Results
```

---

## Security Considerations

### Token Handling
- FHIR tokens passed in SHARP context
- Never log tokens
- Validate token before use
- Handle expired tokens gracefully

### Data Privacy
- Only access FHIR data specified in context
- No PHI in logs or traces
- Synthetic data only for hackathon
- Clear data retention policy

### API Security
- HTTPS only
- API key authentication
- Rate limiting
- Input validation

---

## Error Handling

### Context Errors
- Missing patient_id → Return clear error message
- Invalid FHIR token → Request token refresh
- Malformed SHARP context → Validation error with details

### FHIR Errors
- Server unreachable → Retry with exponential backoff
- Patient not found → Clear user message
- Insufficient data → Partial results with warnings

### Agent Errors
- Agent timeout → Proceed with partial results
- Agent failure → Graceful degradation
- All agents fail → Return error with trace

---

## Documentation Links

- **Prompt Opinion Docs:** [https://docs.promptopinion.com](https://docs.promptopinion.com) *(placeholder)*
- **A2A Specification:** [https://a2a-spec.org](https://a2a-spec.org) *(placeholder)*
- **SHARP on MCP:** [https://sharponmcp.com](https://sharponmcp.com)
- **Hackathon Rules:** [https://agents-assemble.devpost.com/rules](https://agents-assemble.devpost.com/rules)

---

## Action Items for Today (Mar 6-7)

### Immediate Tasks
- [ ] Review Prompt Opinion documentation (if available)
- [ ] Understand A2A agent registration process
- [ ] Study SHARP context specification
- [ ] Create test SHARP context JSON
- [ ] Design agent manifest schema
- [ ] Plan authentication flow
- [ ] Document API contracts

### Questions to Resolve
- What is the exact SHARP context schema?
- How are FHIR tokens provisioned?
- What authentication is required for agent endpoints?
- How does Marketplace approval process work?
- Are there sandbox credentials available?
- What are rate limits?

---

## Resources Needed

### Access
- [ ] Prompt Opinion developer account
- [ ] Sandbox API credentials
- [ ] FHIR test server access
- [ ] Agent registration documentation

### Tools
- [ ] Postman collection for API testing
- [ ] Sample SHARP context files
- [ ] Agent manifest template
- [ ] Marketplace listing checklist

---

**Status:** Research phase  
**Next Update:** March 7, 2026 (after documentation review)  
**Owner:** Tech Lead + Full Team
