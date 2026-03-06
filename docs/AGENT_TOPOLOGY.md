# TwinCare AI - Agent Topology Design

**Version:** 0.1.0  
**Date:** March 6, 2026  
**Status:** Initial Design

---

## Overview

TwinCare AI uses a **multi-agent architecture** with 9 specialized agents orchestrated to create digital twins and simulate treatment scenarios.

---

## Agent Topology Diagram

```
                        ┌──────────────────────────────┐
                        │   Prompt Opinion Platform    │
                        │      (A2A Coordinator)       │
                        └──────────────┬───────────────┘
                                       │
                              SHARP Context
                          (Patient ID, FHIR Token)
                                       │
                                       ▼
        ╔══════════════════════════════════════════════════════════╗
        ║            TWINCARE AI ORCHESTRATOR                      ║
        ║         (Agent Coordinator + Router)                     ║
        ╚══════════════════════╦═══════════════════════════════════╝
                               │
                               ▼
        ┌──────────────────────────────────────────────────────────┐
        │                   PHASE 1: INTAKE                        │
        └──────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  1. CONTEXT INTAKE  │
                    │       AGENT         │
                    └──────────┬──────────┘
                               │
                    Validates SHARP Context
                    Resolves Patient ID
                    Extracts FHIR Token
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FHIR Data Fetch   │
                    │   (Service Layer)   │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────────────────────────────────────────┐
        │              PHASE 2: TWIN CONSTRUCTION                  │
        └──────────────────────────────────────────────────────────┘
                               │
                               ▼
                 ┌───────────────────────────┐
                 │  2. CLINICAL STATE        │
                 │     BUILDER AGENT         │
                 └────────────┬──────────────┘
                              │
                   Converts FHIR → Twin State
                   Calculates Completeness
                   Identifies Care Gaps
                              │
                              ▼
                    ┌──────────────────┐
                    │  PATIENT TWIN    │
                    │  STATE OBJECT    │
                    └────────┬─────────┘
                             │
        ┌──────────────────────────────────────────────────────────┐
        │            PHASE 3: SCENARIO PLANNING                    │
        └──────────────────────────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  3. SCENARIO         │
                  │     GENERATOR AGENT  │
                  └──────────┬───────────┘
                             │
                  Generates 3 Scenarios:
                  - Baseline (current)
                  - Intensification
                  - Lifestyle/Adherence
                             │
                             ▼
              [Scenario 1]  [Scenario 2]  [Scenario 3]
                    │             │              │
        ┌───────────┴─────────────┴──────────────┴─────────────────┐
        │           PHASE 4: PARALLEL SIMULATION                   │
        └──────────────────────────────────────────────────────────┘
                    │             │              │
        ┌───────────▼─────┐  ┌────▼────────┐  ┌─▼────────────┐
        │ 4. RISK         │  │ 4. RISK     │  │ 4. RISK      │
        │    PROJECTION   │  │ PROJECTION  │  │ PROJECTION   │
        │    AGENT        │  │ AGENT       │  │ AGENT        │
        └───────────┬─────┘  └────┬────────┘  └─┬────────────┘
                    │             │              │
        ┌───────────▼─────┐  ┌────▼────────┐  ┌─▼────────────┐
        │ 5. MEDICATION   │  │ 5. MED      │  │ 5. MED       │
        │    IMPACT       │  │ IMPACT      │  │ IMPACT       │
        │    AGENT        │  │ AGENT       │  │ AGENT        │
        └───────────┬─────┘  └────┬────────┘  └─┬────────────┘
                    │             │              │
        ┌───────────▼─────┐  ┌────▼────────┐  ┌─▼────────────┐
        │ 6. GUIDELINE    │  │ 6. GUIDE    │  │ 6. GUIDE     │
        │    ALIGNMENT    │  │ ALIGNMENT   │  │ ALIGNMENT    │
        │    AGENT        │  │ AGENT       │  │ AGENT        │
        └───────────┬─────┘  └────┬────────┘  └─┬────────────┘
                    │             │              │
              [Result 1]    [Result 2]     [Result 3]
                    │             │              │
                    └─────────────┴──────────────┘
                                  │
        ┌──────────────────────────────────────────────────────────┐
        │         PHASE 5: SAFETY & CONSENSUS                      │
        └──────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                      ┌────────────────────┐
                      │  7. SAFETY         │
                      │     GUARDRAIL      │
                      │     AGENT          │
                      └──────────┬─────────┘
                                 │
                      Validates Safety Rules
                      Injects Disclaimers
                      Flags Missing Data
                      Downgrades Confidence
                                 │
                                 ▼
                      ┌────────────────────┐
                      │  8. EXPLANATION    │
                      │     AGENT          │
                      └──────────┬─────────┘
                                 │
                      Generates Plain Language
                      Creates Rationale
                      Builds "Why" Narratives
                                 │
                                 ▼
                      ┌────────────────────┐
                      │  9. CONSENSUS      │
                      │     AGENT          │
                      └──────────┬─────────┘
                                 │
                      Ranks Scenarios
                      Resolves Conflicts
                      Aggregates Results
                                 │
                                 ▼
                    ┌───────────────────────┐
                    │   FINAL RESULTS       │
                    │   + TRACE + SAFETY    │
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │   REACT FRONTEND UI   │
                    └───────────────────────┘
```

---

## Agent Specifications

### 1. Context Intake Agent 📥

**Purpose:** Receive and validate incoming context from Prompt Opinion

**Inputs:**
- SHARP context (from Prompt Opinion)
- Patient identifier
- FHIR access token
- Session metadata

**Responsibilities:**
- Parse SHARP context
- Validate patient ID
- Extract FHIR token
- Plan resource fetch
- Handle missing context errors

**Outputs:**
- Validated context object
- FHIR fetch plan
- Error messages (if invalid)

**Error Handling:**
- Missing patient ID → Request clarification
- Invalid token → Token refresh flow
- Malformed context → Validation error

**Timeout:** 5 seconds

---

### 2. Clinical State Builder Agent 🏗️

**Purpose:** Convert FHIR data into structured patient digital twin

**Inputs:**
- FHIR bundle (Patient, Conditions, Medications, Observations, Encounters)
- Patient metadata

**Responsibilities:**
- Extract demographics
- Normalize conditions (active only)
- Normalize medications (current)
- Filter recent labs (last 6 months)
- Filter recent vitals (last 3 months)
- Summarize encounter history
- Identify risk factors
- Calculate completeness score
- Flag care gaps

**Outputs:**
- PatientTwin state object
- Completeness score (0-1)
- Missing data report
- Data freshness indicators

**Key Metrics:**
- Completeness score formula:
  ```
  score = (present_fields / required_fields) * data_recency_factor
  ```

**Timeout:** 10 seconds

---

### 3. Scenario Generator Agent 🎯

**Purpose:** Create valid treatment scenarios for simulation

**Inputs:**
- PatientTwin state
- Condition profile
- Available data constraints

**Responsibilities:**
- Generate 3 scenarios:
  1. Baseline (continue current)
  2. Intensification (medication/monitoring)
  3. Behavioral (adherence/lifestyle)
- Validate scenario plausibility
- Generate assumptions list
- Check data sufficiency
- Handle edge cases (sparse data)

**Outputs:**
- List of 3 ScenarioDefinition objects
- Assumptions per scenario
- Validation warnings

**Scenario Templates:**
- **Diabetes Focus:**
  - Scenario A: Continue metformin, current adherence
  - Scenario B: Add GLP-1, increase monitoring
  - Scenario C: Improve adherence, lifestyle changes

**Timeout:** 8 seconds

---

### 4. Risk Projection Agent 📊

**Purpose:** Calculate directional risk changes for each scenario

**Inputs:**
- PatientTwin state
- ScenarioDefinition
- Time horizon (3, 6, 12 months)

**Responsibilities:**
- **Tier 1:** Deterministic transforms
  - More monitoring → lower uncertainty
  - Recent abnormal labs → higher concern
- **Tier 2:** Guideline-informed heuristics
  - Diabetes intensification → improved HbA1c trajectory
  - Statin adherence → lower CVD risk
- **Tier 3:** LLM-based reasoning
  - Synthesize rationale
  - Identify assumption sensitivity

**Outputs:**
- Directional risk projection
- Risk delta (vs baseline)
- Confidence level
- Uncertainty estimate
- Key assumptions
- Rationale text

**Risk Categories:**
- Short-term (3 months)
- Medium-term (6 months)
- Long-term (12 months)

**Timeout:** 15 seconds

---

### 5. Medication Impact Agent 💊

**Purpose:** Assess medication burden and interactions

**Inputs:**
- Current medication list
- Proposed medication changes (from scenario)
- Patient allergies
- Condition profile

**Responsibilities:**
- Calculate medication burden score
- Check basic interactions
- Assess adherence complexity
- Flag contraindication signals
- Estimate side effect risk
- Evaluate regimen simplicity

**Outputs:**
- Medication burden score
- Interaction warnings
- Adherence complexity rating
- Caution flags
- Simplification opportunities

**Burden Calculation:**
```
burden = (medication_count * 0.3) + 
         (daily_doses * 0.2) + 
         (interaction_risk * 0.3) + 
         (complexity * 0.2)
```

**Timeout:** 10 seconds

---

### 6. Guideline Alignment Agent 📋

**Purpose:** Validate scenarios against clinical guidelines

**Inputs:**
- Condition profile
- ScenarioDefinition
- Patient characteristics

**Responsibilities:**
- Load relevant guidelines (ADA, AHA, etc.)
- Check scenario-guideline consistency
- Identify evidence strength
- Avoid false certainty claims
- Flag deviations from standard care
- Provide guideline references

**Outputs:**
- Alignment score (0-100)
- Evidence strength (strong/moderate/weak)
- Guideline references
- Deviation notes
- Recommendation consistency

**Guidelines Covered:**
- ADA: Diabetes management
- AHA/ACC: Cardiovascular risk
- JNC8: Hypertension
- USPSTF: Preventive care

**Timeout:** 10 seconds

---

### 7. Safety Guardrail Agent 🛡️

**Purpose:** Enforce safety rules and prevent unsafe outputs

**Inputs:**
- All agent outputs
- Scenario results
- Proposed final report

**Responsibilities:**
- **Block unsafe claims:**
  - No definitive treatment directives
  - No autonomous prescriptions
  - No diagnosis statements
- **Inject disclaimers:**
  - "For simulation purposes only"
  - "Not a substitute for clinical judgment"
- **Flag missing data:**
  - Critical labs absent
  - Stale data warnings
- **Downgrade confidence:**
  - Insufficient evidence → lower confidence
  - Data gaps → explicit uncertainty

**Outputs:**
- Safety status (approved/warning/blocked)
- Modified output with disclaimers
- Safety flags
- Confidence adjustments
- Required user warnings

**Safety Rules:**
```python
rules = [
    "no_autonomous_prescription",
    "no_definitive_diagnosis",
    "require_disclaimer",
    "flag_missing_critical_data",
    "downgrade_confidence_on_uncertainty",
    "synthetic_data_badge_required"
]
```

**Timeout:** 5 seconds

---

### 8. Explanation Agent 💬

**Purpose:** Generate human-readable explanations

**Inputs:**
- Scenario results
- Agent reasoning traces
- Confidence levels

**Responsibilities:**
- Generate clinician-facing summaries
- Generate patient-friendly plain language
- Create assumption explanations
- Build "why this changed" narratives
- Explain confidence levels
- Highlight key tradeoffs

**Outputs:**
- Clinician summary (technical)
- Patient summary (plain language)
- Assumption list (explicit)
- Change rationale
- Confidence explanation
- Key tradeoffs

**Explanation Templates:**
```
Clinician: "Scenario B projects a moderate reduction in 
12-month cardiovascular risk due to improved glycemic control 
from GLP-1 addition. Confidence is moderate due to missing 
recent lipid panel."

Patient: "If you add the new diabetes medication and check 
your blood sugar more often, your heart health risk might 
improve over the next year. We're moderately confident, but 
would be more certain with recent cholesterol labs."
```

**Timeout:** 8 seconds

---

### 9. Consensus Agent 🤝

**Purpose:** Aggregate results and resolve conflicts

**Inputs:**
- All specialist agent outputs
- Scenario rankings from each agent
- Confidence scores
- Safety approvals

**Responsibilities:**
- Rank scenarios by projected benefit
- Resolve agent disagreements
- Handle tie-breaking
- Aggregate confidence scores
- Compile final report
- Generate execution trace

**Outputs:**
- Ranked scenario list (1st, 2nd, 3rd)
- Final comparison narrative
- Aggregated confidence
- Conflict resolution notes
- Agent trace summary
- Recommendation (if any)

**Consensus Logic:**
```python
def rank_scenarios(scenario_results):
    scores = []
    for scenario in scenario_results:
        score = (
            risk_projection_score * 0.4 +
            guideline_alignment * 0.3 +
            medication_burden * 0.2 +
            safety_approval * 0.1
        )
        scores.append(score)
    return sorted(scenarios, key=lambda x: x.score, reverse=True)
```

**Conflict Resolution:**
- If 2+ agents disagree significantly → "Requires more data"
- If safety blocks → Exclude scenario
- If tie → Prefer simpler intervention

**Timeout:** 10 seconds

---

## Agent Communication Flow

### Sequential Flow (Phases 1-3)
```
Context Intake → Clinical State Builder → Scenario Generator
```

### Parallel Flow (Phase 4)
```
For each scenario:
  [Risk Projection, Medication Impact, Guideline Alignment] 
  run in parallel
```

### Sequential Flow (Phase 5)
```
Safety Guardrail → Explanation → Consensus
```

---

## Agent Input/Output Contracts

### Standard Message Format
```typescript
interface AgentMessage {
  agent_id: string;
  session_id: string;
  timestamp: string;
  message_type: string;
  payload: any;
  context: {
    patient_id: string;
    sharp_context?: any;
  };
  metadata: {
    execution_time_ms: number;
    status: 'success' | 'partial' | 'error';
    confidence?: number;
  };
}
```

### Error Response Format
```typescript
interface AgentError {
  agent_id: string;
  error_type: string;
  error_message: string;
  retry_possible: boolean;
  fallback_available: boolean;
}
```

---

## Agent Orchestration Strategy

### Execution Modes

**Mode 1: Sequential (Phases 1-3)**
- Strict order required
- Each agent depends on previous output
- Fail fast on critical errors

**Mode 2: Parallel (Phase 4)**
- Independent evaluation per scenario
- No inter-agent dependencies
- Aggregate results after all complete
- Timeout: continue with partial results

**Mode 3: Sequential (Phase 5)**
- Safety must run first
- Explanation depends on safety approval
- Consensus requires all inputs

### Timeout Handling
```python
async def orchestrate_parallel_agents(scenario):
    tasks = [
        run_agent('risk_projection', scenario, timeout=15),
        run_agent('medication_impact', scenario, timeout=10),
        run_agent('guideline_alignment', scenario, timeout=10),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Handle timeouts and partial results
    return filter_successful_results(results)
```

### Retry Logic
- Transient errors: Retry up to 3 times with exponential backoff
- Validation errors: Fail immediately (no retry)
- Timeout: Use partial results if available

---

## Agent Technology Stack

### Implementation
- Python 3.11+
- FastAPI for agent endpoints
- Pydantic for data validation
- Async/await for orchestration

### LLM Integration
- OpenAI GPT-4 for Tier 3 reasoning
- Function calling for structured outputs
- Prompt templates per agent

### Agent Testing
- Unit tests per agent
- Mock inputs/outputs
- Integration tests for orchestration
- End-to-end flow tests

---

## Monitoring & Observability

### Per-Agent Metrics
- Execution time
- Success/failure rate
- Confidence distribution
- Retry count

### Orchestration Metrics
- End-to-end latency
- Agent timeout frequency
- Partial result rate
- Safety block rate

### Trace Logging
- Agent sequence
- Input/output per step
- Timing breakdown
- Error stack traces

---

## Next Steps

1. ✅ Agent topology designed
2. ⏳ Implement base Agent class
3. ⏳ Create agent registry
4. ⏳ Build orchestrator service
5. ⏳ Develop individual agents
6. ⏳ Add unit tests
7. ⏳ Integration testing

---

**Document Status:** Complete  
**Next Review:** March 12, 2026  
**Owner:** Tech Lead
