# TwinCare AI - Database Schema

**Version:** 0.1.0  
**Date:** March 6, 2026  
**Status:** Finalized

---

## Overview

This document defines the complete database schema for TwinCare AI, including tables, relationships, indexes, and migration strategy.

---

## Database Technology

- **Development:** SQLite 3.x
- **Production:** PostgreSQL 14+
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic

---

## Entity Relationship Diagram

```
┌─────────────────┐
│    sessions     │
│─────────────────│
│ id (PK)         │───┐
│ patient_id      │   │
│ created_at      │   │
│ updated_at      │   │
│ status          │   │
│ context         │   │
│ results         │   │
│ execution_time  │   │
│ error_message   │   │
└─────────────────┘   │
                      │ 1:N
                      │
        ┌─────────────┴─────────────┬─────────────────┐
        │                           │                 │
        ▼                           ▼                 ▼
┌─────────────────┐    ┌─────────────────┐   ┌──────────────┐
│     traces      │    │    scenarios    │   │patient_twins │
│─────────────────│    │─────────────────│   │──────────────│
│ id (PK)         │    │ id (PK)         │   │ id (PK)      │
│ session_id (FK) │    │ session_id (FK) │   │ session_id(FK)│
│ step_number     │    │ scenario_id     │   │ patient_id   │
│ agent_name      │    │ label           │   │ twin_state   │
│ input_summary   │    │ rank            │   │ completeness │
│ output_summary  │    │ definition      │   │ created_at   │
│ duration_ms     │    │ result          │   └──────────────┘
│ status          │    │ created_at      │
│ timestamp       │    └─────────────────┘
│ metadata        │
└─────────────────┘
```

---

## Table Definitions

### 1. sessions

**Purpose:** Store session metadata and final results

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    context JSONB,
    results JSONB,
    execution_time_ms INTEGER,
    error_message TEXT,
    
    -- Indexes
    CONSTRAINT sessions_status_check 
        CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'timeout'))
);

CREATE INDEX idx_sessions_patient_id ON sessions(patient_id);
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
```

**Columns:**
- `id`: Unique session identifier (UUID)
- `patient_id`: Patient identifier from SHARP context
- `created_at`: Session creation timestamp
- `updated_at`: Last update timestamp
- `status`: Current session status
- `context`: SHARP context (FHIR tokens redacted), JSONB
- `results`: Final simulation results, JSONB
- `execution_time_ms`: Total execution time
- `error_message`: Error details if failed

**Example Row:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_id": "synthetic-001",
  "created_at": "2026-03-06T10:00:00Z",
  "updated_at": "2026-03-06T10:00:12Z",
  "status": "completed",
  "context": {
    "session_id": "...",
    "patient_context": {"patient_id": "synthetic-001"},
    "requesting_agent": "prompt-opinion"
  },
  "results": {
    "patient_twin": {...},
    "scenarios": [...],
    "ranked_results": [...]
  },
  "execution_time_ms": 12450,
  "error_message": null
}
```

---

### 2. traces

**Purpose:** Store agent execution trace for debugging and transparency

```sql
CREATE TABLE traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    duration_ms INTEGER,
    status VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    -- Constraints
    CONSTRAINT traces_status_check 
        CHECK (status IN ('success', 'partial', 'failed', 'timeout', 'skipped')),
    CONSTRAINT traces_step_unique UNIQUE (session_id, step_number)
);

CREATE INDEX idx_traces_session_id ON traces(session_id);
CREATE INDEX idx_traces_agent_name ON traces(agent_name);
CREATE INDEX idx_traces_status ON traces(status);
CREATE INDEX idx_traces_timestamp ON traces(timestamp DESC);
```

**Columns:**
- `id`: Unique trace record ID
- `session_id`: Foreign key to sessions
- `step_number`: Sequential step in execution
- `agent_name`: Name of agent (e.g., "Risk Projection Agent")
- `input_summary`: Brief input description
- `output_summary`: Brief output description
- `duration_ms`: Agent execution time
- `status`: Execution status
- `timestamp`: Execution timestamp
- `metadata`: Additional data (JSONB)

**Example Row:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "step_number": 4,
  "agent_name": "Risk Projection Agent",
  "input_summary": "PatientTwin + Scenario 2 (Intensification)",
  "output_summary": "Risk delta: improved (moderate confidence)",
  "duration_ms": 2100,
  "status": "success",
  "timestamp": "2026-03-06T10:00:05.234Z",
  "metadata": {
    "tier_1_score": 0.7,
    "tier_2_score": 0.8,
    "tier_3_used": true
  }
}
```

---

### 3. scenarios

**Purpose:** Store scenario definitions and results

```sql
CREATE TABLE scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    scenario_id VARCHAR(50) NOT NULL,
    label VARCHAR(255) NOT NULL,
    rank INTEGER,
    definition JSONB NOT NULL,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT scenarios_rank_check CHECK (rank >= 1 AND rank <= 10),
    CONSTRAINT scenarios_scenario_id_unique UNIQUE (session_id, scenario_id)
);

CREATE INDEX idx_scenarios_session_id ON scenarios(session_id);
CREATE INDEX idx_scenarios_rank ON scenarios(rank);
```

**Columns:**
- `id`: Unique scenario record ID
- `session_id`: Foreign key to sessions
- `scenario_id`: Scenario identifier (e.g., "scenario-1")
- `label`: Human-readable label
- `rank`: Final ranking (1=best)
- `definition`: Scenario parameters (JSONB)
- `result`: Simulation results (JSONB)
- `created_at`: Creation timestamp

**Example Row:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_id": "scenario-2",
  "label": "Medication Intensification",
  "rank": 1,
  "definition": {
    "intervention_type": "medication",
    "parameters": {
      "add_medication": "GLP-1 agonist"
    },
    "assumptions": ["85% adherence"]
  },
  "result": {
    "risk_projection": {...},
    "medication_impact": {...},
    "guideline_alignment": {...},
    "confidence": "moderate"
  },
  "created_at": "2026-03-06T10:00:03Z"
}
```

---

### 4. patient_twins

**Purpose:** Cache patient twin states for reuse

```sql
CREATE TABLE patient_twins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    patient_id VARCHAR(255) NOT NULL,
    twin_state JSONB NOT NULL,
    completeness_score DECIMAL(3, 2),
    missing_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT patient_twins_completeness_check 
        CHECK (completeness_score >= 0 AND completeness_score <= 1)
);

CREATE INDEX idx_patient_twins_patient_id ON patient_twins(patient_id);
CREATE INDEX idx_patient_twins_created_at ON patient_twins(created_at DESC);
CREATE INDEX idx_patient_twins_expires_at ON patient_twins(expires_at);
```

**Columns:**
- `id`: Unique twin record ID
- `session_id`: Foreign key to sessions
- `patient_id`: Patient identifier
- `twin_state`: Complete PatientTwin object (JSONB)
- `completeness_score`: Data completeness (0-1)
- `missing_data`: List of missing fields (JSONB)
- `created_at`: Creation timestamp
- `expires_at`: Cache expiration (optional)

**Example Row:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_id": "synthetic-001",
  "twin_state": {
    "patient_id": "synthetic-001",
    "demographics": {"age": 56, "sex": "M"},
    "conditions": [...],
    "medications": [...],
    "labs": [...],
    "vitals": [...]
  },
  "completeness_score": 0.85,
  "missing_data": ["lipid_panel", "recent_hba1c"],
  "created_at": "2026-03-06T10:00:02Z",
  "expires_at": "2026-03-06T22:00:00Z"
}
```

---

## Additional Tables (Optional/Future)

### 5. agent_metrics

**Purpose:** Store agent performance metrics

```sql
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 2),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_agent_metrics_agent_name ON agent_metrics(agent_name);
CREATE INDEX idx_agent_metrics_recorded_at ON agent_metrics(recorded_at DESC);
```

**Metrics Tracked:**
- Average execution time
- Success rate
- Timeout frequency
- Confidence distribution

---

### 6. api_audit_log

**Purpose:** Audit API access

```sql
CREATE TABLE api_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    request_ip VARCHAR(45),
    user_agent TEXT,
    request_body_hash VARCHAR(64),
    response_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_timestamp ON api_audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_endpoint ON api_audit_log(endpoint);
```

---

## SQLAlchemy Models

### sessions model

```python
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), nullable=False, default='pending', index=True)
    context = Column(JSONB)
    results = Column(JSONB)
    execution_time_ms = Column(Integer)
    error_message = Column(Text)
    
    # Relationships
    traces = relationship("Trace", back_populates="session", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="session", cascade="all, delete-orphan")
    patient_twin = relationship("PatientTwin", back_populates="session", uselist=False)
```

### traces model

```python
class Trace(Base):
    __tablename__ = 'traces'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    agent_name = Column(String(100), nullable=False, index=True)
    input_summary = Column(Text)
    output_summary = Column(Text)
    duration_ms = Column(Integer)
    status = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSONB)
    
    # Relationships
    session = relationship("Session", back_populates="traces")
```

---

## Indexes Strategy

### Primary Indexes (Already Defined)
- All primary keys
- Foreign keys
- Common query fields (patient_id, created_at, status)

### Composite Indexes (Add if needed)

```sql
-- Fast session lookup by patient and time
CREATE INDEX idx_sessions_patient_time 
ON sessions(patient_id, created_at DESC);

-- Fast trace retrieval by session and step
CREATE INDEX idx_traces_session_step 
ON traces(session_id, step_number);

-- Fast scenario ranking
CREATE INDEX idx_scenarios_session_rank 
ON scenarios(session_id, rank);
```

---

## Data Retention Policy

### Development
- Keep all data indefinitely

### Production
- **Sessions:** Retain for 90 days
- **Traces:** Retain for 30 days
- **Scenarios:** Retain for 90 days
- **Patient Twins:** Cache for 12 hours, then delete
- **Audit Logs:** Retain for 1 year

### Cleanup Job (Example)

```sql
-- Delete old sessions and cascaded data
DELETE FROM sessions 
WHERE created_at < NOW() - INTERVAL '90 days' 
  AND status IN ('completed', 'failed');

-- Delete expired twin caches
DELETE FROM patient_twins 
WHERE expires_at < NOW();
```

---

## Migration Strategy

### Initial Migration (v1)

```python
# alembic/versions/001_initial_schema.py

def upgrade():
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('patient_id', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        # ... rest of columns
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_sessions_patient_id', 'sessions', ['patient_id'])
    # ... rest of indexes
    
    # Repeat for other tables
```

### Running Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Query Examples

### 1. Get Session with All Data

```python
from sqlalchemy.orm import selectinload

session = await db.execute(
    select(Session)
    .options(
        selectinload(Session.traces),
        selectinload(Session.scenarios),
        selectinload(Session.patient_twin)
    )
    .where(Session.id == session_id)
)
```

### 2. Get Recent Sessions for Patient

```sql
SELECT * FROM sessions 
WHERE patient_id = 'synthetic-001'
ORDER BY created_at DESC 
LIMIT 10;
```

### 3. Get Agent Performance Stats

```sql
SELECT 
    agent_name,
    COUNT(*) as executions,
    AVG(duration_ms) as avg_duration,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
FROM traces
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY agent_name
ORDER BY avg_duration DESC;
```

### 4. Get Session Trace Timeline

```sql
SELECT 
    step_number,
    agent_name,
    duration_ms,
    status,
    timestamp
FROM traces
WHERE session_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY step_number;
```

---

## Backup Strategy

### Development
- SQLite file backup: Daily

### Production
- **PostgreSQL:** Continuous WAL archiving
- **Point-in-time recovery:** Enabled
- **Backup retention:** 30 days
- **Backup location:** S3 or equivalent

---

## Security Considerations

### Data Protection
-  No real PHI stored
-  FHIR tokens redacted in context field
-  Patient IDs are synthetic only
-  Audit logging for access

### Access Control
- Database user with minimal privileges
- Read-only user for analytics
- No direct database access from frontend

### Encryption
- Encryption at rest (database level)
- TLS for database connections
- Sensitive fields encrypted in JSONB

---

**Document Status:** Finalized  
**Next Review:** March 12, 2026  
**Database Version:** v1.0
