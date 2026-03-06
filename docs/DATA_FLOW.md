# TwinCare AI - Detailed Data Flow Diagram

**Version:** 0.1.0  
**Date:** March 6, 2026  
**Status:** Complete

---

## Overview

This document provides a detailed visualization of data flow through the TwinCare AI system, from invocation to final response.

---

## Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROMPT OPINION PLATFORM                          │
│                                                                     │
│  User Action: "Simulate treatment scenarios for Patient X"         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   A2A Message Packet   │
                    │  ─────────────────────│
                    │  • session_id          │
                    │  • patient_id          │
                    │  • fhir_server_url     │
                    │  • fhir_access_token   │
                    │  • requesting_agent    │
                    │  • timestamp           │
                    └────────────┬───────────┘
                                 │
                                 ▼
╔═════════════════════════════════════════════════════════════════════╗
║                   TWINCARE AI BACKEND (FastAPI)                     ║
╚═════════════════════════════════════════════════════════════════════╝
                                 │
                    ┌────────────▼───────────┐
                    │   POST /api/v1/invoke  │
                    │   (Entry Endpoint)     │
                    └────────────┬───────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: CONTEXT INTAKE                          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼───────────┐
                    │  Context Intake Agent  │
                    │  ───────────────────── │
                    │  Input:                │
                    │  • SHARP context       │
                    │  • Raw A2A message     │
                    │                        │
                    │  Processing:           │
                    │  • Parse context       │
                    │  • Validate patient_id │
                    │  • Extract FHIR token  │
                    │  • Validate token      │
                    │                        │
                    │  Output:               │
                    │  • ValidatedContext    │
                    │  • FHIRFetchPlan       │
                    └────────────┬───────────┘
                                 │
                    ┌────────────▼───────────┐
                    │  Context Object        │
                    │  {                     │
                    │    patient_id: "...",  │
                    │    fhir_url: "...",    │
                    │    token: "...",       │
                    │    session_id: "..."   │
                    │  }                     │
                    └────────────┬───────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: FHIR DATA FETCH                         │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │   FHIR Client Service      │
                    │   ─────────────────────    │
                    │   GET /Patient/{id}        │
                    │   GET /Condition?patient   │
                    │   GET /MedicationRequest   │
                    │   GET /Observation?patient │
                    │   GET /Encounter?patient   │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────┐
                    │   FHIR Bundle          │
                    │   {                    │
                    │     resourceType: "...",│
                    │     entry: [           │
                    │       Patient,         │
                    │       Conditions[],    │
                    │       Medications[],   │
                    │       Observations[],  │
                    │       Encounters[]     │
                    │     ]                  │
                    │   }                    │
                    └────────────┬───────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────┐
│               PHASE 3: TWIN STATE CONSTRUCTION                      │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │ Clinical State Builder     │
                    │ ─────────────────────────  │
                    │ Input: FHIR Bundle         │
                    │                            │
                    │ Processing:                │
                    │ 1. Extract demographics    │
                    │    • age, sex, ethnicity   │
                    │ 2. Filter active conditions│
                    │    • status = active       │
                    │    • map to standard codes │
                    │ 3. Current medications     │
                    │    • active only           │
                    │    • deduplicate           │
                    │ 4. Recent labs (<6 months) │
                    │    • HbA1c, lipids, eGFR   │
                    │    • latest values         │
                    │ 5. Recent vitals (<3 mo)   │
                    │    • BP, weight, BMI       │
                    │ 6. Encounter summary       │
                    │ 7. Calculate completeness  │
                    │ 8. Identify care gaps      │
                    │                            │
                    │ Output:                    │
                    │ • PatientTwin object       │
                    │ • Completeness score       │
                    │ • Missing data list        │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────┐
                    │   PatientTwin          │
                    │   {                    │
                    │     patient_id,        │
                    │     demographics: {    │
                    │       age: 56,         │
                    │       sex: "M"         │
                    │     },                 │
                    │     conditions: [      │
                    │       {code: "E11",    │
                    │        display: "T2DM"}│
                    │     ],                 │
                    │     medications: [...],│
                    │     labs: [...],       │
                    │     vitals: [...],     │
                    │     completeness: 0.85,│
                    │     care_gaps: [...]   │
                    │   }                    │
                    └────────────┬───────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────┐
│                PHASE 4: SCENARIO GENERATION                         │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │ Scenario Generator Agent   │
                    │ ─────────────────────────  │
                    │ Input: PatientTwin         │
                    │                            │
                    │ Logic:                     │
                    │ • Analyze condition profile│
                    │ • Check data availability  │
                    │ • Generate 3 scenarios:    │
                    │                            │
                    │   Scenario 1: Baseline     │
                    │   - Continue current meds  │
                    │   - Current adherence      │
                    │                            │
                    │   Scenario 2: Intensify    │
                    │   - Add GLP-1 agonist      │
                    │   - Increase monitoring    │
                    │                            │
                    │   Scenario 3: Lifestyle    │
                    │   - Improve adherence 80→95%│
                    │   - Add lifestyle coaching │
                    │                            │
                    │ Output:                    │
                    │ • ScenarioDefinition[3]    │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────┐
                    │   Scenario Objects     │
                    │   [                    │
                    │     {id: "S1", ...},   │
                    │     {id: "S2", ...},   │
                    │     {id: "S3", ...}    │
                    │   ]                    │
                    └────────────┬───────────┘
                                 │
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 5: PARALLEL SIMULATION                           │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼───────────┐
                    │   Orchestrator         │
                    │   spawns 3x parallel   │
                    │   evaluation chains    │
                    └──┬─────────┬────────┬──┘
                       │         │        │
        ┌──────────────┘         │        └──────────────┐
        │                        │                       │
        ▼                        ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  SCENARIO 1   │      │  SCENARIO 2   │      │  SCENARIO 3   │
│  Evaluation   │      │  Evaluation   │      │  Evaluation   │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                       │
        │ ┌────────────────────┼───────────────────────┘
        │ │                    │
        ▼ ▼                    ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Risk Projection │   │ Risk Projection │   │ Risk Projection │
│     Agent       │   │     Agent       │   │     Agent       │
│ ─────────────── │   │ ─────────────── │   │ ─────────────── │
│ Input:          │   │ Input:          │   │ Input:          │
│ • PatientTwin   │   │ • PatientTwin   │   │ • PatientTwin   │
│ • Scenario def  │   │ • Scenario def  │   │ • Scenario def  │
│                 │   │                 │   │                 │
│ Processing:     │   │ Processing:     │   │ Processing:     │
│ • Tier 1: Labs  │   │ • Tier 1: Labs  │   │ • Tier 1: Labs  │
│ • Tier 2: Rules │   │ • Tier 2: Rules │   │ • Tier 2: Rules │
│ • Tier 3: LLM   │   │ • Tier 3: LLM   │   │ • Tier 3: LLM   │
│                 │   │                 │   │                 │
│ Output:         │   │ Output:         │   │ Output:         │
│ • Risk delta    │   │ • Risk delta    │   │ • Risk delta    │
│ • Confidence    │   │ • Confidence    │   │ • Confidence    │
│ • Rationale     │   │ • Rationale     │   │ • Rationale     │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Medication      │   │ Medication      │   │ Medication      │
│ Impact Agent    │   │ Impact Agent    │   │ Impact Agent    │
│ ─────────────── │   │ ─────────────── │   │ ─────────────── │
│ • Burden score  │   │ • Burden score  │   │ • Burden score  │
│ • Interactions  │   │ • Interactions  │   │ • Interactions  │
│ • Adherence     │   │ • Adherence     │   │ • Adherence     │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Guideline       │   │ Guideline       │   │ Guideline       │
│ Alignment Agent │   │ Alignment Agent │   │ Alignment Agent │
│ ─────────────── │   │ ─────────────── │   │ ─────────────── │
│ • ADA check     │   │ • ADA check     │   │ • ADA check     │
│ • AHA check     │   │ • AHA check     │   │ • AHA check     │
│ • Evidence str  │   │ • Evidence str  │   │ • Evidence str  │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                      │
         └─────────────────────┼──────────────────────┘
                               │
                    ┌──────────▼─────────┐
                    │   Results Array    │
                    │   [                │
                    │     Result1,       │
                    │     Result2,       │
                    │     Result3        │
                    │   ]                │
                    └──────────┬─────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                 PHASE 6: SAFETY & CONSENSUS                         │
└─────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────▼─────────────┐
                    │ Safety Guardrail Agent │
                    │ ────────────────────── │
                    │ Validates each result: │
                    │                        │
                    │ ✓ No definitive claims │
                    │ ✓ No Rx orders         │
                    │ ✓ Disclaimers present  │
                    │ ✓ Missing data flagged │
                    │ ✓ Confidence adjusted  │
                    │                        │
                    │ Actions:               │
                    │ • Inject disclaimers   │
                    │ • Downgrade confidence │
                    │ • Block unsafe outputs │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────┐
                    │ Validated Results  │
                    │ (with safety tags) │
                    └──────────┬─────────┘
                               │
                    ┌──────────▼─────────────┐
                    │  Explanation Agent     │
                    │  ────────────────────  │
                    │  For each scenario:    │
                    │                        │
                    │  • Clinician summary   │
                    │    "Scenario B shows..." │
                    │                        │
                    │  • Patient summary     │
                    │    "If you add..."     │
                    │                        │
                    │  • Assumption list     │
                    │  • Change rationale    │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────┐
                    │ Explained Results  │
                    └──────────┬─────────┘
                               │
                    ┌──────────▼─────────────┐
                    │   Consensus Agent      │
                    │   ──────────────────   │
                    │   Aggregation:         │
                    │                        │
                    │   Score calculation:   │
                    │   rank = (             │
                    │     risk_score * 0.4 + │
                    │     guideline * 0.3 +  │
                    │     med_burden * 0.2 + │
                    │     safety * 0.1       │
                    │   )                    │
                    │                        │
                    │   Ranking:             │
                    │   1. Scenario 2 (85)   │
                    │   2. Scenario 1 (70)   │
                    │   3. Scenario 3 (65)   │
                    │                        │
                    │   Conflict resolution  │
                    │   Final narrative      │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────┐
                    │  Final Results     │
                    │  {                 │
                    │    ranked: [...],  │
                    │    consensus: {},  │
                    │    trace: {...}    │
                    │  }                 │
                    └──────────┬─────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 7: PERSISTENCE                             │
└─────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────▼─────────┐
                    │   Database Write   │
                    │   ──────────────   │
                    │   • sessions table │
                    │   • traces table   │
                    │   • scenarios table│
                    └──────────┬─────────┘
                               │
                    ┌──────────▼─────────┐
                    │  session_id: "..." │
                    │  trace_id: "..."   │
                    └──────────┬─────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 8: RESPONSE                                │
└─────────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────▼─────────────┐
                    │  Response Builder      │
                    │  ────────────────────  │
                    │  Compile:              │
                    │  • Patient twin summary│
                    │  • Ranked scenarios    │
                    │  • Explanations        │
                    │  • Safety notices      │
                    │  • Trace ID            │
                    │  • Session ID          │
                    │  • Execution time      │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────┐
                    │   JSON Response    │
                    │   200 OK           │
                    │   {                │
                    │     session_id,    │
                    │     patient_twin,  │
                    │     scenarios[],   │
                    │     explanation,   │
                    │     safety_notes[],│
                    │     trace_id       │
                    │   }                │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Prompt Opinion    │
                    │  (receives result) │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  React Frontend UI │
                    │  renders results   │
                    └────────────────────┘
```

---

## Data Transformation Examples

### 1. FHIR → PatientTwin Transformation

**Input (FHIR Observation):**
```json
{
  "resourceType": "Observation",
  "id": "obs-123",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "4548-4",
      "display": "Hemoglobin A1c/Hemoglobin.total in Blood"
    }]
  },
  "valueQuantity": {
    "value": 8.2,
    "unit": "%",
    "system": "http://unitsofmeasure.org",
    "code": "%"
  },
  "effectiveDateTime": "2026-02-15"
}
```

**Output (PatientTwin.labs):**
```python
{
  "test_name": "HbA1c",
  "value": 8.2,
  "unit": "%",
  "date": "2026-02-15",
  "abnormal": True,
  "reference_range": "4.0-5.6%",
  "age_days": 20
}
```

### 2. PatientTwin → Scenario Transformation

**Input (PatientTwin excerpt):**
```python
{
  "active_medications": [
    {"name": "Metformin", "dose": "1000mg BID"}
  ],
  "labs": [
    {"test_name": "HbA1c", "value": 8.2, "abnormal": True}
  ],
  "conditions": [
    {"code": "E11", "display": "Type 2 Diabetes"}
  ]
}
```

**Output (Scenario):**
```python
{
  "scenario_id": "scenario-2",
  "label": "Medication Intensification",
  "intervention_type": "medication",
  "parameters": {
    "add_medication": "GLP-1 agonist (semaglutide)",
    "continue_medication": ["Metformin 1000mg BID"],
    "monitoring": "HbA1c every 3 months"
  },
  "assumptions": [
    "Patient adherence: 85%",
    "No contraindications to GLP-1",
    "Patient accepts weekly injection"
  ],
  "time_horizon_months": 12
}
```

### 3. Scenario → Risk Projection Transformation

**Input (Scenario + Twin):**
```python
{
  "baseline_hba1c": 8.2,
  "intervention": "Add GLP-1 agonist",
  "adherence": 0.85
}
```

**Output (Risk Projection):**
```python
{
  "risk_category": "cardiometabolic",
  "direction": "improved",
  "magnitude": "moderate",
  "projected_hba1c": {
    "3_months": 7.8,
    "6_months": 7.4,
    "12_months": 7.0
  },
  "confidence": "moderate",
  "rationale": "GLP-1 agonists typically reduce HbA1c by 1-1.5% at high adherence. Patient's baseline renal function supports this projection.",
  "uncertainty_factors": [
    "Actual adherence may vary",
    "No recent lipid panel to assess CV benefit fully"
  ]
}
```

---

## Data Storage Flow

### Session Storage
```
Request → Create Session → Generate session_id → Store:
  • patient_id
  • context (redacted)
  • created_at
  • status: "in_progress"
  
After completion → Update:
  • status: "completed"
  • results: {full_json}
  • execution_time_ms
```

### Trace Storage
```
Each agent execution → Insert trace record:
  • session_id (FK)
  • step_number (sequential)
  • agent_name
  • input_summary
  • output_summary
  • duration_ms
  • status
  • timestamp
```

---

## Error Data Flow

```
Error occurs in any agent
         │
         ▼
┌────────────────┐
│ Error Handler  │
│ ──────────────│
│ • Capture error│
│ • Log to trace │
│ • Determine:   │
│   - Retry?     │
│   - Fallback?  │
│   - Fail?      │
└────────┬───────┘
         │
    ┌────┴─────┐
    │          │
Retry?      Fail?
    │          │
    ▼          ▼
[Retry    [Return
 logic]    error
           response]
```

---

## Performance Metrics Flow

```
Request Start
    │
    ├─ Context Intake: 234ms
    ├─ FHIR Fetch: 1,567ms
    ├─ Twin Builder: 892ms
    ├─ Scenario Gen: 445ms
    ├─ Parallel Sim: 6,234ms
    │   ├─ Risk Agent: 2,100ms
    │   ├─ Med Agent: 1,800ms
    │   └─ Guideline: 1,900ms
    ├─ Safety: 123ms
    ├─ Explanation: 678ms
    ├─ Consensus: 234ms
    └─ Database: 89ms
    │
Total: 10,496ms ✓ (under 15s target)
```

---

**Document Status:** Complete  
**Next Review:** March 12, 2026
