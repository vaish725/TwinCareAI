# TwinCare AI - System Architecture

**Version:** 0.1.0  
**Last Updated:** March 6, 2026

---

## Overview

TwinCare AI is a multi-agent healthcare simulation system that creates patient-specific digital twins from FHIR data and runs what-if treatment scenarios within the Prompt Opinion platform.

## Architecture Principles

1. **Interoperability First** - FHIR R4, A2A, MCP, SHARP standards
2. **Agent Specialization** - Single responsibility per agent
3. **Safety by Design** - Guardrails, disclaimers, synthetic data only
4. **Explainability** - Full trace and reasoning transparency
5. **Async & Scalable** - FastAPI async, orchestrated workflows

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Prompt Opinion Platform                     │
│                          (A2A Agent Host)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ SHARP Context
                             │ (Patient ID, FHIR Token)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TwinCare Orchestrator                         │
│                    (FastAPI + Agent Router)                      │
└───────┬─────────────────────────────────────────────────┬───────┘
        │                                                   │
        │                                                   │
┌───────▼────────┐  ┌──────────────┐  ┌─────────────┐   │
│  Context       │  │  Clinical    │  │  Scenario   │   │
│  Intake Agent  │  │  State       │  │  Generator  │   │
│                │  │  Builder     │  │  Agent      │   │
└───────┬────────┘  └──────┬───────┘  └──────┬──────┘   │
        │                  │                   │           │
        │                  │                   │           │
        └──────────────────┴───────────────────┘           │
                           │                               │
                  ┌────────▼─────────┐                     │
                  │  Patient Twin    │                     │
                  │  State Object    │                     │
                  └────────┬─────────┘                     │
                           │                               │
        ┌──────────────────┴──────────────────┐           │
        │                                      │           │
┌───────▼──────┐  ┌────────────┐  ┌──────────▼──────┐   │
│  Risk        │  │ Medication │  │  Guideline      │   │
│  Projection  │  │ Impact     │  │  Alignment      │   │
│  Agent       │  │ Agent      │  │  Agent          │   │
└───────┬──────┘  └─────┬──────┘  └──────┬──────────┘   │
        │               │                 │               │
        └───────────────┴─────────────────┘               │
                        │                                 │
        ┌───────────────┴────────────────┐               │
        │                                 │               │
┌───────▼─────────┐  ┌─────────────┐  ┌─▼──────────┐   │
│  Safety         │  │ Explanation │  │ Consensus   │   │
│  Guardrail      │  │ Agent       │  │ Agent       │   │
│  Agent          │  │             │  │             │   │
└───────┬─────────┘  └──────┬──────┘  └──────┬──────┘   │
        │                   │                 │           │
        └───────────────────┴─────────────────┘           │
                            │                             │
                   ┌────────▼────────┐                    │
                   │ Scenario Results │                   │
                   │ + Trace + Safety │                   │
                   └────────┬─────────┘                   │
                            │                             │
                            ▼                             │
┌─────────────────────────────────────────────────────────▼───────┐
│                     React Frontend UI                            │
│  (Patient Selection → Twin View → Scenarios → Results → Trace)  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Context Intake Layer

**Responsibility:** Receive and validate Prompt Opinion/SHARP context

**Components:**
- SHARP context parser
- Patient ID resolver
- FHIR token handler
- Context validation

**Input:** Prompt Opinion invocation with SHARP context  
**Output:** Validated context object with patient identifier and FHIR access

---

### 2. Data Ingestion Layer

**Responsibility:** Fetch and normalize FHIR resources

**Components:**
- FHIR client service
- Resource fetcher (Patient, Condition, Medication, Observation, Encounter)
- Data normalizer
- Bundle deduplicator

**FHIR Resources:**
- Patient (demographics)
- Condition (active diagnoses)
- MedicationRequest/Statement (current meds)
- Observation (labs, vitals)
- Encounter (care history)
- AllergyIntolerance (optional)

**Output:** Normalized FHIR bundle

---

### 3. Twin State Construction

**Responsibility:** Convert FHIR to structured patient twin

**Agent:** Clinical State Builder Agent

**Twin State Schema:**
```python
class PatientTwin:
    patient_id: str
    synthetic_flag: bool
    demographics: Demographics
    active_conditions: List[Condition]
    active_medications: List[Medication]
    recent_labs: List[Observation]
    recent_vitals: List[Observation]
    encounter_summary: EncounterSummary
    risk_factors: RiskFactors
    care_gaps: List[CareGap]
    completeness_score: float
    data_freshness: DataFreshness
```

**Output:** PatientTwin object + missing data report

---

### 4. Scenario Generation

**Responsibility:** Create valid treatment scenarios

**Agent:** Scenario Generator Agent

**Scenario Types:**
1. Continue current treatment (baseline)
2. Medication intensification
3. Lifestyle intervention
4. Improved adherence
5. Delayed follow-up
6. Custom (advanced editor)

**Output:** List[ScenarioDefinition] (max 3 for comparison)

---

### 5. Multi-Agent Simulation

**Responsibility:** Run parallel scenario evaluations

**Agents:**
- **Risk Projection Agent:** Calculate directional risk changes
- **Medication Impact Agent:** Assess drug burden and interactions
- **Guideline Alignment Agent:** Validate against clinical guidelines

**Simulation Tiers:**
1. **Tier 1:** Deterministic transforms (monitoring frequency, lab recency)
2. **Tier 2:** Guideline-informed heuristics (diabetes intensification, statin adherence)
3. **Tier 3:** LLM-based generative reasoning (rationale synthesis)

**Output:** Per-scenario projections with uncertainty

---

### 6. Safety & Consensus Layer

**Responsibility:** Validate safety and aggregate results

**Agents:**
- **Safety Guardrail Agent:** Block unsafe claims, inject disclaimers
- **Explanation Agent:** Generate plain-language summaries
- **Consensus Agent:** Rank scenarios, resolve conflicts

**Safety Rules:**
- No definitive treatment directives
- No autonomous prescriptions
- Explicit confidence levels
- Missing data transparency
- Mandatory disclaimers

**Output:** Ranked scenarios + explanations + safety notes

---

### 7. Orchestration Layer

**Responsibility:** Coordinate agent workflow

**Components:**
- Agent sequencer
- Timeout handler
- Retry logic
- Result aggregator
- Trace logger

**Flow:**
```
Context Intake → Twin Builder → Scenario Gen → 
[Risk + Medication + Guideline] in parallel → 
Safety + Explanation + Consensus → 
Result + Trace
```

**Timeouts:**
- Per-agent: 30s
- Total orchestration: 120s

---

### 8. API Layer

**Endpoints:**
- `POST /invoke` - Main invocation from Prompt Opinion
- `POST /simulate` - Run scenario simulation
- `POST /compare` - Compare multiple scenarios
- `GET /session/{id}` - Retrieve session results
- `GET /trace/{id}` - Get agent execution trace
- `GET /health` - Health check

**Authentication:** 
- SHARP context validation
- API key (production)

---

### 9. Frontend Layer

**Technology:** React + TypeScript + Tailwind + shadcn/ui

**Screens:**
1. **Patient Selection** - Load synthetic patient
2. **Twin Overview** - View patient digital twin state
3. **Scenario Workspace** - Build and configure scenarios
4. **Simulation Results** - Compare scenario outcomes
5. **Agent Trace** - View agent execution timeline
6. **Export/Share** - Export reports

**State Management:** Zustand or Context API

**API Client:** Axios with retry logic

---

## Data Flow Diagram

```
Prompt Opinion → SHARP Context → Context Intake Agent
                                         ↓
FHIR Server ← FHIR Token ← Context Intake Agent
     ↓
FHIR Bundle → Clinical State Builder Agent
                          ↓
                   Patient Twin State
                          ↓
              Scenario Generator Agent
                          ↓
              [Scenario 1, 2, 3]
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                  ↓
   Scenario 1        Scenario 2         Scenario 3
        ↓                 ↓                  ↓
   [Risk Agent      [Risk Agent        [Risk Agent
    Med Agent        Med Agent          Med Agent
    Guideline]       Guideline]         Guideline]
        ↓                 ↓                  ↓
   Results 1         Results 2          Results 3
        └─────────────────┼─────────────────┘
                          ↓
              Safety Guardrail Agent
                          ↓
               Explanation Agent
                          ↓
                Consensus Agent
                          ↓
         Ranked Scenarios + Trace + Safety
                          ↓
                  Frontend UI
```

---

## Agent Communication Protocol

### A2A (Agent-to-Agent)

**Primary Protocol:** Prompt Opinion A2A standard

**Message Format:**
```json
{
  "sender_agent_id": "context_intake",
  "receiver_agent_id": "clinical_state_builder",
  "message_type": "twin_state_request",
  "payload": {
    "patient_id": "synthetic-001",
    "fhir_bundle": { ... }
  },
  "context": {
    "session_id": "uuid",
    "sharp_context": { ... }
  }
}
```

**Response:**
```json
{
  "sender_agent_id": "clinical_state_builder",
  "receiver_agent_id": "orchestrator",
  "message_type": "twin_state_response",
  "payload": {
    "twin_state": { ... },
    "completeness_score": 0.85,
    "missing_data": [ ... ]
  },
  "status": "success"
}
```

---

### MCP (Model Context Protocol) - Optional

**Purpose:** Enhance interoperability with reusable healthcare tools

**MCP Tools:**
1. `fetch_patient_context_bundle(patient_id, fhir_token)`
2. `build_digital_twin(fhir_bundle)`
3. `run_scenario_projection(twin_state, scenario_def)`
4. `compare_scenario_outcomes(results_list)`
5. `explain_projection(result_id)`

**Server:** Separate Python MCP server (optional for bonus points)

---

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    patient_id VARCHAR(255),
    created_at TIMESTAMP,
    status VARCHAR(50),
    context JSONB,
    results JSONB
);
```

### Traces Table
```sql
CREATE TABLE traces (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    agent_name VARCHAR(100),
    step_number INT,
    input_summary TEXT,
    output_summary TEXT,
    duration_ms INT,
    status VARCHAR(50),
    timestamp TIMESTAMP
);
```

### Scenarios Table
```sql
CREATE TABLE scenarios (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    scenario_label VARCHAR(255),
    definition JSONB,
    result JSONB,
    rank INT
);
```

---

## Security Architecture

### Data Security
-  Synthetic data only (ENFORCED)
-  No real PHI storage
-  FHIR tokens redacted in logs
-  Encrypted connections (TLS)

### Authentication
- API key for backend endpoints
- SHARP context validation
- Rate limiting

### Authorization
- Scope validation per Prompt Opinion context
- Patient ID validation

### Audit Trail
- All agent actions logged
- Session traces stored
- No sensitive data in logs

---

## Scalability Considerations

### Current Scope (Hackathon)
- Single backend instance
- SQLite database
- 10-50 concurrent requests
- Demo/prototype scale

### Future Production Scale
- Horizontal scaling (multiple backend instances)
- PostgreSQL with connection pooling
- Redis for caching
- Load balancer
- Message queue for async jobs (Celery/RabbitMQ)
- Kubernetes deployment

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| End-to-end latency | <15s | Invoke → Result |
| Agent execution | <5s each | Per agent timeout |
| FHIR fetch | <2s | Bundle retrieval |
| Twin construction | <3s | FHIR → Twin |
| Scenario simulation | <8s | All 3 scenarios |
| Frontend load | <2s | Initial page load |

---

## Deployment Architecture

### Development
```
Local Machine
├── Backend: localhost:8000
├── Frontend: localhost:5173
└── FHIR: Synthetic bundle files
```

### Production
```
Cloud Provider (AWS/GCP/Azure)
├── Frontend: Vercel/Netlify (or S3 + CloudFront)
├── Backend: Container (ECS/GKE/App Service)
├── Database: PostgreSQL (RDS/Cloud SQL)
├── FHIR: External synthetic server or bundled
└── Monitoring: Prometheus + Grafana
```

---

## Technology Decisions

### Backend: Python + FastAPI
**Why:**
- Async/await native
- Excellent for orchestration
- Strong typing (Pydantic)
- FHIR library support
- LLM SDK compatibility

### Frontend: React + TypeScript
**Why:**
- Component reusability
- Type safety
- Rich ecosystem
- Fast development (Vite)
- shadcn/ui for rapid UI

### Database: SQLite → PostgreSQL
**Why:**
- SQLite for rapid development
- PostgreSQL for production scale
- SQLAlchemy async support

### LLM: OpenAI/Anthropic
**Why:**
- Strong reasoning for Tier 3 simulation
- Function calling for agent tools
- High quality medical reasoning

---

## Next Steps (Days 1-2)

1.  Project structure created
2.  Initialize Git repository
3.  Design detailed agent topology diagram
4.  Define API contracts (OpenAPI spec)
5.  Create FHIR synthetic patient data
6.  Study Prompt Opinion documentation
7.  Set up development environment

---

**Document Status:** Draft  
**Next Review:** March 12, 2026 (End of Week 1)
