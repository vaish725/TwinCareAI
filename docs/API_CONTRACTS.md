# TwinCare AI - API Contracts

**Version:** 0.1.0  
**Date:** March 6, 2026  
**Status:** Initial Design

---

## Overview

API contracts define the interfaces between Prompt Opinion, TwinCare AI backend, and the frontend UI.

---

## 1. Main Invocation Endpoint

### POST /api/v1/invoke

**Purpose:** Main entry point from Prompt Opinion

**Authentication:** Bearer token in header

**Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
X-SHARP-Context: {base64_encoded_sharp_context}
```

**Request Body:**
```json
{
  "session_id": "uuid-v4",
  "patient_id": "synthetic-001",
  "sharp_context": {
    "patient_context": {
      "patient_id": "synthetic-001",
      "fhir_server_url": "https://fhir.example.com/r4",
      "fhir_access_token": "bearer-token"
    },
    "requesting_agent": {
      "agent_id": "prompt-opinion-coordinator"
    }
  },
  "request_type": "scenario_simulation",
  "parameters": {
    "scenario_count": 3,
    "time_horizon_months": 12
  }
}
```

**Response (Success - 200 OK):**
```json
{
  "session_id": "uuid-v4",
  "status": "success",
  "execution_time_ms": 12450,
  "patient_twin": {
    "patient_id": "synthetic-001",
    "completeness_score": 0.85,
    "demographics": {
      "age": 56,
      "sex": "male"
    },
    "active_conditions": [
      {
        "code": "E11",
        "display": "Type 2 Diabetes Mellitus"
      }
    ],
    "missing_data": ["lipid_panel", "recent_hba1c"]
  },
  "scenarios": [
    {
      "scenario_id": "scenario-1",
      "label": "Continue Current Treatment",
      "rank": 2,
      "risk_projection": {
        "direction": "stable",
        "confidence": "moderate"
      }
    },
    {
      "scenario_id": "scenario-2",
      "label": "Medication Intensification",
      "rank": 1,
      "risk_projection": {
        "direction": "improved",
        "confidence": "moderate"
      }
    },
    {
      "scenario_id": "scenario-3",
      "label": "Lifestyle Intervention",
      "rank": 3,
      "risk_projection": {
        "direction": "improved",
        "confidence": "low"
      }
    }
  ],
  "explanation": {
    "clinician_summary": "...",
    "patient_summary": "..."
  },
  "safety_notes": [
    "For simulation purposes only",
    "Missing recent lipid panel"
  ],
  "trace_id": "trace-uuid"
}
```

**Response (Error - 400 Bad Request):**
```json
{
  "status": "error",
  "error_code": "INVALID_CONTEXT",
  "error_message": "Missing patient_id in SHARP context",
  "details": {
    "field": "sharp_context.patient_context.patient_id",
    "expected": "string"
  }
}
```

---

## 2. Scenario Simulation Endpoint

### POST /api/v1/simulate

**Purpose:** Run simulation for custom scenarios

**Request:**
```json
{
  "session_id": "uuid-v4",
  "patient_id": "synthetic-001",
  "twin_state": { /* PatientTwin object */ },
  "scenarios": [
    {
      "label": "Custom Scenario",
      "intervention_type": "medication_change",
      "parameters": {
        "add_medication": "GLP-1 agonist",
        "adjust_monitoring": "weekly glucose checks"
      },
      "assumptions": [
        "Patient adherence: 90%",
        "No medication contraindications"
      ]
    }
  ]
}
```

**Response:**
```json
{
  "session_id": "uuid-v4",
  "results": [
    {
      "scenario_id": "custom-1",
      "risk_projection": { /* ... */ },
      "medication_impact": { /* ... */ },
      "guideline_alignment": { /* ... */ },
      "confidence": "moderate"
    }
  ]
}
```

---

## 3. Session Retrieval

### GET /api/v1/sessions/{session_id}

**Purpose:** Retrieve past session results

**Response:**
```json
{
  "session_id": "uuid-v4",
  "created_at": "2026-03-06T10:00:00Z",
  "status": "completed",
  "patient_id": "synthetic-001",
  "results": { /* Full results */ },
  "trace_id": "trace-uuid"
}
```

---

## 4. Trace Retrieval

### GET /api/v1/traces/{trace_id}

**Purpose:** Get detailed agent execution trace

**Response:**
```json
{
  "trace_id": "trace-uuid",
  "session_id": "uuid-v4",
  "total_execution_time_ms": 12450,
  "steps": [
    {
      "step_number": 1,
      "agent_name": "Context Intake Agent",
      "input_summary": "SHARP context with patient synthetic-001",
      "output_summary": "Valid context, FHIR token extracted",
      "duration_ms": 234,
      "status": "success",
      "timestamp": "2026-03-06T10:00:00.123Z"
    },
    {
      "step_number": 2,
      "agent_name": "Clinical State Builder Agent",
      "input_summary": "FHIR bundle with 12 resources",
      "output_summary": "Twin state created, completeness: 0.85",
      "duration_ms": 1567,
      "status": "success",
      "timestamp": "2026-03-06T10:00:01.357Z"
    }
    /* ... more steps ... */
  ]
}
```

---

## 5. Health Check

### GET /api/v1/health

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 12345,
  "checks": {
    "database": "ok",
    "fhir_connection": "ok",
    "llm_service": "ok"
  }
}
```

---

## Data Models

### PatientTwin
```typescript
interface PatientTwin {
  patient_id: string;
  synthetic_flag: boolean;
  demographics: {
    age: number;
    sex: string;
  };
  active_conditions: Condition[];
  active_medications: Medication[];
  recent_labs: Observation[];
  recent_vitals: Observation[];
  risk_factors: string[];
  care_gaps: string[];
  completeness_score: number;
  data_freshness: {
    labs_last_updated: string;
    vitals_last_updated: string;
    medications_last_updated: string;
  };
}
```

### ScenarioDefinition
```typescript
interface ScenarioDefinition {
  scenario_id: string;
  label: string;
  intervention_type: 'medication' | 'lifestyle' | 'monitoring' | 'combined';
  parameters: Record<string, any>;
  assumptions: string[];
  time_horizon_months: number;
}
```

### ScenarioResult
```typescript
interface ScenarioResult {
  scenario_id: string;
  label: string;
  rank: number;
  risk_projection: {
    direction: 'improved' | 'stable' | 'worsened';
    magnitude: 'small' | 'moderate' | 'large';
    confidence: 'low' | 'moderate' | 'high';
    rationale: string;
  };
  medication_impact: {
    burden_score: number;
    interaction_warnings: string[];
    adherence_complexity: 'low' | 'moderate' | 'high';
  };
  guideline_alignment: {
    alignment_score: number;
    evidence_strength: 'weak' | 'moderate' | 'strong';
    references: string[];
  };
  safety_flags: string[];
  uncertainty_notes: string[];
}
```

---

## Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| INVALID_CONTEXT | Missing or malformed SHARP context | 400 |
| PATIENT_NOT_FOUND | Patient ID not found in FHIR server | 404 |
| FHIR_ERROR | FHIR server error or timeout | 502 |
| AGENT_TIMEOUT | One or more agents timed out | 504 |
| INSUFFICIENT_DATA | Not enough data to run simulation | 422 |
| SAFETY_BLOCK | Scenario blocked by safety agent | 403 |
| INTERNAL_ERROR | Unexpected server error | 500 |

---

**Status:** Design phase  
**Next:** OpenAPI specification generation
