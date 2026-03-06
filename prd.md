# Product Requirements Document

## Product Name

**TwinCare AI — Digital Twin Healthcare Simulator**

## One-line summary

A multi-agent healthcare simulation system that creates a patient-specific digital twin from FHIR data, runs what-if treatment scenarios, and returns explainable outcome projections inside the Prompt Opinion platform.

## Product thesis

Clinicians and care teams often know a patient’s current state, but struggle to quickly estimate how outcomes may differ under alternate interventions such as medication changes, delayed follow-up, lab rechecks, or lifestyle adherence. TwinCare AI turns structured FHIR context into a simulated “digital twin” and allows interoperable agents to collaborate on future-state projections that traditional static rule engines cannot easily provide. This directly targets the hackathon’s emphasis on turning AI into actionable deliverables through MCP, A2A, and FHIR-based collaboration. ([Agents Assemble][1])

---

# 1. Hackathon alignment

## 1.1 Required technical path

**Primary submission path:** **A2A Agent** on Prompt Opinion.
Reason: the core value is an orchestrated multi-agent workflow around a healthcare use case, and Prompt Opinion explicitly supports agent development on-platform while handling much of the underlying A2A communication. ([Agents Assemble][1])

## 1.2 Optional bonus architecture

Add one small **MCP “superpower” server** as a supporting toolset, not as the primary entry path:

* `simulate_risk_projection`
* `fetch_patient_context_bundle`
* `compare_treatment_scenarios`
* `generate_explanation_trace`

This helps demonstrate interoperability and makes the project stronger for Marketplace discoverability while still keeping the main submission clear and feasible. The hackathon allows either path, and Prompt Opinion supports agents connecting to MCP servers and other agents. ([Agents Assemble][2])

## 1.3 Hard submission constraints reflected in this PRD

The product **must**:

* integrate into Prompt Opinion
* be published to the Prompt Opinion Marketplace
* be discoverable and invokable in the platform
* function exactly as shown in the demo video
* use only synthetic or de-identified data
* include a public demo video under 3 minutes
* include a project description and Marketplace URL in the Devpost submission ([Agents Assemble][2])

## 1.4 Judging-criteria mapping

**AI Factor:** scenario simulation, explanation, and agent debate over projected outcomes are not just rule lookups. ([Agents Assemble][2])
**Potential Impact:** supports treatment planning, preventive care, and care coordination by reducing uncertainty and highlighting tradeoffs. ([Agents Assemble][2])
**Feasibility:** uses FHIR context, synthetic data, constrained scope, explicit disclaimers, safety guardrails, and explainable outputs to fit real-world healthcare constraints. ([Agents Assemble][2])

---

# 2. Problem statement

Healthcare workflows are rich in current-state data but weak in fast, interactive future-state reasoning. Clinicians frequently ask:

* What happens if we intensify therapy?
* What happens if follow-up is delayed?
* What happens if adherence improves?
* Which scenario most reduces near-term risk?

Existing systems are often static alerts, guideline popups, or retrospective dashboards. They do not present collaborative, patient-specific, explainable simulations from interoperable agents using standardized healthcare context.

TwinCare AI addresses this gap by:

1. ingesting patient context from FHIR,
2. constructing a structured digital twin state,
3. running multiple scenario simulations,
4. returning ranked outcome comparisons with rationale and safety notes.

---

# 3. Goals and non-goals

## 3.1 Goals

* Build an interoperable healthcare AI agent that works inside Prompt Opinion.
* Use FHIR context and SHARP-style context propagation.
* Demonstrate clear multi-agent collaboration.
* Produce useful scenario comparisons for a single patient.
* Make the product demoable in under 3 minutes.
* Keep the system realistic enough to satisfy feasibility and safety expectations. ([Agents Assemble][1])

## 3.2 Non-goals

* No diagnosis generation as a final authoritative clinical judgment.
* No autonomous order placement or medication execution.
* No claims of FDA-cleared predictive performance.
* No production EHR write-back in hackathon scope.
* No real PHI. Synthetic/de-identified only. ([Agents Assemble][2])

---

# 4. Users

## Primary users

* clinician demo user inside Prompt Opinion
* care manager
* utilization review / population health analyst
* digital health evaluator or hackathon judge

## Secondary users

* agent developers exploring interoperable healthcare workflows
* health system innovation teams
* payer/provider workflow designers

---

# 5. Core use cases

## Use case A: Treatment intensification comparison

A clinician selects a patient and compares:

* current treatment
* medication intensification
* lifestyle intervention
* delayed intervention

Output:

* projected short-term and medium-term risk changes
* explanation of assumptions
* confidence tier
* missing-data warnings

## Use case B: Preventive care planning

A care manager asks:

* what likely risk reduction occurs if HbA1c improves?
* what if statin adherence improves?
* what if follow-up is missed?

## Use case C: Shared decision support

The agent produces plain-language scenario summaries for discussion:

* “Scenario B may reduce projected 12-month cardiovascular risk relative to current therapy, but confidence is limited because recent lipid labs are missing.”

## Use case D: Multi-agent consultation

An orchestration agent calls specialist agents:

* risk projection
* medication reasoning
* guideline alignment
* explanation and safety

---

# 6. Product concept

TwinCare AI creates a **digital twin** as a structured internal patient model, then simulates multiple future scenarios. It does not claim mechanistic physiological simulation. In hackathon scope, “digital twin” means a **patient-specific computational representation** built from standardized clinical facts, temporal events, and modeled assumptions.

The twin includes:

* demographics
* conditions
* medications
* vitals
* labs
* recent encounters
* adherence assumptions
* risk factors
* care gaps
* scenario modifiers

The system then compares scenario outcomes such as:

* estimated risk trend
* likely adherence burden
* care pathway implications
* escalation flags
* recommended next questions

---

# 7. Product architecture

## 7.1 High-level architecture

**Frontend UI**
→ **TwinCare Orchestrator Agent (A2A agent on Prompt Opinion)**
→ specialist agents and/or MCP tools
→ FHIR data source + simulation engine
→ final response card + scenario comparison + explanation

## 7.2 Agent topology

1. **Context Intake Agent**
   Resolves patient ID, FHIR token/context, and gathers needed resources.

2. **Clinical State Builder Agent**
   Converts FHIR bundle into normalized twin state.

3. **Scenario Generator Agent**
   Builds valid intervention scenarios based on available data.

4. **Risk Projection Agent**
   Estimates directional changes and simplified outcome projections.

5. **Medication Impact Agent**
   Evaluates medication changes, contraindication cues, and burden tradeoffs.

6. **Guideline Alignment Agent**
   Checks whether scenario ideas align broadly with accepted care pathways.

7. **Safety Guardrail Agent**
   Blocks unsafe overclaiming, flags missing data, injects disclaimers.

8. **Explanation Agent**
   Produces clinician-facing and patient-facing summaries.

9. **Consensus / Report Agent**
   Combines outputs into a final ranked scenario report.

This structure directly demonstrates collaborative AI rather than a single monolithic chatbot, which matches the hackathon’s emphasis on collaboration and interoperable agents. ([Agents Assemble][1])

## 7.3 Optional MCP tool layer

Possible MCP endpoints:

* `get_patient_bundle(patient_id, context)`
* `extract_recent_labs(bundle)`
* `simulate_scenario(twin_state, scenario_definition)`
* `compare_scenarios(results)`
* `generate_audit_trace(result_id)`

SHARP-on-MCP is meant to enable reusable remote healthcare services leveraging FHIR and consistent communication patterns for pluggable agent services. ([sharponmcp.com][3])

---

# 8. Frontend PRD

## 8.1 Frontend principles

The UI must be:

* fast to understand in a demo
* constrained to avoid unsafe free-form use
* explicit about simulation assumptions
* visually clear enough for a 3-minute video

## 8.2 Main screens

### Screen 1: Launch / patient selection

Features:

* patient picker or synthetic patient ID input
* “load patient context” button
* visible synthetic-data badge
* FHIR connection status
* Prompt Opinion invocation context banner

States:

* loading
* invalid patient
* FHIR auth/context missing
* success

### Screen 2: Patient twin overview

Features:

* summary card: age, sex, conditions, meds, latest vitals, latest labs
* missing data indicators
* data freshness badges
* confidence meter for twin completeness
* “build scenarios” CTA

### Screen 3: Scenario workspace

Features:

* prebuilt scenario templates:

  * continue current treatment
  * intensify medication
  * add lifestyle intervention
  * delayed follow-up
  * improve adherence
* advanced scenario editor:

  * change medication class
  * change adherence assumption
  * add monitoring cadence
  * adjust follow-up interval
* max of 3 side-by-side scenarios for clarity

Validation:

* cannot create impossible scenarios
* cannot claim unsupported medication changes if required data missing
* must show assumptions before run

### Screen 4: Simulation results

Features:

* ranked scenarios
* relative risk direction arrows
* projected outcome cards
* explanation panel
* confidence and evidence notes
* “why this changed” expandable section
* safety warnings section
* “not a medical diagnosis / demo use only” persistent notice

### Screen 5: Agent trace view

Features:

* timeline of agent contributions
* collapsed/expanded messages
* which agent used which tool
* FHIR resources referenced
* final consensus trace

This is crucial for demonstrating both interoperability and explainability.

### Screen 6: Export / share

Features:

* export report as markdown/pdf-lite
* copy summary to clipboard
* generate shareable demo link if supported
* link to Marketplace listing

## 8.3 Frontend components

* PatientHeader
* DataFreshnessCard
* TwinCompletenessMeter
* ScenarioBuilder
* ScenarioCard
* ComparisonTable
* ConfidenceBadge
* SafetyNotice
* AgentTracePanel
* MissingDataAlert
* RecommendationSummary
* MarketplaceInfoFooter

## 8.4 Frontend edge cases

* patient bundle incomplete
* labs missing
* medication list empty
* unsupported condition profile
* agent timeout
* simulation failed for one scenario
* scenario comparison partially available
* token/context expired
* FHIR server unreachable
* duplicate user click / rerun

## 8.5 Accessibility and UX

* color plus icon for risk direction, not color alone
* keyboard navigable controls
* concise labels for demo
* patient-safe plain-language tab
* clinician tab with more detail

---

# 9. Backend PRD

## 9.1 Backend responsibilities

* accept invocation from Prompt Opinion
* resolve SHARP/FHIR context
* fetch synthetic FHIR resources
* normalize data into twin state
* orchestrate agents
* run scenario simulations
* validate safety and confidence
* persist session results
* return structured response to UI/platform

## 9.2 Backend modules

### A. Context adapter

Responsibilities:

* parse incoming Prompt Opinion / SHARP context
* extract patient ID and FHIR token if present
* attach invocation metadata
* validate required context
* mask/log safely

### B. FHIR ingestion service

FHIR resources in scope:

* Patient
* Condition
* MedicationRequest / MedicationStatement
* Observation
* Encounter
* CarePlan
* AllergyIntolerance
* Procedure, if useful
* ServiceRequest, optional

Responsibilities:

* fetch by patient and timeframe
* bundle normalization
* deduplicate observations
* choose latest clinically relevant values
* identify stale/missing data

### C. Twin state builder

Converts raw FHIR into:

```text
TwinState
- demographics
- active_conditions
- active_medications
- recent_labs
- recent_vitals
- encounter_history_summary
- risk_factor_vector
- adherence_assumptions
- care_gap_flags
- confidence_profile
```

### D. Scenario engine

Accepts:

* base twin state
* scenario definition
* simulation horizon

Produces:

* projected directional outcome
* relative risk movement
* caution notes
* uncertainty estimate
* rationale chain

### E. Multi-agent orchestrator

Responsible for:

* agent sequencing
* retries
* timeout handling
* result fusion
* conflict resolution
* trace generation

### F. Safety and policy layer

Responsible for:

* disallowing unsupported claims
* preventing treatment directives from being framed as final medical advice
* requiring disclaimer injection
* flagging missing evidence
* limiting output to comparison support

### G. Results store

Stores:

* session metadata
* scenario definitions
* projection outputs
* trace summaries
* audit log
* non-PHI synthetic identifiers only

---

# 10. Backend logic in detail

## 10.1 Invocation flow

1. Prompt Opinion invokes TwinCare AI.
2. Context adapter reads SHARP-like healthcare context including patient identifiers and FHIR access context.
3. Backend validates synthetic-demo mode.
4. FHIR ingestion retrieves patient bundle.
5. Twin state builder produces normalized patient twin.
6. Scenario generator proposes 3 valid scenarios.
7. Orchestrator dispatches specialist agents.
8. Consensus agent ranks scenarios.
9. Safety layer finalizes output.
10. Result returned to Prompt Opinion and rendered in UI.

Prompt Opinion explicitly calls for SHARP Extension Specs to handle healthcare context such as patient IDs and FHIR tokens through multi-agent call chains. ([Agents Assemble][1])

## 10.2 Scenario simulation logic

For hackathon scope, use a **tiered simulation approach**:

### Tier 1: deterministic transforms

Examples:

* more frequent monitoring lowers uncertainty but not direct risk
* recent abnormal labs increase near-term concern score
* poor adherence assumption worsens projected trajectory

### Tier 2: retrieval + guideline-informed heuristics

Examples:

* diabetes intensification may improve projected metabolic control scenario
* missed follow-up may increase unresolved-risk burden
* statin adherence improvement may lower projected cardiovascular risk directionally

### Tier 3: generative reasoning

LLM synthesizes:

* why scenario B is preferable to scenario A
* which assumptions most drive uncertainty
* what additional data would improve confidence

This mix helps satisfy the AI Factor while keeping enough structure for feasibility. ([Agents Assemble][2])

## 10.3 Consensus logic

If agents disagree:

* record disagreements explicitly
* show majority rationale
* show “requires more data” status when conflict is unresolved
* never suppress major safety disagreement

## 10.4 Confidence logic

Confidence score derives from:

* twin completeness
* recency of labs
* condition-model support
* scenario realism
* cross-agent agreement

Buckets:

* High
* Moderate
* Low
* Insufficient data

## 10.5 Missing data logic

If key data absent:

* still produce report if possible
* downgrade confidence
* prominently list missing fields
* recommend next data needed, not next treatment only

Example:

* missing A1c in last 6 months
* missing blood pressure trend
* medication adherence unknown

---

# 11. Data model

## Core entities

### PatientTwin

* `patient_id`
* `synthetic_flag`
* `demographics`
* `conditions[]`
* `medications[]`
* `labs[]`
* `vitals[]`
* `encounters[]`
* `risk_factors[]`
* `care_gaps[]`
* `completeness_score`

### ScenarioDefinition

* `scenario_id`
* `label`
* `intervention_type`
* `parameter_changes`
* `time_horizon`
* `assumptions[]`

### ScenarioResult

* `scenario_id`
* `risk_delta_summary`
* `outcome_projection_summary`
* `uncertainty_notes[]`
* `safety_flags[]`
* `guideline_notes[]`
* `confidence_bucket`
* `agent_trace_refs[]`

### AgentTrace

* `step_id`
* `agent_name`
* `input_summary`
* `tool_calls[]`
* `output_summary`
* `duration_ms`
* `status`

---

# 12. Agent specifications

## 12.1 Context Intake Agent

Inputs:

* patient ID
* SHARP/FHIR context
  Outputs:
* validated context object
* resource fetch plan

Failure modes:

* missing patient
* expired token
* unsupported context format

## 12.2 Clinical State Builder Agent

Inputs:

* FHIR bundle
  Outputs:
* TwinState
* missing-data report

## 12.3 Scenario Generator Agent

Inputs:

* TwinState
  Outputs:
* 3 scenario candidates
* assumptions for each

Rules:

* keep scenarios clinically plausible
* avoid over-broad exploration
* prefer demo-friendly scenarios

## 12.4 Risk Projection Agent

Inputs:

* TwinState, scenario
  Outputs:
* directional projection
* rationale
* uncertainty

## 12.5 Medication Impact Agent

Inputs:

* active meds, scenario med changes
  Outputs:
* burden/interaction notes
* caution flags

## 12.6 Guideline Alignment Agent

Inputs:

* condition profile, scenario
  Outputs:
* broad consistency notes
* evidence strength wording
* no false certainty

## 12.7 Safety Guardrail Agent

Inputs:

* all agent outputs
  Outputs:
* approved / revise / block
* disclaimer additions
* red flags

## 12.8 Consensus Agent

Inputs:

* all specialist outputs
  Outputs:
* ranked scenarios
* final comparison narrative

---

# 13. API and tool design

## 13.1 Internal endpoints

* `POST /invoke`
* `POST /build-twin`
* `POST /generate-scenarios`
* `POST /simulate`
* `POST /compare`
* `GET /session/{id}`
* `GET /trace/{id}`

## 13.2 MCP tools

* `fetch_patient_context`
* `build_digital_twin`
* `run_scenario_projection`
* `compare_scenario_outcomes`
* `explain_projection`

## 13.3 Response format

All responses should be structured JSON-first, with a rendered natural-language layer on top. This improves A2A composability and Marketplace robustness.

---

# 14. FHIR and SHARP requirements

## 14.1 FHIR usage

FHIR use is not mandatory by the rules but is highly recommended, and this project should use it centrally because the whole product value depends on patient-context simulation. ([Agents Assemble][1])

## 14.2 SHARP context propagation

The system should pass:

* patient identifier
* FHIR endpoint reference
* token or token handle
* invocation/session metadata
* minimal necessary context between agents

This directly aligns with Prompt Opinion’s stated SHARP context propagation model and the broader SHARP-on-MCP idea of pluggable remote healthcare services built on consistent patterns for accessing FHIR-linked context. ([Agents Assemble][1])

## 14.3 Minimum FHIR demo bundle

For the demo, ensure one or two synthetic patients have:

* chronic condition profile
* recent labs
* active medications
* at least one recent encounter
* enough data for scenario variation

---

# 15. Safety, privacy, and compliance

## 15.1 Hard safety requirement

Only synthetic or de-identified data may be used. Real PHI is grounds for immediate disqualification. ([Agents Assemble][2])

## 15.2 Product safety principles

* never present output as definitive clinical advice
* always display uncertainty and assumptions
* require explicit “for simulation / decision support only” notice
* list missing data that could materially change result
* no autonomous prescription or diagnosis wording
* do not fabricate evidence citations

## 15.3 Prompt safety rules

The LLM should be instructed to:

* avoid certainty claims
* avoid hallucinated numbers when unsupported
* prefer comparative language
* escalate ambiguity
* state when a scenario is not valid

## 15.4 Logging rules

* no raw sensitive free text beyond demo-safe synthetic content
* structured logs only
* redact tokens
* store trace summaries, not unnecessary payloads

---

# 16. Frontend-feature requirements list

## Must-have

* patient selection
* twin overview
* scenario builder
* compare up to 3 scenarios
* result ranking
* safety disclaimer
* missing-data alerts
* agent trace
* Marketplace metadata footer

## Should-have

* plain-language mode
* export summary
* confidence visualization
* scenario presets by condition type

## Nice-to-have

* animated twin timeline
* multi-patient batch mode
* sandbox mode for changing lab assumptions manually

---

# 17. Backend-feature requirements list

## Must-have

* Prompt Opinion invocation handler
* FHIR bundle ingestion
* twin-state construction
* 3-scenario simulation
* multi-agent orchestration
* guardrail filtering
* trace generation
* marketplace-ready discoverability metadata

## Should-have

* retry logic
* caching of fetched synthetic bundles
* async simulation jobs
* confidence scoring framework

## Nice-to-have

* pluggable model providers
* alternate simulation templates
* side-by-side patient explanation view

---

# 18. Failure cases and edge cases

## Data-related

* no recent labs
* multiple conflicting medication records
* condition missing code
* observations missing units
* duplicate encounters
* sparse patient history

## Workflow-related

* Prompt Opinion invocation missing context
* MCP tool unavailable
* one agent times out
* scenario 2 fails while 1 and 3 succeed
* Marketplace config broken
* UI can invoke but backend callback malformed

## Safety-related

* user asks for definitive treatment order
* user attempts unsupported scenario
* model output overstates certainty
* data pattern outside supported disease areas

## UX handling

Every failure should degrade gracefully with:

* partial output if safe
* clear banner
* retry option
* visible unsupported-state note

---

# 19. Scope control for hackathon

## In scope for v1

Target one condition cluster to keep the demo excellent:

* Type 2 diabetes + cardiovascular risk
  or
* hypertension + lipid management
  or
* chronic disease preventive care

Best recommendation: **Type 2 diabetes with cardiometabolic risk**, because it is easy to understand, has rich FHIR-friendly data, and supports clear what-if scenarios.

## Out of scope for v1

* oncology-grade longitudinal simulation
* ICU deterioration prediction
* complex inpatient medication titration
* pediatric dosing
* pregnancy-specific pathways

---

# 20. Demo script requirements

The video must be under 3 minutes and show the project functioning within Prompt Opinion. ([Agents Assemble][2])

## Recommended 3-minute narrative

1. “This is TwinCare AI inside Prompt Opinion.”
2. Open synthetic patient.
3. Show FHIR-derived twin summary.
4. Run three scenarios.
5. Show agents collaborating in trace view.
6. Show ranked results and safety/uncertainty notes.
7. End with Marketplace discoverability + why this matters.

## Demo patient example

Synthetic patient:

* age 56
* Type 2 diabetes
* hypertension
* BMI elevated
* on metformin and statin with partial adherence
* A1c recently high
* BP mildly uncontrolled

Scenarios:

* current therapy
* improved adherence + earlier follow-up
* therapy intensification + monitoring

This gives a crisp, understandable outcome story.

---

# 21. Marketplace and submission requirements

## Product must be ready for Marketplace validation

The rules require the project to be published to the Prompt Opinion Marketplace with a functioning configuration and to be discoverable/invokable in the platform. This is stage-one mandatory qualification, not optional polish. ([Agents Assemble][2])

## Submission package checklist

* project title and description
* Prompt Opinion Marketplace URL
* public demo video under 3 minutes
* proof of integration inside Prompt Opinion
* English materials
* testing instructions
* clear statement that synthetic/de-identified data only was used ([Agents Assemble][2])

---

# 22. Success metrics

## Hackathon success metrics

* passes technical qualification
* discoverable in Marketplace
* invokable within Prompt Opinion
* demo works exactly as shown
* clearly shows AI beyond rules
* clearly shows patient-impact story
* clearly shows safe architecture

## Product success metrics

* time to first simulation < 15 seconds on demo data
* three scenarios compared in one session
* visible trace from at least 4 agents
* missing-data detection works
* no unsafe definitive treatment language in final output

---

# 23. Suggested tech stack

Based on your background, this is a strong, feasible stack:

**Frontend**

* React + TypeScript
* Tailwind
* shadcn/ui
* lightweight charts for comparison

**Backend**

* Python + FastAPI
* Pydantic models for twin state and scenarios
* async orchestration

**Agents**

* Prompt Opinion A2A-native configuration for main workflow
* optional LangGraph-like local orchestration if needed behind the scenes

**FHIR**

* synthetic FHIR server or bundled synthetic FHIR data
* normalized resource-fetch layer

**Storage**

* SQLite or Postgres for sessions/traces

**Deployment**

* one small backend service
* one small frontend, unless Prompt Opinion-hosted UI pattern is enough

---

# 24. Open product decisions to finalize immediately

You should lock these before implementation:

1. **Primary condition area**: diabetes/cardiometabolic
2. **A2A as official path**: yes
3. **MCP add-on**: yes, but tiny
4. **Number of scenarios in demo**: 3
5. **Number of agents visible in trace**: 5 minimum
6. **Result style**: directional comparative, not absolute clinical prediction
7. **UI style**: clinician-first, with optional patient-friendly tab

---

# 25. Final product positioning statement

**TwinCare AI** is an interoperable healthcare simulation agent that uses FHIR context and SHARP-compatible context propagation to build a patient digital twin, coordinate specialist agents, and compare treatment scenarios inside the Prompt Opinion platform. It is designed to be Marketplace-publishable, demonstrably safe for hackathon use with synthetic data only, and aligned with the event’s requirements around MCP/A2A/FHIR interoperability, AI-enabled reasoning, and real-world healthcare feasibility. ([Agents Assemble][1])


[1]: https://agents-assemble.devpost.com/ "Agents Assemble - The Healthcare AI Endgame: Build Interoperable Healthcare Agents at the Intersection of MCP, A2A, and FHIR - Devpost"
[2]: https://agents-assemble.devpost.com/rules "Agents Assemble - The Healthcare AI Endgame: Build Interoperable Healthcare Agents at the Intersection of MCP, A2A, and FHIR - Devpost"
[3]: https://sharponmcp.com/overview "Standardized Healthcare Agent Remote Protocol (SHARP) | SHARP on MCP"
