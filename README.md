# TwinCare AI — Digital Twin Healthcare Simulator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.0+-61DAFB.svg)](https://reactjs.org/)

A multi-agent healthcare simulation system that creates a patient-specific digital twin from FHIR data, runs what-if treatment scenarios, and returns explainable outcome projections inside the Prompt Opinion platform.

## Project Overview

**Hackathon:** Agents Assemble - Healthcare AI Endgame  
**Submission Path:** A2A Agent on Prompt Opinion  
**Focus Area:** Type 2 Diabetes + Cardiometabolic Risk  
**Deadline:** May 11, 2026  
**Repository:** https://github.com/vaish725/TwinCareAI

## Project Status

**Current Phase:** Phase 1 - Foundation & Architecture  
**Completed:** Day 1-2 (Mar 6-7, 2026)  
**Next:** Days 3-5 - Data & FHIR Foundation

### Completed Milestones
- Git repository initialized and pushed to GitHub
- Project structure created (backend, frontend, docs)
- Development tools configured (Python, Node.js, CI/CD)
- Complete architecture documentation
- 9-agent topology designed and specified
- Database schema finalized
- Agent communication protocol defined
- Error handling strategy documented
- API contracts defined
- Comprehensive platform research completed
- SHARP context propagation specifications documented
- A2A agent registration requirements defined
- Prompt Opinion Marketplace integration strategy established

## Architecture

### Tech Stack

**Frontend:**
- React 18+ with TypeScript
- Tailwind CSS + shadcn/ui
- Vite (build tool)
- State management: Context API/Zustand

**Backend:**
- Python 3.11+ with FastAPI
- Pydantic for data validation
- Async/await architecture
- SQLite (development) / PostgreSQL (production)

**Agents:**
- 9 specialized agents orchestrated via A2A
- Optional MCP server for enhanced interoperability
- FHIR R4 data integration
- SHARP context propagation

### Agent Topology

1. **Context Intake Agent** - FHIR context resolution
2. **Clinical State Builder Agent** - Digital twin construction
3. **Scenario Generator Agent** - Treatment scenario creation
4. **Risk Projection Agent** - Outcome simulation
5. **Medication Impact Agent** - Drug interaction analysis
6. **Guideline Alignment Agent** - Clinical guideline validation
7. **Safety Guardrail Agent** - Safety enforcement
8. **Explanation Agent** - Natural language summaries
9. **Consensus Agent** - Result aggregation

## 📁 Project Structure

```
TwinCareAI/
├── backend/                 # Python/FastAPI backend
│   ├── agents/             # Agent implementations
│   ├── models/             # Pydantic data models
│   ├── services/           # FHIR, orchestration services
│   ├── api/                # API endpoints
│   ├── tests/              # Unit & integration tests
│   └── main.py             # Application entry point
├── frontend/               # React/TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Screen layouts
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
│   └── public/
├── docs/                   # Documentation
│   ├── architecture/      # Architecture diagrams
│   ├── agents/            # Agent specifications
│   └── api/               # API documentation
├── .github/workflows/      # CI/CD pipelines
├── prd.md                 # Product Requirements Document
├── PROJECT_TIMELINE.md    # Development timeline
└── README.md              # This file
```

##  Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git
- Docker (optional)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Key Links

- **PRD:** [prd.md](./prd.md)
- **Timeline:** [PROJECT_TIMELINE.md](./PROJECT_TIMELINE.md)
- **Architecture:** [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- **Agent Topology:** [docs/AGENT_TOPOLOGY.md](./docs/AGENT_TOPOLOGY.md)
- **Prompt Opinion:** [https://promptopinion.com](https://promptopinion.com)
- **SHARP on MCP:** [https://sharponmcp.com](https://sharponmcp.com)
- **Hackathon:** [https://agents-assemble.devpost.com](https://agents-assemble.devpost.com)

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## Success Metrics

- Integrated into Prompt Opinion
- Published to Marketplace
- End-to-end latency under 15 seconds
- All 9 agents functional
- Demo video under 3 minutes
- Synthetic data only

## Safety & Compliance

**CRITICAL:** This system uses **SYNTHETIC DATA ONLY**. No real PHI is permitted.

- All outputs include safety disclaimers
- No autonomous prescriptions or diagnoses
- Explicit uncertainty communication
- Missing data transparency
- For simulation/decision support only

## Team

- **Project Manager:** Timeline, coordination, demo
- **Tech Lead:** Architecture, orchestration
- **Backend Team:** Python, agents, FHIR
- **Frontend Team:** React, UI/UX
- **DevOps:** Deployment, CI/CD

## License

MIT License - See LICENSE file for details

## Contributing

This is a hackathon project. For questions or collaboration, please open an issue.

---

**Built for Agents Assemble Hackathon 2026**  
*Interoperable Healthcare Agents at the Intersection of MCP, A2A, and FHIR*
